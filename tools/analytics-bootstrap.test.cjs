const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../static/js/analytics-bootstrap.js'), 'utf8');
const tracker = fs.readFileSync(path.join(__dirname, '../static/js/affiliate-tracking.js'), 'utf8');
const tagId = 'G-2RHGK56598';

function visit(url = 'https://lovekorea.me/posts/example/', options = {}) {
  const store = options.store || new Map();
  const scripts = [];
  const listeners = new Map();
  const window = { location: new URL(url) };
  if (options.dataLayer) window.dataLayer = options.dataLayer;
  Object.defineProperty(window, 'sessionStorage', { get() {
    if (options.storageBlocked) throw new Error('Storage denied');
    return {
      setItem: (key, value) => store.set(key, value),
      getItem: key => store.get(key) ?? null
    };
  } });
  const context = vm.createContext({ window, URL, URLSearchParams, console, document: {
    createElement(name) { assert.equal(name, 'script'); return {}; },
    head: { appendChild(script) { scripts.push(script); } },
    addEventListener: (name, callback) => listeners.set(name, callback)
  } });
  vm.runInContext(options.source || source, context);
  return { window, scripts, store,
    clickOffer(marker) {
      vm.runInContext(tracker, context);
      const values = { href: 'https://partner.example.test/activity?ref=existing', [marker]: '1' };
      const original = { ...values };
      const anchor = { getAttribute: name => values[name] ?? null, closest: () => anchor };
      listeners.get('click')({ target: anchor,
        preventDefault() { assert.fail('Analytics must not block navigation'); }
      });
      assert.deepEqual(values, original, 'The destination and referral parameters stay intact');
    }
  };
}

function assertExcluded(page) {
  assert.equal(page.window['ga-disable-' + tagId], true);
  assert.equal(page.window.gtag, undefined);
  assert.equal(page.window.dataLayer, undefined);
  assert.equal(page.scripts.length, 0, 'No remote measurement library is requested');
}

test('ordinary canonical visitors keep one standard GA config and the existing queue', () => {
  const existing = ['previous entry'];
  const page = visit(undefined, { dataLayer: existing });
  assert.equal(page.window.dataLayer, existing);
  assert.equal(existing.length, 3);
  assert.equal(existing[1][0], 'js');
  assert.deepEqual(Array.from(existing[2]), ['config', tagId]);
  assert.equal(page.scripts.length, 1);
  assert.equal(page.scripts[0].src, 'https://www.googletagmanager.com/gtag/js?id=' + tagId);
  assert.equal(page.scripts[0].async, true);
  assert.equal(page.window['ga-disable-' + tagId], undefined);
  assert.equal(page.store.size, 0, 'Ordinary visitors get no QA marker');
});

test('explicit QA URL excludes the first page and following unmarked pages in the tab', () => {
  const first = visit('https://lovekorea.me/posts/example/?lk_qa=1');
  assertExcluded(first);
  const next = visit('https://lovekorea.me/search/', { store: first.store });
  assertExcluded(next);
  assert.equal(visit().scripts.length, 1, 'A fresh unmarked tab still measures readers');
});

test('a marked URL remains excluded when browser storage throws', () => {
  assertExcluded(visit('https://lovekorea.me/?lk_qa=1', { storageBlocked: true }));
  assert.equal(visit(undefined, { storageBlocked: true }).scripts.length, 1);
});

test('only the exact opt-out query value or session marker enables QA mode', () => {
  for (const suffix of ['?lk_qa=0', '?lk_qa=true', '?utm_campaign=lk_qa%3D1', '#lk_qa=1']) {
    assert.equal(visit('https://lovekorea.me/' + suffix).scripts.length, 1, suffix);
  }
  assert.equal(visit(undefined, { store: new Map([['lovekorea_qa', '0']]) }).scripts.length, 1);
});

test('local, staging, and lookalike hosts cannot send production measurements', () => {
  for (const url of ['http://127.0.0.1:8765/', 'http://localhost:1313/',
    'https://preview.example.test/', 'https://lovekorea.me.example.test/',
    'https://www.lovekorea.me/']) assertExcluded(visit(url));
});

for (const [marker, event] of [
  ['data-affiliate', 'affiliate_click'], ['data-outbound-offer', 'offer_outbound_click']
]) {
  test(event + ' remains queued for readers and absent for QA without changing links', () => {
    const reader = visit();
    reader.clickOffer(marker);
    assert.equal(reader.window.dataLayer.length, 3);
    assert.equal(reader.window.dataLayer[2][1], event);
    const qa = visit('https://lovekorea.me/?lk_qa=1');
    qa.clickOffer(marker);
    assertExcluded(qa);
  });
}

const builtHome = path.join(__dirname, '../public/index.html');
if (fs.existsSync(builtHome)) {
  test('built HTML runs the same exclusion before any remote Google tag', () => {
    const html = fs.readFileSync(builtHome, 'utf8');
    const match = html.match(/<script data-lk-analytics-bootstrap[^>]*>([\s\S]*?)<\/script>/);
    assert.ok(match, 'The production template must include the guard inline');
    assert.doesNotMatch(html, /<script[^>]+src=["']?https:\/\/www\.googletagmanager\.com/);
    assertExcluded(visit('https://lovekorea.me/?lk_qa=1', { source: match[1] }));
    assert.equal(visit(undefined, { source: match[1] }).scripts.length, 1);
    const privacy = fs.readFileSync(path.join(__dirname, '../public/privacy/index.html'), 'utf8');
    assert.doesNotMatch(privacy, /data-lk-analytics-bootstrap|googletagmanager\.com|affiliate-tracking\.js/);
  });
}
