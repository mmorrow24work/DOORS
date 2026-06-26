# pdfplumber — Guide to Extracting Numbered Requirements to CSV

This guide explains how to use [pdfplumber](https://github.com/jsvine/pdfplumber) to extract requirements from PDF documents with up to 6 levels of hierarchical section numbering into a CSV file ready for import into IBM DOORS.

## What You Get

- **`scripts/pdf_to_csv.py`** — the extraction script
- **`scripts/generate_sample_0N_*.py`** — six generator scripts for sample PDFs
- **`sample-pdfs/`** — the generated PDFs and their extracted CSVs

---

## Prerequisites

```bash
pip install pdfplumber reportlab
```

---

## Quickstart

### Step 1: Generate the sample PDFs

```bash
cd scripts/
python generate_sample_01_clean.py
python generate_sample_02_styled.py
python generate_sample_03_complex.py
python generate_sample_04_toc_annex.py
python generate_sample_05_bullets.py
python generate_sample_06_defence.py
```

### Step 2: Extract requirements to CSV

```bash
python pdf_to_csv.py ../sample-pdfs/sample_01_clean.pdf output_01.csv
python pdf_to_csv.py ../sample-pdfs/sample_04_toc_annex.pdf output_04.csv

# Any document with debug output to trace what is happening
python pdf_to_csv.py your_spec.pdf output.csv --debug
```

### Step 3: Review and import

Open the output CSV. It has six columns ready for DOORS Next import:

| section | Identifier | Primary Text | Artifact Type | Name | parentBinding |
|---------|-----------|-------------|--------------|------|---------------|
| Section 1 — Authentication | 1.A::1 | The system shall provide a web-based... | Functional Requirement | The system shall provide... | |
| Section 1 — Authentication | 1.A::1.1 | The system shall support user authentication... | Functional Requirement | The system shall support... | 1.A::1 |
| Section 2 — Data Requirements | 2.DR::1.1 | The system shall store all personal data... | Functional Requirement | The system shall store... | 2.DR::1 |
| Section 2 — Data Requirements | 2.DR::1.1.1 | The system shall encrypt all stored... | Functional Requirement | The system shall encrypt... | 2.DR::1.1 |

**Column guide:**

| Column | DOORS role | Notes |
|--------|-----------|-------|
| `section` | Custom attribute | Document heading context (e.g. `Schedule 4.1 – Annex A`). DOORS imports it if a matching custom attribute exists in your artifact type; otherwise ignored. |
| `Identifier` | **DOORS standard** | Unique requirement identifier. `parentBinding` is matched against this column by DOORS to build the requirement hierarchy. Prefixed with a section code (e.g. `4.1.AA::`) when the document restarts numbering across sections. |
| `Primary Text` | **DOORS standard** | Full requirement text. Bullet sub-items appear on separate lines with a `- ` prefix. |
| `Artifact Type` | **DOORS standard** | Always `Functional Requirement` — edit to match your DOORS artifact type name. |
| `Name` | **DOORS standard** | First line of the requirement text — used as the artifact's short display title in DOORS. |
| `parentBinding` | **DOORS standard** | Identifier of the parent artifact. DOORS reads this to construct the parent-child tree. Empty for top-level requirements within a section. |

Bullet sub-items are preserved on separate lines with a `- ` prefix:

```
1.1  The system shall support the following authentication methods:
     • Username and password
     • Single sign-on via SAML
```

becomes one `Primary Text` cell:

```
The system shall support the following authentication methods:
- Username and password
- Single sign-on via SAML
```

This CSV is ready for [DOORS Next CSV import](../workarounds.md#path-2-pdf--csv--doors) without post-processing.

---

## How the Script Works

### 1. Text extraction via pdfplumber

pdfplumber extracts text **word by word** with precise bounding box coordinates (`x0`, `top`, `x1`, `bottom`). This is more reliable than `page.extract_text()` for documents with tables, headers, footers, and multi-column layouts.

```python
words = page.extract_words(x_tolerance=3, y_tolerance=3)
```

### 2. Header/footer stripping

Words near the top or bottom of the page are discarded before parsing:

```
Page height (A4 = 842 points)
│
├── [top 60pt] ← HEADER ZONE — discarded
│
├── [content zone] ← requirements parsed here
│
├── [bottom 50pt] ← FOOTER ZONE — discarded
│
```

```python
HEADER_MARGIN_TOP = 60      # points from top of page
FOOTER_MARGIN_BOTTOM = 50   # points from bottom of page
```

### 3. Line reconstruction

Words are grouped into lines using their `top` y-coordinate (bucketed to 2-point precision). Words on the same line are sorted left-to-right and joined with spaces.

### 4. Section number detection

Each reconstructed line is tested against:

```python
SECTION_PATTERN = re.compile(r"^(\d+(?:\.\d+){0,5})\s{1,4}(.+)$")
```

| Input line | Matched section | Matched text |
|-----------|-----------------|-------------|
| `1.1.1 The system shall...` | `1.1.1` | `The system shall...` |
| `2.3.1.1.2.1 Certificates shall...` | `2.3.1.1.2.1` | `Certificates shall...` |
| `PART I — PERFORMANCE` | — | — (no match, treated as noise) |

### 5. Continuation lines

Lines that do not match the section pattern are appended to the previous requirement's text. This handles requirements that wrap across multiple lines in the PDF.

### 6. Noise filtering

Lines matching any noise pattern are silently discarded:

```python
NOISE_PATTERNS = [
    re.compile(r"^\[(?:NOTE|ANNOTATION):"),   # [NOTE: ...] annotations
    re.compile(r"^FOR TEST(?:ING)? ONLY"),    # watermarks
    re.compile(r"^OFFICIAL SENSITIVE$"),      # classification markings
    re.compile(r"^CONFIDENTIAL$"),
    # ... add your own patterns here
]
```

Multi-line annotations (where `[NOTE: ...]` spans more than one extracted line) are handled by an `in_annotation` flag — lines are suppressed until the `]` closer is found.

### 7. Section / annex tracking

When the parser encounters a line matching `SECTION_HEADER_PATTERN` (e.g., `Section 1 — Authentication`, `Annex A`, `Part IV`), it records that header as the current section context. Every subsequent requirement is tagged with that context in the `section` column. This prevents requirement `1.1` of *Annex A* from being conflated with requirement `1.1` of *Annex B*.

### 8. Bullet normalisation

Bullet characters in PDF text are often extracted in garbled forms. The script handles three variants:

| Source | Raw extraction | After fix |
|--------|---------------|-----------|
| UTF-8 bytes decoded as Windows-1252 | `â€¢` | `•` |
| UTF-8 bytes decoded as ISO-8859-1 | `â\x80¢` | `•` |
| Font lacks ToUnicode map (CID ref) | `(cid:127)` | `•` |

After encoding repair, bullet lines (lines starting with `•`, `-`, `–`, `*`, or a CID reference) are appended to the current requirement text on a new line with a `- ` prefix.

### 9. Orphaned bullet marker merge

pdfplumber sometimes extracts a bullet marker (`-`, `•`, etc.) on a slightly different y-coordinate from its text, producing a bare `-` line followed by the text. A preprocessing step detects these orphaned markers and merges them with the following line before parsing:

```
"-"  +  "Defender for Servers"  →  "- Defender for Servers"
```

---

## Tuning the Script for Your Documents

### Bullet items from two lines are merging into one

pdfplumber groups words within `y_tolerance=3` points into the same line. If list items have tight vertical spacing, two bullets may land in the same y-band and merge. Reduce `y_tolerance`:

```python
words = page.extract_words(x_tolerance=3, y_tolerance=1)
```

Use `--debug` to see the y-coordinates and identify which items are merging.

### Section column shows mojibake (â€", â€¢)

The script handles both ISO-8859-1 and Windows-1252 (cp1252) variants of the most common characters. If you see an unrecognised sequence, add it to `_MOJIBAKE_MAP`:

```python
_MOJIBAKE_MAP.insert(0, ("â€X", "—"))   # replace â€X with the actual observed string
```

Use `--debug` and look at the raw section column output to identify the sequence.

### The section pattern doesn't match my numbering

Edit `SECTION_PATTERN`:

```python
# Example: match "REQ-1.1.2 The system shall..."
SECTION_PATTERN = re.compile(r"^REQ-(\d+(?:\.\d+){0,5})\s+(.+)$")
```

### Headers/footers are being included

Increase the margin values:

```python
HEADER_MARGIN_TOP = 80
FOOTER_MARGIN_BOTTOM = 70
```

Use `--debug` to see the y-coordinates of captured lines:
```
  [y=  42.0] SAMPLE REQUIREMENTS SPECIFICATION — DOCUMENT 2  ← this is a header
```

### Table of Contents entries are appearing as requirements

TOC entries match `SECTION_PATTERN` (they start with a section number). Filter them by requiring a modal verb in the requirement text:

```python
REQUIREMENT_VERB_PATTERN = re.compile(r"\b(shall|should|will|must|may)\b", re.IGNORECASE)

# In parse_requirements(), after matching SECTION_PATTERN:
if not REQUIREMENT_VERB_PATTERN.search(req_text):
    continue   # skip TOC entries — they don't contain requirement verbs
```

Sample 04 (`sample_04_toc_annex.pdf`) demonstrates this problem — the TOC entries appear in the CSV with an empty `section` column (before the first section header is encountered). Add the filter above to clean them up.

### Annotations are being included as requirements

Add a pattern to `NOISE_PATTERNS`:

```python
NOISE_PATTERNS.append(re.compile(r"^Note:", re.IGNORECASE))
NOISE_PATTERNS.append(re.compile(r"^\*\*"))   # lines starting with **
```

### Scanned PDF — no text extracted

pdfplumber cannot extract text from image-based (scanned) PDFs. Pre-process with OCRmyPDF:

```bash
pip install ocrmypdf
ocrmypdf input_scanned.pdf input_with_text_layer.pdf
python pdf_to_csv.py input_with_text_layer.pdf output.csv
```

---

## Understanding the Six Sample Documents

### Sample 1 — Clean (`sample_01_clean.pdf`)

**Format:** Times-Roman, bold section numbers at levels 1–2, no page decorations.  
**Extraction result:** 99/100  
**Challenge level:** Minimal — baseline test.

### Sample 2 — Styled (`sample_02_styled.pdf`)

**Format:** Title page, page headers/footers, colour-banded rows, section numbers in a separate table column.  
**Extraction result:** 97/100  
**Challenges:** Header/footer stripping, two-column table layout, title page noise.

### Sample 3 — Complex (`sample_03_complex.pdf`)

**Format:** Diagonal watermark, page headers/footers, section divider banners (`PART I` … `PART VII`), inline `[NOTE: ...]` / `[ANNOTATION: ...]` blocks, mixed Helvetica/Courier fonts.  
**Extraction result:** 100/100  
**Challenges:** Watermark filtering (`MAX_CONTENT_FONT_SIZE`), multi-line annotation suppression, font-size-based noise removal.

### Sample 4 — TOC + Multi-Annex (`sample_04_toc_annex.pdf`)

**Format:** Table of Contents (2 pages), 3 main sections + 2 annexes. Requirement numbers restart at `1.x` in each section and annex. Page headers.  
**Extraction result:** 68 requirements + 11 TOC contamination entries (in empty section)  
**Challenges:**
- **TOC contamination** — TOC entries match `SECTION_PATTERN`. They appear in the CSV with an empty `section` column. Add the modal verb filter (see Tuning section) to eliminate them.
- **Section/annex tracking** — requirement `1.1` appears in Section 1, Section 2, Section 3, Annex A, and Annex B. The `section` column keeps them distinct.
- **Bullet sub-items** — mix of `•` and `-` styles across sections.

### Sample 5 — Bullet-Heavy (`sample_05_bullets.pdf`)

**Format:** Security controls specification, ~30 requirements each with 2–5 bullet sub-items. Three bullet styles: `•` (CID), `-`, `–`. Bullet markers rendered in a narrow table column separate from the text.  
**Extraction result:** 30/30  
**Challenges:**
- **CID glyph reference** — reportlab embeds `•` in Helvetica without a ToUnicode map, so pdfplumber extracts it as `(cid:127)`. The script converts `(cid:127)` → `•` then to `\n- `.
- **Table-column bullet separation** — bullet marker in column 0 and text in column 1 may land on different y-bands, producing orphaned markers. The merge step corrects this.
- **Double-marker case** (`- – Defender for Endpoint`) — when a table column has a `-` marker AND the text item starts with `–`, the result is `- –` prefix. This reflects a real-world scenario; use `--debug` to identify and adjust.

### Sample 6 — Defence Spec (`sample_06_defence.pdf`)

**Format:** `OFFICIAL SENSITIVE` classification in header AND footer on every page. Three annexes (A, B, C), each restarting at `1.x`. Deep nesting up to 6 levels. Government typography.  
**Extraction result:** 59/59  
**Challenges:**
- **Classification noise** — `OFFICIAL SENSITIVE` is stripped by `HEADER_MARGIN_TOP` / `FOOTER_MARGIN_BOTTOM` margins. If your document has a larger header, increase `HEADER_MARGIN_TOP`.
- **Annex tracking** — Annex A, B, and C each have requirement `1.1`. The `section` column correctly distinguishes them.
- **Deep nesting** — requirements up to `1.4.3.1.1.1` (6 levels) are extracted correctly.

---

## Importing into DOORS Next

The CSV is ready to import directly — no post-processing needed.  All six columns map to DOORS Next standard attributes.

### What DOORS receives from each column

| Column | What DOORS does with it |
|--------|------------------------|
| `Identifier` | Stores it on each artifact as its unique reference number. The section prefix (e.g. `4.1.AA::`) makes it unique across the whole file even when the source document restarts numbering in each section. |
| `parentBinding` | Reads the value, finds the row whose `Identifier` matches, and creates a parent-child link between the two artifacts. This is how DOORS builds the traceability tree — **no manual linking needed**. |
| `Primary Text` | Stores the full requirement text as the artifact's main rich-text content, including bullet sub-items on separate lines. |
| `Artifact Type` | Determines which DOORS artifact template to use (e.g. `Functional Requirement`). Must match a type that exists in your DOORS module. |
| `Name` | Stores the first line of the requirement text as the artifact's short display title — this is what you see in the DOORS outline view. |
| `section` | Stores the document heading (e.g. `Schedule 4.1 – Annex A`) as a custom attribute **if** that attribute has been defined in your artifact type. If not, DOORS silently ignores the column — the hierarchy built by `Identifier`/`parentBinding` is unaffected. The column is still useful as human context when reviewing the CSV before import. |

### How DOORS builds the hierarchy

DOORS Next reads `parentBinding` and looks up the matching `Identifier` in the same import file.  This creates the parent-child relationship between requirements.

```
Identifier: 4.1.AA::2       parentBinding: (empty)       ← top-level in this section
Identifier: 4.1.AA::2.1     parentBinding: 4.1.AA::2     ← child of 2
Identifier: 4.1.AA::2.1.1   parentBinding: 4.1.AA::2.1   ← grandchild of 2
```

The `4.1.AA::` prefix ensures uniqueness when the source document restarts numbering in each section or annex.  If your document uses globally unique numbering throughout, the prefix is omitted and `Identifier` is just the plain requirement number.

### Custom `section` attribute

The `section` column holds the document heading context (e.g. `Schedule 4.1 – Annex A`).  DOORS does not have a built-in `section` attribute, so you have two options:

1. **Create a custom attribute** called `section` in your DOORS artifact type — DOORS will populate it during import.
2. **Ignore the column** — DOORS silently skips columns it does not recognise.  The `Identifier` / `parentBinding` hierarchy is unaffected.

### Changing `Artifact Type`

The script writes `Functional Requirement` for every row.  If your DOORS module uses a different type name, edit the constant at the top of `pdf_to_csv.py`:

```python
# pdf_to_csv.py — edit to match your DOORS artifact type name
ARTIFACT_TYPE = "Functional Requirement"
```

Or, for a mix of types, post-process the CSV in Python:

```python
import csv, re

with open("output.csv", encoding="utf-8-sig") as fin, \
     open("doors_import.csv", "w", newline="", encoding="utf-8-sig") as fout:
    reader = csv.DictReader(fin)
    writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
    writer.writeheader()
    for row in reader:
        # Top-level rows (no :: separator in Identifier) become Headings
        row["Artifact Type"] = (
            "Heading" if "::" not in row["Identifier"] and "." not in row["Identifier"]
            else "Functional Requirement"
        )
        writer.writerow(row)
```

---

## Limitations

| Limitation | Workaround |
|-----------|-----------|
| Scanned / image PDFs have no extractable text | Pre-process with OCRmyPDF |
| Table of Contents entries appear as requirements | Add modal verb filter (see Tuning) |
| Tight bullet spacing merges items into one line | Reduce `y_tolerance` from 3 to 1 |
| Font lacks ToUnicode map — bullets appear as `(cid:N)` | `(cid:127)` and `(cid:149)` are already handled; add others to `_MOJIBAKE_MAP` |
| Extended Unicode bullets (`▪`, `◦`) in standard fonts | These may render as wrong glyphs; use `-` or `–` bullets in source docs |
| Multi-column layouts may merge columns | Use `extract_words()` and filter by `x0` position |
| Password-protected PDFs | Unlock with `pikepdf` before processing |
| Right-to-left languages | pdfplumber has limited RTL support |
| Schedule/section container headings not in CSV | Add them manually as `Artifact Type = Heading` rows above the first requirement in each section, or create them in DOORS before import |
| `section` prefix collisions (two sections with the same number and same initial letters) | Override `make_section_prefix()` to return a fully spelled-out prefix, or set `IDENTIFIER_SEP` to a different separator |
| Client data — can't share debug output | Run with `--obfuscate` to create a `<output>-OBF.csv` with all text replaced by `x` sequences; share that file for diagnostics |

---

## Why This Became v1.0 — and What Comes Next

This script (`pdf_to_csv.py`) was built for a single type of requirements document: numbered paragraphs in flowing prose.  As real client documents arrived, two practical limits appeared:

1. **Different table layouts.** Several client documents store requirements in tables rather than paragraphs, and the column names differ between clients — "Module Requirement ID", "Req #", "ID", "Requirement Reference", etc.  Adding each new layout meant editing Python constants at the top of the script.

2. **One size doesn't fit all.** Some clients use modal verbs ("shall", "should") reliably; others mix requirements with definitions, rationale, and commentary in the same numbered list.  Section-header keyword lists differ.  Margin sizes differ.  Every difference required a code change.

**The config-file approach** separates the extraction engine (which barely changes) from the document-specific settings (which change for every client).  Instead of editing Python, you write a small YAML file that describes your document:

```yaml
# configs/client_a.yaml
table_column_map:
  - {pattern: "requirement id", role: identifier}
  - {pattern: "shall statement",  role: primary_text}
  - {pattern: "rationale",        role: rationale}
require_modal_verb: true
artifact_type: "Functional Requirement"
```

Then run:
```bash
python pdf_to_csv.py --config configs/client_a.yaml input.pdf output.csv
```

A new client is a new YAML file, not a code change.  Bug fixes and new features in the engine apply to all clients automatically.

**See [`../pdfplumber-guide-v2.0/`](../pdfplumber-guide-v2.0/README.md)** for the config-driven version, including ready-made configs for common document types and a customisation guide.
