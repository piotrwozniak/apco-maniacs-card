import test from 'node:test';
import assert from 'node:assert/strict';
import {MESSAGES,languageFor,localeFor} from './i18n.mjs';
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
const Card=registry.get('apco-weather-card');
function cardIn(language){
  const card=new Card();card.setConfig({language});card.render();return card;
}
test('all four translations have identical complete key sets',()=>{
  assert.deepEqual(Object.keys(MESSAGES.pl).sort(),Object.keys(MESSAGES.en).sort());
  for(const words of Object.values(MESSAGES)){
    assert.deepEqual(Object.keys(words).sort(),Object.keys(MESSAGES.en).sort());
    for(const value of Object.values(words))assert.ok(value.length);
  }
});
test('language setting supports four languages and falls back to English',()=>{
  assert.equal(configFor().language,'pl');assert.equal(configFor({language:'en'}).language,'en');
  assert.equal(configFor({language:'de'}).language,'en');
  assert.equal(configFor({language:'it'}).language,'it');
  assert.equal(configFor({language:'es-MX'}).language,'es');
});
test('English render localizes controls, zero precipitation and decimal numbers',()=>{
  const card=cardIn('en');
  assert.match(card.shadowRoot.innerHTML,/Location and threshold settings/);
  assert.match(card.shadowRoot.innerHTML,/APCO Weather/);
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
test('HA cards expose real config editor and hide temporary standalone form',async()=>{
  const card=cardIn('en');card.hass={};card.render();
  assert.doesNotMatch(card.shadowRoot.innerHTML,/<details class="settings">/);
  const editor=await Card.getConfigElement();editor.setConfig({language:'en'});
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

test('HA editor publishes selected language together with existing location settings',async()=>{
  const editor=await Card.getConfigElement();editor.setConfig({type:'custom:apco-maniacs-card',name:'Piecki',latitude:53.721,longitude:21.015});
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
  assert.doesNotMatch(html,/<span class="brand-name">APCO Weather/);
  assert.match(html,/<div class="name-row"><h1[^>]*>Piecki<\/h1><button[^>]*data-refresh/);
  assert.doesNotMatch(html,/<footer>.*data-refresh/);
});

test('forecast begins with a prominent capitalized date without an extra heading',()=>{
 const card=cardIn('pl');card.previewTime=Date.parse('2026-11-14T10:15:00+01:00');
 card.data={hours:[{time:Date.parse('2026-11-14T10:00:00+01:00'),temperature:10,wind:3,precip:0,direction:90}],current:{},days:[{rise:Date.parse('2026-11-14T07:00:00+01:00'),set:Date.parse('2026-11-14T16:00:00+01:00')}]};card.render();
 assert.match(card.shadowRoot.innerHTML,/<h3>Sobota, 14 listopada<\/h3>/);
 assert.doesNotMatch(card.shadowRoot.innerHTML,/forecast-heading|<h2>Okna pogodowe|<span>Tylko pora lotów/);
});

test('card picker loads the native HA form before opening the map editor',async()=>{
  let initialized=false;
  window.loadCardHelpers=async()=>({createCardElement(config){
    assert.equal(config.type,'entities');
    return {constructor:{async getConfigElement(){initialized=true;registry.set('ha-form',class {});}}};
  }});
  try{
    const editor=await Card.getConfigElement();
    assert.ok(initialized);editor.setConfig({});
    assert.match(editor.shadowRoot.innerHTML,/<ha-form data-location>/);
  }finally{delete window.loadCardHelpers;registry.delete('ha-form');}
});

test('map pin changes persist exact coordinates and preserve all other settings',async()=>{
  const editor=await Card.getConfigElement();editor.setConfig({type:'custom:apco-maniacs-card',name:'Startowisko',language:'en',wind_threshold:6,daylight_only:false});
  const map={},latitude={},longitude={},error={};
  editor.shadowRoot.querySelector=selector=>selector==='ha-form[data-location]'?map:selector==='[name="latitude"]'?latitude:selector==='[name="longitude"]'?longitude:error;
  const hass={config:{latitude:53,longitude:21}};editor.hass=hass;
  assert.equal(map.hass,hass);
  assert.deepEqual(map.schema[0].selector,{location:{}});
  let emitted;editor.addEventListener('config-changed',event=>{emitted=event.detail.config;});
  editor.shadowRoot.handlers['value-changed']({target:{matches:selector=>selector==='ha-form[data-location]'},detail:{value:{location:{latitude:53.719876,longitude:21.012345}}},stopPropagation(){}});
  assert.equal(emitted.latitude,53.719876);assert.equal(emitted.longitude,21.012345);
  assert.equal(emitted.name,'Startowisko');assert.equal(emitted.language,'en');assert.equal(emitted.wind_threshold,6);assert.equal(emitted.daylight_only,false);
  assert.equal(emitted.type,'custom:apco-maniacs-card');
  assert.equal(latitude.value,53.719876);assert.equal(longitude.value,21.012345);
  assert.equal(configFor(emitted).latitude,53.719876);
  let renders=0;editor.render=()=>renders++;editor.setConfig(emitted);
  assert.equal(renders,0,'HA echo must not reset map zoom or pin');
  emitted=null;
  editor.shadowRoot.handlers['value-changed']({target:{matches:selector=>selector==='ha-form[data-location]'},detail:{value:{location:{latitude:999,longitude:0}}},stopPropagation(){}});
  assert.equal(emitted,null);assert.equal(editor.config.latitude,53.719876);
});

test('new cards start at the HA home coordinates and support links are present',()=>{
  const config=Card.getStubConfig({config:{latitude:52.2,longitude:20.9,time_zone:'Europe/Warsaw'}});
  assert.equal(config.latitude,52.2);assert.equal(config.longitude,20.9);
  const card=cardIn('pl');card.hass={};card.render();
  assert.match(card.shadowRoot.innerHTML,/https:\/\/buymeacoffee.com\/piotrwoznil/);
  assert.match(card.shadowRoot.innerHTML,/https:\/\/www.youtube.com\/@piter_fly/);
});

 test('HA language detection supports regional forms and defaults to English',()=>{
  for(const [input,expected] of [['pl-PL','pl'],['en-US','en'],['it-IT','it'],['es-419','es'],['ES_mx','es'],['de','en'],['fr','en'],['','en'],[null,'en'],['toString','en']])assert.equal(languageFor(input),expected);
  assert.equal(localeFor('it'),'it-IT');assert.equal(localeFor('es'),'es-ES');
 });
 test('unconfigured cards follow HA language changes without refetching weather',()=>{
  const card=cardIn('pl');card.setConfig({});const data={hours:[],days:[],current:{}};card.data=data;
  card.refresh=()=>assert.fail('Language must not refetch weather');card.isConnected=true;
  card.hass={language:'it-IT'};assert.equal(card.config.language,'it');assert.equal(card.data,data);
  card.hass={language:'es-MX'};assert.equal(card.config.language,'es');
  card.hass={language:'de'};assert.equal(card.config.language,'en');
  card.setConfig({language:'pl'});card.hass={language:'it'};assert.equal(card.config.language,'pl');
  assert.equal(Card.getStubConfig({language:'es'}).language,'es');
 });
 test('Italian and Spanish localize labels dates and decimal separators',()=>{
  for(const [language,now,weekday] of [['it','Adesso','Sabato'],['es','Ahora','Sábado']]){
    const card=cardIn(language);assert.match(card.shadowRoot.innerHTML,new RegExp(now));
    assert.match(card.day(Date.parse('2026-11-14T12:00:00Z')),new RegExp(weekday));
    assert.equal(card.fmt(3.2,1),'3,2');
    assert.match(card.shadowRoot.innerHTML,/value="it"/);assert.match(card.shadowRoot.innerHTML,/value="es"/);
    assert.doesNotMatch(card.shadowRoot.innerHTML,/undefined/);
  }
 });
 test('editor honors explicit language and otherwise follows the HA frontend',async()=>{
  const editor=await Card.getConfigElement();editor.setConfig({});editor.hass={language:'es'};
  assert.equal(editor.config.language,'es');assert.match(editor.shadowRoot.innerHTML,/Nombre del lugar/);
  editor.setConfig({language:'it'});editor.hass={language:'es'};assert.equal(editor.config.language,'it');
 });

const backendFixture=JSON.parse(await (await import('node:fs/promises')).readFile(new URL('../tests/fixtures/open_meteo.json',import.meta.url),'utf8'));
function integrationState(overrides={}) {
  return {state:'good',attributes:{apco_maniacs:true,forecast:backendFixture,updated_at:Date.now()/1000,
    location:{name:'Piecki',latitude:53.7,longitude:21,timezone:'Europe/Warsaw',wind_threshold:4,precip_threshold:20}},...overrides};
}
test('integration card reads the backend contract and never fetches weather in the browser',async()=>{
  const originalFetch=globalThis.fetch;
  globalThis.fetch=()=>assert.fail('Backend mode must not call Open-Meteo');
  try {
    const card=new Card();card.setConfig({entity:'sensor.apco_piecki_conditions',language:'en'});
    card.hass={states:{'sensor.apco_piecki_conditions':integrationState()}};
    await card.refresh();
    assert.equal(card.error,false);assert.equal(card.data.hours.length,72);
    assert.equal(card.weatherConfig.name,'Piecki');assert.equal(card.weatherConfig.wind_threshold,4);
    assert.equal(card.config.language,'en');assert.match(card.shadowRoot.innerHTML,/<h1 class="brand-name">Piecki/);
    assert.equal(card.data.hours[0].wind,3.2);
  }finally{globalThis.fetch=originalFetch;}
});
test('missing unavailable stale and invalid integration data never falls back to direct fetch',async()=>{
  const originalFetch=globalThis.fetch;globalThis.fetch=()=>assert.fail('No silent fallback');
  try {
    const card=new Card();card.setConfig({entity:'sensor.apco_test',language:'en'});
    for(const state of [undefined,integrationState({state:'unavailable'}),
      {state:'good',attributes:{...integrationState().attributes,updated_at:Date.now()/1000-1801}},
      {state:'good',attributes:{...integrationState().attributes,forecast:{}}},
      {state:'good',attributes:{...integrationState().attributes,location:{timezone:'invalid'}}}]){
      card.hass={states:{'sensor.apco_test':state}};await card.refresh();
      assert.equal(card.error,true);assert.match(card.shadowRoot.innerHTML,/entity is unavailable/);
      assert.match(card.shadowRoot.innerHTML,/current alert unknown/);
    }
    card.hass={states:{'sensor.apco_test':integrationState({state:'unknown'})}};await card.refresh();
    assert.equal(card.error,false,'Missing current measurements must not hide the forecast');
  }finally{globalThis.fetch=originalFetch;}
});
test('backend changes update the card and explicit refresh uses HA update_entity',async()=>{
  const card=new Card();card.setConfig({entity:'sensor.apco_test'});card.isConnected=true;
  const calls=[];
  const hass={states:{'sensor.apco_test':integrationState()},callService:async(...args)=>calls.push(args)};
  card.hass=hass;assert.equal(card.error,false);
  hass.states['sensor.apco_test']=integrationState({state:'unavailable'});card.hass=hass;assert.equal(card.error,true);
  hass.states['sensor.apco_test']=integrationState();card.hass=hass;assert.equal(card.error,false);
  await card.refresh();assert.equal(calls.length,0);
  await card.refresh(true);assert.deepEqual(calls,[['homeassistant','update_entity',{entity_id:'sensor.apco_test'}]]);
  card.isConnected=false;
});
test('native editor selects and clears an integration entity without losing other card settings',async()=>{
  registry.set('ha-form',class {});
  try{
    const editor=await Card.getConfigElement();editor.setConfig({name:'Direct location',language:'es',daylight_only:false});
    const source={},map={};editor.shadowRoot.querySelector=selector=>selector==='ha-form[data-source]'?source:selector==='ha-form[data-location]'?map:null;
    editor.hass={states:{}};
    assert.equal(source.schema[0].selector.entity.integration,'apco_maniacs');
    let emitted;editor.addEventListener('config-changed',event=>emitted=event.detail.config);
    const change=entity=>editor.shadowRoot.handlers['value-changed']({target:{matches:selector=>selector==='ha-form[data-source]'},detail:{value:{entity}},stopPropagation(){}});
    change('sensor.apco_test');assert.equal(emitted.entity,'sensor.apco_test');assert.equal(emitted.language,'es');
    assert.equal(emitted.daylight_only,false);assert.doesNotMatch(editor.shadowRoot.innerHTML,/ha-form data-location/);
    assert.doesNotMatch(editor.shadowRoot.innerHTML,/name="latitude"/);
    change('');assert.equal(emitted.entity,undefined);assert.equal(emitted.name,'Direct location');
    assert.match(editor.shadowRoot.innerHTML,/ha-form data-location/);
  }finally{registry.delete('ha-form');}
});

test('integration mode keeps daylight and horizon editable independently from backend settings',()=>{
  const card=new Card();card.setConfig({entity:'sensor.apco_test',language:'pl'});
  card.hass={states:{'sensor.apco_test':integrationState()}};
  card.setConfig({...card.config,daylight_only:false,forecast_hours:72,wind_threshold:30});
  assert.equal(card.weatherConfig.daylight_only,false);assert.equal(card.weatherConfig.forecast_hours,72);
  assert.equal(card.weatherConfig.wind_threshold,4,'Backend thresholds remain authoritative');
});

test('APCO Weather is the card picker name and both older card types stay registered',()=>{
  assert.ok(registry.has('apco-weather-card'));
  assert.ok(registry.has('apco-maniacs-card'));
  assert.ok(registry.has('warun-card'));
  assert.equal(window.customCards.find(card=>card.type==='apco-weather-card').name,'APCO Weather');
});
