# LoveKorea AdSense Readiness Design

Last updated: 2026-07-02

## 1. Purpose

This document defines the work needed to make LoveKorea (`lovekorea.me`) ready for AdSense review and early monetization without weakening user experience or looking like a low-value ad site.

The goal is not to maximize ad density immediately. The goal is to make the site look trustworthy, useful, navigable, and policy-aware before applying or expanding ad coverage.

## 2. Current State

LoveKorea already has a usable content base:

- About 80+ published posts.
- Category hubs for travel, beauty, food, Korean learning, culture, trends, and deals.
- A Deals hub with affiliate disclosure patterns and inactive Amazon slots.
- Google Analytics already present in `layouts/partials/head.html`.
- Existing monetization linting via `tools/lint_monetization.py`.
- Existing cover image validation via `tools/validate_covers.py`.

Main gaps before AdSense:

- No dedicated Privacy Policy page.
- No dedicated Contact page.
- No dedicated Terms page.
- No standalone Affiliate Disclosure page.
- Some older posts have weak AI-style writing, broken encoding, thin content, or missing/low-quality images.
- No formal ad placement rules yet.

## 3. Policy Basis

Implementation should follow the current Google AdSense and Google Publisher policy direction:

- Site should have useful, original, easy-to-navigate content before review.
  Reference: https://support.google.com/adsense/answer/7299563
- Publisher must own/control the site and comply with AdSense eligibility requirements.
  Reference: https://support.google.com/adsense/answer/9724
- Privacy Policy should disclose Google advertising cookies, third-party vendors, personalized ads, and user opt-out paths.
  Reference: https://support.google.com/adsense/answer/1348695
- Ads must not mislead users, encourage accidental clicks, or be placed where they look like navigation/content controls.
  Reference: https://support.google.com/adsense/answer/1346295

This document is an engineering and content readiness plan, not legal advice.

## 4. Scope

### In Scope

1. Add trust and compliance pages.
2. Add navigation/footer links to those pages.
3. Define conservative AdSense placement.
4. Improve home-first content quality.
5. Audit and quarantine older low-quality posts.
6. Extend QA checks so missing covers and risky monetization patterns are caught before deploy.

### Out of Scope

- Aggressive ad optimization.
- Programmatic mass rewriting of all old posts.
- Auto ads everywhere.
- Cookie consent platform implementation, unless required by the target visitor regions.
- Legal localization for every jurisdiction.

## 5. Trust Page Design

Create four content pages under `content/`:

| Page | Path | Purpose | Menu |
|---|---|---|---|
| Privacy Policy | `content/privacy.md` | Disclose analytics, ads, cookies, affiliate tracking, third-party vendors, user controls | Footer, optional main menu |
| Contact | `content/contact.md` | Provide site owner/editor contact path and correction request process | Footer, optional main menu |
| Terms | `content/terms.md` | Explain use of content, no professional advice, affiliate/ad notices, limitations | Footer |
| Affiliate Disclosure | `content/affiliate-disclosure.md` | Central FTC-style disclosure for affiliate links, sponsored links, and editorial independence | Footer, Deals hub link |

Recommended front matter:

```yaml
---
title: "Privacy Policy"
description: "Privacy Policy for LoveKorea, including analytics, advertising cookies, affiliate links, and user choices."
date: 2026-07-02
showToc: true
draft: false
---
```

Page tone:

- Plain English.
- Clear and practical.
- No fake legal overclaiming.
- Explicitly name LoveKorea and `lovekorea.me`.
- Mention that policies may change and include a last-updated date.

## 6. Navigation and Layout Design

### Main Menu

Keep the top menu lean:

- Home
- Categories
- Deals
- Search
- About

Do not add all legal pages to the main menu. Too many top-level legal links makes the blog feel administrative.

### Footer

Add a footer legal row:

- Privacy Policy
- Contact
- Terms
- Affiliate Disclosure

Implementation option:

- Add a footer partial or extend the existing `layouts/partials/extend_footer.html`.
- Keep affiliate disclosure footer visible only as a compact compliance note, not a large repeated block.

## 7. Home-First Quality Cleanup

The home page is the first thing a reviewer and visitor will see. Before AdSense review, prioritize the first 12-20 posts visible on homepage/category pages.

Checklist per visible post:

- Has a real cover image.
- Cover path passes `tools/validate_covers.py`.
- Title is readable, not broken encoding.
- Description is specific and not clickbait.
- Opening paragraph explains the user benefit quickly.
- No obvious hallucinated current facts.
- No broken markdown image paths.
- No excessive affiliate/booking language in purely informational posts.

Acceptance rule:

- Home page should show no broken images.
- First viewport and first two homepage rows should look editorial, not auto-generated.

## 8. Old Content Quarantine / Rewrite Plan

Older content should be sorted into three buckets:

### Bucket A: Keep

Criteria:

- Useful topic.
- Readable title and body.
- Has image.
- No obvious factual or encoding issues.

Action:

- Leave published.

### Bucket B: Rewrite

Criteria:

- Good topic, weak execution.
- Missing or weak image.
- Thin article but salvageable.

Action:

- Rewrite manually or with controlled generation.
- Add/update images.
- Add front matter fields: `topic_pillar`, `target_intent`, `cover`.

### Bucket C: Hide

Criteria:

- Broken title/body encoding.
- Very thin, diary-like, or generic AI content.
- No good monetization/search value.
- Topic is outdated or risky to maintain.

Action:

- Set `draft: true` or move to an archive process.
- Do not delete immediately unless there is no search value and no internal links.

Initial target:

- Review 20 oldest/weakest posts.
- Hide or rewrite 10-20 before applying for AdSense.

## 9. Ad Placement Design

Start with conservative manual placements.

Recommended placements per post:

| Placement | Position | Rule |
|---|---|---|
| Top content ad | After intro / after first meaningful paragraph | Never before the title or immediately under nav |
| Mid content ad | Around 40-60% through article | Only if article is long enough |
| Bottom content ad | Before FAQ or after main conclusion | Clearly separated from content |

Avoid:

- Ads inside card grids.
- Ads that look like post thumbnails.
- Ads directly beside navigation buttons.
- Sticky ads during AdSense review.
- Excessive above-the-fold ads.
- Auto ads until manual placements are accepted and reviewed.

Suggested shortcode:

```go-html-template
{{< ad slot="post-top" >}}
{{< ad slot="post-mid" >}}
{{< ad slot="post-bottom" >}}
```

Shortcode behavior:

- Render nothing unless `params.ads.enabled = true`.
- Label ad container as `Advertisement`.
- Use reserved height to avoid layout shift.
- Never render inside lists/cards.

Suggested config:

```toml
[params.ads]
  enabled = false
  provider = "adsense"
  publisherId = ""
  testMode = true
```

Ad review strategy:

1. Apply with legal pages and cleaned content first.
2. Add AdSense script only after account/site approval flow requires it.
3. Start with manual in-article placements.
4. Enable Auto ads only after traffic and policy stability are confirmed.

## 10. Affiliate Monetization Design

Affiliate and AdSense can coexist, but the site should avoid looking like a pure affiliate bridge page.

Rules:

- Deals pages can use affiliate offers.
- Informational posts should be useful without clicking affiliate links.
- Every affiliate-heavy page needs clear disclosure near the top.
- Amazon slots remain inactive until a valid Associates tag is approved.
- External paid links should use `rel="nofollow sponsored noopener"`.

Existing tools:

- `layouts/shortcodes/affiliate-disclosure.html`
- `layouts/shortcodes/offer.html`
- `tools/lint_monetization.py`

Add:

- A standalone `Affiliate Disclosure` page.
- A link from Deals hub to the disclosure page.

## 11. Technical Implementation Plan

### Phase 1: Trust Pages

Files:

- `content/privacy.md`
- `content/contact.md`
- `content/terms.md`
- `content/affiliate-disclosure.md`
- Footer/menu partial or config update

Validation:

- `hugo --minify`
- Manual check of generated URLs:
  - `/privacy/`
  - `/contact/`
  - `/terms/`
  - `/affiliate-disclosure/`

### Phase 2: Homepage Quality Pass

Files:

- Selected `content/posts/*.md`
- Selected `static/images/*`

Checks:

- `python tools/validate_covers.py`
- Scan home/card image output.
- Confirm no broken images in first 12-20 visible posts.

### Phase 3: Old Post Quarantine

Process:

1. Generate candidate list by old date, short word count, missing cover, broken encoding, or placeholder image.
2. Manually inspect top 20.
3. Apply `draft: true` to hide the worst 10-20.
4. Rewrite only posts with real SEO/monetization value.

Acceptance:

- No obviously broken old posts are reachable from homepage/category first pages.
- Hidden posts should not break internal links.

### Phase 4: Ad Infrastructure

Files:

- `layouts/shortcodes/ad.html`
- `layouts/partials/head.html`
- `hugo.toml`
- Optional CSS in `static/css/custom.css`

Requirements:

- Disabled by default.
- No ad script when `params.ads.enabled = false`.
- Reserved ad box height to avoid layout shift.
- Clear `Advertisement` label.

### Phase 5: Conservative Ad Rollout

Rules:

- Apply only after trust pages and cleanup are complete.
- Enable on long posts first.
- Use max 3 in-content placements per post.
- Avoid sidebar/card-grid/native-looking ad placements.

## 12. QA Checklist

Run before applying or deploying monetization changes:

```powershell
python tools\validate_covers.py
python tools\lint_monetization.py
hugo --minify
git status --short
```

Manual checks:

- Homepage first viewport has no broken images.
- Legal pages render and are linked from footer.
- Privacy Policy mentions Google advertising cookies and opt-out.
- Contact page has a working contact method.
- Terms page has no overbroad legal promises.
- Affiliate Disclosure page matches actual monetization behavior.
- Ads, when enabled, are clearly labeled and not confused with content.

## 13. Acceptance Criteria

AdSense readiness is considered complete when:

- All four trust pages are live.
- Footer links exist for all trust pages.
- Deals hub links to Affiliate Disclosure.
- First 12-20 homepage/category-visible posts have acceptable cover images and readable titles.
- At least 10 weak old posts are hidden or queued for rewrite.
- Ad shortcode infrastructure exists but is disabled by default.
- Site builds cleanly.
- Cover and monetization lint pass with no blocking errors.

## 14. Recommended Execution Order

1. Add trust pages and footer links.
2. Add Deals hub link to Affiliate Disclosure.
3. Audit homepage visible posts and fix missing/weak covers.
4. Hide the worst old 10-20 posts.
5. Add disabled ad shortcode infrastructure.
6. Apply for AdSense or complete site review steps.
7. Enable conservative manual placements after approval.

## 15. Notes for Future Automation

The automated publisher should not add ads or affiliate slots blindly. It should:

- Require `cover.image`.
- Require `topic_pillar` and `target_intent`.
- Avoid affiliate blocks for purely informational posts unless the section is clearly useful.
- Insert ads only when the article length is sufficient.
- Never place ads in homepage card grids.
- Fail the batch if cover validation fails.

