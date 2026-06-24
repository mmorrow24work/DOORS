# Day 1 — What Is DOORS and Why Does It Matter?

**Bloom's Level:** Remember
**Estimated Time:** 90 minutes

---

## Learning Objectives

By the end of today you will be able to:
- [ ] Define IBM DOORS and its role in the engineering lifecycle
- [ ] Explain the difference between DOORS Classic and DOORS Next
- [ ] Describe the concept of a "digital thread" in plain language
- [ ] State why requirements traceability is the foundation of automated testing

---

## Core Concept (15 min)

### What Is IBM DOORS?

**DOORS** stands for *Database for Object-Oriented Requirements Specification*. It is IBM's requirements management tool — a structured database for capturing, organising, and tracing engineering requirements across a system's lifecycle.

DOORS is not a document editor. It is a **requirements database** that:
- Stores requirements as individual *objects* (records), not as pages of text
- Links each requirement to design artefacts, test cases, and test results
- Tracks changes, ownership, and approval status
- Provides reporting on requirement coverage and traceability

### The Problem DOORS Solves

Without a requirements management tool, engineers work with PDFs, Word documents, and spreadsheets. Requirements drift. Tests are written against old versions. Coverage gaps appear. Auditors cannot prove that every stakeholder need has been tested.

DOORS solves this by giving every requirement a **unique identity** that persists through the entire product lifecycle.

### The Digital Thread

The *digital thread* is the unbroken chain of traceability from:

```
Stakeholder Need
    → System Requirement (DOORS)
        → Design Artefact (EWM / Model)
            → Test Case (ETM)
                → Test Execution Result
                    → Deployment Evidence
```

For automated testing, this chain means: when a test passes, DOORS can automatically mark the linked requirement as *verified*. When a requirement changes, suspect links flag the tests that need to be re-run.

### DOORS Classic vs DOORS Next

| | DOORS Classic (v9.x) | DOORS Next (DNG, v7.x) |
|---|---|---|
| Interface | Desktop client | Web browser |
| Scripting | DXL (built-in) | OSLC APIs |
| Integration | File-based + DXL | OSLC + REST |
| Deployment | On-premise | On-premise / Cloud |
| Status | Maintenance mode | Active development |

Many organisations run both. Classic holds legacy requirements; Next handles new projects.

---

## Key Definitions

| Term | Definition |
|------|-----------|
| **Requirement** | A statement of what a system must do or be |
| **Artefact** | An individual item in DOORS (equivalent to a requirement record) |
| **Traceability** | A link between artefacts that shows dependency or relationship |
| **Digital thread** | The unbroken chain from stakeholder need to test evidence |
| **DOORS Classic** | Desktop-based DOORS v9.x — client/server architecture |
| **DOORS Next (DNG)** | Web-based DOORS v7.x — part of the ELM suite |
| **ELM** | Engineering Lifecycle Management — IBM's integrated tool suite |

---

## Practical Exercise (30 min)

**Goal:** Build your personal context map for DOORS in your organisation.

1. Draw a simple diagram showing: *stakeholder → requirement → design → test → evidence*
2. For each node, write down what tool or document currently holds that information in your organisation
3. Identify the gaps: where does the chain break? Where is there no traceability?
4. Mark the gap you most want DOORS to close

*This exercise has no right answer. It is about understanding your starting point.*

---

## Connection to Automated Testing

The power of DOORS for automated testing is **requirement-driven test execution**. Instead of running a test suite and then manually mapping results to requirements, automated testing systems can:
- Query DOORS for all requirements with status *Not Verified*
- Execute only the test cases linked to those requirements
- Write results directly back to DOORS, updating traceability status

This only works if requirements are in DOORS, properly structured, and linked to test cases. Today's lesson establishes why that foundation matters.

---

## Reflection Prompts

Take 5 minutes to write answers to these questions (pen and paper or notes app):

1. What is the biggest risk in your project today from not having requirements traceability?
2. If automated testing could mark requirements as "verified" in real time, what would change in your review process?
3. What would you need to do first to implement the digital thread in your current environment?

---

## Further Reading

- [IBM ELM Overview — Official Documentation](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.1?topic=overview-elm)
- [IBM DOORS Wikipedia — Historical Context](https://en.wikipedia.org/wiki/DOORS)
- [What Is IBM DOORS Software? — Independent Analysis (Jama)](https://www.jamasoftware.com/blog/ibm-doors-software/)

---

## Tomorrow's Preview

**Day 2** covers the most important skill in requirements management: writing requirements that can actually be tested. You will learn INCOSE's 42 quality rules and identify the 8 that matter most for automated testing. Before tomorrow, try this: pick one requirement from your current project and ask — *"Can a machine verify this requirement is satisfied?"*
