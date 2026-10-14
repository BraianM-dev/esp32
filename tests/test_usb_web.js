/* Run: node tests/test_usb_web.js. Execute the actual embedded USB functions. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync(require('node:path').join(__dirname,'..','index.html'),'utf8');
function section(a,b){const start=html.indexOf(a),end=html.indexOf(b,start);assert.ok(start>=0&&end>start);return html.slice(start,end)}
function ctx(extra={}){return vm.createContext({TextEncoder,TextDecoder,Uint8Array,Response,DOMException,URL,setTimeout,clearTimeout,console,...extra})}
async function transport(){
 const context=ctx({enc:new TextEncoder()});
 vm.runInContext(section('class UsbWebTransport {','const usbWeb=new UsbWebTransport(serial);')+'\nglobalThis.UsbWebTransport=UsbWebTransport;',context);
 let usb,requests=[],count=0;
 const serial={connected:true,mode:'raw',rawStage:'result',write:async line=>{
  const frame=JSON.parse(line.slice('@EWSUSB:'.length));
  assert.ok(frame.hex.length<=96); // 48-byte chunks protect firmware RX buffer.
  if(frame.seq===0)requests.push([]);
  requests.at(-1).push(Buffer.from(frame.hex,'hex'));
  const ack='@EWSUSB:'+JSON.stringify({kind:'ack',id:frame.id,seq:frame.seq})+'\r\n';
  // Split at every kind of boundary, including prefix and JSON.
  usb.feed(ack.slice(0,3));usb.feed(ack.slice(3,11));usb.feed(ack.slice(11));
  if(frame.last){
   const answer=Buffer.from('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{"reply":"¡Hola, ñ!"}');
   let seq=0;
   for(let offset=0;offset<answer.length;offset+=7){
    const part='@EWSUSB:'+JSON.stringify({kind:'data',id:frame.id,seq:seq++,hex:answer.subarray(offset,offset+7).toString('hex')})+'\n';
    usb.feed(part.slice(0,part.length-2));usb.feed(part.slice(-2));
   }
   usb.feed('@EWSUSB:'+JSON.stringify({kind:'end',id:frame.id,seq})+'\n');count++;
  }
 }};
 usb=new context.UsbWebTransport(serial);
 assert.equal(usb.feed('Servidor activo\n@EWS'),'Servidor activo\n');
 assert.equal(usb.feed('USB:{"kind":"ack","id":"old","seq":0}\n'),'');
 const replies=await Promise.all([usb.request('/api/chat','POST',{message:'ñ'.repeat(300)}),usb.request('/api/status')]);
 assert.equal(count,2);assert.equal(JSON.parse(replies[0].body).reply,'¡Hola, ñ!');
 assert.equal(replies[0].status,200);assert.ok(usb.claimed);
 assert.match(Buffer.concat(requests[0]).toString(),/Content-Length: 614/);
 assert.equal(usb.pending,null);assert.equal(usb.busy,false);
 serial.write=async()=>{};
 const interrupted=usb.request('/api/status');
 await new Promise(resolve=>setTimeout(resolve,5));usb.reset('Desconectado');
 await assert.rejects(interrupted,/Desconectado/);
 assert.equal(usb.claimed,false);assert.equal(usb.pending,null);
 await assert.rejects(usb.request('/not-allowed'),/no permitida/);
 serial.connected=false;await assert.rejects(usb.request('/'),/Conecta/);
}
async function frameIsolation(){
 let handler,messages=[],parent={postMessage:(msg)=>messages.push(msg)};
 const window={};
 const context=ctx({window,parent,addEventListener:(name,fn)=>{if(name==='message')handler=fn}});
 vm.runInContext(section('function usbFrameBootstrap(', 'function usbWebMessage('),context);
 vm.runInContext('usbFrameBootstrap("secret",{esp32OllamaModel:"small"})',context);
 assert.equal(window.localStorage.getItem('esp32OllamaModel'),'small');
 window.localStorage.setItem('esp32OllamaModel','other');
 assert.equal(messages[0].kind,'storage');assert.equal(messages[0].token,'secret');
 const request=window.fetch('/api/status');const msg=messages.at(-1);
 handler({source:{},data:{channel:'ews-usb-web',token:'secret',id:msg.id,status:200,body:'{}'}});
 handler({source:parent,data:{channel:'ews-usb-web',token:'wrong',id:msg.id,status:200,body:'{}'}});
 handler({source:parent,data:{channel:'ews-usb-web',token:'secret',id:msg.id,status:200,body:'{"ok":true}'}});
 assert.equal((await (await request).json()).ok,true);
 const controller=new AbortController();
 const cancelled=window.fetch('/api/chat',{signal:controller.signal});controller.abort();
 await assert.rejects(cancelled,error=>error.name==='AbortError');
 assert.equal(messages.at(-1).kind,'cancel');
}
async function routes(){
 let calls=[],route='pc';const serial={connected:true};
 const usbWeb={request:async(path,method,body)=>{
  calls.push({path,method,body});
  if(path==='/api/status')return {status:200,body:'{"mode":"Wi-Fi","busy":false}'};
  if(path==='/api/prepare')return {status:200,body:JSON.stringify({request:{model:body.model,options:{temperature:body.temperature},messages:[{role:'user',content:body.message}],stream:false}})};
  return {status:200,body:'{"models":["wifi-model"]}'};
 }};
 const fetch=async(url,options)=>{
  calls.push({url,options});
  return new Response(JSON.stringify(url.endsWith('/api/tags')?{models:[{name:'pc-model'}]}:{message:{content:'Respuesta PC'}}),{status:200});
 };
 const context=ctx({serial,usbWeb,usbPcBusy:false,fetch,$:()=>({value:route}),location:{origin:'https://braianm-dev.github.io'}});
 vm.runInContext(section('async function usbJson(',"window.addEventListener('message',async event=>"),context);
 const invoke=(path,body)=>vm.runInContext('handleUsbWebRequest('+JSON.stringify({path,method:body?'POST':'GET',body:body?JSON.stringify(body):null})+',signal)',context);
 context.signal=new AbortController().signal;
 const status=await invoke('/api/status');assert.equal(status.ollama_default_url,'http://localhost:11434');
 assert.equal((await invoke('/api/models',{ollama_url:'http://localhost:11434'})).models[0],'pc-model');
 const reply=await invoke('/api/chat',{model:'pc-model',message:'Hola',temperature:0.4,ollama_url:'http://localhost:11434'});
 assert.equal(reply.reply,'Respuesta PC');
 assert.ok(calls.some(c=>c.path==='/api/prepare'));
 const pc=calls.find(c=>c.url?.endsWith('/api/chat'));assert.equal(JSON.parse(pc.options.body).options.temperature,0.4);
 assert.equal(pc.options.credentials,'omit');
 route='esp32';assert.equal((await invoke('/api/models',{ollama_url:'192.168.0.2'})).models[0],'wifi-model');
 await assert.rejects(invoke('/arbitrary',{x:1}),/no permitido/);
}
Promise.all([transport(),frameIsolation(),routes()]).then(()=>console.log('USB web transport, iframe and Ollama routes OK')).catch(error=>{console.error(error);process.exitCode=1});
