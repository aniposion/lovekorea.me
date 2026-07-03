#!/usr/bin/env python3
"""Shared helpers for LoveKorea content audit scripts."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
POSTS_DIR = CONTENT_DIR / "posts"
STATIC_DIR = ROOT / "static"

IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
ASSET_EXTENSIONS = IMAGE_EXTENSIONS | {
    ".css",
    ".js",
    ".json",
    ".map",
    ".pdf",
    ".svg",
    ".txt",
    ".xml",
}


@dataclass
class ContentPage:
    path: Path
    rel_path: str
    front_matter: dict[str, Any]
    body: str

    @property
    def title(self) -> str:
        return str(self.front_matter.get("title", "")).strip()

    @property
    def description(self) -> str:
        return str(self.front_matter.get("description", "")).strip()

    @property
    def draft(self) -> bool:
        return bool(self.front_matter.get("draft", False))

    @property
    def slug(self) -> str:
        return str(self.front_matter.get("slug", "")).strip() or self.path.stem

    @property
    def is_post(self) -> bool:
        try:
            self.path.relative_to(POSTS_DIR)
            return self.path.name != "_index.md"
        except ValueError:
            return False

    @property
    def date(self) -> datetime:
        raw = str(self.front_matter.get("date", "")).strip()
        if not raw:
            return datetime.min.replace(tzinfo=timezone.utc)
        raw = raw.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    @property
    def categories(self) -> list[str]:
        return listify(self.front_matter.get("categories", []))

    @property
    def tags(self) -> list[str]:
        return listify(self.front_matter.get("tags", []))

    @property
    def cover(self) -> dict[str, Any]:
        cover = self.front_matter.get("cover", {})
        return cover if isinstance(cover, dict) else {}

    @property
    def cover_image(self) -> str:
        return str(self.cover.get("image", "")).strip()

    @property
    def cover_alt(self) -> str:
        return str(self.cover.get("alt", "")).strip()

    @property
    def url(self) -> str:
        if self.is_post:
            return f"/posts/{self.slug}/"

        rel = self.path.relative_to(CONTENT_DIR)
        if rel.name == "_index.md":
            if len(rel.parts) == 1:
                return "/"
            return "/" + "/".join(rel.parts[:-1]) + "/"

        parts = list(rel.with_suffix("").parts)
        if parts[-1] == "index":
            parts = parts[:-1]
        return "/" + "/".join(parts) + "/"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def split_front_matter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1 :])
    return "", text


def parse_front_matter(front_matter: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    parent_key: str | None = None

    for raw_line in front_matter.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if indent and parent_key:
            if line.startswith("- "):
                current = data.get(parent_key)
                if not isinstance(current, list):
                    current = []
                    data[parent_key] = current
                current.append(parse_scalar(line[2:].strip()))
                continue

            if ":" in line:
                current = data.get(parent_key)
                if not isinstance(current, dict):
                    current = {}
                    data[parent_key] = current
                key, value = line.split(":", 1)
                current[key.strip()] = parse_scalar(value.strip())
                continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value == "":
            data[key] = {}
            parent_key = key
            continue

        data[key] = parse_scalar(value)
        parent_key = None

    return data


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""

    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False

    if value.startswith("[") and value.endswith("]"):
        inside = value[1:-1].strip()
        if not inside:
            return []
        return [item.strip() for item in next(csv.reader([inside], skipinitialspace=True))]

    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]

    return value


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip().strip('"').strip("'") for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [str(value).strip()]


def load_pages(*, include_drafts: bool = True) -> list[ContentPage]:
    pages: list[ContentPage] = []
    for path in sorted(CONTENT_DIR.rglob("*.md")):
        text = read_text(path)
        front_matter_text, body = split_front_matter(text)
        page = ContentPage(
            path=path,
            rel_path=str(path.relative_to(ROOT)),
            front_matter=parse_front_matter(front_matter_text),
            body=body,
        )
        if include_drafts or not page.draft:
            pages.append(page)
    return pages


def load_published_posts() -> list[ContentPage]:
    posts = [page for page in load_pages(include_drafts=False) if page.is_post]
    return sorted(posts, key=lambda page: page.date, reverse=True)


def cover_file_path(page: ContentPage) -> Path | None:
    raw_image = page.cover_image
    if not raw_image or raw_image.startswith(("http://", "https://")):
        return None
    return STATIC_DIR / raw_image.lstrip("/")


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", text))


def has_mojibake(text: str) -> bool:
    if "\ufffd" in text:
        return True
    if re.search(r"\?[\uac00-\ud7af]", text):
        return True
    if re.search(r"[\u4e00-\u9fff]{2,}", text):
        return True
    return False


def normalize_internal_url(url: str) -> str | None:
    url = url.strip()
    if not url or url.startswith("#"):
        return None
    if url.startswith(("mailto:", "tel:", "javascript:")):
        return None

    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc.lower() not in {"lovekorea.me", "www.lovekorea.me"}:
            return None
        path = parsed.path
    elif parsed.scheme:
        return None
    else:
        path = parsed.path if parsed.path.startswith("/") else ""

    if not path:
        return None

    suffix = Path(path).suffix.lower()
    if suffix in ASSET_EXTENSIONS:
        return None

    path = re.sub(r"/index\.html?$", "/", path)
    if not path.endswith("/"):
        path += "/"
    return path


def known_site_urls(pages: list[ContentPage]) -> set[str]:
    urls = {"/", "/posts/", "/categories/", "/tags/", "/search/"}
    for page in pages:
        if not page.draft:
            urls.add(page.url)
            for category in page.categories:
                urls.add(f"/categories/{slugify_taxonomy(category)}/")
            for tag in page.tags:
                urls.add(f"/tags/{slugify_taxonomy(tag)}/")
    return urls


def slugify_taxonomy(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9가-힣_-]+", "", slug)
    return slug


def markdown_links(text: str) -> list[str]:
    links = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text)
    links.extend(re.findall(r"""href=["']([^"']+)["']""", text, flags=re.IGNORECASE))
    return links

