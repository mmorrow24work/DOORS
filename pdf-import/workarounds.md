# PDF Import — Step-by-Step Workarounds

## Overview

IBM DOORS has no native PDF import. This document provides four proven paths for converting PDF documents with numbered requirements paragraphs into DOORS modules.

---

## Path 1: PDF → Word → DOORS

**Best for:** Single PDFs, one-time import, visual fidelity matters, DOORS Next or Classic
**Difficulty:** Low
**Tools needed:** Adobe Acrobat / Smallpdf / Nitro PDF (for conversion); DOORS Next or Classic

### Step 1: Convert PDF to Word

Use one of these tools:
- **Adobe Acrobat Pro:** File → Export To → Microsoft Word → Word Document
- **Microsoft Word:** Open Word → File → Open → select PDF file (Word has built-in PDF conversion)
- **Smallpdf:** https://smallpdf.com/pdf-to-word (online, free tier available)
- **Nitro PDF:** File → Convert → To Word

**Check after conversion:**
- [ ] All numbered paragraphs are present
- [ ] Paragraph numbers are visible as text (not just auto-numbering)
- [ ] Scanned PDFs: was OCR applied? Check that text is selectable, not an image

### Step 2: Prepare the Word Document

This is the most important step. A poorly prepared Word document produces a messy DOORS module.

**Remove the following:**
- [ ] Cover page and title page
- [ ] Table of contents
- [ ] Revision history table
- [ ] Headers and footers (page numbers, document title)
- [ ] Blank pages
- [ ] Appendices that are not requirements (unless intentional)

**Apply Heading styles:**

DOORS uses Word Heading styles to determine hierarchy level:

| Word Style | DOORS Hierarchy Level | Example |
|------------|----------------------|---------|
| Heading 1 | Level 1 | `1.0 System Performance Requirements` |
| Heading 2 | Level 2 | `1.1 Response Time Requirements` |
| Heading 3 | Level 3 | `1.1.1 Authentication Response` |
| Normal/Body | Requirement text | `The system shall respond within 2 seconds.` |

**Rules for numbering:**
- Type the paragraph number directly in the text: `"1.1 The system shall..."` — **not** using Word auto-numbering
- Word auto-numbering is stripped on import; only explicitly typed numbers are preserved
- Each number that DOORS should recognise as a heading must be in a Heading style

**Separate requirement blocks:**
- Each text block separated by a blank line becomes a separate DOORS object
- If two requirements are in the same paragraph with no blank line, they will be imported as one object
- Add blank lines between requirements to ensure each becomes its own artifact

### Step 3: Import into DOORS Next

1. In DOORS Next, open the target module or create a new one
2. Go to **File → Import → Word Document (.docx)**
3. Select your prepared Word file
4. Review the import preview:
   - Check hierarchy levels are correct
   - Verify requirement text is split correctly
5. Click Import

**DOORS Classic:**
1. Open or create the target module
2. Go to **File → Import → Word Document**
3. Select the file and configure heading mapping
4. Click OK

### Step 4: Post-Import Cleanup

After import:
- Review artifacts at each hierarchy level
- Add `Verification Method`, `Verification Status`, `Priority` attributes to each requirement artifact
- Set `Verification Status = "Not Verified"` for all imported requirements
- Link to parent requirements in other modules if this is a derived specification
- Run a coverage report to identify any missed requirements

---

## Path 2: PDF → CSV → DOORS

**Best for:** Large PDFs, multiple custom attributes, maximum control over structure
**Difficulty:** Medium
**Tools needed:** Spreadsheet application; PDF extractor or manual copy

### Step 1: Extract PDF Content to Spreadsheet

**Option A: Manual extraction (small documents)**
- Open PDF in Adobe Acrobat or browser
- Copy numbered paragraphs to a spreadsheet, one requirement per row

**Option B: Automated extraction (large documents)**
- Use Docparser (https://docparser.com) to extract structured data from PDFs
- Use Adobe Acrobat's "Export to Spreadsheet" feature

### Step 2: Structure the Spreadsheet

Create these columns (exact names must match your DOORS Next import template):

| Column | Required | Description |
|--------|----------|-------------|
| `Identifier` | Yes | The paragraph number from the PDF: `1.0`, `1.1`, `1.1.2` |
| `Artifact Type` | Yes | `Functional Requirement`, `Heading`, `Design Constraint`, etc. |
| `Name` | Yes | Short title for the requirement (first 8 words of text) |
| `Primary Text` | Yes | Full requirement text |
| `parentBinding` | Yes for hierarchy | The `Identifier` of the parent requirement |
| `Priority` | Optional | `Critical`, `High`, `Medium`, `Low` |
| `Verification Method` | Optional | `Test`, `Analysis`, `Inspection`, `Demonstration` |
| `Verification Status` | Optional | Default: `Not Verified` |

**Example CSV structure:**

```csv
Identifier,Artifact Type,Name,Primary Text,parentBinding,Priority
1.0,Heading,System Performance Requirements,,, 
1.1,Functional Requirement,Authentication Response,"The system shall respond to authentication requests within 2 seconds under normal load.",1.0,Critical
1.1.1,Functional Requirement,Load Definition,"Normal load is defined as ≤100 concurrent authenticated users.",1.1,High
1.2,Functional Requirement,Concurrent Sessions,"The system shall support a minimum of 500 concurrent sessions.",1.0,Critical
2.0,Heading,Security Requirements,,,
2.1,Functional Requirement,Password Complexity,"The system shall enforce password complexity: minimum 12 characters including one uppercase letter and one special character.",2.0,Critical
```

**Key rules:**
- `parentBinding` must reference an `Identifier` that exists earlier in the CSV
- Use consistent `Artifact Type` values — must match your DOORS Next type system
- `Identifier` values must be unique within the import file
- Export as CSV with **UTF-8 encoding** (not ASCII — UTF-8 handles special characters)

### Step 3: Import into DOORS Next

1. In DOORS Next, create a new empty module
2. Go to **File → Import → CSV / Spreadsheet**
3. Select your CSV file
4. Map CSV columns to DOORS attributes in the mapping dialog
5. Verify the hierarchy preview — parent-child relationships should be correct
6. Click Import

**Source:** [CSV file format and examples — IBM Jazz Documentation](https://jazz.net/help-dev/clm/topic/com.ibm.rational.rrm.help.doc/topics/r_csv_format.html)

---

## Path 3: PDF → ReqIF → DOORS

**Best for:** Regulated industries (DO-178C, ISO 26262, IEC 62443), multi-tool environments, long-term document interchange
**Difficulty:** Medium
**Tools needed:** ReqView or Cameo Requirements Modeler; DOORS Next

### Step 1: Convert PDF → Word

Follow Path 1, Steps 1–2.

### Step 2: Import Word into ReqView

[ReqView](https://www.reqview.com) is a lightweight requirements tool with PDF and Word import and ReqIF export:

1. Open ReqView
2. Create a new project
3. Import the Word document: **File → Import → Microsoft Word**
4. Review the imported requirements structure

### Step 3: Export as ReqIF

1. In ReqView: **File → Export → ReqIF**
2. Select format: `.reqifz` (compressed) or `.reqif` (uncompressed)
3. Save the file

**Important:** Before exporting, remove all hyperlinks from the document. ReqIF import in DOORS Next fails if the file contains invalid hyperlinks (see [known-issues.md — Issue 3](known-issues.md#issue-3-reqif-import-fails-with-invalid-hyperlinks)).

### Step 4: Import ReqIF into DOORS Next

1. In DOORS Next: **File → Import → ReqIF Package**
2. Select the `.reqifz` or `.reqif` file
3. Map ReqIF data types to DOORS Next artifact types
4. Review the import preview
5. Click Import

**Source:** [Importing and exporting ReqIF files — IBM Documentation](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors-next/7.2.0?topic=files-importing-exporting-reqif)

---

## Path 4: DXL Scripting (DOORS Classic)

**Best for:** Recurring imports, multiple similarly-structured PDFs, DOORS Classic environment, full automation
**Difficulty:** High (requires DXL knowledge)
**Tools needed:** DOORS Classic; text editor; PDF-to-text converter

### Step 1: Extract PDF to Plain Text

Use Adobe Acrobat or a command-line tool to export the PDF as plain text (`.txt`).

The text file should preserve the numbered paragraph structure:
```
1.0 System Performance Requirements

1.1 The system shall respond to authentication requests within 2 seconds under normal load.

1.1.1 Normal load is defined as 100 or fewer concurrent authenticated users.

2.0 Security Requirements

2.1 The system shall enforce password complexity rules as specified in section 3.4.
```

### Step 2: DXL Script Skeleton

```dxl
/*
 * PDF Text File Import Script
 * Reads a numbered-paragraph text file and creates DOORS objects
 * Usage: run from DOORS Classic with the target module open
 */

// Configuration — edit these paths
string INPUT_FILE = "C:\\requirements\\spec_numbered.txt"
string MODULE_PATH = "/System Requirements/Functional Requirements"

// Regex patterns for numbered headings
// Matches: "1.0", "1.1", "1.1.1", "2.0" etc at start of line
bool isHeading(string line) {
    return matches("^[0-9]+(\\.[0-9]+)* +[A-Z].*", line)
}

// Calculate hierarchy depth from number (e.g., "1.1.1" = depth 3)
int getDepth(string number) {
    int depth = 1
    int i
    for i = 0; i < length(number); i++ {
        if (number[i] == '.') depth++
    }
    return depth
}

// Extract just the number from a heading line
string extractNumber(string line) {
    int spacePos = 0
    int i
    for i = 0; i < length(line); i++ {
        if (line[i] == ' ') {
            spacePos = i
            break
        }
    }
    return line[0:spacePos]
}

// Main import logic
Module m = read(MODULE_PATH)
if (null m) {
    ack "ERROR: Cannot open module: " MODULE_PATH
    halt
}

Stream s = openFileRead(INPUT_FILE)
if (null s) {
    ack "ERROR: Cannot open file: " INPUT_FILE
    halt
}

string line
Object lastObj = null
string currentNumber = ""

while (!eof s) {
    getLine(s, line)
    
    // Skip empty lines
    if (null line || line == "") continue
    
    if (isHeading(line)) {
        currentNumber = extractNumber(line)
        int depth = getDepth(currentNumber)
        
        // Create heading object
        Object newObj
        if (null lastObj || depth == 1) {
            newObj = create(m)  // Top level
        } else {
            newObj = createObject(lastObj)  // Child of last object
        }
        
        // Set attributes
        newObj."Object Heading" = line
        newObj."Section Number" = currentNumber
        
        lastObj = newObj
    } else {
        // Body text — add as a new object under current heading
        if (!null lastObj) {
            Object bodyObj = createObject(lastObj)
            bodyObj."Object Text" = line
            bodyObj."Verification Status" = "Not Verified"
            bodyObj."Section Number" = currentNumber
        }
    }
}

close s
save m

print "Import complete. Module saved: " MODULE_PATH "\n"
```

**Note:** This is a skeleton. Adapt the attribute names to match your DOORS module's actual attribute schema. Test on a copy of your module before running on production data.

### Step 3: Run the Script

1. Open DOORS Classic
2. Open the target module
3. Go to **Tools → Edit DXL** (or Tools → Run DXL File)
4. Paste or load the script
5. Click Run
6. Review the imported objects

---

## Comparison Table

| Approach | Difficulty | Structure Preservation | Speed | Scalability | Custom Attributes | Cost |
|----------|-----------|----------------------|-------|------------|------------------|------|
| PDF → Word → DOORS | Low | Medium | Medium | Low | Post-import only | Free (if you have Adobe) |
| PDF → CSV → DOORS | Medium | High | Medium | High | Yes, during import | Free |
| PDF → ReqIF → DOORS | Medium | High | Medium | High | Yes | Free–£ (ReqView licence) |
| DXL Scripting | High | High | Fast (once automated) | Very High | Yes | Free (dev time) |
| Manual entry | Very High | Full | Slow | None | Yes | Expensive (time) |

---

## Pre-Import Checklist

Before any import, verify:

- [ ] The PDF contains selectable text (not a scanned image)
- [ ] Numbered paragraphs follow a consistent pattern (1.0, 1.1, 1.1.1 — not mixed formats)
- [ ] The target DOORS module exists and has the correct attribute schema
- [ ] You have a backup of the module before import
- [ ] You know the mapping between PDF section types and DOORS artifact types
- [ ] Custom attributes are defined in the DOORS type system before import
- [ ] The import will be reviewed by the requirements owner after completion

---

## After Import: Mandatory Steps

Regardless of which path you used:

1. **Set `Verification Status = "Not Verified"`** on all imported requirement artifacts
2. **Set `Verification Method`** (Test/Analysis/Inspection) on each requirement
3. **Set `Priority`** based on requirement criticality
4. **Review hierarchy**: confirm parent-child relationships are correct
5. **Verify paragraph numbers**: confirm section numbers are stored in the identifier or a dedicated attribute
6. **Notify test team**: newly imported requirements need test cases written and linked
7. **Create a baseline**: snapshot the module immediately after import as the "initial import" baseline
