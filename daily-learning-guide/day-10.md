# Day 10 — PDF Import Workflows

**Bloom's Level:** Evaluate → Create
**Estimated Time:** 90 minutes

---

## Learning Objectives

By the end of today you will be able to:
- [ ] Explain why DOORS has no native PDF import and why this is unlikely to change
- [ ] Select the correct import path for your specific PDF document characteristics
- [ ] Execute the PDF → Word → DOORS workflow for a numbered requirements document
- [ ] Design a repeatable, automated PDF import process for multiple PDFs

---

## Core Concept (15 min)

### The Fundamental Problem

IBM DOORS does not support direct PDF import — in either Classic or DOORS Next. This is a confirmed, permanent limitation (verified via IBM Jazz community forums, no recorded feature request accepted).

PDFs are presentation-format documents: they encode visual layout, not structured data. DOORS needs structured data: individual objects with attributes, numbering, and hierarchy. The conversion from PDF's visual model to DOORS' data model requires an intermediate step.

The good news: there are four reliable paths, and one of them will fit your situation.

### Why Numbered Paragraphs Are the Key Challenge

Numbered paragraphs (1.0, 1.1, 1.1.1, 2.0, etc.) encode requirement hierarchy. In DOORS, this hierarchy must be represented as parent-child relationships between objects. The import process must:

1. Recognise the numbering pattern
2. Extract the number as an identifier
3. Calculate the parent-child relationship from the number structure
4. Create DOORS objects at the correct hierarchy level

No PDF reader does this automatically. It must happen during conversion.

### The Four Import Paths

#### Path 1: PDF → Word → DOORS (Recommended for Most Cases)

**Best for:** Single PDFs, moderate size, visual fidelity matters

```
Step 1: Convert PDF → .docx
  Tools: Adobe Acrobat Pro, Microsoft Word (built-in), Smallpdf, Nitro PDF

Step 2: Prepare the Word document
  - Remove: headers, footers, cover pages, change logs, revision tables
  - Apply Heading styles: Heading 1 = top level, Heading 2 = sub-level, etc.
  - Ensure numbered paragraphs start with their number: "1.1 The system shall..."
  - Separate requirement blocks with blank lines (each blank-separated block → one DOORS object)

Step 3: Import into DOORS Next
  DNG: File → Import → Select Word Document (.docx)
  DNG automatically:
  - Maps Heading 1/2/3 to hierarchy levels
  - Creates objects for each text block
  - Captures heading numbers in the artifact identifier

Step 4: Post-import cleanup
  - Review each top-level artifact
  - Add Priority, Verification Method, Verification Status attributes
  - Create links to existing requirements if this is a derived specification
```

**Known issue:** DOORS does not preserve numbered lists as numbered — they are imported as bullets. Store the paragraph number in the artifact identifier or a custom attribute.

#### Path 2: PDF → CSV → DOORS (Best for Structured Data)

**Best for:** Large PDFs, many custom attributes, maximum control

```
Step 1: Extract PDF text to spreadsheet
  - Manual copy, or use Docparser / Adobe Acrobat export

Step 2: Structure the spreadsheet:
  Identifier | Artifact Type    | Name              | Primary Text         | parentBinding | Priority
  1.0        | Heading          | System Overview   |                      |               |
  1.1        | Functional Req   | Login Performance | The system shall...  | 1.0           | Critical
  1.1.1      | Derived Req      | Response Time     | Under normal load... | 1.1           | Critical

  Key: parentBinding = the Identifier of the parent requirement

Step 3: Export as CSV (UTF-8 encoded)

Step 4: Import into DOORS Next
  DNG: File → Import → CSV / Spreadsheet
  DNG creates hierarchy from parentBinding column automatically
```

**Advantage:** Complete control over every field. Custom attributes can be set during import.

#### Path 3: PDF → ReqIF → DOORS (Standards-Based)

**Best for:** Regulated industries, multi-tool environments, long-term document management

```
Step 1: Convert PDF → Word (as in Path 1)

Step 2: Import Word into intermediate tool (ReqView, Cameo, etc.)

Step 3: Export as ReqIF (.reqif or .reqifz)
  ReqIF is an OMG standard XML format for requirements exchange

Step 4: Import ReqIF into DOORS Next
  DNG: File → Import → ReqIF Package
  DNG creates artifacts preserving all ReqIF attributes and links
```

**Tools:** ReqView (lightweight, low cost), Cameo Requirements Modeler, Windchill RV&S

#### Path 4: DXL Scripting for DOORS Classic (Automated, Repeatable)

**Best for:** Recurring imports, many similarly-structured PDFs, DOORS Classic environment

```
Step 1: Extract PDF → plain text (.txt) using Adobe Acrobat or similar

Step 2: Write a DXL script that:
  - Opens the .txt file as a DXL Stream
  - Reads line by line
  - Uses regex to detect numbered paragraphs: matches("^[0-9]+(\\.[0-9]+)* ", line)
  - Calculates hierarchy level from the number depth (1.1.1 = level 3)
  - Creates DOORS objects at the correct level
  - Sets Identifier attribute to the paragraph number
  - Sets Object Text to the requirement body

Step 3: Run DXL script for each PDF (batch process)
```

See `pdf-import/workarounds.md` for detailed DXL script skeleton.

---

## Decision Guide: Which Path to Choose?

| Your Situation | Recommended Path |
|---------------|-----------------|
| One-off import, single PDF | Path 1 (Word) |
| Many PDFs, recurring process | Path 4 (DXL) — if Classic; Path 2 (CSV) — if Next |
| Need custom attributes set during import | Path 2 (CSV) |
| Regulated industry, need standards compliance | Path 3 (ReqIF) |
| DOORS Classic environment | Path 1 or 4 |
| DOORS Next environment | Path 1, 2, or 3 |

---

## Key Definitions

| Term | Definition |
|------|-----------|
| **parentBinding** | CSV column in DOORS Next import that establishes parent-child hierarchy |
| **ReqIF** | Requirements Interchange Format — OMG standard XML for requirements exchange |
| **Heading style** | Word document formatting used by DOORS to determine hierarchy level on import |
| **Numbered paragraph** | A requirement identified by a hierarchical number (e.g., 1.1.2) |
| **DXL Stream** | A file I/O object in DXL used to read text files line by line |

---

## Practical Exercise (30 min)

**Goal:** Execute a PDF → Word → DOORS import workflow.

**If you have a sample PDF with numbered requirements:**

1. Convert the PDF to Word using your available tool (Adobe, Word built-in, Smallpdf)
2. Open the Word document and check: are the numbered paragraphs in Heading style?
3. If not: apply Heading 1 to top-level numbers, Heading 2 to sub-levels
4. Remove all front matter (cover page, table of contents, revision history)
5. Ensure each requirement paragraph is separated by a blank line
6. Import into DOORS Next using File → Import → Word Document
7. Review the resulting module: are all requirements at the correct hierarchy level?
8. Identify any conversion issues and note how you would fix them

**If you do not have a PDF:**

1. Create a sample requirements document with this structure:

   ```
   1.0 System Performance Requirements

   1.1 The system shall respond to user authentication requests within 2 seconds under normal operating load (≤ 100 concurrent users).

   1.2 The system shall support a minimum of 500 concurrent sessions without degradation of response time below the thresholds in 1.1.

   2.0 Security Requirements

   2.1 The system shall enforce password complexity: minimum 12 characters, at least one uppercase, one digit, one special character.
   ```

2. Save as Word (.docx) with the above structure using Heading 1 for "1.0" and "2.0", Heading 2 for "1.1", "1.2", "2.1"
3. Attempt import into DOORS Next (or trace through what the result would look like)

---

## Connection to Automated Testing

The PDF import workflow is the **entry point** for the entire automated testing pipeline. Requirements that exist only in PDFs cannot be traced to test cases, cannot be reported on for coverage, and cannot participate in the digital thread.

Every requirement imported from a PDF should immediately receive:
- **Verification Method** attribute (Test/Analysis/Inspection)
- **Verification Status** = "Not Verified"
- **Priority** attribute

These attributes enable Day 9's CI/CD pipeline to immediately discover and schedule test cases for the newly imported requirements.

---

## Reflection Prompts

1. How many PDFs in your current project contain requirements that are not yet in DOORS? What is the total page count?
2. Which of the four import paths best fits your environment? What is the primary obstacle to using it?
3. After completing this 10-day programme: what is the single most valuable action you could take this week to advance automated testing in your organisation?

---

## Further Reading

- [PDF Import Issues & Workarounds (this repo)](../pdf-import/workarounds.md)
- [IBM Best Practice: Importing Customer Specs to DOORS NG (Jazz Forum)](https://jazz.net/forum/questions/271875/best-practice-importing-customer-specs-to-doors-ng)
- [DOORS DXL Reference Manual — for Path 4 scripting](https://www.ibm.com/docs/en/SSYQBZ_9.6.1/com.ibm.doors.requirements.doc/topics/dxl_reference_manual.pdf)

---

## Programme Complete

You have completed the 10-day IBM DOORS ELM learning programme.

**What you have covered:**

| Day | Lesson | Skill Gained |
|-----|--------|-------------|
| 1 | DOORS Architecture | Digital thread mental model |
| 2 | Testable Requirements | Requirements quality auditing |
| 3 | ELM Architecture | Tool landscape understanding |
| 4 | Attributes & Types | Data model design |
| 5 | Traceability Links | RTM creation and interpretation |
| 6 | ETM Integration | OSLC integration configuration |
| 7 | Baselines | Configuration management strategy |
| 8 | DXL Scripting | Automation scripting capability |
| 9 | CI/CD Integration | Digital thread implementation design |
| 10 | PDF Import | Practical data ingestion |

**Recommended next steps:**
1. Apply the attribute schema design (Day 4) to your actual DOORS project
2. Configure or request the OSLC Friend relationship between DNG and ETM (Day 6)
3. Run the PDF import workflow for your most critical specification document (Day 10)
4. Design the CI/CD integration architecture (Day 9) and present it for stakeholder approval

See [automated-testing/research-priorities.md](../automated-testing/research-priorities.md) for a structured roadmap of what to tackle next.
