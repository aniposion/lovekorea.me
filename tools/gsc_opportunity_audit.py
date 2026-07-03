#!/usr/bin/env python3
"""Rank Google Search Console rows that are close to page-one growth."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "gsc" / "latest.csv"
DEFAULT_OUTPUT = ROOT / "docs" / "gsc-opportunity-audit.md"

INTENT_TERMS = {
    "book": 1.5,
    "booking": 1.5,
    "buy": 1.5,
    "compare": 1.5,
    "comparison": 1.5,
    "discount": 1.4,
    "price": 1.5,
    "prices": 1.5,
    "ticket": 1.5,
    "tickets": 1.5,
    "vs": 1.5,
    "where to buy": 1.5,
    "best": 1.2,
    "guide": 1.1,
    "route": 1.3,
    "routes": 1.3,
    "pass": 1.4,
}


@dataclass
class GscRow:
    query: str
    page: str
    clicks: float
    impressions: float
    ctr_percent: float
    position: float
    score: float


def normalize_header(header: str) -> str:
    return "".join(ch for ch in header.lower() if ch.isalnum())


def pick(row: dict[str, str], aliases: Iterable[str]) -> str:
    normalized = {normalize_header(key): value for key, value in row.items()}
    for alias in aliases:
        value = normalized.get(normalize_header(alias))
        if value is not None:
            return value.strip()
    return ""


def parse_number(value: str) -> float:
    value = value.strip().replace(",", "")
    if not value:
        return 0.0
    if value.endswith("%"):
        value = value[:-1]
    try:
        return float(value)
    except ValueError:
        return 0.0


def parse_ctr(value: str) -> float:
    raw = value.strip()
    if not raw:
        return 0.0
    number = parse_number(raw)
    if "%" in raw:
        return number
    if number <= 1:
        return number * 100
    return number


def position_weight(position: float) -> float:
    if 8 <= position < 12:
        return 1.4
    if 12 <= position < 16:
        return 1.2
    return 1.0


def intent_weight(text: str) -> float:
    haystack = text.lower()
    weight = 1.0
    for term, term_weight in INTENT_TERMS.items():
        if term in haystack:
            weight = max(weight, term_weight)
    return weight


def row_from_csv(row: dict[str, str]) -> GscRow:
    query = pick(row, ["query", "queries", "top queries", "search query", "인기 검색어", "검색어"])
    page = pick(row, ["page", "pages", "top pages", "url", "landing page", "인기 페이지", "페이지"])
    clicks = parse_number(pick(row, ["clicks", "클릭수"]))
    impressions = parse_number(pick(row, ["impressions", "노출"]))
    ctr_percent = parse_ctr(pick(row, ["ctr"]))
    position = parse_number(pick(row, ["position", "avg position", "average position", "게재 순위"]))
    score = impressions * position_weight(position) * intent_weight(f"{query} {page}")
    return GscRow(query, page, clicks, impressions, ctr_percent, position, score)


def load_rows(path: Path) -> list[GscRow]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [row_from_csv(row) for row in reader]


def filter_candidates(
    rows: Iterable[GscRow],
    min_position: float,
    max_position: float,
    min_impressions: float,
    max_ctr: float,
) -> list[GscRow]:
    candidates = [
        row
        for row in rows
        if min_position <= row.position <= max_position
        and row.impressions >= min_impressions
        and row.ctr_percent <= max_ctr
    ]
    return sorted(candidates, key=lambda row: row.score, reverse=True)


def render_markdown(candidates: list[GscRow], source: Path, limit: int) -> str:
    source_label = display_path(source)
    lines = [
        "# GSC Opportunity Audit",
        "",
        f"Generated: {date.today().isoformat()}",
        f"Source: `{source_label}`",
        "",
        "These rows are already close enough to improve with better title, description, content fit, and internal links.",
        "",
        "| Rank | Score | Query | Page | Clicks | Impressions | CTR | Position |",
        "|---:|---:|---|---|---:|---:|---:|---:|",
    ]

    for index, row in enumerate(candidates[:limit], start=1):
        lines.append(
            "| {rank} | {score:.0f} | {query} | {page} | {clicks:.0f} | "
            "{impressions:.0f} | {ctr:.2f}% | {position:.1f} |".format(
                rank=index,
                score=row.score,
                query=escape_cell(row.query or "-"),
                page=escape_cell(row.page or "-"),
                clicks=row.clicks,
                impressions=row.impressions,
                ctr=row.ctr_percent,
                position=row.position,
            )
        )

    lines.extend(
        [
            "",
            "Recommended next action:",
            "",
            "1. Rewrite titles and descriptions for the top 10 rows.",
            "2. Check whether the page fully answers the query intent.",
            "3. Add 2-3 contextual internal links into each candidate page.",
            "4. Recheck CTR and average position after 14 and 28 days.",
            "",
        ]
    )
    return "\n".join(lines)


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Find 8-20 position GSC rows worth improving.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--min-position", type=float, default=8.0)
    parser.add_argument("--max-position", type=float, default=20.0)
    parser.add_argument("--min-impressions", type=float, default=50.0)
    parser.add_argument("--max-ctr", type=float, default=1.5, help="CTR threshold in percent.")
    args = parser.parse_args()

    input_path = args.input if args.input.is_absolute() else ROOT / args.input
    output_path = args.output if args.output.is_absolute() else ROOT / args.output

    if not input_path.is_file():
        print(f"GSC opportunity audit skipped: no export found at {input_path}")
        print("Place a Search Console CSV at gsc/latest.csv or pass --input.")
        return 0

    rows = load_rows(input_path)
    candidates = filter_candidates(
        rows,
        args.min_position,
        args.max_position,
        args.min_impressions,
        args.max_ctr,
    )

    print(f"GSC opportunity audit: {len(rows)} rows scanned, {len(candidates)} candidates")
    for index, row in enumerate(candidates[: min(args.limit, 10)], start=1):
        label = row.query or row.page
        print(
            f"  {index}. score={row.score:.0f} pos={row.position:.1f} "
            f"ctr={row.ctr_percent:.2f}% impressions={row.impressions:.0f} {label}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(candidates, input_path, args.limit), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
