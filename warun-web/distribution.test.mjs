import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';

test('HACS artifact registers the real card without external CSS or JS dependencies',()=>{
  const source=readFileSync(new URL('../dist/apco-maniacs-card.js',import.meta.url),'utf8');
  const registry=new Map();
  class Element extends EventTarget {
    attachShadow(){this.shadowRoot={innerHTML:'',addEventListener(){},querySelector(){return null;}};}
  }
  const context={HTMLElement:Element,EventTarget,CustomEvent,URL,Intl,console,window:{},customElements:{get:key=>registry.get(key),define:(key,value)=>registry.set(key,value)}};
  runInNewContext(source,context);
  const card=new (registry.get('apco-maniacs-card'))();card.setConfig({name:'Test HACS'});card.render();
  assert.match(card.shadowRoot.innerHTML,/Test HACS/);
  assert.match(card.shadowRoot.innerHTML,/data:text\/css;charset=utf-8,/);
  assert.doesNotMatch(source,/^import |^export /m);
  assert.match(card.shadowRoot.innerHTML,/https:\/\/www.youtube.com\/@piter_fly/);
  // Loading both legacy and bundled resources must not redefine any custom element.
  runInNewContext(source,context);
  assert.ok(registry.has('warun-card'));assert.ok(registry.has('apco-maniacs-editor'));
});
