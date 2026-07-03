# LoveKorea GSC Growth and Content Quality Design

Last updated: 2026-07-03

## 1. Purpose

This document defines the next growth pass for LoveKorea (`lovekorea.me`) after the AdSense readiness work.

The goal is to improve click-through rate, strengthen page quality, and build more high-intent content while keeping ads disabled until AdSense approval.

Primary baseline from the latest Search Console screenshot:

| Window | Clicks | Impressions | CTR | Average position |
|---|---:|---:|---:|---:|
| 28 days | 19 | 3.32k | 0.6% | 13.4 |

This means the site is already being discovered by Google, but the current search result presentation and content targeting are not yet strong enough to earn many clicks.

## 2. Operating Principles

1. Improve pages that already have Google impressions before creating too much new content.
2. Rewrite titles and descriptions for search intent, not for clickbait.
3. Keep home and category first screens clean, visual, and trustworthy.
4. Draft or rewrite older AI-feeling posts before they weaken review quality.
5. Add internal links so related pages support each other.
6. Publish more commercial-intent articles, especially price, booking, comparison, where-to-buy, and best-product guides.
7. Apply for AdSense, but keep `params.ads.enabled = false` until approval.

## 3. Policy and SEO References

Implementation should follow official Google guidance:

- SEO starter guide: https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- Title links: https://developers.google.com/search/docs/appearance/title-link
- Snippets and meta descriptions: https://developers.google.com/search/docs/appearance/snippet
- Helpful, reliable, people-first content: https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- Crawlable links: https://developers.google.com/search/docs/crawling-indexing/links-crawlable
- AdSense site readiness: https://support.google.com/adsense/answer/7299563

## 4. Workstream A: GSC Position 8-20 Title and Description Improvements

### Target Pages

Use Search Console export data to find pages and queries with:

- Average position between 8 and 20.
- Meaningful impressions in the last 28 days.
- CTR below the expected range for the position.
- Clear user intent.
- Existing content that can satisfy the query after minor improvement.

Suggested first-pass thresholds:

| Rule | Default |
|---|---:|
| Position range | 8.0 to 20.0 |
| Minimum impressions | 50 per 28 days |
| Maximum CTR | 1.5% |
| Minimum clicks | 0 allowed |
| Minimum content match | Manual review required |

### Opportunity Score

Rank candidates with this score:

```text
opportunity = impressions * position_weight * intent_weight * freshness_weight
```

Suggested weights:

| Factor | Value |
|---|---:|
| Position 8-12 | 1.4 |
| Position 12-16 | 1.2 |
| Position 16-20 | 1.0 |
| Price, ticket, booking, comparison, where-to-buy intent | 1.5 |
| Best, guide, list intent | 1.2 |
| Pure information intent | 1.0 |
| Page updated in last 90 days | 1.1 |
| Page older than 180 days | 0.9 |

### Title Rewrite Rules

Titles should make the searcher understand the exact value of the page before clicking.

Preferred formats:

```text
[Topic] 2026: Prices, Best Options, and Where to Buy
[A] vs [B] in Korea: Price, Booking, and Best Choice
How to Book [Thing] in Korea: Tickets, Routes, and Prices
Best [Product Type] in Korea 2026: Price Range and Where to Buy
[Place/Product] Price Guide 2026: What to Expect Before You Go
```

Rules:

- Put the main entity or task near the front.
- Use the current year only when the content is maintained.
- Include commercial modifiers only when the page actually answers them.
- Avoid changing slugs unless the current slug is broken or misleading.
- Avoid vague titles like "Complete Guide" when a stronger intent term exists.

### Description Rewrite Rules

Meta descriptions should be concise summaries of the decision the page helps users make.

Rules:

- Aim for 140 to 160 characters where possible.
- Include the main topic and user task.
- Mention price, ticket, route, comparison, booking, or where-to-buy value when relevant.
- Do not repeat the title word for word.
- Avoid unsupported claims like "ultimate", "guaranteed", or "best ever".

Example:

```text
Compare Seoul city tour bus routes, ticket prices, booking options, and who each pass is best for before planning your Korea trip.
```

### Measurement

Measure each edited page after 14 days and 28 days.

Success targets:

| Metric | Current baseline | 28-day target |
|---|---:|---:|
| Site CTR | 0.6% | 1.2%+ |
| Total clicks | 19 | 40+ |
| Edited-page CTR | Page-specific | 2x baseline |
| Edited-query position | 8-20 | Improve by 1-3 positions |

## 5. Workstream B: Home and Category First-Screen Quality

The home page and first category pages are review surfaces. They should look like a curated site, not an auto-generated archive.

### Required Quality Rules

For the first visible set of cards on the home page and each category page:

- Every visible article must have a working cover image.
- No broken images, empty image alt text, or tiny placeholder assets.
- No draft, thin, broken-title, or encoding-damaged articles.
- Titles should be readable and specific.
- Descriptions should not be generic filler.
- Dates should not make the site look abandoned.
- The first screen should include at least one strong, practical article per major category.

### Validation

Existing check:

```powershell
python tools\validate_covers.py
```

Recommended future check:

```powershell
python tools\audit_first_screen_quality.py
```

The future audit should verify:

- Home page first 12 posts.
- First 12 posts per category.
- Cover path exists.
- Description length is reasonable.
- Title has no encoding damage.
- Draft content is not listed.

## 6. Workstream C: Old AI-Feeling Content Cleanup

Older weak posts should be placed into one of three buckets:

| Bucket | Action |
|---|---|
| Keep | Strong topic, working image, acceptable details, can stay published |
| Rewrite | Useful search intent but weak body, weak title, or missing specifics |
| Draft | Broken, thin, generic, image-less, stale, or not aligned with site value |

### AI-Feeling Signals

Flag posts with several of these signals:

- Generic title with no price, location, comparison, or task.
- Body repeats broad claims without practical details.
- No useful tables, steps, examples, or decision criteria.
- Missing cover image.
- Cover image is unrelated or looks low-quality.
- Very short body for a competitive query.
- Overuse of generic phrases like "hidden gem", "must-visit", or "ultimate guide".
- Old date with no reason to stay evergreen.
- Poor internal linking.
- No Search Console impressions after indexing time.

### Cleanup Target

Next pass target:

- Review 30 old posts.
- Draft 10 to 20 weak posts.
- Rewrite 5 to 10 salvageable posts.
- Preserve URLs only when the topic has search value.

Do not delete posts by default. Drafting is safer than deleting because it avoids accidental loss and gives time to check internal links.

## 7. Workstream D: Internal Link Strengthening

Internal links should help users move through related decisions and help search engines understand content clusters.

### Per-Post Linking Standard

Every important published post should have:

- 3 to 5 relevant internal outbound links.
- At least 2 relevant inbound links from older posts where possible.
- Descriptive anchor text.
- Links placed inside useful context, not dumped at the bottom.

Bad anchor examples:

```text
click here
this article
read more
```

Good anchor examples:

```text
Korean skincare where-to-buy guide
Seoul city tour bus route comparison
Jeju pass price comparison
```

### Topic Clusters

Recommended clusters:

| Cluster | Hub intent | Supporting posts |
|---|---|---|
| K-beauty shopping | Where to buy, price, best products | Sunscreen, cushion, sheet masks, cica, glow makeup |
| Korea travel booking | Tickets, routes, passes, reservations | Bus passes, KTX, airport transfer, Jeju pass, cable car |
| K-food buying | Pantry, snacks, restaurants, convenience store | Gochujang, ramyeon, snacks, kimchi, street food |
| Korean learning | Practical phrases and etiquette | Shopping phrases, restaurant phrases, transit phrases |
| Deals | Affiliate and shopping discovery | Product roundups, seasonal deals, where-to-buy guides |

### Future Tooling

Recommended future check:

```powershell
python tools\audit_internal_links.py
```

Expected output:

- Posts with fewer than 3 internal links.
- Posts with zero inbound links.
- Broken internal links.
- Possible related posts by category and tag.

## 8. Workstream E: High-Intent Content Pipeline

New posts should prioritize searchers who are close to making a decision.

### Recommended Topic Mix

| Topic type | Share |
|---|---:|
| K-beauty where-to-buy, price, comparison, best products | 30% |
| Korea travel ticket, booking, route, pass, price | 30% |
| K-food where-to-buy, price, comparison, pantry guides | 20% |
| Korean learning with practical buyer/traveler context | 10% |
| K-culture evergreen explainers tied to products or visits | 10% |

### Article Templates

#### Price Guide

```text
Title: [Product/Place] Price Guide 2026: Costs, Options, and Tips
Sections:
- Quick answer
- Price table
- What affects the price
- Best option by traveler/buyer type
- Booking or buying tips
- Mistakes to avoid
- Related guides
- FAQ
```

#### Comparison

```text
Title: [A] vs [B] in Korea: Price, Pros, Cons, and Best Choice
Sections:
- Quick recommendation
- Comparison table
- Price and availability
- Best for each use case
- Where to buy or book
- Related guides
- FAQ
```

#### Where to Buy

```text
Title: Where to Buy [Product] in Korea 2026: Stores, Prices, and Tips
Sections:
- Best places to buy
- Price range
- Store-by-store comparison
- Online options
- What to check before buying
- Related guides
- FAQ
```

#### Booking Guide

```text
Title: How to Book [Ticket/Pass] in Korea: Routes, Prices, and Tips
Sections:
- Quick answer
- Booking options
- Route or pass comparison
- Price table
- Best option by itinerary
- Refund or timing notes
- Related guides
- FAQ
```

### Initial Topic Backlog

Priority topics for future posts:

1. Olive Young Sunscreen Price Guide 2026: Best Korean Sunscreens and Where to Buy
2. Where to Buy Korean Skincare in Seoul: Olive Young, Department Stores, and Duty Free
3. Myeongdong vs Hongdae vs Gangnam for K-Beauty Shopping: Prices and Best Stores
4. Korean Sheet Mask Price Guide 2026: Best Packs and Where to Buy
5. Cushion vs Foundation in Korea: Price, Finish, and Best Choice by Skin Type
6. Korea Airport eSIM vs SIM Card vs Wi-Fi Egg: Prices and Best Choice
7. KTX vs Express Bus from Seoul to Busan: Price, Time, and Booking
8. Jeju Car Rental Insurance Explained: Cost, Coverage, and Booking Tips
9. Best Korean Convenience Store Snacks 2026: Prices and What to Try
10. Gochujang vs Doenjang vs Ssamjang: Korean Pantry Guide and Where to Buy
11. Best Korean Ramyeon to Buy in Korea 2026: Price and Flavor Guide
12. Seoul City Tour Bus vs Subway Itinerary: Cost, Routes, and Best Choice

## 9. AdSense Application and Ad State

Apply for AdSense now because low traffic is not, by itself, a blocker for approval.

However, ad rendering must stay inactive until approval:

```toml
[params.ads]
enabled = false
provider = "adsense"
```

Before approval:

- Do not enable Auto Ads.
- Do not add placeholder ad boxes to article lists or sidebars.
- Do not make ad areas look like images or content cards.
- Keep legal pages visible in the footer.
- Keep affiliate disclosures available.

After approval:

- Enable manual in-article placements only.
- Start with one top, one middle, and one bottom ad slot.
- Avoid sidebar/list-card ad placements until traffic and UX are stronger.
- Monitor Search Console, Core Web Vitals, and user experience after enabling.

## 10. Implementation Plan

### Phase 1: Data and Audit

1. Export Search Console page/query data for the last 28 days.
2. Build or manually prepare a candidate list for position 8-20 pages.
3. Review home page and first category pages for image/title quality.
4. Review 30 older posts for AI-feeling signals.

Deliverables:

- GSC opportunity spreadsheet or CSV.
- List of top 20 title/description candidates.
- List of posts to keep, rewrite, or draft.

### Phase 2: Metadata and First-Screen Fixes

1. Rewrite titles and descriptions for the top 10 candidates.
2. Fix missing or weak cover images visible on home/category first screens.
3. Draft or rewrite the worst 10 to 20 older posts.
4. Run cover validation and Hugo build.

Deliverables:

- Updated front matter.
- Clean home/category first screens.
- Drafted low-quality posts.

### Phase 3: Internal Links

1. Add 3 to 5 contextual internal links to updated posts.
2. Add inbound links from related older posts.
3. Add or improve related-guide sections where natural.
4. Run internal link audit when tooling exists.

Deliverables:

- Stronger topic clusters.
- Fewer isolated posts.

### Phase 4: High-Intent Publishing

1. Publish 3 to 5 high-intent posts per month.
2. Use price, comparison, booking, where-to-buy, and best-product templates.
3. Link each new post into an existing cluster.
4. Check GSC after indexing.

Deliverables:

- Consistent commercial-intent content pipeline.
- Better affiliate and future ad monetization potential.

### Phase 5: AdSense Review

1. Submit AdSense application with ads still disabled on site.
2. Keep publishing and cleaning content during review.
3. Enable ad slots only after approval.

Deliverables:

- Site under review without aggressive ad UI.
- Clean post-approval ad activation path.

## 11. Acceptance Criteria

This design is complete when:

- At least 20 GSC opportunity pages are identified.
- Top 10 opportunity pages have improved titles and descriptions.
- Home first screen has no broken or low-quality visible images.
- Main category first screens have no broken or low-quality visible images.
- 10 to 20 old weak posts are drafted or assigned to rewrite.
- Important posts have at least 3 relevant internal links.
- At least 5 high-intent topic briefs are ready for publishing.
- `params.ads.enabled` remains `false` before approval.
- `python tools\validate_covers.py` passes.
- `python tools\lint_monetization.py --verbose` passes.
- `hugo --cleanDestinationDir --minify` passes.

## 12. Next Engineering Tasks

Recommended next code tasks:

1. Create `tools/gsc_opportunity_audit.py` to rank GSC CSV exports.
2. Create `tools/audit_first_screen_quality.py` for home/category visible-card checks.
3. Create `tools/audit_internal_links.py` for internal link counts and broken links.
4. Add a reusable related-guides partial or shortcode.
5. Extend `run_automation.bat` so audits can run before deployment.

