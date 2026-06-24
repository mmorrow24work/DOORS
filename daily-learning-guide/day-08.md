# Day 8 — DXL Scripting for Automation

**Bloom's Level:** Analyse → Evaluate
**Estimated Time:** 90 minutes

---

## Learning Objectives

By the end of today you will be able to:
- [ ] Describe the DXL data model (modules, objects, attributes, links)
- [ ] Read a DXL script and explain what it does
- [ ] Identify use cases where DXL scripting provides the most automation value
- [ ] Explain when DXL is the right tool vs the DOORS Next REST API

---

## Core Concept (15 min)

### What Is DXL?

**DXL (DOORS eXtension Language)** is a proprietary scripting language built into DOORS Classic. It is syntactically similar to C and provides full programmatic access to the DOORS data model.

DXL runs inside the DOORS Classic client and can:
- Read and write requirement attributes
- Create and delete objects and modules
- Create and navigate traceability links
- Generate custom reports
- Automate the import of text files and structured documents
- Run as triggered scripts (on module open, on save, on attribute change)

**Important:** DXL is only available in DOORS Classic (v9.x). DOORS Next uses REST APIs instead.

### The DXL Data Model

| Concept | DXL Name | Description |
|---------|----------|-------------|
| Module | `Module` | A collection of requirements (like a file) |
| Requirement | `Object` | A single requirement record within a module |
| Attribute | Accessed via `obj."Attribute Name"` | A field on an object |
| Link | `Link`, `LinkRef` | A typed connection between two objects |
| Folder | `Folder` | A container for modules in the project tree |

### DXL Example 1 — Read All Requirements in a Module

```dxl
// Open a module and print all requirement IDs and text
Module m = read("/My Project/System Requirements")
Object o
for o in m do {
    string reqID = o."Identifier"
    string reqText = o."Object Text"
    print reqID "\t" reqText "\n"
}
```

### DXL Example 2 — Update Attribute Based on Condition

```dxl
// Mark all requirements with no linked test as "Unverified"
Module m = current
Object o
for o in m do {
    if (o."Verification Status" == "") {
        o."Verification Status" = "Not Verified"
    }
}
save m
```

### DXL Example 3 — Import Numbered Text File

```dxl
// Read a plain text file with numbered paragraphs and create objects
string filename = "C:\\requirements\\spec.txt"
Stream s = openFileRead(filename)
string line
while (!eof s) {
    getLine(s, line)
    if (matches("^[0-9]+\\.[0-9]+ .*", line)) {
        // Create a new object for each numbered paragraph
        Object newObj = create(current)
        newObj."Object Text" = line
    }
}
close s
```

### When to Use DXL

DXL is the right tool when:
- You are working with **DOORS Classic** (not DOORS Next)
- You need to **bulk-import** requirements from text or structured files
- You need to **generate custom reports** that the built-in reporting cannot handle
- You need to **automate repetitive tasks** run by DOORS users (menu scripts)
- You need to **parse PDFs converted to text** and create DOORS objects from numbered paragraphs

### DXL vs DOORS Next REST API

| Scenario | Use DXL | Use REST API |
|----------|---------|-------------|
| DOORS Classic bulk operations | Yes | No (not applicable) |
| DOORS Next CI/CD integration | No | Yes |
| Cross-tool OSLC queries | No | Yes |
| Custom DOORS Classic reports | Yes | No |
| Automated import from text/CSV | Yes (Classic) | REST POST (Next) |

---

## Key Definitions

| Term | Definition |
|------|-----------|
| **DXL** | DOORS eXtension Language — the scripting language in DOORS Classic |
| **Module** | A collection of objects (requirements) in DOORS Classic |
| **Object** | A single requirement record in DOORS Classic |
| **Formal module** | A DOORS Classic module with mandatory heading structure and numbering |
| **Informal module** | A DOORS Classic module without enforced structure |
| **Trigger** | A DXL script that runs automatically on a DOORS event (save, open, attribute change) |
| **Stream** | A DXL `Stream` is a file I/O object (different from DOORS Next stream concept) |

---

## Practical Exercise (30 min)

**Goal:** Read a DXL script and trace its logic.

Read the following DXL script carefully and answer the questions below:

```dxl
Module m = read("/System Requirements/Functional Requirements")
Object o
int verified = 0
int total = 0

for o in m do {
    if (isDeleted o) continue
    total++
    if (o."Verification Status" == "Verified") {
        verified++
    }
}

real coverage = (real verified / real total) * 100
print "Total requirements: " total "\n"
print "Verified: " verified "\n"
print "Coverage: " coverage "%\n"
```

**Questions:**
1. What module does this script read?
2. What does `isDeleted o` check, and why is the `continue` statement needed?
3. What does the script calculate and print?
4. What attribute must exist on each object for this script to work?
5. How would you modify this script to count only *Critical* requirements?

**Extension (if you have DOORS Classic access):**
- Copy this script into a new DXL file
- Run it against a real module
- Modify it to report coverage broken down by Priority attribute

---

## Connection to Automated Testing

DXL's most valuable application for automated testing is **custom import scripts** for complex document formats — especially PDFs converted to text. See [Day 10](day-10.md) and [pdf-import/workarounds.md](../pdf-import/workarounds.md) for the PDF-specific workflow.

Beyond import, DXL enables:
- **Pre-commit validation scripts**: block a module save if requirements don't meet quality criteria
- **Batch verification updates**: update Verification Status for all requirements after a test run
- **Coverage reporting**: generate coverage reports on demand or on schedule

---

## Reflection Prompts

1. What is the most time-consuming manual task in your DOORS workflow that DXL could automate?
2. Do you have DXL scripts already in use in your organisation? If so, are they maintained and documented?
3. Is DXL expertise available in your team, or would this require upskilling or external help?

---

## Further Reading

- [IBM Rational DOORS DXL Reference Manual (9.7.0) — PDF](https://www.ibm.com/docs/en/SSYQBZ_9.6.1/com.ibm.doors.requirements.doc/topics/dxl_reference_manual.pdf)
- [DOORS DXL Unsolved Mysteries — Solved! (Advanced DXL Techniques)](https://www.galactic-solutions.com/downloads/DOORS_DXL_Unsolved_Mysteries_-_Solved!_(paper).PDF)
- [OpenReqEU DOORS Integration Scripts (GitHub)](https://github.com/OpenReqEU/doors-integration-scripts)

---

## Tomorrow's Preview

**Day 9** connects DOORS to your CI/CD pipeline — this is where requirements changes automatically trigger test runs and test results flow back into DOORS. Before tomorrow, consider: *what CI/CD tool does your team use (Jenkins, GitHub Actions, Azure DevOps)? And does it have access to the network where your ELM server runs?*
