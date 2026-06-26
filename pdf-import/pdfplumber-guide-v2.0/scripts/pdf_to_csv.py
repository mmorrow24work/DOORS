"""
pdf_to_csv.py v2.0 — Config-driven PDF requirements extractor.

Extracts numbered requirements and table-based requirements from a PDF
and writes a six-column CSV ready for IBM DOORS Next import.

Usage:
  python pdf_to_csv.py input.pdf output.csv [--config path/to/config.yaml] [--debug] [--obfuscate]

Options:
  --config FILE   YAML config file.  Defaults are used for any omitted key.
                  See configs/README.md for the full schema and examples.
  --debug         Print line-by-line parsing trace to stdout.
  --obfuscate     Also write <output>-OBF.csv with all text words replaced by
                  'x' sequences (numbers and structure preserved).  Safe for
                  sharing without exposing client content.

Output columns (DOORS Next standard):
  section       — document section/annex context
  Identifier    — unique requirement ID, section-scoped when numbers restart
  Primary Text  — full requirement text; bullets as newline-separated "- item" lines
  Artifact Type — configurable; default "Functional Requirement"
  Name          — first line of Primary Text (DOORS artifact short name)
  parentBinding — Identifier of parent; empty for top-level requirements
"""

import csv
import os
import re
import sys
from dataclasses import dataclass
from typing import Optional

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed.  Run: pip install pdfplumber")
    sys.exit(1)

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _yaml = None
    _YAML_AVAILABLE = False


# ---------------------------------------------------------------------------
# Built-in defaults  (all overridable via config YAML)
# ---------------------------------------------------------------------------

_DEFAULT_SECTION_KEYWORDS = [
    "Section", "Annex", "Appendix", "Attachment",
    "Exhibit", "Schedule", "Part", "Chapter",
]

_DEFAULT_TABLE_COLUMN_MAP = [
    {"pattern": r"(?:module\s+)?requirement\s*id",                   "role": "identifier"},
    {"pattern": r"req(?:uirement)?\s*(?:#|no\.?|number|ref(?:erence)?)", "role": "identifier"},
    {"pattern": r"source\s+of\s+requirement",                        "role": "source"},
    {"pattern": r"(?:module\s+)?requirement\s+acceptance\s+criterion", "role": "primary_text"},
    {"pattern": r"acceptance\s+criterion",                           "role": "acceptance_criterion"},
    {"pattern": r"rationale|supporting\s+information",               "role": "rationale"},
    {"pattern": r"(?:module\s+)?requirement",                        "role": "primary_text"},
    {"pattern": r"description|statement|text",                       "role": "primary_text"},
]

# (pattern_string, re_flags) — compiled into Config.noise_patterns in load_config()
_DEFAULT_NOISE_SPECS = [
    (r"^\[(?:NOTE|ANNOTATION):",               re.IGNORECASE),
    (r"^FOR TEST(?:ING)? (?:USE )?ONLY",       re.IGNORECASE),
    (r"^UNCONTROLLED WHEN PRINTED",            re.IGNORECASE),
    (r"^CONFIDENTIAL$",                        re.IGNORECASE),
    (r"^Page \d+",                             re.IGNORECASE),
    (r"^Version \d+\.\d+",                     0),
    (r"^Document \d+\s*[—–-]",                0),
    (r"\.{4,}\s*\d+\s*$",                      0),  # TOC dotted leaders
]

_MODAL_VERB_RE = re.compile(r"\b(shall|should|must|will|may)\b", re.IGNORECASE)

# Requirement section number: up to 6 dot-separated numeric components.
# The \.? allows "4. Introduction" as well as "4 Introduction".
_SECTION_NUMBER_RE = re.compile(r"^(\d+(?:\.\d+){0,5})\.?\s{1,4}(.+)$")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class Config:
    section_keywords: list
    section_header_pattern: re.Pattern
    max_depth: int
    require_modal_verb: bool
    table_extraction: bool
    table_column_map: list          # [(compiled_pattern, role_str), ...]
    artifact_type: str
    identifier_sep: str
    header_margin_top: float
    footer_margin_bottom: float
    max_font_size: Optional[float]
    noise_patterns: list            # [compiled re.Pattern, ...]
    bullet_separator: str
    bullet_prefix: str
    pages: Optional[str] = None     # e.g. "65-128"; None means all pages


def _build_section_header_pattern(keywords: list) -> re.Pattern:
    kw_alt = "|".join(re.escape(k) for k in keywords)
    return re.compile(
        rf"^(?:{kw_alt})\s+(?:[A-Z0-9]+(?:\.\d+)?|[IVX]+)(?:\s|$|[—–:\-])",
        re.IGNORECASE,
    )


def load_config(path: Optional[str]) -> Config:
    """
    Load a YAML config file and merge it over the built-in defaults.
    Any key omitted from the YAML file uses its default value.
    Raises a clear error if PyYAML is not installed and a config path is given.
    """
    raw: dict = {}
    if path:
        if not _YAML_AVAILABLE:
            print("Error: PyYAML not installed.  Run: pip install pyyaml")
            sys.exit(1)
        with open(path, encoding="utf-8") as fh:
            raw = _yaml.safe_load(fh) or {}

    keywords = raw.get("section_keywords", _DEFAULT_SECTION_KEYWORDS)

    # Noise patterns: built-in defaults + any extras from config
    noise_specs = list(_DEFAULT_NOISE_SPECS)
    for p in raw.get("extra_noise_patterns", []):
        noise_specs.append((p, re.IGNORECASE))
    noise_patterns = [re.compile(pat, flags) for pat, flags in noise_specs]

    # Table column map: use config's list if provided, else built-in defaults
    tbl_raw = raw.get("table_column_map", _DEFAULT_TABLE_COLUMN_MAP)
    table_column_map = [
        (re.compile(entry["pattern"], re.IGNORECASE), entry["role"])
        for entry in tbl_raw
    ]

    return Config(
        section_keywords=keywords,
        section_header_pattern=_build_section_header_pattern(keywords),
        max_depth=int(raw.get("max_depth", 6)),
        require_modal_verb=bool(raw.get("require_modal_verb", False)),
        table_extraction=bool(raw.get("table_extraction", True)),
        table_column_map=table_column_map,
        artifact_type=str(raw.get("artifact_type", "Functional Requirement")),
        identifier_sep=str(raw.get("identifier_separator", "::")),
        header_margin_top=float(raw.get("header_margin_top", 60)),
        footer_margin_bottom=float(raw.get("footer_margin_bottom", 50)),
        max_font_size=(None if raw.get("max_content_font_size") is None
                       else float(raw.get("max_content_font_size", 20))),
        noise_patterns=noise_patterns,
        bullet_separator=str(raw.get("bullet_separator", "\n")),
        bullet_prefix=str(raw.get("bullet_prefix", "- ")),
        pages=str(raw["pages"]) if raw.get("pages") is not None else None,
    )


# ---------------------------------------------------------------------------
# Encoding fixup
# ---------------------------------------------------------------------------

_MOJIBAKE_MAP = [
    ("â€“", "–"),   # â€" → –  EN DASH (cp1252)
    ("â€”", "—"),   # â€" → —  EM DASH (cp1252)
    ("â€™", "’"),   # â€™ → '  RIGHT SINGLE QUOTATION MARK
    ("â€œ", "“"),   # â€œ → "  LEFT DOUBLE QUOTATION MARK
    ("â€", "”"),   # â€  → "  RIGHT DOUBLE QUOTATION MARK
    ("â€¢", "•"),   # â€¢ → •  BULLET
    ("â€³", "″"),   # â€³ → ″  DOUBLE PRIME
    ("Ã©", "é"),         # Ã© → é
    ("Ã¨", "è"),         # Ã¨ → è
    ("Ãª", "ê"),         # Ãª → ê
    # Latin-1 variants (pdfplumber using latin-1 decoder)
    ("\x96", "–"),   # EN DASH
    ("\x97", "—"),   # EM DASH
    ("\x92", "’"),   # RIGHT SINGLE QUOTATION MARK
    ("\x93", "“"),   # LEFT DOUBLE QUOTATION MARK
    ("\x94", "”"),   # RIGHT DOUBLE QUOTATION MARK
    ("\x95", "•"),   # BULLET
]


def fix_encoding(text: str) -> str:
    for bad, good in _MOJIBAKE_MAP:
        text = text.replace(bad, good)
    return text


def _obfuscate_text(text: str) -> str:
    return re.sub(r"[A-Za-z]\w*", lambda m: "x" * len(m.group()), text)


# ---------------------------------------------------------------------------
# Bullet normalisation
# ---------------------------------------------------------------------------

_BULLET_CHARS = frozenset({
    "•", "◦", "▪", "▫", "▸", "→",
    "–", "—",
})

_BARE_BULLET_RE = re.compile(
    r"^(?:[-*•◦▪▫▸→]|–|—|\(cid:\d+\))$"
)


def is_bullet_line(line: str) -> bool:
    s = line.strip()
    return (
        bool(re.match(r"^[-*]\s+", s))
        or (len(s) > 1 and s[0] in _BULLET_CHARS)
        or s.startswith("(cid:127)")
        or s.startswith("(cid:149)")
    )


def normalise_bullet_line(line: str, cfg: Config) -> str:
    text = line.strip()
    if text.startswith("(cid:127)") or text.startswith("(cid:149)"):
        text = text[len("(cid:127)"):].lstrip() if text.startswith("(cid:127)") else text[len("(cid:149)"):].lstrip()
    elif text and text[0] in _BULLET_CHARS:
        text = text[1:].lstrip()
    elif re.match(r"^[-*]\s+", text):
        text = re.sub(r"^[-*]\s+", "", text)
    return cfg.bullet_prefix + text.strip()


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------

@dataclass
class Requirement:
    section: str
    section_index: int
    req_number: str
    text: str
    from_table: bool = False


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def is_noise(line: str, cfg: Config) -> bool:
    s = line.strip()
    if not s:
        return True
    for pattern in cfg.noise_patterns:
        if pattern.search(s):
            return True
    return False


def req_depth(req_number: str) -> int:
    return req_number.count(".") + 1


def sort_key(req: Requirement) -> tuple:
    def _part(s):
        try:
            return (0, int(s), "")
        except ValueError:
            return (1, 0, s)
    return (req.section_index,) + tuple(_part(x) for x in req.req_number.split("."))


def derive_parent(req_number: str) -> str:
    parts = req_number.split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else ""


def make_name(text: str) -> str:
    return text.split("\n")[0].strip()


def make_section_prefix(section: str, cfg: Config) -> str:
    """
    Derive a short stable prefix from a section heading for scoping Identifiers.
    "Schedule 4.1 – Annex A"  →  "4.1.AA"
    "Annex B"                 →  "B"
    ""                        →  ""
    """
    if not section:
        return ""
    num_match = re.search(r"\b(\d[\d.]*)", section)
    num = num_match.group(1).rstrip(".") if num_match else ""
    sep_match = re.search(r"[–—\-]\s*(.+)$|\(([^)]+)\)", section)
    if sep_match:
        suffix_text = (sep_match.group(1) or sep_match.group(2) or "").strip()
        words = re.findall(r"[A-Za-z0-9]+", suffix_text)
        if words:
            abbr = "".join(w[0].upper() for w in words[:5])
            return f"{num}.{abbr}" if num else abbr
    return num


# ---------------------------------------------------------------------------
# Table extraction helpers
# ---------------------------------------------------------------------------

def _norm_cell(cell) -> str:
    if cell is None:
        return ""
    return re.sub(r"\s+", " ", str(cell).replace("\n", " ")).strip()


def _detect_table_columns(header_row: list, cfg: Config) -> "dict | None":
    """
    Match header cells to roles using cfg.table_column_map.
    Returns {col_index: role} if an 'identifier' column is found, else None.
    """
    result: dict = {}
    for i, cell in enumerate(header_row):
        norm = _norm_cell(cell).lower()
        if not norm:
            continue
        for pattern, role in cfg.table_column_map:
            if pattern.search(norm):
                result[i] = role
                break
    return result if "identifier" in result.values() else None


def _extract_table_requirements(
    table_rows: list,
    current_section: str,
    current_section_index: int,
    cfg: Config,
    debug: bool = False,
    obfuscate: bool = False,
) -> list:
    if not table_rows or len(table_rows) < 2:
        return []

    col_roles = _detect_table_columns(table_rows[0], cfg)
    if col_roles is None:
        if debug:
            headers = [_norm_cell(c) for c in table_rows[0]]
            print(f"  [TABLE]   skip — no identifier column in {headers}")
        return []

    def _d(t: str) -> str:
        return _obfuscate_text(t) if obfuscate else t

    if debug:
        print(f"  [TABLE]   columns: { {i: r for i, r in col_roles.items()} }")

    label_map = {
        "source": "Source",
        "rationale": "Rationale",
        "acceptance_criterion": "Acceptance Criterion",
    }

    requirements = []
    for row_i, row in enumerate(table_rows[1:], start=1):
        identifier = ""
        primary_text = ""
        extras: dict = {}

        for col_i, role in col_roles.items():
            cell = _norm_cell(row[col_i] if col_i < len(row) else None)
            if not cell:
                continue
            if role == "identifier":
                identifier = cell
            elif role == "primary_text":
                primary_text = cell
            else:
                extras[role] = cell

        if not identifier or not primary_text:
            if debug:
                print(f"  [TABLE]   row {row_i} skip — id={_d(identifier)!r} text={_d(primary_text)[:30]!r}")
            continue

        if cfg.require_modal_verb and not _MODAL_VERB_RE.search(primary_text):
            if debug:
                print(f"  [TABLE]   row {row_i} skip — no modal verb: {_d(primary_text)[:50]}")
            continue

        for role in ("source", "rationale", "acceptance_criterion"):
            if role in extras:
                primary_text += f"\n{label_map[role]}: {extras[role]}"

        requirements.append(Requirement(
            section=current_section,
            section_index=current_section_index,
            req_number=identifier,
            text=primary_text,
            from_table=True,
        ))
        if debug:
            print(f"  [TBLREQ]  {_d(identifier)} — {_d(primary_text)[:50]}")

    return requirements


# ---------------------------------------------------------------------------
# Page extraction
# ---------------------------------------------------------------------------

def extract_lines_from_page(
    page,
    cfg: Config,
    debug: bool = False,
    obfuscate: bool = False,
    table_bboxes: "list | None" = None,
) -> list:
    page_height = page.height

    if cfg.max_font_size is not None:
        page = page.filter(lambda obj: (
            obj.get("object_type") != "char"
            or obj.get("size", 0) <= cfg.max_font_size
        ))

    words = page.extract_words(
        x_tolerance=3, y_tolerance=3,
        keep_blank_chars=False, use_text_flow=True,
    )
    if not words:
        return []

    _TOL = 3

    def in_content_zone(w):
        if w["top"] < cfg.header_margin_top:
            return False
        if w["bottom"] > page_height - cfg.footer_margin_bottom:
            return False
        if table_bboxes:
            for x0, top, x1, bottom in table_bboxes:
                if (w["x0"] >= x0 - _TOL and w["x1"] <= x1 + _TOL
                        and w["top"] >= top - _TOL and w["bottom"] <= bottom + _TOL):
                    return False
        return True

    content_words = [w for w in words if in_content_zone(w)]
    if not content_words:
        return []

    lines_by_y: dict = {}
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


def rejoin_split_section_numbers(lines: list) -> list:
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


def merge_orphaned_bullets(lines: list, cfg: Config) -> list:
    result = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if _BARE_BULLET_RE.match(stripped) and i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            if (not cfg.section_header_pattern.match(next_stripped) and
                    not _SECTION_NUMBER_RE.match(next_stripped)):
                result.append(stripped + " " + next_stripped)
                i += 2
                continue
        result.append(lines[i])
        i += 1
    return result


# ---------------------------------------------------------------------------
# Requirements parser
# ---------------------------------------------------------------------------

def parse_requirements(lines: list, cfg: Config, debug: bool = False, obfuscate: bool = False) -> list:
    """
    Priority per line:
      1. Section header  → update current_section
      2. Noise           → discard
      3. Requirement     → start new Requirement (optionally gated by modal verb)
      4. Bullet          → append to current requirement
      5. Continuation    → append to current requirement
    """
    lines = merge_orphaned_bullets(lines, cfg)

    requirements: list = []
    current: Optional[Requirement] = None
    current_section = ""
    current_section_index = -1
    section_order: dict = {}
    in_annotation = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        def _d(t: str) -> str:
            return _obfuscate_text(t) if obfuscate else t

        if in_annotation:
            if debug:
                print(f"  [ANNOT+]  {_d(stripped)[:70]}")
            if stripped.endswith("]"):
                in_annotation = False
            continue

        # 1. Section header
        if cfg.section_header_pattern.match(stripped):
            if current:
                requirements.append(current)
                current = None
            current_section = re.sub(r"\s*\.{4,}[\s\d]*$", "", stripped).strip()
            if current_section not in section_order:
                current_section_index += 1
                section_order[current_section] = current_section_index
            else:
                current_section_index = section_order[current_section]
            if debug:
                print(f"  [SECTION] {_d(current_section)[:70]}")
            continue

        # 2. Noise
        if is_noise(stripped, cfg):
            if stripped.startswith("[") and not stripped.endswith("]"):
                in_annotation = True
            if debug:
                print(f"  [NOISE]   {_d(stripped)[:70]}")
            continue

        # 3. Requirement number match
        match = _SECTION_NUMBER_RE.match(stripped)
        if match:
            req_num = match.group(1)
            req_text = match.group(2).strip()

            if req_depth(req_num) > cfg.max_depth:
                if debug:
                    print(f"  [DEPTH>]  {_d(stripped)[:70]}")
                if current:
                    current.text += " " + stripped
                continue

            if cfg.require_modal_verb and not _MODAL_VERB_RE.search(req_text):
                if debug:
                    print(f"  [NOVERB]  {_d(stripped)[:70]}")
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

        # 4. Bullet
        if is_bullet_line(stripped):
            if current:
                normalised = normalise_bullet_line(stripped, cfg)
                if normalised[len(cfg.bullet_prefix):].strip():
                    current.text += cfg.bullet_separator + normalised
                    if debug:
                        print(f"  [BULLET]  {_d(normalised)[:60]}")
                elif debug:
                    print(f"  [EMPTY-B] {_d(stripped)[:70]}")
            elif debug:
                print(f"  [SKIP-B]  {_d(stripped)[:70]}")
            continue

        # 5. Continuation
        if current:
            current.text += " " + stripped
            if debug:
                print(f"  [CONT]    {_d(stripped)[:70]}")
        elif debug:
            print(f"  [SKIP]    {_d(stripped)[:70]}")

    if current:
        requirements.append(current)

    return requirements


# ---------------------------------------------------------------------------
# Text cleanup
# ---------------------------------------------------------------------------

def clean_text(text: str, cfg: Config) -> str:
    text = fix_encoding(text)

    _renorm = _BULLET_CHARS - {"–", "—"}
    for ch in _renorm:
        text = re.sub(
            r"(?<=\s)" + re.escape(ch) + r"\s*",
            cfg.bullet_separator + cfg.bullet_prefix,
            text,
        )

    text = re.sub(r"(?<=\w)-[ \t]+(?=[a-z])", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" +$", "", text, flags=re.MULTILINE)
    text = "\n".join(
        ln for ln in text.split("\n")
        if not re.match(r"^[-*•◦▪▫▸→–—]\s*$", ln)
    )
    return text.strip()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

_NUMERIC_ID_RE = re.compile(r"^\d+(\.\d+)*$")


def _page_indices(spec: Optional[str], total: int) -> range:
    """
    Convert a human-readable page range spec to a range of 0-based page indices.

    Spec format (1-indexed, inclusive):
      "65-128"  →  pages 65 to 128
      "65-"     →  page 65 to the last page
      "-128"    →  page 1 to 128
      "65"      →  page 65 only
    """
    if not spec:
        return range(total)
    spec = str(spec).strip()
    if "-" in spec:
        lo, _, hi = spec.partition("-")
        start = int(lo) if lo.strip() else 1
        end   = int(hi) if hi.strip() else total
    else:
        start = end = int(spec)
    start = max(1, start)
    end   = min(total, end)
    if start > end:
        return range(0)
    return range(start - 1, end)   # 0-based


def pdf_to_csv(
    pdf_path: str,
    csv_path: str,
    cfg: Config,
    debug: bool = False,
    obfuscate: bool = False,
) -> int:
    all_lines: list = []
    all_table_reqs: list = []

    # Section context for table extraction (tracked per-page alongside text)
    _sec: dict = {"section": "", "index": -1, "order": {}}

    print(f"Opening: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        indices = _page_indices(cfg.pages, total)
        page_desc = f"pages {indices.start + 1}–{indices.stop}" if cfg.pages else "all pages"
        print(f"  Pages: {total} total, processing {len(indices)} ({page_desc})")
        for page_num_0 in indices:
            page = pdf.pages[page_num_0]
            page_num = page_num_0 + 1
            if debug:
                print(f"\n--- Page {page_num} ---")

            table_bboxes: list = []
            raw_tables: list = []
            if cfg.table_extraction:
                for tbl in page.find_tables():
                    table_bboxes.append(tbl.bbox)
                    raw_tables.append(tbl.extract())

            lines = extract_lines_from_page(
                page, cfg, debug=debug, obfuscate=obfuscate,
                table_bboxes=table_bboxes or None,
            )
            all_lines.extend(lines)

            # Quick section-header scan to set context for table requirements
            for line in lines:
                s = line.strip()
                if cfg.section_header_pattern.match(s):
                    clean = re.sub(r"\s*\.{4,}[\s\d]*$", "", s).strip()
                    if clean not in _sec["order"]:
                        _sec["index"] += 1
                        _sec["order"][clean] = _sec["index"]
                    else:
                        _sec["index"] = _sec["order"][clean]
                    _sec["section"] = clean

            for tbl_rows in raw_tables:
                all_table_reqs.extend(
                    _extract_table_requirements(
                        tbl_rows, _sec["section"], _sec["index"],
                        cfg, debug=debug, obfuscate=obfuscate,
                    )
                )

    print(f"  Lines extracted: {len(all_lines)}")
    all_lines = rejoin_split_section_numbers(all_lines)
    text_reqs = parse_requirements(all_lines, cfg, debug=debug, obfuscate=obfuscate)
    requirements = text_reqs + all_table_reqs
    print(f"  Requirements found: {len(text_reqs)} (text) + {len(all_table_reqs)} (tables)")

    requirements.sort(key=sort_key)

    HEADER = ["section", "Identifier", "Primary Text", "Artifact Type", "Name", "parentBinding"]

    rows = []
    for req in requirements:
        text = clean_text(req.text, cfg)
        section_text = fix_encoding(req.section)

        if req.from_table and not _NUMERIC_ID_RE.match(req.req_number):
            identifier = req.req_number
            parent_binding = ""
        else:
            prefix = make_section_prefix(section_text, cfg)
            parent_num = derive_parent(req.req_number)
            identifier = f"{prefix}{cfg.identifier_sep}{req.req_number}" if prefix else req.req_number
            parent_binding = (
                f"{prefix}{cfg.identifier_sep}{parent_num}"
                if prefix and parent_num else parent_num
            )

        rows.append([
            section_text,
            identifier,
            text,
            cfg.artifact_type,
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
                    identifier,
                    _obfuscate_text(text),
                    art_type,
                    _obfuscate_text(name),
                    parent,
                ])
        print(f"  Obfuscated copy: {obf_path}")

    return len(requirements)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3:
        print("Usage: python pdf_to_csv.py <input.pdf> <output.csv> "
              "[--config FILE] [--pages START-END] [--debug] [--obfuscate]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    csv_path = sys.argv[2]
    debug = "--debug" in sys.argv
    obfuscate = "--obfuscate" in sys.argv

    def _flag_value(flag: str) -> Optional[str]:
        if flag in sys.argv:
            idx = sys.argv.index(flag)
            if idx + 1 >= len(sys.argv):
                print(f"Error: {flag} requires an argument")
                sys.exit(1)
            return sys.argv[idx + 1]
        return None

    config_path = _flag_value("--config")
    if config_path and not os.path.exists(config_path):
        print(f"Error: config file not found: {config_path}")
        sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    cfg = load_config(config_path)
    if config_path:
        print(f"Config: {config_path}")

    # --pages overrides any 'pages' key in the config
    pages_arg = _flag_value("--pages")
    if pages_arg:
        cfg.pages = pages_arg

    count = pdf_to_csv(pdf_path, csv_path, cfg, debug=debug, obfuscate=obfuscate)
    print(f"\nDone. {count} requirements extracted.")

    if count == 0:
        print("\nTIP: Run with --debug to trace line-by-line parsing.")
        if not config_path:
            print("     Try --config with a YAML file tailored to your document.")
        print("     Common causes of zero output:")
        print("       - PDF is scanned (image-only) — needs OCR first")
        print("       - Requirements are not numbered in the expected format (1, 1.1, 1.1.1)")
        print("       - Table columns don't match TABLE_COLUMN_MAP patterns")
        print("       - require_modal_verb: true but text lacks shall/should/must")


if __name__ == "__main__":
    main()
