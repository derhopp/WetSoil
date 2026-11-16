const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadCard() {
  const registry = new Map();
  class HTMLElement {}
  class CustomEvent {}
  const context = {
    HTMLElement, CustomEvent,
    customElements: {define(name, type) {registry.set(name,type);}},
    window: {},
    document: {createElement(tag) {return {tag};}},
    console
  };
  const source = fs.readFileSync(path.join(__dirname,
    "../../custom_components/wetsoil/frontend/wetsoil-card.js"),"utf8");
  vm.runInNewContext(source,context,{filename:"wetsoil-card.js"});
  return registry.get("wetsoil-card");
}
const circuits=[
  {entry_id:"test-1",name:"Test 1",config:{weather_entity:"weather.one",rain_sensor:"binary_sensor.one",start_time:"08:00"}},
  {entry_id:"test-2",name:"Test 2",config:{weather_entity:"weather.two",rain_sensor:"binary_sensor.two",start_time:"09:00"}}
];

test("missing and stale entry IDs never fall back to first circuit",()=>{
  const Card=loadCard(), card=new Card();
  card._circuits=circuits;
  for (const entry_id of [undefined,"","does-not-exist"]) {
    card._config = {entry_id};
    assert.equal(card._current(),undefined);
  }
  card._config={entry_id:"test-2"};
  assert.equal(card._current().name,"Test 2");
});

test("two cards send changes to their own circuit",async()=>{
  const Card=loadCard(), messages=[];
  const hass={language:"en",callWS:async msg=>{messages.push(msg);return {};}};
  const a=new Card(), b=new Card();
  for(const [card,id] of [[a,"test-1"],[b,"test-2"]]) {
    card._config={entry_id:id};
    card._circuits=circuits;
    card._hass=hass;
    card._refresh=async()=>{};
  }
  await a._send("update",{config:{weather_entity:"weather.new",rain_sensor:"binary_sensor.new",start_time:"07:00"}});
  await b._send("update",{config:{weather_entity:"weather.two",rain_sensor:"binary_sensor.two",start_time:"09:30"}});
  assert.deepEqual(messages.map(x=>x.entry_id),["test-1","test-2"]);
  assert.equal(messages[0].config.weather_entity,"weather.new");
  assert.equal(messages[1].config.weather_entity,"weather.two");
});

test("unbound card cannot write or trigger hardware action",async()=>{
  const Card=loadCard(), requests=[];
  const card=new Card();
  card._circuits=circuits;
  card._hass={language:"de",callWS:async m=>requests.push(m)};
  card._render=()=>{};
  for(const entry_id of ["","obsolete"]) {
    card._config={entry_id};
    await card._send("update",{config:{weather_entity:"weather.x"}});
    await card._send("action",{action:"start"});
  }
  assert.equal(requests.length,0);
});

test("additional WebSocket fields cannot change target entry",async()=>{
  const Card=loadCard(), requests=[],card=new Card();
  card._config={entry_id:"test-2"};
  card._circuits=circuits;
  card._hass={language:"en",callWS:async m=>requests.push(m)};
  card._refresh=async()=>{};
  await card._send("update",{entry_id:"test-1",config:{start_time:"11:00"}});
  assert.equal(requests[0].entry_id,"test-2");
});

test("stub configuration does not silently bind to first circuit",()=>{
  const Card=loadCard();
  assert.equal(Card.getStubConfig().entry_id,"");
});


test("structured cyclic chain errors are translated instead of [object Object]",()=>{
  const Card=loadCard(),card=new Card();
  card._hass={locale:{language:"de"}};
  assert.equal(card._errorText({code:"invalid_config",message:"cyclic_predecessor"}),
    "Eine Ringverkettung ist nicht erlaubt.");
  assert.notEqual(card._errorText({code:"invalid_config"}),"[object Object]");
});

test("next start displays a localized time in HA timezone",()=>{
  const Card=loadCard(),card=new Card();
  card._hass={locale:{language:"de-DE"},config:{time_zone:"Europe/Berlin"}};
  const value=card._formatNextStart("2026-11-16T07:00:00+00:00");
  assert.match(value,/16.11.2026/);
  assert.match(value,/08:00/);
  card._circuits=[{entry_id:"first",name:"Test 1"}];
  assert.equal(card._formatNextStart("after:first"),"Nach Test 1");
  assert.equal(card._formatNextStart(null),"Nicht verfügbar");
});

test("error details from rejected websocket updates remain readable",async()=>{
  const Card=loadCard(),card=new Card();
  card._hass={language:"de",callWS:async()=>{
    throw {code:"invalid_config",message:"cyclic_predecessor"};
  }};
  card._circuits=[{entry_id:"first",name:"Test 1"}];
  card._config={entry_id:"first"};
  card._refresh=async()=>{};
  await card._send("update",{config:{predecessor:"first"}});
  assert.equal(card._error,"Eine Ringverkettung ist nicht erlaubt.");
  assert.equal(card._editing,true);
});


test("human-readable status labels cover precipitation and source diagnoses",()=>{
  const Card=loadCard(),card=new Card();
  card._hass={locale:{language:"de-DE"}};
  assert.equal(card._humanize("intensity_72h_complete"),
    "72 Stunden Niederschlagsintensität vollständig ausgewertet");
  assert.equal(card._humanize("recorder_not_loaded"),"Recorder nicht aktiviert");
  assert.equal(card._humanize("forecast_incomplete"),"Wetterprognose unvollständig");
  assert.equal(card._humanize("automatic_disabled"),"Automatik deaktiviert");
  assert.equal(card._humanize(null),"Nicht verfügbar");
  assert.equal(card._humanize("hourly_incomplete,daily_unavailable"),
    "Stundenprognose unvollständig; Tagesprognose nicht verfügbar");
  card._hass={locale:{language:"en-US"}};
  assert.equal(card._humanize("intensity_72h_complete"),
    "72-hour precipitation intensity history complete");
});


test("live event subscription updates only its assigned circuit and unsubscribes",async()=>{
  const Card=loadCard(),card=new Card();
  let handler,subscribed=0,unsubscribed=0,refreshes=0;
  const connection={
    subscribeEvents(fn,kind) {
      assert.equal(kind,"wetsoil_updated");
      handler=fn;subscribed++;
      return Promise.resolve(()=>{unsubscribed++;});
    }
  };
  card._config={entry_id:"test-2"};
  card._refresh=async()=>{refreshes++;};
  card._render=()=>{};
  card.hass={connection,language:"en"};
  card.connectedCallback();
  await Promise.resolve();
  assert.equal(subscribed,1);
  handler({data:{entry_id:"test-1"}});
  assert.equal(refreshes,1); // initial hass setter only
  handler({data:{entry_id:"test-2"}});
  assert.equal(refreshes,2);
  card.disconnectedCallback();
  assert.equal(unsubscribed,1);
  handler({data:{entry_id:"test-2"}});
  assert.equal(refreshes,2);
});
