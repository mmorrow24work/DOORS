# Config Files — Customisation Guide

Each config file is a YAML document that tells `pdf_to_csv.py` how to interpret a specific type of PDF.  You create one config per document type (not per document — all documents of the same layout share one config).

## Quick start

```bash
# Use built-in defaults (no config)
python scripts/pdf_to_csv.py input.pdf output.csv

# Use a ready-made config
python scripts/pdf_to_csv.py input.pdf output.csv --config configs/defence_schedule_annex.yaml

# Copy and customise
cp configs/default.yaml configs/my_client.yaml
# edit configs/my_client.yaml
python scripts/pdf_to_csv.py input.pdf output.csv --config configs/my_client.yaml --debug
```

---

## Available configs

| File | Use when |
|------|----------|
| `default.yaml` | Starting point — all keys documented with their default values |
| `module_requirements_table.yaml` | Requirements are in tables (Module Requirement ID / Acceptance Criterion / Rationale columns) |
| `defence_schedule_annex.yaml` | Flowing numbered paragraphs, strict "shall" language, multiple Schedules/Annexes, large header/footer bands |
| `mixed_prose_and_table.yaml` | Document has both numbered prose sections and requirements tables |

---

## Full key reference

### `section_keywords`

**Type:** list of strings  
**Default:** `[Section, Annex, Appendix, Attachment, Exhibit, Schedule, Part, Chapter]`

Lines that start with one of these words followed by an identifier (A, 1, 2.1, I …) become section headers — they set the `section` column for all requirements that follow, but are not themselves captured as requirements.

```yaml
# Add "Clause" and "Module" for IEC-style documents
section_keywords:
  - Section
  - Annex
  - Clause
  - Module
```

**When to change:** Your document uses heading words not in the default list.  Run with `--debug` and look for lines tagged `[SKIP]` that should be section headers.

---

### `max_depth`

**Type:** integer  
**Default:** `6`

The maximum number of dot-separated components in a requirement number (`1.1.1.1.1.1` = depth 6).  Lines numbered deeper than this are treated as continuation text of the current requirement rather than new requirements.

```yaml
max_depth: 4   # ignore 1.1.1.1.1 and deeper
```

---

### `require_modal_verb`

**Type:** boolean  
**Default:** `false`

When `true`, a numbered line is only captured as a requirement if it contains at least one of: **shall, should, must, will, may**.

```yaml
require_modal_verb: true
```

**When to use:** Your document numbers definitions, rationale paragraphs, and commentary alongside requirements using the same scheme, and you want to exclude the non-requirement lines.

**Warning:** If some genuine requirements don't use modal verbs (e.g. "The system logs all events."), they will be silently dropped.  Check with `--debug` and look for `[NOVERB]` lines.

---

### `table_extraction`

**Type:** boolean  
**Default:** `true`

Set to `false` to skip all tables.  Useful when the document has tables that are figures, compliance matrices, or other non-requirement content and no requirement tables.

```yaml
table_extraction: false
```

---

### `table_column_map`

**Type:** list of `{pattern, role}` objects  
**Default:** built-in list covering common requirement ID and text column phrasings

Maps a column header (detected by regex pattern) to a field role.  The pattern is matched case-insensitively against the normalised header text (whitespace collapsed, newlines removed).

**Roles:**

| Role | Effect |
|------|--------|
| `identifier` | → `Identifier` column.  **Required** — tables without this column are skipped. |
| `primary_text` | → `Primary Text` column (main requirement statement) |
| `acceptance_criterion` | Appended to Primary Text as `Acceptance Criterion: …` |
| `source` | Appended to Primary Text as `Source: …` |
| `rationale` | Appended to Primary Text as `Rationale: …` |

**Order matters** — the first matching pattern wins.  Put more specific patterns before generic ones.

```yaml
table_column_map:
  # Specific phrasings first
  - {pattern: "module requirement id",         role: identifier}
  - {pattern: "source of requirement",         role: source}
  - {pattern: "module requirement acceptance criterion", role: primary_text}
  - {pattern: "rationale",                     role: rationale}
  # Generic fallback last
  - {pattern: "requirement",                   role: primary_text}
```

**Debugging a table:** Run with `--debug` and look for `[TABLE]` lines.  A skipped table prints the actual header values; a matched table prints the column-to-role mapping.

```
[TABLE]   skip — no identifier column in ['Requirement Text', 'Priority', 'Comment']
[TABLE]   columns: {0: 'identifier', 2: 'primary_text', 3: 'rationale'}
```

If the table is skipped when it should be matched, add a pattern that matches the actual header text shown in the `skip` line.

---

### `artifact_type`

**Type:** string  
**Default:** `"Functional Requirement"`

Value written into the `Artifact Type` column for every row.  Must exactly match the artifact type name in your DOORS Next module.

```yaml
artifact_type: "System Requirement"
```

---

### `identifier_separator`

**Type:** string  
**Default:** `"::"`

The string placed between the section prefix and the requirement number when building a composite Identifier for documents that restart numbering in each section.

```yaml
# "4.1.AA" + "::" + "2.1"  →  "4.1.AA::2.1"
identifier_separator: "::"

# Alternative: use a dash
identifier_separator: "-"
```

---

### `header_margin_top` / `footer_margin_bottom`

**Type:** float (points, where 1 pt = 1/72 inch)  
**Default:** `60` / `50`

Words that fall above `header_margin_top` or below `page_height - footer_margin_bottom` are discarded as header/footer text.  A4 page height = 841.89 pt.

```yaml
# For documents with large classification banners and footers
header_margin_top: 80
footer_margin_bottom: 70
```

**When to change:** Header/footer text is appearing in your requirements output.  Run with `--debug` and look for `[y=NN]` lines near the top and bottom of each page.

---

### `max_content_font_size`

**Type:** float or `null`  
**Default:** `20`

Characters in a font larger than this size (pt) are filtered out before extraction.  This removes watermarks, large title text, and classification markings rendered in display fonts.

```yaml
max_content_font_size: 16   # stricter — removes larger body text
max_content_font_size: null # disable — keep all font sizes
```

---

### `bullet_separator` / `bullet_prefix`

**Type:** string  
**Default:** `"\n"` / `"- "`

Controls how bullet sub-items are stored in the `Primary Text` cell.

```yaml
bullet_separator: "\n"  # newline between items (default — renders in DOORS multi-line field)
bullet_prefix: "- "     # prefix added to each bullet item
```

---

### `extra_noise_patterns`

**Type:** list of regex strings  
**Default:** `[]`

Additional lines to discard silently.  The built-in set already removes `CONFIDENTIAL`, `Page N`, `Version N.N`, TOC dotted-leader lines, and `[NOTE:` annotations.

```yaml
extra_noise_patterns:
  - "^OFFICIAL$"                    # classification marking
  - "^Table\\s+\\d+"               # table captions ("Table 3 — …")
  - "^Figure\\s+\\d+"              # figure captions
  - "^Issue\\s+\\d+"               # revision markers
  - "^\\d{1,2}/\\d{1,2}/\\d{4}$"  # standalone date lines
```

Patterns are Python regular expressions matched case-insensitively against each line.  Test a pattern in Python:
```python
import re
re.search(r"^Table\s+\d+", "Table 3 — Module Requirements", re.IGNORECASE)
```

---

## Workflow for a new client document

1. **Run without config and with `--debug`:**
   ```bash
   python scripts/pdf_to_csv.py client.pdf test.csv --debug 2>&1 | head -100
   ```

2. **Identify problems:**
   - `[SKIP]` lines that should be requirements → lower `max_depth`, check `require_modal_verb`
   - `[SECTION]` lines that should be requirements (or vice versa) → adjust `section_keywords`
   - `[TABLE] skip` lines → fix `table_column_map` patterns to match the actual headers shown
   - Header/footer text appearing as `[REQ]` or `[CONT]` → increase `header_margin_top` / `footer_margin_bottom`
   - Garbled text from watermarks → lower `max_content_font_size`

3. **Copy the closest ready-made config and edit it:**
   ```bash
   cp configs/mixed_prose_and_table.yaml configs/client_x.yaml
   ```

4. **Run with `--obfuscate` if you need to share debug output:**
   ```bash
   python scripts/pdf_to_csv.py client.pdf test.csv \
       --config configs/client_x.yaml --debug --obfuscate 2>&1 | head -200
   ```
   The `test-OBF.csv` file has all text words replaced by `x` sequences and is safe to share for diagnostics without exposing client content.

5. **Iterate** until the output CSV looks correct, then run the final extraction without `--debug`.
