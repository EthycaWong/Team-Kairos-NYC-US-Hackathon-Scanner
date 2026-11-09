const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

function setup(fixedNow) {
  const elements = new Map();
  const get = id => {
    if (!elements.has(id)) elements.set(id, {value:id === 'compSlider' ? '7' : '', checked:true, innerHTML:'', textContent:'', style:{}, classList:{toggle(){}},setAttribute(){}});
    return elements.get(id);
  };
  const TestDate = fixedNow ? class extends Date {
    constructor(...args) { super(...(args.length ? args : [fixedNow])); }
    static now() { return new Date(fixedNow).getTime(); }
  } : Date;
  const context = vm.createContext({document:{getElementById:get,querySelectorAll:()=>[]}, URL, Intl, console, Date:TestDate});
  const code = fs.readFileSync(path.join(__dirname, '../front/app.js'),'utf8').replace('var app = new HackathonScanner();','');
  vm.runInContext(code + '\nglobalThis.Scanner = HackathonScanner;', context);
  const scanner = Object.create(context.Scanner.prototype);
  Object.assign(scanner, {events:[],selectedDay:null,activeRegion:'NY'});
  return {scanner,get};
}
const futureYear = new Date().getFullYear() + 1;
function event(changes = {}) {
  return {name:'NY Build',website:'https://example.com',start:`${futureYear}-01-01T15:00:00Z`,end:`${futureYear}-01-03T20:00:00Z`,city:'Brooklyn',state:'New York',countryCode:'US',source:'Test',virtual:false,...changes};
}

test('New York and online scope, format filters, and All intensity', () => {
  const {scanner,get} = setup();
  scanner.processData([event({mlhAssociated:true}), event({name:'Remote',state:null,countryCode:null,virtual:true}),event({name:'California',state:'CA'})]);
  assert.equal(scanner.getFiltered().length,2);
  get('chkVirtual').checked = false;
  assert.equal(scanner.getFiltered().length,1);
  scanner.activeRegion = 'NY-only';
  assert.equal(scanner.getFiltered()[0].name,'NY Build');
  scanner.activeRegion = 'all';
  assert.equal(scanner.getFiltered().length,2);
});

test('ongoing days include their year and New York date', () => {
  const {scanner} = setup();
  scanner.processData([event()]);
  scanner.selectedDay = `${futureYear}-01-02`;
  assert.equal(scanner.getFiltered().length,1);
  scanner.selectedDay = `${futureYear+1}-01-02`;
  assert.equal(scanner.getFiltered().length,0);
});

test('rejects unsafe links and invalid or expired dates; escapes source text', () => {
  const {scanner,get} = setup();
  scanner.processData([event({website:'javascript:alert(1)'}),event({end:'invalid'}),event({start:'2000-01-01',end:'2000-01-02'}),event({name:'<img src=x onerror=alert(1)>',source:'<script>bad</script>',description:'<img src=x>',themes:['<img src=x>'],organizer:'<script>bad</script>'})]);
  assert.equal(scanner.events.length,1);
  scanner.renderEvents(scanner.events);
  const html = get('eventsList').innerHTML;
  assert.ok(!html.includes('<img'));
  assert.ok(html.includes('&lt;img'));
  assert.ok(!html.includes('<script>bad'));
  assert.ok(html.includes('rel="noopener noreferrer"'));
});

test('submission windows retain source dates and do not affect duration score', () => {
  const {scanner} = setup();
  scanner.processData([event({start:`${futureYear}-01-01T00:00:00Z`,dateKind:'Submission window'})]);
  assert.equal(scanner.events[0].startKey,`${futureYear}-01-01`);
  assert.equal(scanner.events[0].competitiveness,0);
  assert.equal(scanner.events[0].durationStr,'Submission window');
});

test('calendar follows filtered events and crosses year boundaries', () => {
  const {scanner,get} = setup('2026-12-28T20:00:00Z');
  scanner.processData([event({start:'2027-01-01T15:00:00Z',end:'2027-01-03T20:00:00Z'})]);
  scanner.renderCalendar([]);
  assert.ok(!get('calendarGrid').innerHTML.includes(' has-event'));
  scanner.renderCalendar(scanner.events);
  assert.ok(get('calendarGrid').innerHTML.includes('January 2027'));
  assert.ok(get('calendarGrid').innerHTML.includes('data-date="2027-01-02" aria-label="2027-01-02, events available"'));
});

test('keyword search combines fields, phrases, alternatives, exclusions and accents', () => {
  const {scanner,get} = setup();
  scanner.processData([
    event({name:'Agent Build',themes:['Machine Learning','Climate'],organizer:'Université Club',description:'Create useful tools with AI'}),
    event({name:'Design Sprint',themes:['Art'],organizer:'Local Studio'})
  ]);
  const count = query => {get('locSearch').value = query; return scanner.getFiltered().length;};
  assert.equal(count('agent climate'),1);
  assert.equal(count('universite'),1);
  assert.equal(count('"machine learning"'),1);
  assert.equal(count('climate OR art'),2);
  assert.equal(count('climate, art'),2);
  assert.equal(count('AI -climate'),0);
  assert.equal(count('"learning machine"'),0);
});

test('source filter keeps cross-listed events under every contributing source', () => {
  const {scanner,get} = setup();
  scanner.processData([event({source:'Eventbrite / Luma',sources:['Eventbrite','Luma']}),event({name:'Other',source:'Devpost'})]);
  get('sourceFilter').value = 'Luma';
  assert.equal(scanner.getFiltered().length,1);
  get('sourceFilter').value = 'Eventbrite';
  assert.equal(scanner.getFiltered().length,1);
  get('sourceFilter').value = 'all';
  assert.equal(scanner.getFiltered().length,2);
});
