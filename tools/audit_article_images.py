#!/usr/bin/env python3
"""Require visible article images for new and opted-in older posts after the build.

This checks delivery and metadata. Photographic quality still needs visual review.
Only the standard library is used so the same check runs on the deploy host.
"""

from __future__ import annotations

import argparse
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from content_audit_lib import ROOT, load_published_posts


REQUIRED_FROM = date(2026, 10, 22)


class ArticleImages(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_article = False
        self.in_figure = False
        self.in_caption = False
        self.images: list[dict] = []
        self.caption: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs = dict(attrs)
        if tag == "article":
            self.in_article = True
        elif tag == "figure" and self.in_article and "data-article-image" in attrs:
            self.in_figure = True
        elif tag == "img" and self.in_figure:
            self.images.append(attrs)
        elif tag == "figcaption" and self.in_figure:
            self.in_caption = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "article":
            self.in_article = False
        elif tag == "figure":
            self.in_figure = False
        elif tag == "figcaption":
            self.in_caption = False

    def handle_data(self, data: str) -> None:
        if self.in_caption:
            self.caption.append(data)


def local_image(value: str, base: Path) -> Path | None:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    target = (base / unquote(parsed.path).lstrip("/")).resolve()
    if not target.is_relative_to(base.resolve()) or not target.is_file():
        return None
    return target


def check_rendered(html: str, cover: dict, public: Path) -> list[str]:
    parser = ArticleImages()
    parser.feed(html)
    errors = []
    if len(parser.images) != 1:
        return [f"expected one visible article cover; found {len(parser.images)}"]
    image = parser.images[0]
    expected = "/" + str(cover.get("image", "")).lstrip("/")
    if image.get("src") != expected:
        errors.append("rendered article image does not match the cover")
    if image.get("alt", "").strip() != str(cover.get("alt", "")).strip():
        errors.append("rendered alt text does not match the cover")
    for attr in ("width", "height"):
        if not str(image.get(attr, "")).isdigit() or int(image.get(attr, "0")) <= 0:
            errors.append(f"missing positive {attr} on article image")
    if image.get("loading") != "eager":
        errors.append("article cover must load eagerly")
    variants = {}
    for entry in image.get("srcset", "").split(","):
        fields = entry.strip().split()
        if len(fields) == 2:
            variants[fields[1]] = fields[0]
    for key, width in (("small", "480w"), ("medium", "960w")):
        if variants.get(width) != cover.get(key):
            errors.append(f"missing or mismatched {width} responsive image")
    if not image.get("sizes"):
        errors.append("missing responsive sizes")
    if "".join(parser.caption).strip() != str(cover.get("caption", "")).strip():
        errors.append("image caption is not rendered")
    for src in [image.get("src", ""), *variants.values()]:
        if local_image(src, public) is None:
            errors.append(f"missing image in production build: {src}")
    return errors


def audit(public: Path) -> tuple[int, list[str]]:
    errors = []
    checked = 0
    for post in load_published_posts():
        cover = post.cover
        if post.date.date() < REQUIRED_FROM and cover.get("showInArticle") is not True:
            continue
        checked += 1
        issues = []
        if cover.get("style") != "photorealistic":
            issues.append("missing photorealistic cover style; review the actual image")
        if cover.get("showInArticle") is not True:
            issues.append("cover.showInArticle must be true")
        if not post.cover_alt:
            issues.append("missing descriptive cover alt text")
        if not str(cover.get("caption", "")).strip():
            issues.append("missing image caption")
        for key in ("image", "small", "medium"):
            src = str(cover.get(key, ""))
            source = local_image(src, ROOT / "static")
            deployed = local_image(src, public)
            if source is None:
                issues.append(f"missing local cover.{key}: {src}")
            elif deployed is None or deployed.read_bytes() != source.read_bytes():
                issues.append(f"cover.{key} missing or stale in build")
        page = public / post.url.strip("/") / "index.html"
        if page.is_file():
            issues.extend(check_rendered(page.read_text(encoding="utf-8"), cover, public))
        else:
            issues.append("missing article HTML; run Hugo production build")
        errors.extend(f"{post.rel_path}: {issue}" for issue in issues)
    if not checked:
        errors.append("No posts checked; verify the content directory and publication dates")
    return checked, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public", type=Path, default=ROOT / "public")
    args = parser.parse_args()
    checked, errors = audit(args.public.resolve())
    print(f"Article image audit: {checked} posts; {len(errors)} errors")
    for error in errors:
        print(f"  - {error}")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
