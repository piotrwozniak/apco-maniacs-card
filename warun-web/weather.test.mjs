import test from 'node:test';
import assert from 'node:assert/strict';
import {DEFAULTS, configFor, forecastURL, normalize, assessment, currentHour, windowsFor, direction} from './weather.mjs';

const HOUR = 3600000;
const noon = Date.parse('2026-11-05T11:00:00Z'); // Noon in Poland.
function dataFor({wind = 3, precip = 5} = {}) {
  return {hours: Array.from({length:40}, (_,i) => ({time:noon + i * HOUR, temperature:10+i, wind, precip})),
    days: [0,1,2].map(day => ({rise:noon + day*24*HOUR - 5*HOUR, set:noon + day*24*HOUR + 4*HOUR}))};
}
const allDay = {...DEFAULTS, daylight_only:false};

test('wind and precipitation thresholds are both exclusive', () => {
  assert.equal(assessment({wind:4.99,precip:9.99}, DEFAULTS), 'good');
  assert.equal(assessment({wind:5,precip:0}, DEFAULTS), 'bad');
  assert.equal(assessment({wind:0,precip:10}, DEFAULTS), 'bad');
});
test('missing or invalid values never become good weather', () => {
  for (const hour of [{wind:null,precip:0},{wind:0,precip:null},{wind:NaN,precip:0},{wind:-1,precip:0},{wind:0,precip:101}])
    assert.equal(assessment(hour,DEFAULTS),'unknown');
});
test('current hour is matched by timestamp rather than the first entry', () => {
  const data = dataFor();
  assert.equal(currentHour(data,noon+2.5*HOUR),data.hours[2]);
  assert.equal(currentHour(data,noon-HOUR),null);
});
test('equal assessments merge until midnight without a three-hour limit', () => {
  const windows = windowsFor(dataFor(), allDay, noon + HOUR/2);
  assert.equal(windows.length,3);
  assert.equal(windows[0].start,noon);
  assert.equal(windows[0].end,noon+12*HOUR);
  assert.equal(windows[0].count,12);
  assert.equal(windows[0].min,10);
  assert.equal(windows[0].max,21);
});
test('bad hours start their own window', () => {
  const data = dataFor(); data.hours[2].wind=8;
  const window = windowsFor(data,allDay,noon)[0];
  assert.equal(window.status,'good'); assert.equal(window.count,2); assert.equal(window.wind,3);
  const bad=windowsFor(data,allDay,noon)[1];
  assert.equal(bad.start,noon+2*HOUR); assert.equal(bad.end,noon+3*HOUR); assert.equal(bad.status,'bad'); assert.equal(bad.wind,8);
});
test('missing precipitation produces an unknown window', () => {
  const data = dataFor(); data.hours[2].precip=null;
  const windows=windowsFor(data,allDay,noon);
  assert.equal(windows[0].status,'good');
  const window=windows[1];
  assert.equal(window.start,noon+2*HOUR);
  assert.equal(window.status,'unknown'); assert.equal(window.precip,null);
});
test('a forecast gap separates runs without hiding available hours', () => {
  const data=dataFor(); data.hours.splice(2,1);
  const windows=windowsFor(data,allDay,noon);
  assert.equal(windows[0].start,noon);
  assert.equal(windows[0].end,noon+2*HOUR);
  assert.equal(windows[1].start,noon+3*HOUR);
});
test('each new day starts on its own first full hour after sunrise', () => {
  const windows=windowsFor(dataFor(), DEFAULTS,noon);
  assert.deepEqual(windows.map(w=>(w.start-noon)/HOUR),[0,19]);
  assert.ok(windows.every(w=>dataFor().days.some(d=>w.start>=d.rise && w.end<=d.set)));
});
test('absence of solar data does not silently enable nighttime windows', () => {
  const data=dataFor(); data.days=[];
  assert.equal(windowsFor(data,DEFAULTS,noon).length,0);
  assert.equal(windowsFor(data,allDay,noon).length,3);
});
test('DST transition uses actual elapsed hours', () => {
  const data=dataFor(); const shift=Date.parse('2026-10-25T00:00:00Z')-noon;
  data.hours=data.hours.map(hour=>({...hour,time:hour.time+shift}));
  const window=windowsFor(data,allDay,noon+shift)[0];
  assert.equal(window.end-window.start,23*HOUR);
});
test('input bounds, integers and timezone are validated', () => {
  for (const input of [{latitude:91},{longitude:-181},{wind_threshold:NaN},{forecast_hours:4.5},{forecast_hours:73},{precip_threshold:-1},{name:' '},{daylight_only:'false'},{timezone:'No/Such'}])
    assert.throws(()=>configFor(input));
  assert.deepEqual(configFor(),DEFAULTS);
});
test('request explicitly uses m/s, Celsius and unambiguous UNIX timestamps', () => {
  const url=forecastURL(DEFAULTS);
  assert.equal(url.searchParams.get('wind_speed_unit'),'ms');
  assert.equal(url.searchParams.get('timeformat'),'unixtime');
  assert.equal(url.searchParams.get('timezone'),'Europe/Warsaw');
});
test('normalization preserves missing values and does not change the response', () => {
  const raw={hourly_units:{wind_speed_10m:'m/s',temperature_2m:'°C'},hourly:{time:[noon/1000],temperature_2m:[10],wind_speed_10m:[null],precipitation_probability:[null]},daily:{sunrise:[null],sunset:[null]}};
  const before=structuredClone(raw); const data=normalize(raw);
  assert.equal(data.hours[0].time,noon); assert.equal(data.hours[0].wind,null);
  assert.equal(assessment(data.hours[0],DEFAULTS),'unknown');
  assert.ok(Number.isNaN(data.days[0].rise)); assert.deepEqual(raw,before);
});
test('incorrect units and empty responses are rejected', () => {
  assert.throws(()=>normalize({}));
  assert.throws(()=>normalize({hourly_units:{wind_speed_10m:'km/h'}}));
});
test('wind directions wrap correctly', () => {
  assert.equal(direction(0),'N'); assert.equal(direction(90),'E');
  assert.equal(direction(180),'S'); assert.equal(direction(270),'W');
  assert.equal(direction(360),'N'); assert.equal(direction(-90),'W'); assert.equal(direction(null),'—');
});

test('window direction belongs to its strongest wind rather than the first hour', () => {
  const data = dataFor();
  data.hours[1].direction = 0;
  data.hours[2].wind = 4;
  data.hours[2].direction = 315;
  data.hours[3].direction = 90;
  const window = windowsFor(data, allDay, noon)[0];
  assert.equal(window.wind, 4);
  assert.equal(window.direction, 315);
});

function afternoonData() {
  const base=Date.parse('2026-11-05T00:00:00+01:00');
  return {hours:Array.from({length:72},(_,i)=>({time:base+i*HOUR,wind:3,precip:0,temperature:10,direction:90})),
    days:[5,6,7].map(day=>({rise:Date.parse(`2026-11-0${day}T09:20:00+01:00`),set:Date.parse(`2026-11-0${day}T17:24:00+01:00`)}))};
}
test('14:15 merges all good hours through sunset, then restarts after sunrise', () => {
  const windows=windowsFor(afternoonData(),DEFAULTS,Date.parse('2026-11-05T14:15:00+01:00'));
  assert.equal(windows[0].start,Date.parse('2026-11-05T14:00:00+01:00'));
  assert.equal(windows[0].end,Date.parse('2026-11-05T17:24:00+01:00'));
  assert.equal(windows[1].start,Date.parse('2026-11-06T10:00:00+01:00'));
  assert.equal(windows[1].end,Date.parse('2026-11-06T17:24:00+01:00'));
});
test('15:10 retains the current window and clips it to sunset at 17:24', () => {
  const data=afternoonData();
  data.hours.find(h=>h.time===Date.parse('2026-11-05T17:00:00+01:00')).wind=8;
  const windows=windowsFor(data,DEFAULTS,Date.parse('2026-11-05T15:10:00+01:00'));
  assert.equal(windows[0].start,Date.parse('2026-11-05T15:00:00+01:00'));
  assert.equal(windows[0].end,Date.parse('2026-11-05T17:00:00+01:00'));
  assert.equal(windows[0].wind,3);
  assert.equal(windows[0].status,'good');
  assert.equal(windows[1].start,Date.parse('2026-11-05T17:00:00+01:00'));
  assert.equal(windows[1].end,Date.parse('2026-11-05T17:24:00+01:00'));
  assert.equal(windows[1].status,'bad');
  assert.equal(windows[2].start,Date.parse('2026-11-06T10:00:00+01:00'));
});
test('sunrise at 09:20 never creates a 09:00 morning window', () => {
  const windows=windowsFor(afternoonData(),DEFAULTS,Date.parse('2026-11-05T07:00:00+01:00'));
  assert.equal(windows[0].start,Date.parse('2026-11-05T10:00:00+01:00'));
  assert.equal(windows[0].end,Date.parse('2026-11-05T17:24:00+01:00'));
});
test('at sunset no remaining window from today is displayed', () => {
  const windows=windowsFor(afternoonData(),DEFAULTS,Date.parse('2026-11-05T17:24:00+01:00'));
  assert.equal(windows[0].start,Date.parse('2026-11-06T10:00:00+01:00'));
});
test('a shortened final hour uses only the hours before sunset', () => {
  const windows=windowsFor(afternoonData(),DEFAULTS,Date.parse('2026-11-05T17:10:00+01:00'));
  assert.equal(windows[0].hours.length,1);
  assert.equal(windows[0].min,10);
  assert.equal(windows[0].end,Date.parse('2026-11-05T17:24:00+01:00'));
});

 test('remaining good hours stay green when the next hour deteriorates',()=>{
  const data=dataFor();
  for(const hour of data.hours.slice(3))hour.wind=8;
  for(const offset of [0,1]){
    const windows=windowsFor(data,allDay,noon+(offset+.25)*HOUR);
    assert.equal(windows[0].start,noon+offset*HOUR);
    assert.equal(windows[0].end,noon+3*HOUR);
    assert.equal(windows[0].status,'good');
    assert.equal(windows[1].start,noon+3*HOUR);
    assert.equal(windows[1].status,'bad');
    assert.ok(windows.every(w=>w.hours.every(h=>assessment(h,allDay)===w.status)));
  }
 });
 test('runs cross former triple boundaries without overlapping or mixing assessments',()=>{
  const data=dataFor();
  for(const hour of data.hours.slice(2,6))hour.precip=70;
  const windows=windowsFor(data,allDay,noon);
  assert.deepEqual(windows.slice(0,3).map(w=>[(w.start-noon)/HOUR,(w.end-noon)/HOUR,w.status]),[[0,2,'good'],[2,6,'bad'],[6,12,'good']]);
  assert.equal(windows[1].precip,70);
  assert.equal(windows[0].max,11);
  assert.equal(windows[1].min,12);
  for(let i=0;i<windows.length;i++){
    assert.ok(windows[i].hours.every(h=>assessment(h,allDay)===windows[i].status));
    if(i)assert.equal(windows[i-1].end,windows[i].start);
  }
 });

test('all-day coverage retains the last forecast hour and separates calendar days',()=>{
 const data=dataFor();const windows=windowsFor(data,allDay,noon);
 assert.equal(windows.at(-1).end,noon+40*HOUR);
 assert.equal(windows.reduce((n,w)=>n+w.hours.length,0),40);
 assert.ok(windows.some(w=>w.hours.length>3));
 assert.equal(windows[1].start,noon+12*HOUR);
});
