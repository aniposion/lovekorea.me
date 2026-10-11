# Security header and analytics rollout

Reviewed on October 11, 2026. The live homepage returned neither a CSP header nor
Permissions-Policy, and `/.well-known/security.txt` returned HTTP 404. The custom
click tracker sent complete destination URLs. These observations do not establish
an XSS vulnerability or an actual personal-data leak.

`security.txt` is optional contact metadata for vulnerability reports, not a
security control. It is intentionally not published for this site; its absence
does not require remediation.

## Changes

- The active Netlify configuration is `netlify.toml`. Security headers are also
  mirrored in the legacy `.netlify.toml` file to avoid conflicting examples.
- `Permissions-Policy` disables camera, microphone, and geolocation. The site
  does not use those browser APIs.
- The `link_url` parameter in `owned_shop_click`, `affiliate_click`, and
  `offer_outbound_click` retains only HTTP(S) origin and path. Query parameters,
  fragments, and URL credentials are discarded. Invalid URLs and other schemes
  are not reported as offer destinations. The actual anchor URL is untouched,
  preserving navigation and affiliate attribution. Owned-shop `placement` and
  `campaign` still use the editorial UTM values as separate event parameters.
- The manually maintained About page gets a new tracking-script cache key; Hugo
  pages already use a source hash in the script URL.

## CSP deferred

The proposed Report-Only CSP was evaluated locally and removed at the owner's
request before deployment. Neither `Content-Security-Policy` nor
`Content-Security-Policy-Report-Only` is configured. This release adds only
Permissions-Policy and the custom analytics URL sanitizer described above.

If CSP is reconsidered, review existing inline scripts and giscus's external
stylesheet before enforcing it. The local Report-Only trial exposed those
compatibility issues without blocking the tested features.

## Browser comparison on October 11, 2026

The production build was served on two loopback-only origins. The candidate
used Permissions-Policy, the proposed Report-Only CSP, and tracking version 2.3.1.
The baseline omitted the two proposed headers and served tracking version 2.3.0
from Git HEAD. CSP was subsequently removed from the release configuration.
Diagnostic code was added only by the temporary preview server; it is not present
in site files or the production build.

Observed results:

- Homepage and About rendered with no captured JavaScript runtime errors. The
  Google tag resource loaded and the inline `gtag` bootstrap ran in both modes.
- Searching for `AREX` returned the same 87 results in the same order in both
  modes. The homepage-to-About navigation and the hotel page's table-of-contents
  expand and anchor navigation worked with the proposed headers.
- The hotel calculator returned KRW 380,000 versus KRW 390,000, a KRW 10,000
  difference, in both modes for the same inputs.
- The giscus widget displayed its comment count and GitHub sign-in control in
  both modes. Signing in and posting comments were not tested.
- `/privacy/` still omitted the Google tag and custom tracker in both modes.
- Browser feature-policy inspection confirmed camera, microphone, and geolocation
  are disabled by the candidate, without requesting access to any device.
- A browser fixture using the real tracker captured all four event types locally.
  Anchor URLs stayed unchanged and the tracker did not cancel navigation. Only
  the three destination `link_url` values lost queries, fragments and credentials.

The Report-Only policy reported existing inline scripts and giscus's
`https://giscus.app/default.css`. These are real outstanding compatibility issues
before enforcement. Local favicon reports for `https://lovekorea.me/...` resulted
from the preview origin differing from the configured production origin. Do not
broaden the production policy merely to suppress those local-origin reports.

Analytics tradeoff: multiple Klook offers become the same
`https://affiliate.klook.com/redirect` value in `link_url`. The existing `slot`,
`pos`, and `provider` dimensions still distinguish recommendations, but reports
grouped only by the full destination URL lose query-level detail. Merchant
navigation URLs and referral parameters remain intact.

Google Analytics collection/dashboard receipt was not verified. The checks above
confirm tag loading, bootstrap execution and custom event payloads, not GA4
property settings or end-to-end event receipt. The observations apply to the
tested browser and pages, and were collected before deployment.

## Analytics settings outside this repository

The sanitizer covers the site's custom destination parameters. GA4 Enhanced
Measurement can independently send `link_url` for outbound clicks and downloads;
the GA4 configuration also determines automatic `page_location`, `page_referrer`,
and site-search collection. Repository changes do not verify those settings.
Check the web stream's Enhanced Measurement and Data Redaction settings, enable
email redaction, and configure sensitive query keys such as `email`, `token`,
`access_token`, and `code` as appropriate. Avoid personal data in URL paths or
editorial campaign labels; stripping queries cannot sanitize those fields.

## Local verification

```powershell
node --test tools/affiliate-tracking.test.cjs
python tools/lint_monetization.py
hugo --cleanDestinationDir --environment production --minify
python tools/audit_indexing_policy.py
python tools/audit_social_images.py
npx pagefind --site public --output-path public/pagefind
```

After deploying, recheck the real Netlify response headers; a successful local
build alone cannot verify deployed headers or third-party analytics behavior.

## References

- [Netlify custom headers](https://docs.netlify.com/manage/routing/headers/)
- [CSP Report-Only](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy-Report-Only)
- [Google tag CSP requirements](https://developers.google.com/tag-platform/security/guides/csp)
- [Permissions-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy)
- [security.txt standard, RFC 9116](https://www.rfc-editor.org/rfc/rfc9116.html)
- [GA4 Data Redaction](https://support.google.com/analytics/answer/13544947?hl=en)
