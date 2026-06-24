# Day 2 — Writing Testable Requirements (INCOSE Quality Rules)

**Bloom's Level:** Remember → Understand
**Estimated Time:** 90 minutes

---

## Learning Objectives

By the end of today you will be able to:
- [ ] State the 8 INCOSE quality criteria most critical for automated testing
- [ ] Identify anti-patterns in requirement text that prevent automated verification
- [ ] Rewrite a poorly worded requirement to make it testable
- [ ] Explain why ambiguous requirements cause test case explosion

---

## Core Concept (15 min)

### Why Requirements Quality Matters for Automation

Automated testing can only verify a requirement if that requirement describes **observable, measurable behaviour**. A requirement like *"The system shall be user-friendly"* cannot be tested by any automated system — or even by a human tester, reliably. A requirement like *"The system shall respond to user login within 2 seconds under normal load (≤ 100 concurrent users)"* can.

INCOSE (International Council on Systems Engineering) defines **42 quality criteria** for individual requirements. For automated testing, eight are critical:

### The 8 Critical INCOSE Rules for Automated Testing

| Rule | Name | What It Means for Automation |
|------|------|------------------------------|
| 1 | **Verifiable** | There must be a test that can pass or fail for this requirement |
| 2 | **Unambiguous** | Only one interpretation is possible; no "approximately", "fast", "user-friendly" |
| 3 | **Singular** | One requirement per statement; compound requirements need two tests but only one ID |
| 4 | **Complete** | Enough detail to write a test case without consulting the author |
| 5 | **Consistent** | No contradiction with other requirements in the same document |
| 6 | **Measurable** | Quantitative criteria — numbers, not adjectives |
| 7 | **Implementation-free** | Describes *what*, not *how*; implementation choices constrain design |
| 8 | **Traceable** | Has a unique identifier that a test case can reference |

### Common Anti-Patterns

These patterns appear constantly in real requirements and all break automated testing:

| Anti-Pattern | Example | Problem |
|-------------|---------|---------|
| Compound requirement | "The system shall log errors and alert the operator" | Two verifiable behaviours; one test cannot cover both cleanly |
| Undefined quantity | "The system shall respond quickly" | How fast? No pass/fail criterion |
| Passive voice ambiguity | "Data shall be stored securely" | By whom? In what way? AES-256? |
| Wishful thinking | "The system should be easy to maintain" | "Should" is not mandatory; what does "easy" mean? |
| Modal confusion | Mix of "shall/should/may" without a defined hierarchy | INCOSE requires "shall" for mandatory, "should" for desired, "may" for optional |
| Undefined acronym | "The system shall comply with ICD v2.1" | Which ICD? Where is it? Is it available to the test system? |

### The SMART Test

Before entering a requirement into DOORS, apply SMART:
- **S**pecific: does it name one specific behaviour?
- **M**easurable: can a test system produce a pass/fail verdict?
- **A**chievable: is it technically feasible within project constraints?
- **R**elevant: does it trace back to a stakeholder need?
- **T**estable: can a concrete test case be written for it right now?

---

## Key Definitions

| Term | Definition |
|------|-----------|
| **Shall** | Mandatory requirement — must be implemented and tested |
| **Should** | Desired but not mandatory; often excluded from test coverage |
| **May** | Optional — not tested unless specifically scoped |
| **Verifiable** | A requirement for which a definitive pass/fail test exists |
| **Singular** | One requirement, one ID, one test responsibility |
| **Compound requirement** | Two or more requirements joined by "and/or" — an anti-pattern |
| **INCOSE 42 Rules** | INCOSE's complete quality criteria set for requirements |

---

## Practical Exercise (30 min)

**Goal:** Audit 5 requirements from your current project using the SMART test and 8 INCOSE criteria.

For each requirement:

1. Write the requirement text as-is
2. Apply each of the 8 criteria — pass / fail / unclear
3. Identify the worst anti-pattern present
4. Rewrite the requirement to fix the most critical defect

**Example:**

*Original:* "The system shall handle errors gracefully and provide feedback to users."

*Audit:* Fails *Singular* (two behaviours), fails *Measurable* ("gracefully" is undefined), fails *Verifiable* (no test criterion)

*Rewritten:*
- REQ-001: "The system shall log all runtime errors to the error log within 500ms of occurrence."
- REQ-002: "The system shall display an error notification to the active user within 2 seconds of detecting a runtime error."

---

## Connection to Automated Testing

Every defect in requirement quality translates directly to one of these problems in automated testing:

- **Ambiguous requirements** → test engineers interpret differently → inconsistent test cases → unreproducible results
- **Compound requirements** → one test must verify two behaviours → when it fails, which behaviour failed?
- **Unmeasurable requirements** → test engineers must invent their own pass/fail criteria → coverage is unmeasurable
- **Requirements without IDs** → automated traceability links cannot be established

Fix the requirements first. Automation built on top of bad requirements generates bad results — fast.

---

## Reflection Prompts

1. Of the 8 criteria, which is most commonly violated in your project's existing requirements?
2. If you had to pick one anti-pattern to address across your entire requirements database, which would have the greatest impact on test automation?
3. Who in your organisation is responsible for requirements quality? Is there a review process?

---

## Further Reading

- [INCOSE 42 Requirements Quality Rules — Simple Guide](https://reqi.io/articles/incose-requirements-quality-42-rule-guide)
- [INCOSE Guide to Writing Requirements (Visure Summary)](https://visuresolutions.com/alm-guide/incose-guide-to-writing-requirements/)
- [INCOSE Requirements Management Pamphlet (PDF — official)](https://www.incose.org/docs/default-source/TWG-Documents/003-requirements-management-and-se-pamphlet.pdf)

---

## Tomorrow's Preview

**Day 3** maps out the IBM DOORS ELM architecture so you know exactly which tool does what. Before tomorrow, ask yourself: *does your organisation use DOORS Classic, DOORS Next, or both?* If you don't know — that's fine; Day 3 will help you find out.
