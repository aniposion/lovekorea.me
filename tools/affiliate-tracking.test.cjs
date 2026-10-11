const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(
  path.join(__dirname, '..', 'static', 'js', 'affiliate-tracking.js'), 'utf8'
);

function tracker({ analytics = true } = {}) {
  const events = [];
  const listeners = new Map();
  const window = {
    location: new URL('https://lovekorea.me/posts/example/?token=page-secret#private')
  };
  if (analytics) window.gtag = (...args) => events.push(args);
  vm.runInNewContext(source, {
    window,
    document: {
      addEventListener: (name, callback) => listeners.set(name, callback)
    },
    URL,
    console
  });

  return {
    events,
    click(href, attributes = {}) {
      const values = { ...attributes, href };
      const before = { ...values };
      const anchor = {
        getAttribute: (name) => values[name] ?? null,
        closest(selector) {
          if (selector === 'a[href]') return this;
          return values['data-affiliate'] === '1' || values['data-outbound-offer'] === '1'
            ? this : null;
        }
      };
      // Exercise delegated clicks on a child of the anchor, as in the real UI.
      listeners.get('click')({
        target: { closest: (selector) => anchor.closest(selector) },
        preventDefault() { assert.fail('Tracking must not cancel navigation'); }
      });
      assert.deepEqual(values, before, 'Tracking must preserve the original link');
    },
    clickNonElement() {
      listeners.get('click')({ target: {} });
    }
  };
}

test('owned-shop events remove URL secrets while retaining attribution labels', () => {
  const instance = tracker();
  instance.click('https://user:password@obanghouse.com/products/bag?utm_source=lovekorea&' +
    'utm_content=footer&utm_campaign=autumn&email=reader%40example.test&token=secret#access_token=private');
  const [command, name, data] = instance.events[0];
  assert.equal(command, 'event');
  assert.equal(name, 'owned_shop_click');
  assert.equal(data.link_url, 'https://obanghouse.com/products/bag');
  assert.equal(data.placement, 'footer');
  assert.equal(data.campaign, 'autumn');
  assert.equal(data.shop_name, 'obang_house');
  assert.equal(data.page_path, '/posts/example/');
  assert.equal(instance.events.length, 1);
  assert.doesNotMatch(JSON.stringify(data), /secret|private|password|reader|access_token/);
});

for (const [marker, eventName] of [
  ['data-affiliate', 'affiliate_click'],
  ['data-outbound-offer', 'offer_outbound_click']
]) {
  test(`${eventName} sends only the destination origin and path`, () => {
    const instance = tracker();
    instance.click('https://user:password@booking.example.test:8443/activity/123?' +
      'affiliate_id=42&email=reader%40example.test&token=secret&redirect=https%3A%2F%2Fexample.test#private', {
      [marker]: '1',
      'data-slot': 'KOREA_TOUR_DEALS',
      'data-pos': 'top',
      'data-provider': 'klook',
      'data-page-type': 'post',
      'data-page-path': '/posts/example/',
      'data-slug': 'example',
      'data-page-category': 'k-travel'
    });
    const [command, name, data] = instance.events[0];
    assert.equal(command, 'event');
    assert.equal(name, eventName);
    assert.equal(data.link_url, 'https://booking.example.test:8443/activity/123');
    assert.equal(data.slot, 'KOREA_TOUR_DEALS');
    assert.equal(data.pos, 'top');
    assert.equal(data.provider, 'klook');
    assert.equal(data.page_type, 'post');
    assert.equal(data.page_path, '/posts/example/');
    assert.equal(data.slug, 'example');
    assert.equal(data.page_category, 'k-travel');
    assert.equal(instance.events.length, 1);
    assert.doesNotMatch(JSON.stringify(data), /secret|private|password|reader|redirect/);
  });
}

test('relative and protocol-relative destinations are resolved without queries or fragments', () => {
  for (const [href, expected] of [
    ['/deals/?token=secret#private', 'https://lovekorea.me/deals/'],
    ['../other/?email=reader%40example.test', 'https://lovekorea.me/posts/other/'],
    ['//partner.example.test/path?code=secret', 'https://partner.example.test/path'],
    ['http://partner.example.test/path?code=secret', 'http://partner.example.test/path'],
    ['https://partner.example.test/path', 'https://partner.example.test/path']
  ]) {
    const instance = tracker();
    instance.click(href, { 'data-outbound-offer': '1' });
    assert.equal(instance.events[0][2].link_url, expected);
  }
});

test('missing, malformed, and non-HTTP destinations never fall back to raw values', () => {
  for (const href of [null, '', '  ', 'https://[invalid', 'javascript:alert(1)',
    'data:text/plain,secret', 'mailto:reader@example.test?body=secret', 'tel:123456',
    'ftp://example.test/private']) {
    const instance = tracker();
    instance.click(href, { 'data-affiliate': '1' });
    assert.equal(instance.events.length, 0, String(href));
  }
});

test('business inquiries send only the recognized inquiry type and page path', () => {
  const instance = tracker();
  instance.click('mailto:admin@yoonisoft.com?subject=LoveKorea%20sponsorship%20inquiry&body=secret');
  assert.equal(instance.events.length, 1);
  assert.equal(instance.events[0][1], 'business_inquiry_click');
  assert.deepEqual(JSON.parse(JSON.stringify(instance.events[0][2])), {
    inquiry_type: 'sponsorship', page_path: '/posts/example/'
  });
});

test('unmarked links and lookalike shop hosts do not produce owned-shop events', () => {
  const instance = tracker();
  for (const href of [
    'https://example.test/?token=secret',
    'https://obanghouse.com.evil.test/?utm_source=lovekorea',
    'https://obanghouse.com/?utm_source=another',
    'http://obanghouse.com/?utm_source=lovekorea'
  ]) instance.click(href);
  instance.clickNonElement();
  assert.equal(instance.events.length, 0);
});

test('analytics unavailability never interferes with navigation', () => {
  const instance = tracker({ analytics: false });
  instance.click('https://obanghouse.com/?utm_source=lovekorea&token=secret');
  instance.click('https://partner.example.test/?token=secret', { 'data-affiliate': '1' });
  instance.click('mailto:admin@yoonisoft.com?subject=LoveKorea%20sponsorship%20inquiry');
  assert.equal(instance.events.length, 0);
});
