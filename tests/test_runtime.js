/* Focused tests that execute the real functions extracted from index.html. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(require('node:path').join(__dirname, '..', 'index.html'), 'utf8');
function section(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a + start.length);
  assert.ok(a >= 0 && b > a, `Missing section ${start}`);
  return html.slice(a, b);
}
function context(extra = {}) {
  const ctx = vm.createContext({TextDecoder, TextEncoder, Uint8Array, setTimeout,
    clearTimeout, console, ...extra});
  return ctx;
}
async function serialStream() {
  const ctx=context({sleep:async()=>{},enc:new TextEncoder(),dec:new TextDecoder(),
    bytesAsLatin1:b=>Buffer.from(b).toString('latin1'),decodeRawText:b=>Buffer.from(b,'latin1').toString('utf8')});
  vm.runInContext(section('class SerialManager {','const serial = new SerialManager();')+
    '\nglobalThis.SerialManager=SerialManager;',ctx);
  const serial=new ctx.SerialManager();
  serial.write=async()=>{};
  serial.mode='raw';serial.rawStage='result';serial.rawPaste=false;
  serial.rawAckPending=true;serial.rawStreamDecoder=new TextDecoder();
  let visible='';
  serial.rawOnStdout=chunk=>visible+=chunk;
  const completed=new Promise(resolve=>serial.rawResolver=resolve);
  serial._handleData('O');assert.equal(visible,'');
  serial._handleData('KHola ');assert.equal(visible,'Hola ');
  const utf8=Buffer.from('ñ');
  serial._handleData(utf8.subarray(0,1).toString('latin1'));
  assert.equal(visible,'Hola ');
  serial._handleData(utf8.subarray(1).toString('latin1')+'!');
  assert.equal(visible,'Hola ñ!');
  assert.equal(serial.rawBuffer.length,0,'stream drains an indefinitely running service');
  serial._handleData('\x04traceback\x04>');
  const result=await completed;
  assert.equal(result.stderr,'traceback');
  assert.equal(visible,'Hola ñ!');
  assert.equal(serial.mode,'terminal');
}
async function draftAndSave() {
  const values=new Map();
  const localStorage={getItem:key=>values.get(key)||null,setItem:(k,v)=>values.set(k,v),
    removeItem:key=>values.delete(key)};
  const state={docs:[{id:'one',name:'old.py',content:'print(1)',dirty:true,isLocal:false,
    devicePath:'/old.py',blockState:null}],activeId:'one',cwd:'/'};
  const doc=()=>state.docs.find(d=>d.id===state.activeId);
  let current='print(2)',shouldFail=true;
  const serial={connected:true,rawExec:async()=>{if(shouldFail) throw Error('write failed');
    return {stdout:'OK',stderr:''};}};
  const ctx=context({state,settings:{recoverDrafts:true},localStorage,cm:{getValue:()=>current,
    setValue:value=>{current=value}},activeDoc:doc,serial,prompt:()=> 'new.py',
    renderTabs:()=>{},updateEditorMode:()=>{},toast:()=>{},setBusy:()=>{},
    syncFilesystem:async()=>{},highlightActiveFile:()=>{},
    bytesToBase64:bytes=>Buffer.from(bytes).toString('base64'),enc:new TextEncoder(),
    pyStr:x=>x,joinPath:(dir,name)=>dir+name});
  vm.runInContext(section("const DRAFTS_KEY=",'function newDoc(')+
    section('async function saveActiveToDevice(', '/* ---------- Nuevo archivo local ---------- */'),ctx);
  vm.runInContext('saveDrafts()',ctx);
  assert.ok(values.has('espwebstudio.code.drafts.v1'));
  state.docs=[];state.activeId=null;
  assert.equal(vm.runInContext('restoreDrafts()',ctx),true);
  assert.equal(doc().content,'print(2)');
  assert.equal(doc().isLocal,true);
  assert.equal(doc().devicePath,null);
  assert.equal(await vm.runInContext('saveActiveAs()',ctx),false);
  assert.equal(doc().name,'old.py');
  assert.equal(doc().isLocal,true);
  shouldFail=false;
  assert.equal(await vm.runInContext('saveActiveAs()',ctx),true);
  assert.equal(doc().name,'new.py');
  assert.equal(doc().devicePath,'/new.py');
  assert.equal(doc().dirty,false);
  vm.runInContext('settings.recoverDrafts=false; saveDrafts()',ctx);
  assert.equal(values.has('espwebstudio.code.drafts.v1'),false);
}
async function interactiveInput() {
  const ctx=context();
  vm.runInContext(section('function pythonWithoutLiterals(', 'const BOARD_MODULES')+
    section('function localInteractiveCode(', 'function runLocalPython('),ctx);
  for (const id of ['chatbot','dungeon-master']) {
    const source=html.match(new RegExp('<script type="text/x-micropython" id="example-'+id+'">\\n([\\s\\S]*?)\\n</script>'))[1];
    const converted=vm.runInContext('localInteractiveCode('+JSON.stringify(source)+')',ctx);
    assert.equal(converted.interactive,true);
    assert.match(converted.code,/\(await __ews_input\(/);
    assert.ok(!converted.code.includes('input("') || converted.code.includes('await __ews_input("'));
  }
  const chained=vm.runInContext('localInteractiveCode('+JSON.stringify('answer = input("X: ").strip().lower()')+')',ctx);
  assert.equal(chained.code,'answer = (await __ews_input("X: ")).strip().lower()');
  const nested=vm.runInContext('localInteractiveCode('+JSON.stringify('print(input(input("X: ")))')+')',ctx);
  assert.equal(nested.code,'print((await __ews_input((await __ews_input("X: ")))))');
  const noChange=vm.runInContext('localInteractiveCode('+JSON.stringify('print("input(\") # input(\n')+')',ctx);
  assert.equal(noChange.interactive,false);

  const workerCtx=context();
  vm.runInContext(section('const LOCAL_PYODIDE_URL=', 'let localWorker=null'),workerCtx);
  const source=vm.runInContext('LOCAL_WORKER_SOURCE',workerCtx);
  const messages=[];
  const self={postMessage:msg=>messages.push(msg)};
  const fakePyodide={
    globals:{get:()=>()=>({destroy(){}})},
    setStdout(){},setStderr(){},
    async runPythonAsync(code) {if (code==='COMPAT') return;
      const answer=await self.ewsAsk('Nombre del jugador: ');
      assert.equal(answer,'Ana');}
  };
  const simulated=context({self,loadPyodide:async()=>fakePyodide});
  vm.runInContext(source.replace(/^import [^\n]+\n/,''),simulated);
  const execution=self.onmessage({data:{id:7,code:'interactive',compat:'COMPAT',interactive:true,preamble:''}});
  for(let i=0;i<8 && !messages.some(m=>m.kind==='input-request');i++) await Promise.resolve();
  assert.equal(messages.find(m=>m.kind==='input-request')?.text,'Nombre del jugador: ');
  await self.onmessage({data:{id:7,kind:'input-response',text:'Ana'}});
  await execution;
  assert.ok(messages.some(m=>m.kind==='done'));
}
Promise.all([serialStream(),draftAndSave(),interactiveInput()]).then(()=>console.log('Runtime regression tests OK'))
  .catch(error=>{console.error(error);process.exitCode=1});
