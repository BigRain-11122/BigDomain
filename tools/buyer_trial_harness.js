// Headless harness for preview/buyer-trial.html: runs the page's own inline
// script against a minimal DOM stub and drives one purchase plus a repeated
// callback. Proves AC-BT4 (books balance) and AC-BT5 (idempotent) without a browser.
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const payloadText = /<script id="payload" type="application\/json">([\s\S]*?)<\/script>/.exec(html)[1];
const code = /<script>([\s\S]*?)<\/script>/.exec(html)[1];

function Node(tag) {
  this.tag = tag; this.children = []; this._text = ''; this.className = '';
  this.hidden = false; this.attrs = {}; this.handlers = {};
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
Object.defineProperty(Node.prototype, 'rows', {
  get() { return this.children.filter((c) => c.tag === 'tr'); },
});
Node.prototype.setAttribute = function (k, v) { this.attrs[k] = v; };
Node.prototype.getAttribute = function (k) { return this.attrs[k]; };
Node.prototype.addEventListener = function (e, f) { this.handlers[e] = f; };

const ids = {};
function node(id) { if (!ids[id]) { ids[id] = new Node('div'); ids[id].attrs.id = id; } return ids[id]; }

const products = [];
for (const p of JSON.parse(payloadText).products) {
  const n = new Node('div');
  n.attrs.class = 'prod';
  n.attrs['data-product'] = p.id;
  products.push(n);
}

const document = {
  getElementById: (id) => node(id),
  querySelectorAll: (sel) => (sel === '.prod' ? products : []),
  createElement: (t) => new Node(t),
  createTextNode: (t) => ({ tag: '#text', textContent: t, children: [] }),
};

// run the page script with a synchronous timer so the callback lands immediately
node('payload').textContent = payloadText;   // the page reads its data from this node
new Function('document', 'setTimeout', code)(document, (fn) => fn());

function rows(id) { return node(id).children.length; }
const out = [];
function ok(name, cond, detail) {
  out.push((cond ? 'PASS ' : 'FAIL ') + name + (detail ? ' :: ' + detail : ''));
  if (!cond) process.exitCode = 2;
}

// 1) a virtual-channel product can be ordered and paid
products[1].handlers.click();
ok('order created', node('oid').textContent === 'BT-0001', node('oid').textContent);
node('pay').handlers.click();
ok('virtual product booked', node('ostatus').textContent === '已入账', node('ostatus').textContent);
const cashAfter = rows('cashbook'), tokenAfter = rows('tokenbook');
ok('cash book has 2 entries (4 legs)', cashAfter === 2, 'entries=' + cashAfter);
ok('token book has 1 entry (2 legs)', tokenAfter === 1, 'entries=' + tokenAfter);
ok('books balance', /配平/.test(node('balance').textContent) && /pass/.test(node('balance').className),
   node('balance').textContent);
ok('receipt delivered', node('receipt').children.length > 0, 'children=' + node('receipt').children.length);

// 2) repeated callback must not double-book
node('replay').handlers.click();
node('replay').handlers.click();
ok('repeated callback books nothing', rows('cashbook') === cashAfter && rows('tokenbook') === tokenAfter,
   'cash=' + rows('cashbook') + ' token=' + rows('tokenbook'));
const logText = node('log').children.map((c) => c.children[0] ? c.children[0].tag : '').join('|');
const logPlain = node('log').children.length;
ok('idempotent replay logged', logPlain >= 5, 'log_lines=' + logPlain);

// 3) a standard-channel product must refuse to pass
products[2].handlers.click();
ok('standard channel blocked', node('pay').disabled === true && node('blocked').hidden === false,
   'pay.disabled=' + node('pay').disabled + ' blocked.hidden=' + node('blocked').hidden);

// 4) reset clears both books
node('reset').handlers.click();
ok('reset clears books', rows('cashbook') === 0 && rows('tokenbook') === 0,
   'cash=' + rows('cashbook') + ' token=' + rows('tokenbook'));

console.log(out.join('\n'));
console.log('HARNESS ' + (process.exitCode === 2 ? 'FAIL' : 'PASS') + ' checks=' + out.length);
