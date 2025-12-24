#!/usr/bin/env python3
"""
lint_monetization.py - Comprehensive Affiliate Compliance Linter

This script scans markdown files and ensures FTC/Amazon Associates compliance:
1. Detects offer shortcodes and maps slot -> provider via slots.yaml
2. Amazon-specific checks:
   - No redirect patterns (/go/, /redirect/, etc.)
   - Required disclosure within first 30 lines
   - Warn if url has no 'tag=' parameter
3. General affiliate checks:
   - FTC disclosure exists near top OR immediately above first offer block

Usage:
    python tools/lint_monetization.py [--verbose] [--warnings-as-errors]

Exit Codes:
    0 - All checks passed
    1 - Compliance violations found
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("Warning: PyYAML not installed. Slot-to-provider mapping disabled.")


# ============================================================================
# CONFIGURATION
# ============================================================================

# Directories to scan
CONTENT_DIRS = [
    Path("content/posts"),
    Path("content/deals"),
]
SLOTS_FILE = Path("data/monetization/slots.yaml")

# EXACT required Amazon disclosure text (do not modify!)
AMAZON_DISCLOSURE_EXACT = "As an Amazon Associate I earn from qualifying purchases."
AMAZON_DISCLOSURE_PATTERN = r"As an Amazon Associate I earn from qualifying purchases"

# General FTC disclosure patterns
FTC_DISCLOSURE_PATTERNS = [
    r"This post may contain affiliate links",
    r"This article may contain affiliate links",
    r"This page may contain affiliate links",
    r"This section may contain affiliate links",
    r"may earn a commission",
    r"\*?Disclosure\*?:?\s*.*affiliate",
]

# Shortcode pattern to detect offer slots
OFFER_SHORTCODE_PATTERN = r'\{\{<\s*offer\s+slot=["\']([^"\']+)["\']'

# Amazon direct link patterns
AMAZON_URL_PATTERNS = [
    r"https?://(?:www\.)?amazon\.com",
    r"https?://(?:www\.)?amazon\.co\.[a-z]{2}",
    r"https?://(?:www\.)?amazon\.[a-z]{2,3}",
    r"https?://amzn\.to",
    r"https?://amzn\.com",
]

# Forbidden redirect patterns (violate Amazon ToS)
FORBIDDEN_REDIRECT_PATTERNS = [
    r"/go/",
    r"/redirect/",
    r"/out/",
    r"/link/",
    r"/aff/",
    r"/click/",
]


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Violation:
    """Represents a single compliance violation."""
    file: Path
    line_number: int
    rule: str
    message: str
    severity: str = "ERROR"  # ERROR, WARNING, INFO

    def __str__(self):
        return f"[{self.severity}] {self.file}:{self.line_number} - {self.rule}: {self.message}"


@dataclass
class SlotInfo:
    """Information about an offer slot."""
    slot_key: str
    provider: str
    url: str
    line_number: int


@dataclass
class LintResult:
    """Results from linting a single file."""
    file: Path
    violations: List[Violation] = field(default_factory=list)
    slots_used: List[SlotInfo] = field(default_factory=list)
    has_amazon_slots: bool = False
    has_amazon_disclosure: bool = False
    amazon_disclosure_line: int = -1
    has_ftc_disclosure: bool = False
    ftc_disclosure_line: int = -1
    body_start_line: int = 1


# ============================================================================
# SLOT LOADING
# ============================================================================

def load_slots_config(slots_file: Path) -> Dict[str, Dict[str, Any]]:
    """Load slot configuration from YAML file."""
    if not HAS_YAML:
        return {}
    
    if not slots_file.exists():
        print(f"  ⚠️ Slots file not found: {slots_file}")
        return {}
    
    try:
        with open(slots_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"  ⚠️ Error loading slots file: {e}")
        return {}


def get_slot_provider(slot_key: str, slots_config: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """Get provider for a slot key."""
    slot = slots_config.get(slot_key, {})
    return slot.get("provider")


def get_slot_url(slot_key: str, slots_config: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """Get URL for a slot key."""
    slot = slots_config.get(slot_key, {})
    return slot.get("url")


# ============================================================================
# PARSING FUNCTIONS
# ============================================================================

def find_markdown_files(content_dirs: List[Path]) -> List[Path]:
    """Find all markdown files in the content directories."""
    all_files = []
    for content_dir in content_dirs:
        if content_dir.exists():
            all_files.extend(content_dir.glob("**/*.md"))
    return all_files


def extract_frontmatter_and_body(content: str) -> Tuple[str, str, int]:
    """
    Extract YAML frontmatter and body content.
    Returns: (frontmatter, body, body_start_line)
    """
    lines = content.split('\n')
    
    if not lines or lines[0].strip() != '---':
        return "", content, 1
    
    frontmatter_end = -1
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            frontmatter_end = i
            break
    
    if frontmatter_end == -1:
        return "", content, 1
    
    frontmatter = '\n'.join(lines[1:frontmatter_end])
    body = '\n'.join(lines[frontmatter_end + 1:])
    body_start_line = frontmatter_end + 2  # 1-indexed
    
    return frontmatter, body, body_start_line


def find_offer_shortcodes(content: str) -> List[Tuple[int, str]]:
    """
    Find all offer shortcodes in content.
    Returns: list of (line_number, slot_key)
    """
    results = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, start=1):
        matches = re.findall(OFFER_SHORTCODE_PATTERN, line)
        for slot_key in matches:
            results.append((i, slot_key))
    
    return results


def find_amazon_disclosure(content: str, body_start_line: int) -> Tuple[bool, int, bool]:
    """
    Check if Amazon Associate disclosure exists.
    Returns: (found, line_number, is_within_30_lines)
    """
    lines = content.split('\n')
    
    for i, line in enumerate(lines, start=1):
        if re.search(AMAZON_DISCLOSURE_PATTERN, line, re.IGNORECASE):
            is_within_30 = (i - body_start_line) < 30
            return True, i, is_within_30
    
    return False, -1, False


def find_ftc_disclosure(content: str, body_start_line: int) -> Tuple[bool, int, bool]:
    """
    Check if FTC disclosure exists and is near the top.
    Returns: (found, line_number, is_at_top)
    """
    lines = content.split('\n')
    
    for pattern in FTC_DISCLOSURE_PATTERNS:
        for i, line in enumerate(lines, start=1):
            if re.search(pattern, line, re.IGNORECASE):
                is_at_top = (i - body_start_line) < 30
                return True, i, is_at_top
    
    return False, -1, False


def check_forbidden_redirects(content: str, file_path: Path) -> List[Violation]:
    """Check for forbidden redirect patterns in URLs."""
    violations = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, start=1):
        for pattern in FORBIDDEN_REDIRECT_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Check if this looks like an Amazon-related redirect
                if re.search(r'amazon|amzn', line, re.IGNORECASE):
                    violations.append(Violation(
                        file=file_path,
                        line_number=i,
                        rule="AMAZON_REDIRECT_FORBIDDEN",
                        message=f"Amazon links must NOT use redirect paths (violates Amazon ToS): {line.strip()[:60]}...",
                        severity="ERROR"
                    ))
                else:
                    # Non-Amazon redirect - just warn
                    violations.append(Violation(
                        file=file_path,
                        line_number=i,
                        rule="REDIRECT_LINK_DETECTED",
                        message=f"Redirect link detected (consider using direct links): {line.strip()[:60]}...",
                        severity="WARNING"
                    ))
    
    return violations


def check_amazon_url_compliance(url: str, slot_key: str, line_number: int, file_path: Path) -> List[Violation]:
    """Check Amazon URL for compliance issues."""
    violations = []
    
    # Check for forbidden redirect patterns in URL
    for pattern in FORBIDDEN_REDIRECT_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            violations.append(Violation(
                file=file_path,
                line_number=line_number,
                rule="AMAZON_REDIRECT_IN_SLOT",
                message=f"Slot '{slot_key}' uses forbidden redirect pattern in URL",
                severity="ERROR"
            ))
    
    # Check for tracking tag (warn if missing)
    if not re.search(r'tag=', url, re.IGNORECASE):
        violations.append(Violation(
            file=file_path,
            line_number=line_number,
            rule="AMAZON_TAG_MISSING",
            message=f"Slot '{slot_key}' Amazon URL missing 'tag=' parameter (untracked link)",
            severity="WARNING"
        ))
    
    return violations


# ============================================================================
# MAIN LINTING
# ============================================================================

def lint_file(file_path: Path, slots_config: Dict[str, Dict[str, Any]], verbose: bool = False) -> LintResult:
    """Lint a single markdown file for compliance violations."""
    result = LintResult(file=file_path)
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        result.violations.append(Violation(
            file=file_path,
            line_number=0,
            rule="FILE_READ_ERROR",
            message=f"Could not read file: {e}",
            severity="ERROR"
        ))
        return result
    
    frontmatter, body, body_start_line = extract_frontmatter_and_body(content)
    result.body_start_line = body_start_line
    
    # -------------------------------------------------------------------------
    # 1. Find all offer shortcodes and map to providers
    # -------------------------------------------------------------------------
    shortcodes = find_offer_shortcodes(content)
    amazon_slots = []
    
    for line_num, slot_key in shortcodes:
        provider = get_slot_provider(slot_key, slots_config)
        url = get_slot_url(slot_key, slots_config) or ""
        
        slot_info = SlotInfo(
            slot_key=slot_key,
            provider=provider or "unknown",
            url=url,
            line_number=line_num
        )
        result.slots_used.append(slot_info)
        
        if provider == "amazon":
            amazon_slots.append(slot_info)
            result.has_amazon_slots = True
            
            # Check Amazon URL compliance
            if url:
                url_violations = check_amazon_url_compliance(url, slot_key, line_num, file_path)
                result.violations.extend(url_violations)
    
    if verbose and shortcodes:
        print(f"  📦 Found {len(shortcodes)} offer shortcodes in {file_path.name}")
        if amazon_slots:
            print(f"     ↳ {len(amazon_slots)} Amazon slots")
    
    # -------------------------------------------------------------------------
    # 2. Check for forbidden redirect patterns in content
    # -------------------------------------------------------------------------
    redirect_violations = check_forbidden_redirects(content, file_path)
    result.violations.extend(redirect_violations)
    
    # -------------------------------------------------------------------------
    # 3. Amazon disclosure check (if Amazon slots used)
    # -------------------------------------------------------------------------
    if result.has_amazon_slots:
        found, line_num, within_30 = find_amazon_disclosure(content, body_start_line)
        result.has_amazon_disclosure = found
        result.amazon_disclosure_line = line_num
        
        if not found:
            first_amazon_line = amazon_slots[0].line_number if amazon_slots else body_start_line
            result.violations.append(Violation(
                file=file_path,
                line_number=first_amazon_line,
                rule="AMAZON_DISCLOSURE_MISSING",
                message=f"Page uses Amazon slots but missing required disclosure: '{AMAZON_DISCLOSURE_EXACT}'",
                severity="ERROR"
            ))
        elif not within_30:
            result.violations.append(Violation(
                file=file_path,
                line_number=line_num,
                rule="AMAZON_DISCLOSURE_POSITION",
                message=f"Amazon disclosure must appear within first 30 lines of body (found at line {line_num}, body starts at {body_start_line})",
                severity="ERROR"
            ))
    
    # -------------------------------------------------------------------------
    # 4. General FTC disclosure check (if any affiliate content)
    # -------------------------------------------------------------------------
    has_affiliate_content = (
        len(result.slots_used) > 0 or
        re.search(r'affiliate|commission|earn.*commission', content, re.IGNORECASE)
    )
    
    if has_affiliate_content:
        found, line_num, at_top = find_ftc_disclosure(content, body_start_line)
        result.has_ftc_disclosure = found
        result.ftc_disclosure_line = line_num
        
        if not found:
            first_offer_line = result.slots_used[0].line_number if result.slots_used else body_start_line
            result.violations.append(Violation(
                file=file_path,
                line_number=first_offer_line,
                rule="FTC_DISCLOSURE_MISSING",
                message="Page contains affiliate content but missing FTC disclosure near top or above first offer",
                severity="WARNING"
            ))
        elif not at_top:
            # Check if disclosure is immediately above first offer block
            first_offer_line = result.slots_used[0].line_number if result.slots_used else 9999
            if line_num > first_offer_line:
                result.violations.append(Violation(
                    file=file_path,
                    line_number=line_num,
                    rule="FTC_DISCLOSURE_POSITION",
                    message=f"FTC disclosure should be near top OR immediately above first offer (disclosure at line {line_num}, first offer at line {first_offer_line})",
                    severity="WARNING"
                ))
    
    return result


# ============================================================================
# REPORTING
# ============================================================================

def print_summary(results: List[LintResult], verbose: bool = False) -> Tuple[int, int]:
    """Print a summary of all lint results."""
    total_files = len(results)
    files_with_violations = [r for r in results if r.violations]
    error_count = sum(1 for r in results for v in r.violations if v.severity == "ERROR")
    warning_count = sum(1 for r in results for v in r.violations if v.severity == "WARNING")
    files_with_amazon = sum(1 for r in results if r.has_amazon_slots)
    total_slots = sum(len(r.slots_used) for r in results)
    
    print("\n" + "=" * 70)
    print("📊 MONETIZATION COMPLIANCE LINT REPORT")
    print("=" * 70)
    print(f"  Files scanned:           {total_files}")
    print(f"  Offer shortcodes found:  {total_slots}")
    print(f"  Files with Amazon slots: {files_with_amazon}")
    print(f"  Files with violations:   {len(files_with_violations)}")
    print(f"  Total errors:            {error_count}")
    print(f"  Total warnings:          {warning_count}")
    print("=" * 70)
    
    if error_count > 0:
        print("\n❌ ERRORS (must fix before deploy):\n")
        for result in results:
            for v in result.violations:
                if v.severity == "ERROR":
                    print(f"  {v}")
    
    if warning_count > 0 and verbose:
        print("\n⚠️  WARNINGS:\n")
        for result in results:
            for v in result.violations:
                if v.severity == "WARNING":
                    print(f"  {v}")
    elif warning_count > 0:
        print(f"\n⚠️  {warning_count} warnings (use --verbose to see details)")
    
    print()
    
    return error_count, warning_count


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Lint markdown files for affiliate compliance (Amazon Associates, FTC)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including warnings"
    )
    parser.add_argument(
        "--warnings-as-errors", "-W",
        action="store_true",
        help="Treat warnings as errors (fail build on warnings)"
    )
    parser.add_argument(
        "--content-dir",
        type=Path,
        action="append",
        dest="content_dirs",
        help="Additional content directory to scan"
    )
    
    args = parser.parse_args()
    
    # Merge default dirs with any custom dirs
    scan_dirs = CONTENT_DIRS.copy()
    if args.content_dirs:
        scan_dirs.extend(args.content_dirs)
    
    print("🔍 Starting Monetization Compliance Lint...")
    print(f"   Scanning: {', '.join(str(d) for d in scan_dirs)}")
    
    # Load slots configuration
    slots_config = load_slots_config(SLOTS_FILE)
    if slots_config:
        print(f"   Loaded {len(slots_config)} slots from {SLOTS_FILE}")
    
    # Find all markdown files
    md_files = find_markdown_files(scan_dirs)
    
    if not md_files:
        print("⚠️  No markdown files found to lint.")
        return 0
    
    print(f"   Found {len(md_files)} markdown files\n")
    
    # Lint each file
    results = []
    for md_file in md_files:
        if args.verbose:
            print(f"  Checking: {md_file}")
        result = lint_file(md_file, slots_config, verbose=args.verbose)
        results.append(result)
    
    # Print summary
    error_count, warning_count = print_summary(results, verbose=args.verbose)
    
    # Determine exit code
    if args.warnings_as_errors and warning_count > 0:
        print("❌ Build failed: Warnings treated as errors (-W flag)")
        return 1
    
    if error_count > 0:
        print("❌ Build failed: Compliance errors found")
        return 1
    
    print("✅ All compliance checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
