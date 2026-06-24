# Day 5 — Requirements Traceability Links & Matrices

**Bloom's Level:** Apply
**Estimated Time:** 90 minutes

---

## Learning Objectives

By the end of today you will be able to:
- [ ] Name the five standard OSLC link types and their direction
- [ ] Create a traceability link between a DOORS Next requirement and an ETM test case
- [ ] Interpret a Requirements Traceability Matrix (RTM) for coverage gaps
- [ ] Explain what a suspect link is and how it protects test integrity

---

## Core Concept (15 min)

### Link Types in DOORS Next

DOORS Next supports typed links — each link has a defined meaning. The most important for automated testing:

| Link Type | Direction | Meaning |
|-----------|-----------|---------|
| **Validates** | Test Case → Requirement | This test case validates this requirement |
| **Satisfies** | Design Artefact → Requirement | This design element satisfies this requirement |
| **Refines** | Child Req → Parent Req | This requirement elaborates a higher-level requirement |
| **Derives** | Child Req → Parent Req | This requirement is derived from a higher-level requirement |
| **Traces** | Any → Any | General traceability (use sparingly — less semantics) |

For automated testing, the critical link type is **Validates**: the link from an ETM test case to a DNG requirement. This is the link that lets DOORS report on test coverage.

### Bidirectional Traceability

Every link is navigable in both directions:
- **Forward traceability**: Start from a requirement → find all test cases that validate it → check execution status
- **Backward traceability**: Start from a test case → find the requirement it validates → check if requirement changed since test was written

Both directions are needed for complete coverage analysis.

### The Requirements Traceability Matrix (RTM)

The RTM is a table that maps requirements to test cases:

```
Requirement ID | Requirement Name        | Test Case(s)  | Status
-----------------------------------------------------------------
REQ-001        | Login response < 2s     | TC-042        | Verified
REQ-002        | Password min 8 chars    | TC-043, TC-044| Verified
REQ-003        | Session timeout 30 min  | (none)        | Not Covered ← gap
REQ-004        | Audit log on login      | TC-045        | Failed
```

DOORS Next can generate this report automatically — but only if every requirement has the correct links established.

### Suspect Links — Protecting Test Integrity

When a requirement is modified after a test case links to it, DOORS marks the link as **suspect**. This is one of DOORS' most powerful safety features for automated testing.

A suspect link means:
- *"This test was written against an older version of the requirement"*
- The test may no longer correctly verify the current requirement
- The test should be reviewed and either updated or confirmed as still valid

In a CI/CD pipeline, suspect links can be surfaced as warnings or build failures.

### Coverage Metrics

From the RTM, DOORS can calculate:
- **Requirement coverage**: % of requirements with at least one test case linked
- **Verified coverage**: % of requirements where linked tests have passed
- **Suspect coverage**: % of requirements where linked tests may be stale
- **Orphan requirements**: requirements with no test case at all
- **Orphan test cases**: test cases with no requirement (untargeted testing)

---

## Key Definitions

| Term | Definition |
|------|-----------|
| **Validates** | Link type from test case to requirement — the core traceability link |
| **Satisfies** | Link type from design element to requirement |
| **Bidirectional traceability** | Ability to navigate from requirement→test AND test→requirement |
| **RTM** | Requirements Traceability Matrix — the coverage reporting table |
| **Suspect link** | A link flagged because a linked artifact was modified after the link was created |
| **Orphan requirement** | A requirement with no linked test case — a coverage gap |
| **Coverage** | The percentage of requirements with verified test cases |

---

## Practical Exercise (30 min)

**Goal:** Build a manual RTM for a small requirement set, then identify gaps.

1. Pick 5–10 requirements from your project (or invent them if needed)
2. Build this table in a spreadsheet:

   ```
   REQ ID | Requirement Summary | Test Case ID | Test Status | Link Type | Suspect?
   ```

3. For each requirement, find and record:
   - Is there a test case for it? If so, what is its ID?
   - Has the requirement changed since the test was written?
   - Is the link type correct (Validates, not just a vague reference)?

4. Calculate: what percentage of requirements have test coverage?
5. Identify your top 3 coverage gaps

*If you have DOORS Next access: replicate this exercise by creating the links directly in the tool. Use the traceability view to verify the links are correct.*

---

## Connection to Automated Testing

The RTM is the **primary input to automated test selection**. When a CI/CD pipeline asks "which tests should I run?", the answer comes from the RTM:

1. Query DOORS: find all requirements where `Verification Status ≠ Verified` OR `Suspect Link = True`
2. From each requirement, retrieve the linked test cases via the `Validates` link
3. Execute those test cases
4. Write results back to DOORS: update `Verification Status` and clear `Suspect` flags where tests pass

This loop — requirements drive tests, test results update requirements — is the digital thread in operation.

---

## Reflection Prompts

1. Do your existing test cases have a documented link to the requirements they verify? If not, what is preventing this?
2. What would a suspect link mean in your team's workflow — would it block a CI build, or just generate a warning?
3. If you generated an RTM today from your existing requirements and test cases, what percentage coverage would you expect?

---

## Further Reading

- [How to Create a Requirements Traceability Matrix in IBM DOORS (Valispace)](https://www.valispace.com/how-to-create-a-requirements-traceability-matrix-in-ibm-doors/)
- [How to Set Up Traceability Links in DOORS Next (SodiusWillert)](https://www.sodiuswillert.com/en/blog/how-to-set-up-create-and-use-traceability-links-in-ibm-doors-next)
- [IBM DOORS / ETM Integration (IBM Docs)](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.2?topic=integrating-doors-engineering-test-management)

---

## Tomorrow's Preview

**Day 6** goes hands-on with the OSLC integration between DOORS Next and IBM Engineering Test Management. Before tomorrow, find out: *does your organisation have ETM deployed alongside DNG? If so, is the OSLC Friend relationship configured between them?* Ask your ELM administrator if unsure.
