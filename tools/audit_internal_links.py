#!/usr/bin/env python3
"""Audit internal links across published LoveKorea posts."""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from content_audit_lib import (
    ContentPage,
    known_site_urls,
    load_pages,
    markdown_links,
    normalize_internal_url,
)


HIGH_INTENT_TERMS = {
    "best",
    "book",
    "booking",
    "buy",
    "compare",
    "comparison",
    "discount",
    "pass",
    "price",
    "prices",
    "route",
    "ticket",
    "tickets",
    "vs",
    "where",
}


@dataclass
class LinkIssue:
    severity: str
    file: Path
    message: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.file} - {self.message}"


def is_high_intent(page: ContentPage) -> bool:
    haystack = f"{page.title} {page.slug} {' '.join(page.tags)}".lower()
    return any(term in haystack for term in HIGH_INTENT_TERMS)


def is_recent(page: ContentPage) -> bool:
    cutoff = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return page.date >= cutoff


def main() -> int:
    parser = argparse.ArgumentParser(description="Check broken and thin internal linking.")
    parser.add_argument("--min-outbound", type=int, default=3)
    parser.add_argument("--warnings-as-errors", action="store_true")
    args = parser.parse_args()

    pages = load_pages(include_drafts=False)
    posts = [page for page in pages if page.is_post]
    known_urls = known_site_urls(pages)

    errors: list[LinkIssue] = []
    warnings: list[LinkIssue] = []
    outbound: dict[str, set[str]] = defaultdict(set)
    inbound = Counter()

    for post in posts:
        links = markdown_links(post.body)
        for raw_link in links:
            normalized = normalize_internal_url(raw_link)
            if normalized is None:
                continue
            if normalized not in known_urls:
                errors.append(
                    LinkIssue("ERROR", post.path, f"broken internal link: {raw_link} -> {normalized}")
                )
                continue
            if normalized != post.url:
                outbound[post.url].add(normalized)
                inbound[normalized] += 1

    for post in posts:
        count = len(outbound[post.url])
        if (is_recent(post) or is_high_intent(post)) and count < args.min_outbound:
            warnings.append(
                LinkIssue(
                    "WARNING",
                    post.path,
                    f"only {count} outbound internal links; target is {args.min_outbound}+",
                )
            )
        if (is_recent(post) or is_high_intent(post)) and inbound[post.url] == 0:
            warnings.append(LinkIssue("WARNING", post.path, "no inbound links from other published posts"))

    print(f"Internal link audit: {len(posts)} published posts, {len(known_urls)} known URLs")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    if args.warnings_as_errors and warnings:
        print("\nWarnings treated as errors.")
        return 1

    print("Internal link audit passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

