const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const Fuse = require('../themes/PaperMod/assets/js/fuse.basic.min.js');

const moduleSource = fs.readFileSync(path.join(__dirname, '../assets/js/guide-search.js'), 'utf8');
const searchModule = import('data:text/javascript;base64,' + Buffer.from(moduleSource).toString('base64'));
const documents = [
    { title: 'Privacy Policy', content: 'We may delete information.', permalink: '/privacy/' },
    { title: 'Airport transfer planning', content: 'A Deluxe vehicle is a service category.', permalink: '/transfer/' },
    { title: 'Incheon Taxi: Deluxe or Large?', content: 'Choose capacity before paying.', permalink: '/taxi/' },
    { title: 'KTX luggage rules', content: 'Keep your bags with you.', permalink: '/luggage/' },
    { title: 'Korean honorifics: 존댓말 and 반말', content: 'Use polite speech.', permalink: '/honorifics/' }
];

test('Deluxe excludes unrelated near-spelling text and ranks the title above a body mention', async () => {
    const { createGuideSearch } = await searchModule;
    const found = createGuideSearch(documents, Fuse)('Deluxe');
    assert.equal(found.approximate, false);
    assert.deepEqual(found.results.map(({ item }) => item.permalink), ['/taxi/', '/transfer/']);
});

test('multiple words can appear in either order but every word must occur', async () => {
    const { createGuideSearch } = await searchModule;
    const find = createGuideSearch(documents, Fuse);
    assert.deepEqual(find('luggage KTX').results.map(({ item }) => item.permalink), ['/luggage/']);
    assert.equal(find('KTX taxi').results.length, 0);
});

test('typing prefixes, punctuation, case and Korean terms remain searchable', async () => {
    const { createGuideSearch } = await searchModule;
    const find = createGuideSearch(documents, Fuse);
    assert.equal(find(' INCheon—delu ').results[0].item.permalink, '/taxi/');
    assert.equal(find('존댓말').results[0].item.permalink, '/honorifics/');
    assert.equal(find('   ').results.length, 0);
    assert.equal(find('???').results.length, 0);
});

test('a typo offers labelled title suggestions without mixing them into exact matches', async () => {
    const { createGuideSearch } = await searchModule;
    const found = createGuideSearch(documents, Fuse)('Deluxxe');
    assert.equal(found.approximate, true);
    assert.equal(found.results[0].item.permalink, '/taxi/');
    assert.ok(!found.results.some(({ item }) => item.permalink === '/privacy/'));
});

test('published corpus keeps the reported false positive out and finds key reader tasks', async () => {
    const { createGuideSearch } = await searchModule;
    const data = JSON.parse(fs.readFileSync(path.join(__dirname, '../public/index.json'), 'utf8'));
    const find = createGuideSearch(data, Fuse);
    const deluxe = find('Deluxe');
    assert.equal(deluxe.results[0].item.permalink, 'https://lovekorea.me/posts/incheon-taxi-four-people-luggage/');
    assert.ok(!deluxe.results.some(({ item }) => item.permalink.endsWith('/privacy/')));
    for (const [query, slug] of [
        ['luggage KTX', '/posts/ktx-luggage-two-bag-rule/'],
        ['NAVER address', '/posts/naver-map-hotel-address-search/'],
        ['lost phone', '/posts/lost-phone-seoul-taxi-subway/'],
        ['존댓말', '/posts/korean-honorifics-banmal-guide/']
    ]) {
        assert.ok(find(query).results.slice(0, 5).some(({ item }) => item.permalink === 'https://lovekorea.me' + slug), query);
    }
    assert.equal(find('qzxwvunfindable').results.length, 0);
});
