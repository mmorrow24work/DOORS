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

Open the output CSV. It has three columns:

| section | req_number | requirement |
|---------|-----------|-------------|
| Section 1 — Authentication | 1 | The system shall provide a web-based user interface... |
| Section 1 — Authentication | 1.1 | The system shall support user authentication using... |
| Section 2 — Data Requirements | 1.1 | The system shall store all personal data in... |
| Section 2 — Data Requirements | 1.1.1 | The system shall encrypt all stored personal data... |

The `section` column ensures that requirement `1.1` of *Section 1* and requirement `1.1` of *Section 2* are kept distinct.

Bullet sub-items are appended to their parent requirement using a newline + `- ` prefix:

```
1.1  The system shall support the following authentication methods:
     • Username and password
     • Single sign-on via SAML
```

becomes one CSV cell:

```
The system shall support the following authentication methods:
- Username and password
- Single sign-on via SAML
```

This CSV is compatible with the [DOORS Next CSV import format](../workarounds.md#path-2-pdf--csv--doors) — add `Artifact Type`, `Name`, and `parentBinding` columns to complete the import template.

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

## Adding to DOORS Import Template

The script outputs a 3-column CSV (`section`, `req_number`, `requirement`). To use it with the DOORS Next CSV import (see [workarounds.md](../workarounds.md#path-2-pdf--csv--doors)), add three more columns:

| section | req_number | requirement | Artifact Type | Name | parentBinding |
|---------|-----------|-------------|--------------|------|---------------|
| Section 1 | 1 | The system shall... | Heading | System Overview | |
| Section 1 | 1.1 | The system shall support... | Functional Requirement | Authentication | 1 |
| Section 1 | 1.1.1 | The system shall validate... | Functional Requirement | Password Complexity | 1.1 |

The `parentBinding` value is the `req_number` with its last component removed (`1.1.1` → `1.1`).

```python
import csv

def derive_parent(req_number: str) -> str:
    parts = req_number.split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else ""

with open("output.csv") as fin, open("doors_import.csv", "w", newline="") as fout:
    reader = csv.DictReader(fin)
    writer = csv.writer(fout)
    writer.writerow(["Identifier", "Artifact Type", "Name", "Primary Text", "parentBinding"])
    for row in reader:
        num = row["req_number"]
        text = row["requirement"]
        name = text[:60] + ("..." if len(text) > 60 else "")
        writer.writerow([num, "Functional Requirement", name, text, derive_parent(num)])
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
