#!/usr/bin/env python3
"""Validate generated indexing policy for low-value archive pages."""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROBOTS_RE = re.compile(
    r"<meta\s+[^>]*\bname=(?:[\"']?robots[\"']?)\b[^>]*\bcontent=[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)


def robots_content(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    match = ROBOTS_RE.search(path.read_text(encoding="utf-8", errors="replace"))
    if not match:
        return ""
    return match.group(1).lower()


def sitemap_urls(path: Path) -> list[str]:
    if not path.is_file():
        raise FileNotFoundError(path)
    tree = ET.parse(path)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [node.text or "" for node in tree.findall(".//sm:loc", namespace)]


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.is_file():
            return path
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ensure noindex archives are not submitted for indexing."
    )
    parser.add_argument("--public-dir", default="public")
    args = parser.parse_args()

    public_dir = Path(args.public_dir)
    errors: list[str] = []

    try:
        urls = sitemap_urls(public_dir / "sitemap.xml")
    except (FileNotFoundError, ET.ParseError) as exc:
        print(f"Indexing policy audit failed: cannot read sitemap.xml ({exc})")
        return 1

    blocked_prefixes = ("https://lovekorea.me/tags/", "https://lovekorea.me/search/")
    blocked_urls = [url for url in urls if url.startswith(blocked_prefixes)]
    if blocked_urls:
        errors.append(
            "sitemap includes noindex archive URLs: "
            + ", ".join(blocked_urls[:10])
            + (" ..." if len(blocked_urls) > 10 else "")
        )

    required_index_urls = {"https://lovekorea.me/", "https://lovekorea.me/categories/"}
    missing_required = sorted(required_index_urls - set(urls))
    if missing_required:
        errors.append("sitemap is missing required indexable URLs: " + ", ".join(missing_required))

    tag_root = public_dir / "tags" / "index.html"
    tag_sample = first_existing(
        sorted(path for path in (public_dir / "tags").glob("*/index.html") if path.is_file())
    )
    search_page = public_dir / "search" / "index.html"

    for label, path in (("tags root", tag_root), ("tag term", tag_sample), ("search", search_page)):
        if path is None:
            continue
        try:
            robots = robots_content(path)
        except FileNotFoundError:
            errors.append(f"{label} page is missing: {path}")
            continue
        if "noindex" not in robots or "follow" not in robots:
            errors.append(f"{label} page robots meta should be noindex, follow: {path}")

    home_robots = robots_content(public_dir / "index.html")
    if "index" not in home_robots or "noindex" in home_robots:
        errors.append("home page robots meta should be index, follow")

    post_sample = first_existing(
        sorted(path for path in (public_dir / "posts").glob("*/index.html") if path.is_file())
    )
    if post_sample is not None:
        post_robots = robots_content(post_sample)
        if "index" not in post_robots or "noindex" in post_robots:
            errors.append(f"post page robots meta should be index, follow: {post_sample}")

    print(f"Indexing policy audit: {len(urls)} sitemap URLs checked.")
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Indexing policy audit passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
