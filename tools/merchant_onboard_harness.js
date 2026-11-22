// Headless harness for preview/merchant-onboard.html: runs the page's own
// inline script against a minimal DOM stub and drives the checklist. Proves
// AC-MO5 (arithmetic and printed counts) and AC-MO4/AC-MO6 surface laws
// without a browser.
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const payloadText = /<script id="payload" type="application\/json">([\s\S]*?)<\/script>/.exec(html)[1];
const pageCode = /<script>([\s\S]*?)<\/script>/.exec(html)[1];
const payload = JSON.parse(payloadText);

function Node(tag, attrs) {
  this.tag = tag; this.children = []; this._text = ''; this.className = '';
  this.checked = false; this.disabled = false; this.handlers = {};
  this.attrs = attrs || {};
}
Object.defineProperty(Node.prototype, 'textContent', {
  get() { return this._text; },
  set(v) { this._text = v; this.children = []; }
});
Object.defineProperty(Node.prototype, 'innerHTML', {
  get() { return ''; },
  set(v) { this.children = []; }
});
Node.prototype.appendChild = function (n) { this.children.push(n); return n; };
Node.prototype.setAttribute = function (k, v) { this.attrs[k] = v; };
Node.prototype.getAttribute = function (k) { return this.attrs[k] === undefined ? null : this.attrs[k]; };
Node.prototype.addEventListener = function (e, f) { this.handlers[e] = f; };

const ids = {};
function node(id) {
  if (!ids[id]) { ids[id] = new Node('div'); ids[id].attrs.id = id; }
  return ids[id];
}

// mirror the server-rendered checkboxes: one per item, proven ones pre-ticked
const boxes = payload.items.map((it) => {
  const n = new Node('input', { id: 'tick-' + it.id, 'data-item': it.id, type: 'checkbox' });
  n.checked = !!it.proven;
  n.disabled = !!it.proven;
  return n;
});

const store = {};
const localStorage = {
  getItem: (k) => (store[k] === undefined ? null : store[k]),
  setItem: (k, v) => { store[k] = String(v); },
};

const document = {
  getElementById: (id) => node(id),
  querySelectorAll: (sel) => (sel === 'input.tick' ? boxes : []),
  createElement: (t) => new Node(t),
  createTextNode: (t) => ({ tag: '#text', textContent: t, children: [] }),
};

node('payload').textContent = payloadText;
new Function('document', 'localStorage', 'setTimeout', pageCode)(document, localStorage, (fn) => fn());

function box(id) { return boxes.find((b) => b.getAttribute('data-item') === id); }
function txt(id) { return node(id).textContent; }
const out = [];
function ok(name, cond, detail) {
  out.push((cond ? 'PASS ' : 'FAIL ') + name + (detail ? ' :: ' + detail : ''));
  if (!cond) process.exitCode = 2;
}

const ceoItems = payload.items.filter((i) => i.owner === 'ceo');
const provenItems = payload.items.filter((i) => i.proven);
const total = payload.items.length;

// 1) initial state is server-rendered and consistent with the payload
ok('initial progress printed', /0\/6/.test(txt('progress')), txt('progress'));
ok('initial proven count matches payload', txt('progress').indexOf(String(provenItems.length) + '/' + total) >= 0, txt('progress'));
ok('initial verdict refuses to open the door', txt('verdict').indexOf('\u8fd8\u4e0d\u80fd\u5f00\u95e8') >= 0, txt('verdict'));
ok('initial verdict carries the fail class', node('verdict').className.indexOf('fail') >= 0, node('verdict').className);

// 2) proven items are locked, CEO items are not
ok('proven boxes are checked and disabled', provenItems.every((i) => box(i.id).checked && box(i.id).disabled));
ok('ceo boxes start unticked and enabled', ceoItems.every((i) => !box(i.id).checked && !box(i.id).disabled));

// 3) ticking every CEO item reaches declared==ceo but never claims payable
ceoItems.forEach((i) => { box(i.id).checked = true; box(i.id).handlers.change(); });
ok('all ceo declared printed', txt('progress').indexOf(String(ceoItems.length) + '/' + ceoItems.length) >= 0, txt('progress'));
ok('declared-but-not-verified verdict', txt('verdict').indexOf('\u4ecd\u4e0d\u80fd\u5f00\u95e8') >= 0, txt('verdict'));
ok('verdict stays fail at full declaration', node('verdict').className.indexOf('fail') >= 0, node('verdict').className);
ok('ticks persisted to localStorage', !!store['bd-merchant-onboard-v1'] && JSON.parse(store['bd-merchant-onboard-v1']).mchid === true, store['bd-merchant-onboard-v1']);

// 4) arithmetic is re-derived, not accumulated: untick one and come back
box('mchid').checked = false; box('mchid').handlers.change();
ok('untick lowers declared count', txt('progress').indexOf(String(ceoItems.length - 1) + '/' + ceoItems.length) >= 0, txt('progress'));
ok('missing count printed', txt('verdict').indexOf(String(total - provenItems.length - (ceoItems.length - 1))) >= 0, txt('verdict'));

// 5) reset clears only the self-declared side, evidence stays
node('reset').handlers.click();
ok('reset returns declared to zero', txt('progress').indexOf('0/' + ceoItems.length) >= 0, txt('progress'));
ok('reset keeps proven evidence', provenItems.every((i) => box(i.id).checked && box(i.id).disabled));

// 6) self-test lines are computed and all pass
const lines = node('selftest').children.map((c) => (c.children[0] ? c.children[0].textContent : ''));
ok('self-test has three lines', lines.length === 3, 'lines=' + lines.length);
ok('self-test all PASS', lines.every((l) => l.indexOf('PASS') === 0), lines.join(' | '));

// 7) surface laws the harness can still see in the file
ok('no password input in the face', !/type\s*=\s*["']password/i.test(html));
ok('no textarea in the face', html.toLowerCase().indexOf('<textarea') < 0);
ok('secret rule sentence present', html.indexOf(payload.secret_rule) >= 0);
ok('three bands present', payload.bands.length === 3 && payload.bands.every((b) => html.indexOf(b) >= 0));

console.log(out.join('\n'));
console.log('HARNESS ' + (process.exitCode === 2 ? 'FAIL' : 'PASS') + ' checks=' + out.length);
