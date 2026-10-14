"""Exercise the delivered MicroPython firmware with simulated USB/HTTP streams."""
import ast
import asyncio
import contextlib
import gc
import io
import json
from pathlib import Path
import sys
import time
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

def firmware():
    tree=ast.parse((ROOT/'ejemplos/chat_ollama/main.py').read_text())
    tree.body.pop()  # only the automatic hardware startup try/finally
    scope={}
    with patch.dict(sys.modules,{'network':types.ModuleType('network')}):
        exec(compile(tree,'main.py','exec'),scope)
    scope['ESTACION']=types.SimpleNamespace(isconnected=lambda:True)
    scope['MODO_RED']='Wi-Fi'
    scope['direccion_actual']=lambda:'192.168.0.4'
    return scope

class UsbFirmwareTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.env=firmware()
        self.patches=[patch.object(asyncio,'sleep_ms',lambda ms:asyncio.sleep(ms/1000),create=True),
                      patch.object(gc,'mem_free',lambda:100000,create=True),
                      patch.object(time,'ticks_ms',lambda:int(time.monotonic()*1000),create=True),
                      patch.object(time,'ticks_diff',lambda a,b:a-b,create=True)]
        for item in self.patches:item.start()

    async def asyncTearDown(self):
        for item in reversed(self.patches):item.stop()

    async def request(self,path,body=None):
        data=b'' if body is None else json.dumps(body,ensure_ascii=False).encode()
        request=(('GET' if body is None else 'POST')+' '+path+' HTTP/1.1\r\nContent-Length: '+str(len(data))+'\r\n\r\n').encode()+data
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            await self.env['atender'](self.env['LectorUSB'](request),self.env['EscritorUSB']('test'))
        frames=[json.loads(line[len('@EWSUSB:'):]) for line in output.getvalue().splitlines() if line.startswith('@EWSUSB:')]
        chunks=[frame for frame in frames if frame['kind']=='data']
        self.assertEqual([frame['seq'] for frame in chunks],list(range(len(chunks))))
        self.assertEqual(frames[-1]['kind'],'end')
        self.assertTrue(all(len(frame['hex'])<=256 for frame in chunks))
        response=b''.join(bytes.fromhex(frame['hex']) for frame in chunks)
        header,body=response.split(b'\r\n\r\n',1)
        self.assertIn(('Content-Length: '+str(len(body))).encode(),header)
        self.assertEqual(self.env['CLIENTES'],0)
        return header,json.loads(body)

    async def test_status_and_prepare_preserve_settings(self):
        header,state=await self.request('/api/status')
        self.assertIn(b'200 OK',header)
        self.assertEqual(state['usb_protocol'],1)
        _,data=await self.request('/api/prepare',{'model':'small','message':'¿Qué es Python?',
                      'system_prompt':'Docente','temperature':0.3,'top_p':0.8,'num_ctx':1024,
                      'max_tokens':64,'history_messages':1,'history':[{'role':'assistant','content':'Previo'}]})
        request=data['request']
        self.assertEqual(request['messages'][0]['content'],'Docente')
        self.assertEqual(request['messages'][1]['content'],'Previo')
        self.assertEqual(request['messages'][2]['content'],'¿Qué es Python?')
        self.assertEqual(request['options']['temperature'],0.3)
        self.assertFalse(request['stream'])

    async def test_wifi_routes_and_error_recovery(self):
        async def ollama(address,path,request=None):
            self.assertEqual(address,'192.168.0.2')
            return {'models':[{'name':'small'}]} if path=='/api/tags' else {'message':{'content':'¡Hola!'}}
        self.env['peticion_ollama']=ollama
        _,models=await self.request('/api/models',{'ollama_url':'192.168.0.2'})
        self.assertEqual(models['models'],['small'])
        _,chat=await self.request('/api/chat',{'ollama_url':'192.168.0.2','model':'small','message':'Hola'})
        self.assertEqual(chat['reply'],'¡Hola!')
        header,error=await self.request('/api/prepare',{'model':'small','message':''})
        self.assertIn(b'400 Bad Request',header)
        self.assertIn('mensaje',error['error'])
        self.assertFalse(self.env['OLLAMA_OCUPADO'])

    async def test_input_ack_fragmentation_and_sequence_error(self):
        request=b'GET /api/status HTTP/1.1\r\nContent-Length: 0\r\n\r\n'
        lines=[]
        for seq,start in enumerate(range(0,len(request),48)):
            lines.append('@EWSUSB:'+json.dumps({'kind':'request','id':'rx','seq':seq,
                  'hex':request[start:start+48].hex(),'last':start+48>=len(request)})+'\n')
        lines.append('@EWSUSB:'+json.dumps({'kind':'request','id':'bad','seq':4,'hex':'','last':True})+'\n')
        source=''.join(lines);stream=io.StringIO(source)
        class Poll:
            def register(self,*args):pass
            def poll(self,*args):return [(stream,1)] if stream.tell()<len(source) else []
        output=io.StringIO()
        with patch.object(sys,'stdin',stream),patch.object(self.env['select'],'poll',Poll),contextlib.redirect_stdout(output):
            task=asyncio.create_task(self.env['escuchar_usb']())
            try:
                for _ in range(200):
                    await asyncio.sleep(0.005)
                    if '"kind": "end"' in output.getvalue() and stream.tell()==len(source):break
                else:self.fail('USB request did not finish')
            finally:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):await task
        frames=[json.loads(line[8:]) for line in output.getvalue().splitlines() if line.startswith('@EWSUSB:')]
        self.assertTrue(any(f['kind']=='ack' and f['seq']==0 for f in frames))
        self.assertTrue(any(f['kind']=='end' and f['id']=='rx' for f in frames))
        self.assertTrue(any(f['kind']=='error' and f['id']=='bad' for f in frames))
        self.assertFalse(self.env['USB_OCUPADO'])

if __name__=='__main__':unittest.main()
