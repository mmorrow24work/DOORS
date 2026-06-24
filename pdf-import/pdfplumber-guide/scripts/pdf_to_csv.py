"""
pdf_to_csv.py — Extract numbered requirements from a PDF to CSV.

Handles up to 6 levels of section numbering:
  1   1.1   1.1.1   1.1.1.1   1.1.1.1.1   1.1.1.1.1.1

Output CSV: three columns
  Column A (section)     — section/annex context, e.g. "Section A", "Annex B", "Part I"
  Column B (req_number)  — requirement number, e.g. "1.1.1"
  Column C (requirement) — requirement text; inline bullets normalised to "- item | - item"

Why three columns?
  A document may contain multiple sections or annexes that each restart numbering
  from 1.1. Without a section column, requirement 1.1 of Section A and requirement
  1.1 of Annex B would be indistinguishable in the CSV and wrong after sorting.

Usage:
  python pdf_to_csv.py input.pdf output.csv [--debug]

Strategy:
  1. Strip large-font characters (watermarks) via pdfplumber page.filter().
  2. Reconstruct lines from word bounding boxes; strip header/footer y-bands.
  3. Detect section/annex header lines — update current section context.
  4. Detect requirement lines via section-number regex.
  5. Accumulate continuation lines and bullet lines into requirement text.
  6. Normalise mojibake encoding and bullet characters in all text.
  7. Write three-column CSV sorted by (section_index, section_number).
"""

import pdfplumber
import csv
import re
import sys
import os
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Configuration — edit these to tune the script for your documents
# ---------------------------------------------------------------------------

# Requirement section number: 1 to 6 dot-separated numeric components.
# Matches: 1  1.1  1.1.1  1.1.1.1  1.1.1.1.1  1.1.1.1.1.1
SECTION_PATTERN = re.compile(r"^(\d+(?:\.\d+){0,5})\s{1,4}(.+)$")

MAX_DEPTH = 6

# Section/annex header lines.
# When matched the FULL line text becomes the section context for subsequent
# requirements.  Requirements in two sections with the same number (e.g. 1.1)
# will have different values in the "section" column.
#
# Matches (case-insensitive, must be at LINE START):
#   Section A    Section 1    Section 2.3
#   Annex A      Annex B
#   Appendix A   Appendix 1
#   Part I       Part A       Part 2
#   Chapter 1    Chapter A
#   Schedule A   Attachment B  Exhibit C
#   PART I — title text ...
SECTION_HEADER_PATTERN = re.compile(
    r"^(?:Section|Annex|Appendix|Attachment|Exhibit|Schedule|Part|Chapter)\s+"
    r"(?:[A-Z0-9]+(?:\.\d+)?|[IVX]+)"   # identifier: A, 1, 2.1, I, II …
    r"(?:\s|$|[—–:\-])",                 # followed by space, end, or separator
    re.IGNORECASE,
)

# Lines matching these are silently discarded (not captured as noise or sections).
NOISE_PATTERNS = [
    re.compile(r"^\[(?:NOTE|ANNOTATION):", re.IGNORECASE),
    re.compile(r"^FOR TEST(?:ING)? (?:USE )?ONLY", re.IGNORECASE),
    re.compile(r"^UNCONTROLLED WHEN PRINTED", re.IGNORECASE),
    re.compile(r"^CONFIDENTIAL$", re.IGNORECASE),
    re.compile(r"^SAMPLE REQUIREMENTS SPEC", re.IGNORECASE),
    re.compile(r"^DRAFT\s*[—–-]", re.IGNORECASE),
    re.compile(r"^Page \d+", re.IGNORECASE),
    re.compile(r"^Version \d+\.\d+"),
    re.compile(r"^Document \d+\s*[—–-]"),
]

# y-coordinate bands (points from page edge) treated as header/footer.
# A4 height = 841.89 pt.  Increase these if your docs have large headers/footers.
HEADER_MARGIN_TOP = 60
FOOTER_MARGIN_BOTTOM = 50

# Characters larger than this (pt) are decorative (watermarks, banners).
# Set to None to disable.
MAX_CONTENT_FONT_SIZE = 20

# ---------------------------------------------------------------------------
# Bullet normalisation
# ---------------------------------------------------------------------------

# Unicode bullet characters that may appear at the start of a continuation line.
_BULLET_CHARS = frozenset({
    "•",   # • BULLET
    "◦",   # ◦ WHITE BULLET
    "▪",   # ▪ BLACK SMALL SQUARE
    "▫",   # ▫ WHITE SMALL SQUARE
    "▸",   # ▸ BLACK RIGHT-POINTING SMALL TRIANGLE
    "→",   # → RIGHTWARDS ARROW
    "–",   # – EN DASH (used as bullet in some docs)
    "—",   # — EM DASH (used as bullet in some docs)
})

# Separator inserted between the parent requirement text and bullet items,
# and between successive bullet items.
BULLET_SEPARATOR = " | "
# Prefix applied to each normalised bullet item.
BULLET_PREFIX = "- "

# ---------------------------------------------------------------------------
# Encoding fixup
# ---------------------------------------------------------------------------
# Maps mojibake strings (UTF-8 bytes decoded as Windows-1252) to their
# correct Unicode equivalents.  Apply this before any other text processing.
#
# How the mojibake arises:
#   PDF font stores char as Unicode codepoint U+2022 (BULLET).
#   Its UTF-8 representation is bytes 0xE2 0x80 0xA2.
#   If those bytes are (mis)interpreted as Windows-1252:
#     0xE2 → â    0x80 → €    0xA2 → ¢   →  "â€¢"
#   The table below maps each such triple back to the original character.
#
# Listed longest-first so that overlapping prefixes are caught correctly.
_MOJIBAKE_MAP = [
    # Each tuple: (mojibake_string, correct_unicode_replacement)
    # Mojibake arises when UTF-8 bytes are decoded as Windows-1252.
    # U+2022 BULLET: UTF-8 E2 80 A2 -> cp1252: a-hat + euro + cent -> "a€\xa2"
    # Listed longest-first so overlapping prefixes match correctly.
    ("\xe2\x80\xa2",    "•"),  # BULLET
    ("\xe2\x80\x9c",    "“"),  # LEFT DOUBLE QUOTATION MARK
    ("\xe2\x80\x9d",    "”"),  # RIGHT DOUBLE QUOTATION MARK
    ("\xe2\x80\x98",    "‘"),  # LEFT SINGLE QUOTATION MARK
    ("\xe2\x80\x99",    "’"),  # RIGHT SINGLE QUOTATION MARK
    ("\xe2\x80\x94",    "—"),  # EM DASH
    ("\xe2\x80\x93",    "–"),  # EN DASH
    ("\xe2\x80\xa6",    "…"),  # HORIZONTAL ELLIPSIS
    ("\xe2\x80\xa1",    "‡"),  # DOUBLE DAGGER
    ("\xe2\x80\xb0",    "‰"),  # PER MILLE SIGN
    ("\xe2\x84\xa2",    "™"),  # TRADE MARK SIGN
    ("\xe2\x86\x92",    "→"),  # RIGHTWARDS ARROW
    ("\xe2\x86\x90",    "←"),  # LEFTWARDS ARROW
    ("\xc3\xa9",        "é"),  # e WITH ACUTE
    ("\xc3\xa8",        "è"),  # e WITH GRAVE
    ("\xc3\xa0",        "à"),  # a WITH GRAVE
    ("\xc3\xbc",        "ü"),  # u WITH DIAERESIS
    ("\xc3\xb6",        "ö"),  # o WITH DIAERESIS
    ("\xc3\xa4",        "ä"),  # a WITH DIAERESIS
    ("�",          ""),        # REPLACEMENT CHARACTER - strip
]


def fix_encoding(text: str) -> str:
    """Replace Windows-1252 mojibake sequences with their correct Unicode."""
    for bad, good in _MOJIBAKE_MAP:
        if bad in text:
            text = text.replace(bad, good)
    return text


def is_bullet_line(text: str) -> bool:
    """Return True if the line starts with any recognised bullet character."""
    if not text:
        return False
    # Direct Unicode bullet at start
    if text[0] in _BULLET_CHARS:
        return True
    # Dash-style bullet: "- text" or "* text" (require a space after the marker)
    if re.match(r"^[-*]\s+\S", text):
        return True
    # Mojibake bullet at start (fix_encoding hasn't been called yet on raw lines)
    if text.startswith("â€¢"):
        return True
    return False


def normalise_bullet_line(text: str) -> str:
    """
    Strip leading bullet character (and any variants) from a line and
    return the content prefixed with BULLET_PREFIX.
    """
    text = fix_encoding(text)
    # Strip leading bullet char
    if text and text[0] in _BULLET_CHARS:
        text = text[1:].lstrip()
    elif re.match(r"^[-*]\s+", text):
        text = re.sub(r"^[-*]\s+", "", text)
    return BULLET_PREFIX + text.strip()


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------

@dataclass
class Requirement:
    section: str           # section/annex context, e.g. "Section A", "Annex B"
    section_index: int     # ordinal position of this section in the document
    req_number: str        # requirement number, e.g. "1.1.1"
    text: str


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def is_noise(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    for pattern in NOISE_PATTERNS:
        if pattern.search(stripped):
            return True
    return False


def req_depth(req_number: str) -> int:
    return req_number.count(".") + 1


def sort_key(req: Requirement) -> tuple:
    """Sort by section order then numeric requirement hierarchy."""
    return (req.section_index,) + tuple(int(x) for x in req.req_number.split("."))


def extract_lines_from_page(page, debug: bool = False) -> list[str]:
    """
    Extract content lines from a page, stripping watermarks (large font),
    headers, and footers.
    """
    page_height = page.height

    if MAX_CONTENT_FONT_SIZE is not None:
        page = page.filter(lambda obj: (
            obj.get("object_type") != "char"
            or obj.get("size", 0) <= MAX_CONTENT_FONT_SIZE
        ))

    words = page.extract_words(
        x_tolerance=3,
        y_tolerance=3,
        keep_blank_chars=False,
        use_text_flow=True,
    )
    if not words:
        return []

    def in_content_zone(w):
        if w["top"] < HEADER_MARGIN_TOP:
            return False
        if w["bottom"] > page_height - FOOTER_MARGIN_BOTTOM:
            return False
        return True

    content_words = [w for w in words if in_content_zone(w)]
    if not content_words:
        return []

    lines_by_y: dict[int, list] = {}
    for w in content_words:
        bucket = round(w["top"] / 2) * 2
        lines_by_y.setdefault(bucket, []).append(w)

    reconstructed = []
    for y in sorted(lines_by_y):
        line_words = sorted(lines_by_y[y], key=lambda w: w["x0"])
        line_text = " ".join(w["text"] for w in line_words).strip()
        if line_text:
            reconstructed.append(line_text)
            if debug:
                print(f"  [y={y:5.1f}] {line_text[:90]}")

    return reconstructed


def rejoin_split_section_numbers(lines: list[str]) -> list[str]:
    """
    Rejoin a section number that a narrow column has split across two lines:
      "1.1."  +  "1 The system shall..." -> "1.1.1 The system shall..."
    """
    PARTIAL = re.compile(r"^(\d+\.)+$")
    result = []
    i = 0
    while i < len(lines):
        if PARTIAL.match(lines[i].strip()) and i + 1 < len(lines):
            result.append(lines[i].strip() + lines[i + 1].strip())
            i += 2
        else:
            result.append(lines[i])
            i += 1
    return result


def parse_requirements(lines: list[str], debug: bool = False) -> list[Requirement]:
    """
    Parse lines into Requirement objects, tracking section/annex context.

    Priority order for each line:
      1. Section header  → update current_section
      2. Noise           → discard
      3. Requirement     → start new Requirement
      4. Bullet          → append normalised bullet to current requirement
      5. Continuation    → append text to current requirement
    """
    requirements: list[Requirement] = []
    current: Optional[Requirement] = None

    current_section = ""        # section name for requirements without an explicit section
    current_section_index = -1  # -1 so first increment gives 0
    section_order: dict[str, int] = {}
    in_annotation = False       # True while inside a multi-line [NOTE: ...] block

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Consume remaining lines of a multi-line annotation / note block.
        # A block opened by "[NOTE: ..." closes when a line ends with "]".
        if in_annotation:
            if debug:
                print(f"  [ANNOT+]  {stripped[:70]}")
            if stripped.endswith("]"):
                in_annotation = False
            continue

        # 1. Section/annex header — capture, don't discard
        if SECTION_HEADER_PATTERN.match(stripped):
            if current:
                requirements.append(current)
                current = None
            current_section = stripped
            if current_section not in section_order:
                current_section_index += 1
                section_order[current_section] = current_section_index
            else:
                current_section_index = section_order[current_section]
            if debug:
                print(f"  [SECTION] {stripped[:70]}")
            continue

        # 2. Noise — discard; detect opening of multi-line annotation blocks
        if is_noise(stripped):
            if stripped.startswith("[") and not stripped.endswith("]"):
                in_annotation = True
            if debug:
                print(f"  [NOISE]   {stripped[:70]}")
            continue

        # 3. Requirement number match
        match = SECTION_PATTERN.match(stripped)
        if match:
            req_num = match.group(1)
            req_text = match.group(2).strip()

            if req_depth(req_num) > MAX_DEPTH:
                if debug:
                    print(f"  [DEPTH>6] {stripped[:70]}")
                if current:
                    current.text += " " + stripped
                continue

            if current:
                requirements.append(current)

            current = Requirement(
                section=current_section,
                section_index=current_section_index,
                req_number=req_num,
                text=req_text,
            )
            if debug:
                print(f"  [REQ {req_num:20s}] {req_text[:50]}")
            continue

        # 4. Bullet continuation
        if is_bullet_line(stripped):
            if current:
                normalised = normalise_bullet_line(stripped)
                current.text += BULLET_SEPARATOR + normalised
                if debug:
                    print(f"  [BULLET]  {normalised[:60]}")
            else:
                if debug:
                    print(f"  [SKIP-B]  {stripped[:70]}")
            continue

        # 5. Plain continuation
        if current:
            current.text += " " + stripped
            if debug:
                print(f"  [CONT]    {stripped[:70]}")
        else:
            if debug:
                print(f"  [SKIP]    {stripped[:70]}")

    if current:
        requirements.append(current)

    return requirements


def clean_text(text: str) -> str:
    """
    Final cleanup of requirement text:
      1. Fix encoding mojibake (â€¢ → •, etc.)
      2. Re-normalise any remaining raw bullet chars to BULLET_PREFIX
      3. Fix soft-hyphen line-break artefacts
      4. Collapse whitespace
    """
    text = fix_encoding(text)

    # Normalise any bullet chars that survived (e.g. raw • in continuation text)
    # Only at word boundaries where they look like bullets (preceded by space or |)
    for ch in _BULLET_CHARS:
        # Replace " • text" with " | - text"
        text = re.sub(
            r"(?<=\s)" + re.escape(ch) + r"\s*",
            BULLET_SEPARATOR + BULLET_PREFIX,
            text,
        )

    # Fix hyphenated line-break artefacts: "require- ment" → "requirement"
    text = re.sub(r"-\s+(?=[a-z])", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def pdf_to_csv(pdf_path: str, csv_path: str, debug: bool = False) -> int:
    all_lines: list[str] = []

    print(f"Opening: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        print(f"  Pages: {len(pdf.pages)}")
        for page_num, page in enumerate(pdf.pages, start=1):
            if debug:
                print(f"\n--- Page {page_num} ---")
            all_lines.extend(extract_lines_from_page(page, debug=debug))

    print(f"  Lines extracted: {len(all_lines)}")

    all_lines = rejoin_split_section_numbers(all_lines)
    requirements = parse_requirements(all_lines, debug=debug)
    print(f"  Requirements found: {len(requirements)}")

    requirements.sort(key=sort_key)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["section", "req_number", "requirement"])
        for req in requirements:
            writer.writerow([req.section, req.req_number, clean_text(req.text)])

    print(f"  Written to: {csv_path}")
    return len(requirements)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3:
        print("Usage: python pdf_to_csv.py <input.pdf> <output.csv> [--debug]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    csv_path = sys.argv[2]
    debug = "--debug" in sys.argv

    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    count = pdf_to_csv(pdf_path, csv_path, debug=debug)
    print(f"\nDone. {count} requirements extracted.")

    if count == 0:
        print("\nTIP: Run with --debug to trace line-by-line parsing.")
        print("     Common causes of zero output:")
        print("     - SECTION_PATTERN not matching your numbering format")
        print("     - HEADER_MARGIN_TOP too large, stripping content")
        print("     - NOISE_PATTERNS accidentally matching requirement lines")


if __name__ == "__main__":
    main()
