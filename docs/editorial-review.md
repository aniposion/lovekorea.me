# Editorial review before publishing

The legacy paid generator in `create_post.py` is disabled. `run_automation.bat`
stops at that step; it must not generate, stage every file, or publish unattended.
The active operating workflow prepares and reviews individual changes.

## A publishable guide

- Define the reader's decision and answer it in the opening paragraph.
- A numbered title must deliver that many real, distinguishable items.
- Link mutable facts to the specific official page checked, with a check date.
- Use the source's actual date and scope. A price range needs evidence too.
- Show an original comparison, calculation, route, decision table, or other
  concrete help beyond rephrasing the sources.
- Never fabricate visits, product tests, testimonials, qualifications, or photos.
- Label hypothetical examples and distinguish illustrations from evidence.
- Remove internal research notes, repetitive sales prompts, and unsupported
  discount promises. A minimum word count is not a quality requirement.
- Keep original publication dates. Change `lastmod` for substantive revisions.
- Link relevant follow-up guides and explain affiliate relationships near links.

## Required article images

- The owner's October 23, 2026 instruction requires natural, photorealistic
  images with each new article. Use the built-in image generation tool; do not
  replace the requested photographic asset with a code-drawn text card or diagram.
- Save each final image in the repository and set its cover image, descriptive
  alt text, `style: photorealistic`, and `showInArticle: true`. A social preview
  image or homepage thumbnail alone does not satisfy the article-image requirement.
- Include optimized 480px and 960px variants in `cover.small` and `cover.medium`.
  Review the full image and its actual mobile crop for coherent subjects, natural
  texture, legible composition, malformed anatomy, invented signs and misleading
  product or location details. A text overlay is optional, never a replacement
  for the photographic scene.
- Label generated scenes briefly as AI-generated editorial images. Do not present
  them as photographs documenting a visit, an official screen, a product test,
  a verified facility layout or current availability.
- If image generation is unavailable, keep the article in preparation and record
  the missing asset. Do not silently publish a text-only article or use a paid
  API fallback without the owner's authorization.

## Review and deploy

1. Read the current operating record and inspect the diff.
2. Run monetization lint, internal-link audit, relevant content/cover checks,
   production Hugo build, indexing audit, `python tools/audit_social_images.py`,
   `python tools/audit_article_images.py`, and Pagefind. Static covers under `/images/` use `cover.relative: false`;
   the social-image audit checks rendered Open Graph, Twitter and article schema
   against image files in the build.
3. Check the actual rendered page, including mobile when layout changes.
4. Stage only the reviewed files, commit, push, and confirm the public result.
5. Record source evidence, corrections, limitations, and the remaining review queue
   in the private operating record, never in reader-facing pages.

Do not treat passing technical checks as proof of factual quality or AdSense
eligibility. A review request must follow completion of the substantive content
review; approval and revenue cannot be guaranteed.
