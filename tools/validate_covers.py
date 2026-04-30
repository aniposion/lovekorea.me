#!/usr/bin/env python3
"""Validate Hugo post cover images before publishing."""

from __future__ import annotations

import re
import sys
import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "content" / "posts"
STATIC_DIR = ROOT / "static"

IMAGE_LINE_RE = re.compile(r'^\s*image:\s*"([^"]*)"\s*$', re.MULTILINE)
RELATIVE_TRUE_RE = re.compile(r"^\s*relative:\s*true\s*$", re.MULTILINE)
IMAGE_EXT_RE = re.compile(r"\.(?:webp|jpe?g|png|gif|avif)(?:[?#].*)?$", re.IGNORECASE)


def extract_front_matter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:index])
    return ""


def validate_post(path: Path, warn_relative: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    text = path.read_text(encoding="utf-8")
    front_matter = extract_front_matter(text)
    match = IMAGE_LINE_RE.search(front_matter)

    if not match:
        errors.append(f"{path}: missing cover.image")
        return errors, warnings

    raw_image = match.group(1).strip()
    if not raw_image:
        errors.append(f"{path}: cover.image is empty")
        return errors, warnings

    if not IMAGE_EXT_RE.search(raw_image):
        errors.append(f"{path}: cover.image is not an image path: {raw_image!r}")
        return errors, warnings

    if raw_image.startswith(("http://", "https://")):
        return errors, warnings

    rel_image = raw_image.lstrip("/")
    if not rel_image.startswith("images/"):
        errors.append(f"{path}: cover.image should point under images/: {raw_image!r}")
        return errors, warnings

    image_path = STATIC_DIR / rel_image
    if not image_path.is_file():
        errors.append(f"{path}: missing cover file: {image_path}")

    if warn_relative and RELATIVE_TRUE_RE.search(front_matter):
        warnings.append(f"{path}: cover.relative is true for a static image; false is safer for social meta tags")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Hugo post cover image paths.")
    parser.add_argument(
        "--warn-relative",
        action="store_true",
        help="Warn when static cover images still use cover.relative = true.",
    )
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    posts = sorted(p for p in POSTS_DIR.glob("*.md") if p.name != "_index.md")
    for post in posts:
        post_errors, post_warnings = validate_post(post, warn_relative=args.warn_relative)
        errors.extend(post_errors)
        warnings.extend(post_warnings)

    print(f"Cover validation: scanned {len(posts)} posts")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Cover validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
