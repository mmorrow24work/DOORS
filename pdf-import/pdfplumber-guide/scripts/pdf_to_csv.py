"""
pdf_to_csv.py — Extract numbered requirements from a PDF to CSV.

Handles up to 6 levels of section numbering:
  1   1.1   1.1.1   1.1.1.1   1.1.1.1.1   1.1.1.1.1.1

Output CSV: two columns
  Column A (section_number) — e.g. "1.1.1"
  Column B (requirement)    — the requirement text

Usage:
  python pdf_to_csv.py input.pdf output.csv [--debug]

Strategy:
  1. Extract all text from each page using pdfplumber, word-by-word with
     bounding boxes so we can reconstruct lines accurately.
  2. Reconstruct lines from word positions (handles multi-column and
     header/footer stripping by y-coordinate bands).
  3. Apply a regex to detect lines that BEGIN with a valid section number.
  4. Accumulate continuation lines (lines with no section number that
     follow a matched line) into the same requirement text.
  5. Ignore decorative content: divider banners, annotations in brackets,
     page headers/footers (detected by y-position proximity to page edges).
  6. Write results to CSV.
"""

import pdfplumber
import csv
import re
import sys
import os
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Section number pattern: 1 to 6 dot-separated numeric components
# Matches: 1, 1.1, 1.1.1, 1.1.1.1, 1.1.1.1.1, 1.1.1.1.1.1
SECTION_PATTERN = re.compile(
    r"^(\d+(?:\.\d+){0,5})\s{1,4}(.+)$"
)

# Maximum section depth we will recognise (6 = 6 dot-separated groups)
MAX_DEPTH = 6

# Lines whose text matches these patterns are treated as noise and ignored.
# Add patterns here as you discover new noise in your documents.
NOISE_PATTERNS = [
    re.compile(r"^\[(?:NOTE|ANNOTATION):", re.IGNORECASE),   # inline notes
    re.compile(r"^FOR TEST(?:ING)? (?:USE )?ONLY", re.IGNORECASE),  # watermarks
    re.compile(r"^UNCONTROLLED WHEN PRINTED", re.IGNORECASE),
    re.compile(r"^CONFIDENTIAL$", re.IGNORECASE),
    re.compile(r"^SAMPLE REQUIREMENTS SPEC", re.IGNORECASE),
    re.compile(r"^DRAFT\s*—", re.IGNORECASE),
    re.compile(r"^Page \d+", re.IGNORECASE),
    re.compile(r"^Version \d+\.\d+"),
    re.compile(r"^Document \d+\s*—"),
]

# Section divider banners: all-uppercase lines with no section number
# that are likely structural headings, not requirements.
DIVIDER_PATTERN = re.compile(r"^PART\s+[IVX]+\s*—", re.IGNORECASE)

# y-coordinate margin (points) from top/bottom of page within which
# we discard text as likely header/footer. A4 = 841.89pt height.
# Adjust if your documents have unusually large headers or footers.
HEADER_MARGIN_TOP = 60      # ignore text above (page_height - 60) from bottom = top 60pt
FOOTER_MARGIN_BOTTOM = 50   # ignore text below 50pt from bottom of page

# Maximum font size (points) for content characters.
# Characters larger than this are treated as decorative (watermarks, banners).
# Set to None to disable font-size filtering.
MAX_CONTENT_FONT_SIZE = 20


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Requirement:
    section_number: str
    text: str


# ---------------------------------------------------------------------------
# Core extraction logic
# ---------------------------------------------------------------------------

def is_noise(line: str) -> bool:
    """Return True if this line should be discarded as noise."""
    stripped = line.strip()
    if not stripped:
        return True
    for pattern in NOISE_PATTERNS:
        if pattern.search(stripped):
            return True
    if DIVIDER_PATTERN.match(stripped):
        return True
    return False


def section_depth(section_number: str) -> int:
    """Return the nesting depth of a section number. '1.1.1' -> 3."""
    return section_number.count(".") + 1


def section_key(section_number: str) -> tuple:
    """Convert '1.1.2' to (1, 1, 2) for numeric sorting."""
    return tuple(int(x) for x in section_number.split("."))


def extract_lines_from_page(page, debug: bool = False) -> list[str]:
    """
    Extract text lines from a pdfplumber page object.

    Approach: use word-level extraction with bounding boxes to reconstruct
    lines, then strip header/footer bands by y-coordinate.

    Font-size filtering removes watermarks and large decorative text before
    word grouping, preventing them from interleaving with content lines.
    """
    page_height = page.height

    # Strip large-font characters (watermarks, banner decorations) before
    # extracting words. pdfplumber.Page.filter() returns a new page object
    # containing only characters that pass the predicate.
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

    # Filter words in header/footer bands
    def in_content_zone(word):
        y_bottom = word["bottom"]
        y_top = word["top"]
        # Discard words near the top (header) or bottom (footer)
        if y_top < HEADER_MARGIN_TOP:          # near top of page
            return False
        if y_bottom > page_height - FOOTER_MARGIN_BOTTOM:  # near bottom
            return False
        return True

    content_words = [w for w in words if in_content_zone(w)]

    if not content_words:
        return []

    # Group words into lines by their top y-coordinate (within 2pt tolerance)
    lines_by_y: dict[int, list] = {}
    for word in content_words:
        y_bucket = round(word["top"] / 2) * 2   # bucket to nearest 2pt
        lines_by_y.setdefault(y_bucket, []).append(word)

    # Sort buckets top-to-bottom (lower y = higher on page in PDF coords)
    sorted_ys = sorted(lines_by_y.keys())

    reconstructed = []
    for y in sorted_ys:
        line_words = sorted(lines_by_y[y], key=lambda w: w["x0"])
        line_text = " ".join(w["text"] for w in line_words).strip()
        if line_text:
            reconstructed.append(line_text)
            if debug:
                print(f"  [y={y:5.1f}] {line_text[:80]}")

    return reconstructed


def rejoin_split_section_numbers(lines: list[str]) -> list[str]:
    """
    Rejoin lines where a section number has been split across two lines
    by a narrow table column. E.g.:
        "1.1."          <- section number truncated mid-way
        "1 The system..." <- continuation digit + rest of line
    becomes:
        "1.1.1 The system..."
    Detection: a line that is ONLY digits and dots (a partial section number)
    is joined to the next line.
    """
    PARTIAL_SECTION = re.compile(r"^(\d+\.)+$")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if PARTIAL_SECTION.match(line.strip()) and i + 1 < len(lines):
            # Glue the partial number onto the front of the next line
            joined = line.strip() + lines[i + 1].strip()
            result.append(joined)
            i += 2
        else:
            result.append(line)
            i += 1
    return result


def parse_requirements(lines: list[str], debug: bool = False) -> list[Requirement]:
    """
    Parse a flat list of text lines into Requirement objects.

    Rules:
    - A line matching SECTION_PATTERN starts a new requirement.
    - Subsequent non-matching, non-noise lines are appended to the
      current requirement's text (continuation lines).
    - Noise lines are discarded.
    - Section numbers exceeding MAX_DEPTH are treated as continuation text.
    """
    requirements: list[Requirement] = []
    current: Optional[Requirement] = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if is_noise(stripped):
            if debug:
                print(f"  [NOISE]  {stripped[:60]}")
            continue

        match = SECTION_PATTERN.match(stripped)
        if match:
            sec_num = match.group(1)
            req_text = match.group(2).strip()

            # Validate depth
            if section_depth(sec_num) > MAX_DEPTH:
                if debug:
                    print(f"  [DEPTH>6] treating as continuation: {stripped[:60]}")
                if current:
                    current.text += " " + stripped
                continue

            # Save previous requirement
            if current:
                requirements.append(current)

            current = Requirement(section_number=sec_num, text=req_text)
            if debug:
                print(f"  [REQ {sec_num}] {req_text[:50]}")

        else:
            # Continuation line — append to current requirement
            if current:
                current.text += " " + stripped
                if debug:
                    print(f"  [CONT]   {stripped[:60]}")
            else:
                if debug:
                    print(f"  [SKIP]   {stripped[:60]}")

    # Don't forget the last requirement
    if current:
        requirements.append(current)

    return requirements


def clean_requirement_text(text: str) -> str:
    """
    Clean up extracted requirement text:
    - Collapse multiple spaces into one
    - Remove hyphenation artefacts from line breaks (word- broken)
    - Strip leading/trailing whitespace
    """
    # Fix hyphenated line breaks: "require- ment" -> "requirement"
    text = re.sub(r"-\s+", "", text)
    # Collapse internal whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def pdf_to_csv(pdf_path: str, csv_path: str, debug: bool = False) -> int:
    """
    Extract requirements from pdf_path and write to csv_path.
    Returns the number of requirements extracted.
    """
    all_lines: list[str] = []

    print(f"Opening: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        print(f"  Pages: {len(pdf.pages)}")
        for page_num, page in enumerate(pdf.pages, start=1):
            if debug:
                print(f"\n--- Page {page_num} ---")
            lines = extract_lines_from_page(page, debug=debug)
            all_lines.extend(lines)

    print(f"  Total lines extracted: {len(all_lines)}")

    all_lines = rejoin_split_section_numbers(all_lines)
    requirements = parse_requirements(all_lines, debug=debug)
    print(f"  Requirements found: {len(requirements)}")

    # Sort by section number for clean output
    requirements.sort(key=lambda r: section_key(r.section_number))

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["section_number", "requirement"])
        for req in requirements:
            writer.writerow([req.section_number, clean_requirement_text(req.text)])

    print(f"  Written to: {csv_path}")
    return len(requirements)


# ---------------------------------------------------------------------------
# CLI entry point
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
        print("\nTIP: If zero requirements were extracted, try --debug to see")
        print("     how lines are being parsed. Common causes:")
        print("     - SECTION_PATTERN not matching your numbering format")
        print("     - Header/footer margins stripping content lines")
        print("     - NOISE_PATTERNS matching requirement lines")


if __name__ == "__main__":
    main()
