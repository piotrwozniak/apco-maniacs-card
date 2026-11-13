import test from 'node:test';
import assert from 'node:assert/strict';
import {MESSAGES} from './i18n.mjs';
import {configFor} from './weather.mjs';

// Minimal host for testing the real card classes, without a browser or HA.
globalThis.HTMLElement=class extends EventTarget {
  attachShadow(){const handlers={};this.shadowRoot={innerHTML:'',handlers,addEventListener(type,fn){handlers[type]=fn;},querySelector(){return null;}};}
};
const registry=new Map();
globalThis.customElements={get:key=>registry.get(key),define:(key,value)=>registry.set(key,value)};
globalThis.window={};
globalThis.document={createElement:tag=>new (registry.get(tag))()};
await import('./warun-card.js');
const Card=registry.get('apco-maniacs-card');
function cardIn(language){
  const card=new Card();card.setConfig({language});card.render();return card;
}
test('PL and EN translations have identical complete key sets',()=>{
  assert.deepEqual(Object.keys(MESSAGES.pl).sort(),Object.keys(MESSAGES.en).sort());
  for(const words of Object.values(MESSAGES))for(const value of Object.values(words))assert.ok(value.length);
});
test('language setting accepts only PL or EN',()=>{
  assert.equal(configFor().language,'pl');assert.equal(configFor({language:'en'}).language,'en');
  assert.throws(()=>configFor({language:'de'}));
});
test('English render localizes controls, zero precipitation and decimal numbers',()=>{
  const card=cardIn('en');
  assert.match(card.shadowRoot.innerHTML,/Location and threshold settings/);
  assert.match(card.shadowRoot.innerHTML,/APCO Maniacs/);
  assert.doesNotMatch(card.shadowRoot.innerHTML,/Ustawienia|Przedziały|Teraz|Odśwież/);
  assert.equal(card.precipitation(0),'no precipitation');
  assert.equal(card.precipitation(12),'precipitation 12%');
  assert.equal(card.fmt(3.2,1),'3.2');
});
test('Polish render retains agreed precipitation wording and decimal comma',()=>{
  const card=cardIn('pl');assert.equal(card.precipitation(0),'brak opadów');
  assert.equal(card.precipitation(12),'opady 12%');assert.equal(card.fmt(3.2,1),'3,2');
});
test('dates use selected language, independent of the host locale',()=>{
  const date=Date.parse('2026-11-06T14:00:00Z');
  assert.match(cardIn('en').day(date),/Friday/);assert.match(cardIn('pl').day(date),/Piątek/);
});
test('HA cards expose real config editor and hide temporary standalone form',()=>{
  const card=cardIn('en');card.hass={};card.render();
  assert.doesNotMatch(card.shadowRoot.innerHTML,/<details class="settings">/);
  const editor=Card.getConfigElement();editor.setConfig({language:'en'});
  assert.match(editor.shadowRoot.innerHTML,/value="en" selected/);
  assert.match(editor.shadowRoot.innerHTML,/Location name/);
});
test('renamed card preserves old dashboard type',()=>{
  assert.ok(registry.has('warun-card'));assert.ok(registry.has('apco-maniacs-card'));
});
test('switching language keeps fetched weather without a new API call',()=>{
  const card=cardIn('pl');const data={hours:[],current:{},days:[]};card.data=data;
  card.refresh=()=>assert.fail('Language changes must not refetch data');
  card.isConnected=true;card.setConfig({...card.config,language:'en'});
  assert.equal(card.data,data);assert.equal(card.config.language,'en');
});

test('HA editor publishes selected language together with existing location settings',()=>{
  const editor=Card.getConfigElement();editor.setConfig({type:'custom:apco-maniacs-card',name:'Piecki',latitude:53.721,longitude:21.015});
  const values={...editor.config,language:'en'};
  const form={reportValidity:()=>true,values};
  const NativeFormData=globalThis.FormData;
  globalThis.FormData=class {constructor(form){this.values=form.values;}get(key){return this.values[key];}has(key){return Boolean(this.values[key]);}};
  let emitted;
  editor.addEventListener('config-changed',event=>{emitted=event.detail.config;});
  try{editor.shadowRoot.handlers.change({target:{closest:()=>form}});}finally{globalThis.FormData=NativeFormData;}
  assert.equal(emitted.language,'en');assert.equal(emitted.name,'Piecki');
  assert.equal(emitted.latitude,53.721);assert.equal(emitted.type,'custom:apco-maniacs-card');
});

test('compact header shows location once with APCO subtitle and refresh',()=>{
  const card=cardIn('pl');card.setConfig({name:'Piecki'});card.render();
  const html=card.shadowRoot.innerHTML;
  assert.match(html,/<h1 class="brand-name">Piecki<\/h1>/);
  assert.match(html,/APCO Pogoda dla Paralotniarzy/);
  assert.equal((html.match(/<h1/g)||[]).length,1);
  assert.doesNotMatch(html,/<span class="brand-name">APCO Maniacs/);
  assert.match(html,/<div class="name-row"><h1[^>]*>Piecki<\/h1><button[^>]*data-refresh/);
  assert.doesNotMatch(html,/<footer>.*data-refresh/);
});

test('forecast begins with a prominent capitalized date without an extra heading',()=>{
 const card=cardIn('pl');card.previewTime=Date.parse('2026-11-14T10:15:00+01:00');
 card.data={hours:[{time:Date.parse('2026-11-14T10:00:00+01:00'),temperature:10,wind:3,precip:0,direction:90}],current:{},days:[{rise:Date.parse('2026-11-14T07:00:00+01:00'),set:Date.parse('2026-11-14T16:00:00+01:00')}]};card.render();
 assert.match(card.shadowRoot.innerHTML,/<h3>Sobota, 14 listopada<\/h3>/);
 assert.doesNotMatch(card.shadowRoot.innerHTML,/forecast-heading|<h2>Okna pogodowe|<span>Tylko pora lotów/);
});
