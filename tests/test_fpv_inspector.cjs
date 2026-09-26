// Unit-test the original UI logic with synthetic data and a tiny DOM stub.
// This does not open a browser, render a page, or read any commercial artifact.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {test}=require('node:test');
const template=fs.readFileSync(require('node:path').join(__dirname,'../tools/fpv_inspector.html'),'utf8');
const program=[...template.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
const pairs={};
for(const name of ['aim','aimshot','arm','daim','disarm','idle1','jammed','rel','shot']) {
 pairs[name]={vertices:[[0,0,0],[1,0,0],[0,1,0]],faces:[[0,1,2]],frame_end:10,
  nodes:[{id:1,parent:0,name:'root',position:[0,0,0]},{id:2,parent:1,name:'joint',position:[0,0,1]}],
  tracks:[{name:'root',channels:{position:{frames:[0,10],values:[[0,0,0],[1,2,3]]},scale:{frames:[5],values:[[1,1,1]]}}},
          {name:'prop',channels:{rotation:{frames:[0],values:[[0,0,0,1]]}}}]};
}
function setup(){
 const ctx=new Proxy({}, {get:(o,k)=>k in o?o[k]:(...args)=>{for(const a of args)if(typeof a==='number')assert(Number.isFinite(a));},set:(o,k,v)=>(o[k]=v,true)});
 class Element {
  constructor(tag='div'){this.tag=tag;this.children=[];this.listeners={};this.value='';this.width=1200;this.height=400;this.pauses=0;}
  append(...items){this.children.push(...items);if(this.tag==='select'&&this.value==='')this.value=String(items[0].value);}
  replaceChildren(){this.children=[];this.value='';}
  addEventListener(name,fn){this.listeners[name]=fn;}
  getContext(){return ctx;}
  pause(){this.pauses++;}
  querySelectorAll(tag){return this.children.flatMap(c=>[...(c.tag===tag?[c]:[]),...c.querySelectorAll(tag)]);}
 }
 const elements={};
 for(const id of ['resource-data','state','track','channel','mesh','model-info','plot','key','values','previous','next','joints','textures','audio'])
  elements[id]=new Element(['state','track','channel'].includes(id)?'select':'div');
 elements.key.value=0;
 elements['resource-data'].textContent=JSON.stringify({pairs,textures:{'maps/invented.bmp':'AA=='},audio:{'sounds/a.wav':'AA==','sounds/b.wav':'AA=='}});
 const context=vm.createContext({document:{getElementById:id=>elements[id],createElement:tag=>new Element(tag)}});
 vm.runInContext(program,context);
 return {elements,context};
}
test('all nine states and raw-key controls work without playback',()=>{
 const {elements:e}=setup();
 for(const name of Object.keys(pairs)){
  e.state.value=name;e.state.listeners.change();assert.match(e['model-info'].textContent,/2 pistes/);
  e.next.listeners.click();assert.match(e.values.textContent,/repère 10/);assert(e.next.disabled);
  e.previous.listeners.click();assert.match(e.values.textContent,/repère 0/);assert(e.previous.disabled);
  e.channel.value='scale';e.channel.listeners.change();assert.equal(e.key.max,0);assert(e.next.disabled);assert(e.previous.disabled);
  e.track.value=1;e.track.listeners.change();assert.equal(e.channel.value,'rotation');
  e.joints.checked=true;e.joints.listeners.change();
 }
});
test('audio is manual, isolated, and stopped on state selection',()=>{
 const {elements:e}=setup(),audio=e.audio.querySelectorAll('audio');
 assert.equal(audio.length,2);assert(audio.every(a=>a.preload==='none'&&a.controls===true));
 assert(audio.every(a=>a.autoplay===undefined&&a.pauses===1&&a.currentTime===0));
 audio[0].listeners.play();assert.equal(audio[1].pauses,2);assert.equal(audio[0].pauses,1);
 e.state.listeners.change();assert.equal(audio[0].pauses,2);assert.equal(audio[1].pauses,3);
});
test('source has no network or automatic animation scheduler',()=>{
 assert.match(template,/connect-src 'none'/);assert.match(template,/media-src data:/);
 assert(!/fetch\(|XMLHttpRequest|setInterval|requestAnimationFrame|\.play\(\)/.test(program));
});
