#!/usr/bin/env python3
"""Check article preview images in the production HTML without external requests."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


class ArticleMetadata(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.articles: list[dict] = []
        self.json_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs = dict(attrs)
        if tag == "meta":
            key = attrs.get("property") or attrs.get("name")
            if key:
                self.meta[key] = attrs.get("content", "")
        elif tag == "script" and attrs.get("type") == "application/ld+json":
            self.json_parts = []

    def handle_data(self, data: str) -> None:
        if self.json_parts is not None:
            self.json_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.json_parts is not None:
            value = json.loads("".join(self.json_parts))
            if isinstance(value, dict) and value.get("@type") == "BlogPosting":
                self.articles.append(value)
            self.json_parts = None


def audit(public: Path) -> tuple[int, int, list[str]]:
    public = public.resolve()
    checked = 0
    external = 0
    errors: list[str] = []
    for page in sorted((public / "posts").rglob("index.html")):
        metadata = ArticleMetadata()
        try:
            metadata.feed(page.read_text(encoding="utf-8"))
        except (ValueError, TypeError) as error:
            errors.append(f"{page.relative_to(public)}: invalid JSON-LD: {error}")
            continue
        if not metadata.articles:
            continue
        checked += 1
        label = page.relative_to(public)
        image = metadata.meta.get("og:image", "")
        parsed = urlsplit(image)
        if parsed.scheme not in ("https", "http") or not parsed.netloc:
            errors.append(f"{label}: missing or non-absolute og:image: {image!r}")
            continue
        if metadata.meta.get("twitter:image") != image:
            errors.append(f"{label}: twitter:image differs from og:image")
        for article in metadata.articles:
            images = article.get("image", [])
            if isinstance(images, str):
                images = [images]
            if image not in images:
                errors.append(f"{label}: BlogPosting image differs from og:image")
        page_host = urlsplit(metadata.meta.get("og:url", "")).netloc
        if not page_host:
            errors.append(f"{label}: missing absolute og:url")
        elif parsed.netloc != page_host:
            external += 1  # External availability is not verified by this local audit.
        else:
            target = (public / unquote(parsed.path).lstrip("/")).resolve()
            if not target.is_relative_to(public) or not target.is_file():
                errors.append(f"{label}: preview image is missing from build: {image}")
    if not checked:
        errors.append("No rendered articles found; run the production Hugo build first.")
    return checked, external, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public", type=Path, default=ROOT / "public")
    args = parser.parse_args()
    checked, external, errors = audit(args.public)
    print(f"Social image audit: {checked} articles; {len(errors)} errors; "
          f"{external} external images unverified")
    for error in errors:
        print(f"  - {error}")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
