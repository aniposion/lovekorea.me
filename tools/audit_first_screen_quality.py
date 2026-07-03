#!/usr/bin/env python3
"""Audit home and taxonomy first-screen post quality."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from content_audit_lib import ContentPage, cover_file_path, has_mojibake, load_published_posts


@dataclass
class Issue:
    severity: str
    view: str
    file: Path
    message: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.view}: {self.file} - {self.message}"


def check_page(page: ContentPage, view: str, min_image_bytes: int) -> tuple[list[Issue], list[Issue]]:
    errors: list[Issue] = []
    warnings: list[Issue] = []

    title = page.title
    description = page.description

    if not title:
        errors.append(Issue("ERROR", view, page.path, "missing title"))
    elif has_mojibake(title):
        errors.append(Issue("ERROR", view, page.path, "title appears to contain mojibake"))
    elif len(title) > 95:
        warnings.append(Issue("WARNING", view, page.path, f"title is long ({len(title)} chars)"))

    if not description:
        errors.append(Issue("ERROR", view, page.path, "missing description"))
    elif has_mojibake(description):
        errors.append(Issue("ERROR", view, page.path, "description appears to contain mojibake"))
    else:
        if len(description) < 80:
            warnings.append(
                Issue("WARNING", view, page.path, f"description is short ({len(description)} chars)")
            )
        if len(description) > 175:
            warnings.append(
                Issue("WARNING", view, page.path, f"description is long ({len(description)} chars)")
            )

    if not page.cover_image:
        errors.append(Issue("ERROR", view, page.path, "missing cover.image"))
    else:
        image_path = cover_file_path(page)
        if image_path is not None:
            if not image_path.is_file():
                errors.append(Issue("ERROR", view, page.path, f"cover file not found: {image_path}"))
            elif image_path.stat().st_size < min_image_bytes:
                errors.append(
                    Issue(
                        "ERROR",
                        view,
                        page.path,
                        f"cover file is too small ({image_path.stat().st_size} bytes): {image_path}",
                    )
                )

    if not page.cover_alt:
        warnings.append(Issue("WARNING", view, page.path, "missing cover.alt"))
    elif has_mojibake(page.cover_alt):
        warnings.append(Issue("WARNING", view, page.path, "cover.alt appears to contain mojibake"))

    return errors, warnings


def selected_views(posts: list[ContentPage], limit: int) -> dict[str, list[ContentPage]]:
    views: dict[str, list[ContentPage]] = {"home": posts[:limit]}
    by_category: dict[str, list[ContentPage]] = defaultdict(list)

    for post in posts:
        for category in post.categories:
            by_category[category].append(post)

    for category, category_posts in sorted(by_category.items()):
        views[f"category:{category}"] = category_posts[:limit]

    return views


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check visible home/category article cards for image and metadata quality."
    )
    parser.add_argument("--limit", type=int, default=12, help="Number of posts to audit per view.")
    parser.add_argument(
        "--min-image-bytes",
        type=int,
        default=10_000,
        help="Minimum acceptable static cover image size.",
    )
    parser.add_argument("--warnings-as-errors", action="store_true")
    args = parser.parse_args()

    posts = load_published_posts()
    views = selected_views(posts, args.limit)

    errors: list[Issue] = []
    warnings: list[Issue] = []
    for view, pages in views.items():
        for page in pages:
            page_errors, page_warnings = check_page(page, view, args.min_image_bytes)
            errors.extend(page_errors)
            warnings.extend(page_warnings)

    print(
        f"First-screen quality audit: {len(posts)} published posts, "
        f"{len(views)} views, limit {args.limit}"
    )

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

    print("First-screen quality audit passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

