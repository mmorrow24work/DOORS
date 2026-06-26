# pdfplumber Requirements Extractor — v2.0

Config-driven extraction of numbered and table-based requirements from PDF documents into a six-column CSV ready for IBM DOORS Next import.

## What changed from v1.0

v1.0 had a single script with configurable constants at the top.  Every new client document meant editing Python.  v2.0 separates the extraction engine from the document-specific settings:

```
scripts/pdf_to_csv.py   ← engine (one file, never changes per client)
configs/client_a.yaml   ← settings for client A
configs/client_b.yaml   ← settings for client B
```

A new client is a new YAML file.  Bug fixes and new features in the engine apply to all clients automatically.

## Requirements

```bash
pip install pdfplumber pyyaml
```

## Usage

```bash
# No config — uses built-in defaults (equivalent to default.yaml)
python scripts/pdf_to_csv.py input.pdf output.csv

# With a config file
python scripts/pdf_to_csv.py input.pdf output.csv --config configs/defence_schedule_annex.yaml

# Debug trace + obfuscated output (safe to share)
python scripts/pdf_to_csv.py input.pdf output.csv \
    --config configs/my_client.yaml --debug --obfuscate
```

## Output columns

| Column | DOORS role | Description |
|--------|-----------|-------------|
| `section` | Custom attribute | Section/annex heading that groups this requirement |
| `Identifier` | Standard | Unique requirement ID, section-scoped when numbers restart (e.g. `4.1.AA::2.1`) |
| `Primary Text` | Standard | Full requirement text; bullet sub-items as newline-separated `- item` lines |
| `Artifact Type` | Standard | Configurable; default `"Functional Requirement"` |
| `Name` | Standard | First line of Primary Text (DOORS artifact short name) |
| `parentBinding` | Standard | `Identifier` of parent requirement; DOORS uses this to build the hierarchy |

## Ready-made configs

| Config | Use when |
|--------|----------|
| `configs/default.yaml` | Starting point — all keys documented with defaults |
| `configs/module_requirements_table.yaml` | Requirements are in tables (Module Requirement ID / Acceptance Criterion / Rationale) |
| `configs/defence_schedule_annex.yaml` | Flowing numbered paragraphs, strict "shall" language, Schedules/Annexes |
| `configs/mixed_prose_and_table.yaml` | Document has both numbered paragraphs and requirement tables |

**See [`configs/README.md`](configs/README.md)** for the full key reference and a step-by-step workflow for new client documents.

## How to create a config for a new client

```bash
# 1. Run without config to see what the engine detects
python scripts/pdf_to_csv.py client.pdf test.csv --debug 2>&1 | head -100

# 2. Copy the closest ready-made config
cp configs/mixed_prose_and_table.yaml configs/client_acme.yaml

# 3. Edit configs/client_acme.yaml (adjust table_column_map, section_keywords, etc.)

# 4. Re-run with debug until output looks right
python scripts/pdf_to_csv.py client.pdf test.csv --config configs/client_acme.yaml --debug

# 5. Final run
python scripts/pdf_to_csv.py client.pdf output.csv --config configs/client_acme.yaml
```

## What the engine handles automatically (no config needed)

- **TOC entries** — lines with dotted leaders (`text ........ 42`) are discarded
- **Section-scoped Identifiers** — section prefix prevents clashes when numbering restarts across sections
- **Bullet normalisation** — `•`, `-`, `–`, `▪`, `(cid:N)` etc. all normalised to `- item` format
- **Encoding fixup** — mojibake sequences (`â€"` → `–`) corrected automatically
- **Table cell exclusion** — table text is not double-processed as flowing text
- **Named table IDs** — alphanumeric IDs (`MR-001`) used as-is with no section prefix
- **Obfuscated output** — `--obfuscate` flag writes a second CSV with all text replaced by `x` sequences for safe sharing

## What config controls

- Which heading keywords trigger a section context (`section_keywords`)
- Whether modal verbs are required (`require_modal_verb`)
- How table columns map to DOORS fields (`table_column_map`)
- Header/footer margin sizes (`header_margin_top`, `footer_margin_bottom`)
- Font-size threshold for watermark removal (`max_content_font_size`)
- Artifact type name, identifier separator, extra noise patterns

## Differences from v1.0

| Area | v1.0 | v2.0 |
|------|------|-------|
| Configuration | Edit Python constants | YAML config file per client |
| New client | Edit script | Create new `.yaml` file |
| PyYAML dependency | Not required | Required (`pip install pyyaml`) |
| Table extraction | Yes (hardcoded column map) | Yes (configurable column map) |
| Modal verb filter | No | Yes (`require_modal_verb: true`) |
| All other features | Yes | Yes (same extraction engine) |

For historical context see [`../pdfplumber-guide-v1.0/README.md`](../pdfplumber-guide-v1.0/README.md).
