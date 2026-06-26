# PDF Import — Overview

## The Challenge

Requirements frequently arrive as PDF documents. In regulated industries (defence, aerospace, automotive, medical), customer specifications, standards documents, and interface control documents are often delivered as locked PDFs containing hundreds of numbered requirements paragraphs.

**The problem:** IBM DOORS does not support direct PDF import.

This is a confirmed, permanent limitation. IBM has not released native PDF import functionality for either DOORS Classic or DOORS Next, and there is no indication this will change. (Source: [Jazz Forum: Can DOORS Next Generation import PDF documents?](https://jazz.net/forum/questions/206870/can-doors-next-generation-import-pdf-documents))

## What This Section Covers

| File | Content |
|------|---------|
| [known-issues.md](known-issues.md) | Confirmed issues with PDF import and their IBM sources |
| [workarounds.md](workarounds.md) | Step-by-step workarounds for the most common scenarios |

## The Core Problem with Numbered Paragraphs

Requirements documents often use hierarchical numbering:

```
1.0 System Performance
  1.1 The system shall respond to authentication requests within 2 seconds.
  1.2 The system shall support 500 concurrent sessions.
    1.2.1 Session response shall not degrade below 1.1 thresholds.
2.0 Security
  2.1 The system shall enforce password complexity rules.
```

DOORS needs this information as:
- Individual objects (one per requirement)
- Parent-child relationships (1.2.1 is a child of 1.2 which is a child of 1.0)
- The paragraph number stored as an identifier attribute
- The requirement text as a searchable, attributable record

PDFs encode this as static, visual text. Converting it into a structured DOORS database requires an intermediate step that recognises the numbering pattern and reconstructs the hierarchy.

## Automated Extraction Script

For PDFs containing hierarchically numbered requirements (e.g. `4.1`, `4.1.1`, `4.1.1.1`), an automated Python extraction script is available:

**[pdfplumber-guide-v2.0/](pdfplumber-guide-v2.0/README.md)** *(current)* — config-driven extraction; one YAML file per client document type, no code changes needed per client:

```bash
python pdfplumber-guide-v2.0/scripts/pdf_to_csv.py input.pdf output.csv \
    --config pdfplumber-guide-v2.0/configs/defence_schedule_annex.yaml
```

**[pdfplumber-guide-v1.0/](pdfplumber-guide-v1.0/README.md)** *(reference)* — single-script version with configurable constants; see its README for why v2.0 was introduced.

Both versions extract requirements from a PDF into a six-column CSV ready for DOORS Next import:

```
section       — document section heading (e.g. "Schedule 4.1 – Annex A")
Identifier    — requirement number, scoped to its section (e.g. "4.1.AA::2.1")
Primary Text  — full requirement text, with bullet sub-items preserved
Artifact Type — "Functional Requirement" (configurable)
Name          — first line of the requirement text (artifact short title)
parentBinding — Identifier of the parent requirement; used by DOORS to build hierarchy
```

`Identifier` and `parentBinding` are standard DOORS Next import attributes.  DOORS matches each `parentBinding` value against another row's `Identifier` to create the parent-child requirement tree — this is how DOORS traces requirements without manual linking.  The section prefix in `Identifier` (e.g. `4.1.AA::`) ensures uniqueness when a document restarts numbering in each section or annex.

```bash
pip install pdfplumber
python pdfplumber-guide/scripts/pdf_to_csv.py your_spec.pdf output.csv
```

## Quick Decision Guide

| Situation | Recommended Approach |
|-----------|---------------------|
| Numbered requirements, repeatable | [Automated pdfplumber script](pdfplumber-guide/README.md) |
| Single PDF, one-time import | [PDF → Word → DOORS](workarounds.md#path-1-pdf--word--doors) |
| Large PDFs, many attributes | [PDF → CSV → DOORS](workarounds.md#path-2-pdf--csv--doors) |
| Regulated industry, multi-tool | [PDF → ReqIF → DOORS](workarounds.md#path-3-pdf--reqif--doors) |
| Recurring imports, Classic | [DXL Scripting](workarounds.md#path-4-dxl-scripting-doors-classic) |

For full detail: see [workarounds.md](workarounds.md).
