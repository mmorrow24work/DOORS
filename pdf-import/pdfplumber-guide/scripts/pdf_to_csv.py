"""
pdf_to_csv.py — Extract numbered requirements from a PDF to CSV.

Handles up to 6 levels of section numbering:
  1   1.1   1.1.1   1.1.1.1   1.1.1.1.1   1.1.1.1.1.1

Output CSV: six columns matching IBM DOORS Next standard import attribute names
  section       — document section/annex context, e.g. "Schedule 4.1 – Annex A"
                  (custom attribute — import into a matching DOORS custom attribute)
  Identifier    — unique requirement identifier scoped to its section, e.g. "4.1.AA::2.1"
                  When req numbers restart across sections the section prefix (e.g. "4.1.AA")
                  is prepended so that DOORS can unambiguously resolve parentBinding links.
                  For documents with globally unique numbers the plain number is used.
                  (DOORS standard — parentBinding is matched against this column)
  Primary Text  — full requirement text; bullets normalised to newline-separated "- item" lines
  Artifact Type — always "Functional Requirement" (edit per your DOORS type scheme)
  Name          — first line of requirement text (DOORS artifact short name)
  parentBinding — Identifier of parent artifact; empty for top-level within a section

Why the section column?
  A document may contain multiple sections or annexes that each restart numbering
  from 1.1. Without a section column, requirement 1.1 of Section A and requirement
  1.1 of Annex B would be indistinguishable in the CSV and wrong after sorting.

Usage:
  python pdf_to_csv.py input.pdf output.csv [--debug] [--obfuscate]

  --debug      Print line-by-line parsing trace to stdout.
  --obfuscate  Also write a second CSV named <output>-OBF.csv where every
               text word is replaced with 'x' sequences.  Numbers, section
               numbers, bullet markers, and column structure are preserved so
               the file can be shared for diagnostics without exposing client
               content.  The normal CSV is still written unchanged.

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
# Also matches the "N. Text" format where the top-level number has a trailing
# period (e.g. "4. Identity, Security and Office 365 Services").  The \.? makes
# the trailing period optional so both "4 Text" and "4. Text" are captured.
SECTION_PATTERN = re.compile(r"^(\d+(?:\.\d+){0,5})\.?\s{1,4}(.+)$")

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
    # Table of Contents dotted leader: "2.1 Acronyms ............. 5"
    # Matches any line where text is followed by 4+ dots and a page number.
    re.compile(r"\.{4,}\s*\d+\s*$"),
]

# Separator inserted between the section prefix and the requirement number when
# building a composite Identifier for documents with restarting req numbering.
# E.g. "4.1.AA" + "::" + "2.1"  →  "4.1.AA::2.1"
IDENTIFIER_SEP = "::"

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
BULLET_SEPARATOR = "\n"
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
    #
    # Mojibake arises when a PDF font stores characters as raw UTF-8 byte
    # sequences but the bytes are decoded one-per-character by pdfplumber.
    # Two common decoders produce different results for the 0x80–0x9F range:
    #
    #   ISO-8859-1 (Latin-1): 0x80 → U+0080 (C1 control), 0x94 → U+0094
    #   Windows-1252 (cp1252): 0x80 → U+20AC (€),          0x94 → U+201D (")
    #
    # Both variants are listed so the map works regardless of which decoder
    # pdfplumber used for a given PDF.  cp1252 variants are listed first so
    # that the more visually recognisable sequences are matched before the
    # invisible C1 control-character variants.
    #
    # CID glyph references -- pdfplumber emits (cid:N) when a font has no
    # ToUnicode map entry for a glyph.  Common in PDFs that embed bullet
    # characters in standard fonts (Helvetica, Times) without a ToUnicode CMap.
    ("(cid:127)",       "\u2022"),  # glyph 127 in Helvetica = bullet (U+2022)
    ("(cid:149)",       "\u2022"),  # glyph 149 in some Windows fonts = bullet
    # cp1252 variants (0x80->U+20AC euro, 0x93->U+201C left-dquot, 0x94->U+201D right-dquot)
    ("\u00e2\u20ac\u201d",  "\u2014"),  # EM DASH   E2 80 94 (cp1252: 94->U+201D)
    ("\u00e2\u20ac\u201c",  "\u2013"),  # EN DASH   E2 80 93 (cp1252: 93->U+201C)
    ("\u00e2\u20ac\u00a2",  "\u2022"),  # BULLET    E2 80 A2 (cp1252: A2->U+00A2, same as Latin-1)
    ("\u00e2\u20ac\u0153",  "\u201c"),  # LEFT DOUBLE QUOT  E2 80 9C (cp1252: 9C->U+0153 oe)
    ("\u00e2\u20ac\u2122",  "\u2019"),  # RIGHT SINGLE QUOT E2 80 99 (cp1252: 99->U+2122 TM)
    ("\u00e2\u20ac\u02dc",  "\u2018"),  # LEFT SINGLE QUOT  E2 80 98 (cp1252: 98->U+02DC tilde)
    ("\u00e2\u20ac\u2026",  "\u2026"),  # ELLIPSIS  E2 80 A6
        # ISO-8859-1 / Latin-1 variants (0x80 → U+0080 control char)
    ("\xe2\x80\xa2",    "•"),   # BULLET
    ("\xe2\x80\x9c",    "“"),  # LEFT DOUBLE QUOTATION MARK
    ("\xe2\x80\x9d",    "”"),  # RIGHT DOUBLE QUOTATION MARK
    ("\xe2\x80\x98",    "‘"),  # LEFT SINGLE QUOTATION MARK
    ("\xe2\x80\x99",    "’"),  # RIGHT SINGLE QUOTATION MARK
    ("\xe2\x80\x94",    "—"),   # EM DASH
    ("\xe2\x80\x93",    "–"),   # EN DASH
    ("\xe2\x80\xa6",    "…"),   # HORIZONTAL ELLIPSIS
    ("\xe2\x80\xa1",    "‡"),   # DOUBLE DAGGER
    ("\xe2\x80\xb0",    "‰"),   # PER MILLE SIGN
    ("\xe2\x84\xa2",    "™"),   # TRADE MARK SIGN
    ("\xe2\x86\x92",    "→"),   # RIGHTWARDS ARROW
    ("\xe2\x86\x90",    "←"),   # LEFTWARDS ARROW
    ("\xc3\xa9",        "é"),   # e WITH ACUTE
    ("\xc3\xa8",        "è"),   # e WITH GRAVE
    ("\xc3\xa0",        "à"),   # a WITH GRAVE
    ("\xc3\xbc",        "ü"),   # u WITH DIAERESIS
    ("\xc3\xb6",        "ö"),   # o WITH DIAERESIS
    ("\xc3\xa4",        "ä"),   # a WITH DIAERESIS
    ("�",          ""),    # REPLACEMENT CHARACTER - strip
]


def fix_encoding(text: str) -> str:
    """Replace Windows-1252 mojibake sequences with their correct Unicode."""
    for bad, good in _MOJIBAKE_MAP:
        if bad in text:
            text = text.replace(bad, good)
    return text


def _obfuscate_text(text: str) -> str:
    """Replace words with 'x' sequences for safe debug sharing (keeps numbers/structure)."""
    return re.sub(r'[A-Za-z]\w*', lambda m: 'x' * len(m.group()), text)


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
    # CID glyph reference at start — bullet without ToUnicode map entry
    if text.startswith("(cid:127)") or text.startswith("(cid:149)"):
        return True
    return False


def normalise_bullet_line(text: str) -> str:
    """
    Strip leading bullet character (and any variants) from a line and
    return the content prefixed with BULLET_PREFIX.
    """
    text = fix_encoding(text)
    # Strip leading bullet char or CID reference
    if text.startswith("(cid:127)") or text.startswith("(cid:149)"):
        text = text[len("(cid:127)"):].lstrip() if text.startswith("(cid:127)") else text[len("(cid:149)"):].lstrip()
    elif text and text[0] in _BULLET_CHARS:
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


def derive_parent(req_number: str) -> str:
    """Return the parent req_number (drop the last numeric component)."""
    parts = req_number.split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else ""


def make_name(text: str) -> str:
    """Return the first line of requirement text as the artifact short name."""
    return text.split("\n")[0].strip()


def make_section_prefix(section: str) -> str:
    """
    Derive a short, stable prefix from a section heading for use in Identifier.

    When a document restarts requirement numbering in each section (e.g. every
    Schedule starts again at 2.1), different sections would produce duplicate
    Identifier values.  This prefix scopes each Identifier to its section so
    that DOORS can resolve parentBinding links unambiguously.

    "Schedule 4.1 – Annex A"      →  "4.1.AA"
    "Schedule 4.1 – Foundation"   →  "4.1.F"
    "Section 2 — Authentication"  →  "2.A"
    "Annex B"                     →  "B"
    ""                            →  ""  (no prefix — req_number used as-is)
    """
    if not section:
        return ""
    # Extract leading number (e.g. "4.1" from "Schedule 4.1 – Annex A")
    num_match = re.search(r'\b(\d[\d.]*)', section)
    num = num_match.group(1).rstrip('.') if num_match else ""
    # Extract text after a dash-like separator or inside parentheses
    sep_match = re.search(r'[–—\-]\s*(.+)$|\(([^)]+)\)', section)
    if sep_match:
        suffix_text = (sep_match.group(1) or sep_match.group(2) or "").strip()
        words = re.findall(r'[A-Za-z0-9]+', suffix_text)
        if words:
            abbr = "".join(w[0].upper() for w in words[:5])
            return f"{num}.{abbr}" if num else abbr
    return num


def extract_lines_from_page(page, debug: bool = False, obfuscate: bool = False) -> list[str]:
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
                display = _obfuscate_text(line_text) if obfuscate else line_text
                print(f"  [y={y:5.1f}] {display[:90]}")

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


_BARE_BULLET_RE = re.compile(
    r"^(?:[-*•◦▪▫▸→]|–|—|\(cid:\d+\))$"
)


def merge_orphaned_bullets(lines: list[str]) -> list[str]:
    """
    Merge lines that are only a bullet marker with the line that follows them.

    pdfplumber sometimes extracts the bullet character (e.g. '-', '•') at a
    slightly different y-coordinate from its text, producing two lines where
    one is just the marker and the next is the bare text.  Merging them gives
    '- Defender for Servers' instead of '-' followed by 'Defender for Servers'
    (which would otherwise be treated as a continuation of the preceding item).
    """
    result = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if _BARE_BULLET_RE.match(stripped) and i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            # Don't merge into a section header or a new requirement number
            if (not SECTION_HEADER_PATTERN.match(next_stripped) and
                    not SECTION_PATTERN.match(next_stripped)):
                result.append(stripped + " " + next_stripped)
                i += 2
                continue
        result.append(lines[i])
        i += 1
    return result


def parse_requirements(lines: list[str], debug: bool = False, obfuscate: bool = False) -> list[Requirement]:
    """
    Parse lines into Requirement objects, tracking section/annex context.

    Priority order for each line:
      1. Section header  → update current_section
      2. Noise           → discard
      3. Requirement     → start new Requirement
      4. Bullet          → append normalised bullet to current requirement
      5. Continuation    → append text to current requirement
    """
    lines = merge_orphaned_bullets(lines)

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
        def _d(text: str) -> str:
            return _obfuscate_text(text) if obfuscate else text

        if in_annotation:
            if debug:
                print(f"  [ANNOT+]  {_d(stripped)[:70]}")
            if stripped.endswith("]"):
                in_annotation = False
            continue

        # 1. Section/annex header — capture, don't discard
        if SECTION_HEADER_PATTERN.match(stripped):
            if current:
                requirements.append(current)
                current = None
            # Strip any TOC dotted leader + page number from the heading text so
            # that a TOC entry "Annex 4 – Xyz Spec ......... 82" is stored with
            # the same clean name as the body heading "Annex 4 – Xyz Spec".
            current_section = re.sub(r"\s*\.{4,}[\s\d]*$", "", stripped).strip()
            if current_section not in section_order:
                current_section_index += 1
                section_order[current_section] = current_section_index
            else:
                current_section_index = section_order[current_section]
            if debug:
                print(f"  [SECTION] {_d(current_section)[:70]}")
            continue

        # 2. Noise — discard; detect opening of multi-line annotation blocks
        if is_noise(stripped):
            if stripped.startswith("[") and not stripped.endswith("]"):
                in_annotation = True
            if debug:
                print(f"  [NOISE]   {_d(stripped)[:70]}")
            continue

        # 3. Requirement number match
        match = SECTION_PATTERN.match(stripped)
        if match:
            req_num = match.group(1)
            req_text = match.group(2).strip()

            if req_depth(req_num) > MAX_DEPTH:
                if debug:
                    print(f"  [DEPTH>6] {_d(stripped)[:70]}")
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
                print(f"  [REQ {req_num:20s}] {_d(req_text)[:50]}")
            continue

        # 4. Bullet continuation
        if is_bullet_line(stripped):
            if current:
                normalised = normalise_bullet_line(stripped)
                # Skip bare markers with no text (e.g. orphaned "-" with nothing to merge)
                if normalised[len(BULLET_PREFIX):].strip():
                    current.text += BULLET_SEPARATOR + normalised
                    if debug:
                        print(f"  [BULLET]  {_d(normalised)[:60]}")
                elif debug:
                    print(f"  [EMPTY-B] {_d(stripped)[:70]}")
            else:
                if debug:
                    print(f"  [SKIP-B]  {_d(stripped)[:70]}")
            continue

        # 5. Plain continuation
        if current:
            current.text += " " + stripped
            if debug:
                print(f"  [CONT]    {_d(stripped)[:70]}")
        else:
            if debug:
                print(f"  [SKIP]    {_d(stripped)[:70]}")

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

    # Normalise any bullet chars that survived (e.g. raw • in continuation text).
    # Em/en dashes are excluded: mid-sentence they are grammatical punctuation,
    # not bullets. is_bullet_line() handles them correctly when at line start.
    _RENORM_BULLET_CHARS = _BULLET_CHARS - {"—", "–"}  # — –
    for ch in _RENORM_BULLET_CHARS:
        text = re.sub(
            r"(?<=\s)" + re.escape(ch) + r"\s*",
            BULLET_SEPARATOR + BULLET_PREFIX,
            text,
        )

    # Fix hyphenated line-break artefacts: "require- ment" → "requirement"
    # (?<=\w) ensures only word-internal hyphens are removed, not bullet "- " prefixes.
    text = re.sub(r"(?<=\w)-[ \t]+(?=[a-z])", "", text)
    # Collapse horizontal whitespace only (preserve newlines between bullet items).
    text = re.sub(r"[ \t]+", " ", text)
    # Strip trailing spaces from each line.
    text = re.sub(r" +$", "", text, flags=re.MULTILINE)
    # Remove lines that are bare bullet markers with no content.  These can appear
    # when the re-normalise loop above converts an inline bullet char to "\n- " and
    # the char had no following text (e.g. a bullet at the very end of a line).
    text = "\n".join(
        line for line in text.split("\n")
        if not re.match(r"^[-*•◦▪▫▸→–—]\s*$", line)
    )
    return text.strip()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def pdf_to_csv(pdf_path: str, csv_path: str, debug: bool = False, obfuscate: bool = False) -> int:
    all_lines: list[str] = []

    print(f"Opening: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        print(f"  Pages: {len(pdf.pages)}")
        for page_num, page in enumerate(pdf.pages, start=1):
            if debug:
                print(f"\n--- Page {page_num} ---")
            all_lines.extend(extract_lines_from_page(page, debug=debug, obfuscate=obfuscate))

    print(f"  Lines extracted: {len(all_lines)}")

    all_lines = rejoin_split_section_numbers(all_lines)
    requirements = parse_requirements(all_lines, debug=debug, obfuscate=obfuscate)
    print(f"  Requirements found: {len(requirements)}")

    requirements.sort(key=sort_key)

    # "Identifier" is the DOORS Next standard column that parentBinding matches
    # against to resolve parent-child links.  A section prefix is prepended when
    # req numbers restart across sections so that Identifiers remain unique.
    # "section" is a custom column; DOORS imports it if a matching attribute
    # exists in your artifact type.
    HEADER = ["section", "Identifier", "Primary Text", "Artifact Type", "Name", "parentBinding"]

    rows = []
    for req in requirements:
        text = clean_text(req.text)
        section_text = fix_encoding(req.section)
        prefix = make_section_prefix(section_text)
        parent_num = derive_parent(req.req_number)
        identifier = f"{prefix}{IDENTIFIER_SEP}{req.req_number}" if prefix else req.req_number
        parent_binding = (f"{prefix}{IDENTIFIER_SEP}{parent_num}" if prefix and parent_num
                          else parent_num)
        rows.append([
            section_text,
            identifier,
            text,
            "Functional Requirement",
            make_name(text),
            parent_binding,
        ])

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)
    print(f"  Written to: {csv_path}")

    if obfuscate:
        stem, ext = os.path.splitext(csv_path)
        obf_path = stem + "-OBF" + ext
        with open(obf_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)
            for section, identifier, text, art_type, name, parent in rows:
                writer.writerow([
                    _obfuscate_text(section),
                    identifier,          # section prefix + req number: not sensitive
                    _obfuscate_text(text),
                    art_type,            # constant: not sensitive
                    _obfuscate_text(name),
                    parent,              # section prefix + req number: not sensitive
                ])
        print(f"  Obfuscated copy: {obf_path}")
    return len(requirements)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3:
        print("Usage: python pdf_to_csv.py <input.pdf> <output.csv> [--debug] [--obfuscate]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    csv_path = sys.argv[2]
    debug = "--debug" in sys.argv
    obfuscate = "--obfuscate" in sys.argv

    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    count = pdf_to_csv(pdf_path, csv_path, debug=debug, obfuscate=obfuscate)
    print(f"\nDone. {count} requirements extracted.")

    if count == 0:
        print("\nTIP: Run with --debug to trace line-by-line parsing.")
        print("     Common causes of zero output:")
        print("     - SECTION_PATTERN not matching your numbering format")
        print("     - HEADER_MARGIN_TOP too large, stripping content")
        print("     - NOISE_PATTERNS accidentally matching requirement lines")


if __name__ == "__main__":
    main()
