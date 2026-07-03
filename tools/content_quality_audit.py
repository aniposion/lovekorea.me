#!/usr/bin/env python3
"""Score older published posts for rewrite or draft review."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from content_audit_lib import (
    ContentPage,
    cover_file_path,
    has_mojibake,
    load_published_posts,
    markdown_links,
    normalize_internal_url,
    word_count,
)


GENERIC_TITLE_TERMS = [
    "discovering",
    "exploring",
    "magic",
    "journey",
    "adventure",
    "vibes",
    "ultimate",
    "must-see",
    "must-visit",
]

FIRST_PERSON_PATTERNS = [
    " a personal tip",
    " during my",
    " from personal experience",
    " i decided",
    " i discovered",
    " i found",
    " i had",
    " i learned",
    " i once",
    " i remember",
    " in my case",
    " join me",
    " my first",
    " my last",
    " my own",
    " our group",
    " personal story",
    " we were",
    " we'll",
]


@dataclass
class QualityFinding:
    page: ContentPage
    score: int = 0
    reasons: list[str] = field(default_factory=list)

    def add(self, points: int, reason: str) -> None:
        self.score += points
        self.reasons.append(reason)


def internal_link_count(page: ContentPage) -> int:
    unique_links: set[str] = set()
    for link in markdown_links(page.body):
        normalized = normalize_internal_url(link)
        if normalized and normalized != page.url:
            unique_links.add(normalized)
    return len(unique_links)


def prose_for_tone_scan(body: str) -> str:
    """Remove examples and markup that can cause false positives in tone checks."""
    cleaned_lines: list[str] = []
    in_fence = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith(">"):
            continue
        if stripped.startswith("!["):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def score_page(page: ContentPage, old_before: datetime) -> QualityFinding:
    finding = QualityFinding(page)
    title_lower = f" {page.title.lower()} "
    body_lower = f" {page.body.lower()} "
    tone_body_lower = f" {prose_for_tone_scan(page.body).lower()} "
    wc = word_count(page.body)

    if page.date < old_before:
        finding.add(1, "old post")
    if not page.description:
        finding.add(3, "missing description")
    elif len(page.description) < 80:
        finding.add(1, "short description")
    if not page.cover_image:
        finding.add(4, "missing cover")
    else:
        image_path = cover_file_path(page)
        if image_path is not None and not image_path.is_file():
            finding.add(4, "missing cover file")
    if wc < 700:
        finding.add(2, f"thin body ({wc} words)")
    if any(term in title_lower for term in GENERIC_TITLE_TERMS):
        finding.add(2, "generic title language")
    if any(pattern in tone_body_lower[:2000] for pattern in FIRST_PERSON_PATTERNS):
        finding.add(1, "first-person framing")
    if has_mojibake(f"{page.title}\n{page.description}\n{page.body[:4000]}"):
        finding.add(3, "possible mojibake")
    if internal_link_count(page) < 2:
        finding.add(1, "weak internal linking")

    return finding


def recommendation(score: int) -> str:
    if score >= 7:
        return "draft-or-rewrite"
    if score >= 4:
        return "rewrite"
    return "keep"


def main() -> int:
    parser = argparse.ArgumentParser(description="Find old AI-feeling posts to draft or rewrite.")
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--old-before", default="2026-01-01")
    parser.add_argument("--fail-score", type=int, default=0, help="Exit non-zero if any score meets this.")
    args = parser.parse_args()

    try:
        old_before = datetime.fromisoformat(args.old_before).replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"Invalid --old-before date: {args.old_before}")
        return 1

    findings = [score_page(page, old_before) for page in load_published_posts()]
    findings = sorted(findings, key=lambda item: (item.score, item.page.date), reverse=True)
    findings = [finding for finding in findings if finding.score > 0]

    print(f"Content quality audit: {len(findings)} published posts have at least one finding")
    print("\nTop findings:")
    for finding in findings[: args.top]:
        print(
            f"  - score={finding.score:02d} action={recommendation(finding.score)} "
            f"{finding.page.rel_path}"
        )
        print(f"    reasons: {', '.join(finding.reasons)}")

    if args.fail_score > 0 and any(finding.score >= args.fail_score for finding in findings):
        print(f"\nAt least one published post reached fail score {args.fail_score}.")
        return 1

    print("\nContent quality audit completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
