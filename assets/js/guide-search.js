function words(text) {
    return String(text || '').normalize('NFKC').toLowerCase().match(/[\p{L}\p{N}]+/gu) || [];
}

export function createGuideSearch(data, Fuse, configured = {}) {
    const entries = data.map((item) => ({
        item,
        titleWords: words(item.title),
        bodyWords: words(item.content)
    }));
    // Typo suggestions use titles: approximate matches deep in a long article
    // can otherwise make unrelated pages look like answers to a short query.
    const suggestions = new Fuse(data, {
        keys: ['title'],
        threshold: configured.threshold ?? 0.3,
        ignoreLocation: true
    });
    const limit = configured.limit;

    return function findGuides(query) {
        const terms = [...new Set(words(query))];
        if (!terms.length) return { results: [], approximate: false };
        const matches = (field, term) => field.some((word) => word.startsWith(term));
        const results = entries
            .filter(({ titleWords, bodyWords }) => terms.every((term) =>
                matches(titleWords, term) || matches(bodyWords, term)))
            .map(({ item, titleWords }) => ({
                item,
                titleMatches: terms.filter((term) => matches(titleWords, term)).length
            }))
            .sort((a, b) => b.titleMatches - a.titleMatches);

        if (results.length) {
            return { results: limit > 0 ? results.slice(0, limit) : results, approximate: false };
        }
        // Avoid broad typo guesses for one- or two-character input.
        if (terms.join('').length < 3) return { results: [], approximate: false };
        return {
            results: suggestions.search(query, { limit: limit > 0 ? limit : 10 }),
            approximate: true
        };
    };
}
