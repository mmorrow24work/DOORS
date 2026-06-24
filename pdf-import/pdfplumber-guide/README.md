# pdfplumber — Guide to Extracting Numbered Requirements to CSV

This guide explains how to use [pdfplumber](https://github.com/jsvine/pdfplumber) to extract requirements from PDF documents with up to 6 levels of hierarchical section numbering into a CSV file ready for import into IBM DOORS.

## What You Get

- **`scripts/pdf_to_csv.py`** — the extraction script
- **`scripts/generate_sample_01_clean.py`** — generates a clean, simple 100-requirement PDF
- **`scripts/generate_sample_02_styled.py`** — generates a styled, medium-complexity PDF
- **`scripts/generate_sample_03_complex.py`** — generates a high-noise PDF with watermarks, annotations, mixed fonts
- **`sample-pdfs/`** — the generated PDFs (created by running the generator scripts)

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
```

This creates:
```
sample-pdfs/
├── sample_01_clean.pdf      # Simple: uniform text, no noise
├── sample_02_styled.pdf     # Medium: headers/footers, coloured rows, title page
└── sample_03_complex.pdf    # Hard: watermark, annotations, mixed fonts, dividers
```

### Step 2: Extract requirements to CSV

```bash
# Simple document
python pdf_to_csv.py ../sample-pdfs/sample_01_clean.pdf output_01.csv

# Styled document
python pdf_to_csv.py ../sample-pdfs/sample_02_styled.pdf output_02.csv

# Complex document
python pdf_to_csv.py ../sample-pdfs/sample_03_complex.pdf output_03.csv

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

The `section` column ensures that requirement `1.1` of *Section 1* and requirement `1.1` of *Section 2* are kept distinct — they are placed in the correct section context, not conflated.

This CSV is compatible with the [DOORS Next CSV import format](../workarounds.md#path-2-pdf--csv--doors) — add `Artifact Type`, `Name`, and `parentBinding` columns to complete the import template.

---

## How the Script Works

### 1. Text extraction via pdfplumber

pdfplumber extracts text **word by word** with precise bounding box coordinates (`x0`, `top`, `x1`, `bottom`). This is more reliable than `page.extract_text()` for documents with:
- Tables (text extracted in reading order, not column order)
- Headers and footers (can be filtered by y-coordinate)
- Multi-column layouts

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

The margin values are configurable in `pdf_to_csv.py`:
```python
HEADER_MARGIN_TOP = 60      # points from top of page
FOOTER_MARGIN_BOTTOM = 50   # points from bottom of page
```

### 3. Line reconstruction

Words are grouped into lines using their `top` y-coordinate (bucketed to 2-point precision). Words on the same line are sorted left-to-right by `x0` and joined with spaces.

### 4. Section number detection

Each reconstructed line is tested against:

```python
SECTION_PATTERN = re.compile(r"^(\d+(?:\.\d+){0,5})\s{1,4}(.+)$")
```

This matches lines that start with a valid section number (1 to 6 components) followed by 1–4 spaces and requirement text.

| Input line | Matched section | Matched text |
|-----------|-----------------|-------------|
| `1.1.1 The system shall...` | `1.1.1` | `The system shall...` |
| `2.3.1.1.2.1 Certificates shall...` | `2.3.1.1.2.1` | `Certificates shall...` |
| `PART I — PERFORMANCE` | — | — (no match, treated as noise) |

### 5. Continuation lines

Lines that do **not** match the section pattern are appended to the previous requirement's text. This handles requirements that wrap across multiple lines in the PDF:

```
1.1.1  The system shall validate that the password contains a minimum
       of 12 characters including at least one uppercase letter.
```
→ becomes one requirement: `"The system shall validate that the password contains a minimum of 12 characters including at least one uppercase letter."`

### 6. Noise filtering

Lines matching any noise pattern are silently discarded:

```python
NOISE_PATTERNS = [
    re.compile(r"^\[(?:NOTE|ANNOTATION):"),   # [NOTE: ...] annotations
    re.compile(r"^FOR TEST(?:ING)? ONLY"),    # watermarks
    re.compile(r"^CONFIDENTIAL$"),
    # ... add your own patterns here
]
```

Multi-line annotations (where the `[NOTE: ...]` block spans more than one extracted line) are handled by an `in_annotation` flag. Once a noise line opening with `[` and not closing with `]` is detected, all subsequent lines are suppressed until the block closes.

### 7. Section / annex tracking

When the parser encounters a line matching `SECTION_HEADER_PATTERN` (e.g., `Section 1 — Authentication`, `Annex A`, `Part IV`), it records that header as the current section context. Every subsequent requirement is tagged with that context in the `section` column of the output CSV. This prevents requirement `1.1` of *Section A* from appearing adjacent to requirement `1.1` of *Section B* without distinction.

### 8. Bullet normalisation

Bullet characters in PDF text are often extracted as mojibake (e.g., `â€¢` for the UTF-8 bullet `•`). The script:
1. Repairs common mojibake sequences via a lookup table before any other processing.
2. Detects bullet lines (lines starting with `•`, `-`, `*`, or `–`) and appends them to the current requirement text using `" | "` as a separator, producing a readable inline list rather than losing the structure.

---

## Tuning the Script for Your Documents

### The section pattern doesn't match my numbering

If your document uses a different format (e.g., `REQ-1.1`, `A.1.2`, `3.a.ii`), edit `SECTION_PATTERN`:

```python
# Example: match "REQ-1.1.2 The system shall..."
SECTION_PATTERN = re.compile(r"^REQ-(\d+(?:\.\d+){0,5})\s+(.+)$")
```

### Headers/footers are being included

Increase the margin values:

```python
HEADER_MARGIN_TOP = 80      # was 60 — strip more from top
FOOTER_MARGIN_BOTTOM = 70   # was 50 — strip more from bottom
```

Use `--debug` to see the y-coordinates of the lines being captured:
```
  [y=  42.0] SAMPLE REQUIREMENTS SPECIFICATION — DOCUMENT 2  ← this is a header
  [y= 102.3] 1.1  The system shall support user authentication...
```
If the header is at y=42, set `HEADER_MARGIN_TOP = 50` to catch it.

### Annotations are being included as requirements

Add a pattern to `NOISE_PATTERNS`:

```python
NOISE_PATTERNS.append(re.compile(r"^\[ANNOTATION:", re.IGNORECASE))
```

Or if your annotations follow a different pattern:
```python
NOISE_PATTERNS.append(re.compile(r"^Note:", re.IGNORECASE))
NOISE_PATTERNS.append(re.compile(r"^\*\*"))   # lines starting with **
```

### The same section number appears twice (table of contents duplicate)

Table of contents entries often repeat section numbers before the actual requirements. Filter by checking that the text following the section number looks like a requirement (contains "shall", "should", "will", etc.):

```python
# Optional: only accept lines containing a modal verb
REQUIREMENT_VERB_PATTERN = re.compile(r"\b(shall|should|will|must|may)\b", re.IGNORECASE)

# In parse_requirements(), after matching SECTION_PATTERN:
if not REQUIREMENT_VERB_PATTERN.search(req_text):
    continue   # skip table-of-contents entries and headings
```

### Scanned PDF — no text extracted

pdfplumber cannot extract text from image-based (scanned) PDFs. Pre-process with OCRmyPDF:

```bash
pip install ocrmypdf
ocrmypdf input_scanned.pdf input_with_text_layer.pdf
python pdf_to_csv.py input_with_text_layer.pdf output.csv
```

---

## Understanding the Three Sample Documents

### Sample 1 — Clean (`sample_01_clean.pdf`)

**Format:** Times-Roman font, bold section numbers at levels 1–2, no page decorations.
**Extraction result:** 99/100 (99%) — one requirement missed due to a title-page paragraph matching the section pattern.
**Parser challenge:** Minimal. This is the baseline.

### Sample 2 — Styled (`sample_02_styled.pdf`)

**Format:** Title page, page headers and footers, colour-banded rows, section numbers in a separate table column from requirement text.
**Extraction result:** 97/100 (97%) — title page table and a two-column layout variation account for the 3 missed.
**Parser challenges:**
- Title page content (document number table) must not be captured as requirements
- Page headers/footers repeat on every page — stripped by y-coordinate margins
- Two-column table layout — pdfplumber's word-level extraction handles this well

### Sample 3 — Complex (`sample_03_complex.pdf`)

**Format:** Diagonal watermark, page headers/footers, section divider banners, inline `[NOTE: ...]` annotations, mixed Helvetica/Courier fonts across 7 parts.
**Extraction result:** 100/100 (100%) — all noise filtered correctly.
**Parser challenges (and how they are handled):**
- Watermark text ("FOR TESTING ONLY" at 52pt) — filtered by `MAX_CONTENT_FONT_SIZE = 20`
- `[NOTE: ...]` and `[ANNOTATION: ...]` — filtered by `NOISE_PATTERNS`
- Section divider banners (PART I through PART VII) — filtered by `DIVIDER_PATTERN`
- Courier body text at levels 3 and 5 — transparent to the section-number regex
- Page headers/footers — stripped by y-coordinate margins

---

## Adding to DOORS Import Template

The script outputs a 3-column CSV (`section`, `req_number`, `requirement`). To use it with the DOORS Next CSV import (see [workarounds.md](../workarounds.md#path-2-pdf--csv--doors)), add three more columns:

| section | req_number | requirement | Artifact Type | Name | parentBinding |
|---------|-----------|-------------|--------------|------|---------------|
| Section 1 | 1 | The system shall... | Heading | System Overview | |
| Section 1 | 1.1 | The system shall support... | Functional Requirement | Authentication | 1 |
| Section 1 | 1.1.1 | The system shall validate... | Functional Requirement | Password Complexity | 1.1 |

You can automate `parentBinding` derivation: for `req_number` `1.1.1`, the parent is `1.1` (remove the last `.N` component).

A helper snippet:

```python
import csv

def derive_parent(section_number: str) -> str:
    parts = section_number.split(".")
    if len(parts) <= 1:
        return ""   # top-level, no parent
    return ".".join(parts[:-1])

with open("output.csv") as fin, open("doors_import.csv", "w", newline="") as fout:
    reader = csv.DictReader(fin)
    writer = csv.writer(fout)
    writer.writerow(["Identifier", "Artifact Type", "Name", "Primary Text", "parentBinding"])
    for row in reader:
        sec = row["section_number"]
        text = row["requirement"]
        name = text[:60] + ("..." if len(text) > 60 else "")
        writer.writerow([sec, "Functional Requirement", name, text, derive_parent(sec)])
```

---

## Limitations

| Limitation | Workaround |
|-----------|-----------|
| Scanned / image PDFs have no extractable text | Pre-process with OCRmyPDF |
| Multi-column layouts may merge columns | Use `extract_words()` and check `x0` positions |
| Very complex tables lose structure | Extract tables separately with `page.extract_tables()` |
| Section numbers in a separate PDF column from text | Adjust `SECTION_PATTERN` or pre-process with Word conversion |
| Right-to-left languages | pdfplumber has limited RTL support; consider alternative extraction |
| Password-protected PDFs | Unlock with `pikepdf` before processing |
