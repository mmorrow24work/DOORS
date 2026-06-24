# Automated Testing — Research Priorities for Systems Architects

This document maps the research priorities for a systems architect introducing automated testing with IBM DOORS ELM, from highest to lowest urgency.

---

## Priority 1 — Foundations (Do First)

These topics are prerequisites for all automated testing work. Without them, automation will produce unreliable or unmaintainable results.

### 1A: Testable Requirements Audit

**Research question:** What percentage of your existing requirements are actually testable using automated systems?

**Why first:** Automation applied to ambiguous requirements produces false confidence. It can report "100% test coverage" while the actual system behaviour is unverified.

**Actions:**
- Apply INCOSE 8 criteria to a sample of 50 requirements
- Measure: % verifiable, % singular, % measurable
- Document the most common quality failure mode in your project
- Establish a requirements quality gate before any new requirement enters DOORS

**Resources:**
- [INCOSE 42 Rules Guide](https://reqi.io/articles/incose-requirements-quality-42-rule-guide)
- [Day 2 — Writing Testable Requirements](../daily-learning-guide/day-02.md)

---

### 1B: Attribute Schema Design for Automation

**Research question:** Does your current DOORS attribute schema support automated test selection?

**Why first:** The CI/CD pipeline queries DOORS attributes to decide which tests to run. If `Verification Status`, `Priority`, and `Verification Method` attributes don't exist, are inconsistently named, or use free-text instead of enumerations, the pipeline cannot function.

**Actions:**
- Audit current DOORS attributes for automation readiness
- Define or standardise: `Priority`, `Verification Method`, `Verification Status`, `Automation Test ID`
- Ensure all values are controlled enumerations, not free text
- Document the agreed schema in a DOORS type system configuration document

**Resources:**
- [Day 4 — Attributes, Types & Custom Properties](../daily-learning-guide/day-04.md)
- [IBM DOORS Next 101 Community Hub](https://www.ibm.com/community/101/engineering/ibm-engineering-requirements-management-doors-next-101/)

---

### 1C: Requirement Coverage Baseline

**Research question:** What is the current test coverage of your requirements database?

**Why first:** You cannot improve what you cannot measure. Before introducing automation, establish a baseline coverage number so you can demonstrate improvement.

**Actions:**
- Generate a Requirements Traceability Matrix (RTM) from current tools
- Calculate: % requirements with at least one linked test case
- Identify top 10 coverage gaps by priority
- Document the baseline as "Pre-automation coverage: X%"

**Resources:**
- [Day 5 — Requirements Traceability Links & Matrices](../daily-learning-guide/day-05.md)
- [Requirements Traceability Matrix in IBM DOORS (Valispace)](https://www.valispace.com/how-to-create-a-requirements-traceability-matrix-in-ibm-doors/)

---

## Priority 2 — Core Integration

These topics establish the technical backbone of automated testing traceability.

### 2A: OSLC Integration — DNG and ETM

**Research question:** Is the OSLC Friend relationship between DOORS Next and Engineering Test Management configured and working?

**Why second:** Without OSLC integration, test results cannot flow back to requirements. All other automation work is manual.

**Actions:**
- Verify OSLC Friend configuration: DNG ↔ ETM
- Create one test link (ETM test case → DNG requirement) and confirm backlink appears
- Verify suspect link mechanism works (modify requirement, check ETM marks link suspect)
- Document the integration configuration for your project's ELM administrator

**Resources:**
- [IBM DOORS / ETM Integration — Official Documentation](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.2?topic=integrating-doors-engineering-test-management)
- [Day 6 — DOORS Next + ETM Integration](../daily-learning-guide/day-06.md)

---

### 2B: Traceability Link Governance

**Research question:** Is there a governance process for creating and maintaining traceability links?

**Why second:** Links created inconsistently (wrong link type, missing links, stale links) make the RTM unreliable. Automation built on unreliable traceability produces noise.

**Actions:**
- Define link type policy: which types are mandatory (Validates), which are optional
- Establish: who is responsible for creating requirement-to-test links?
- Define suspect link resolution SLA: how quickly must a suspect link be reviewed?
- Create a link review checklist for test engineers

**Resources:**
- [Traceability Links in DOORS Next (SodiusWillert)](https://www.sodiuswillert.com/en/blog/how-to-set-up-create-and-use-traceability-links-in-ibm-doors-next)

---

## Priority 3 — Automation & Scripting

These topics enable the actual automation workflow.

### 3A: CI/CD Pipeline Integration Design

**Research question:** How will your CI/CD pipeline query DOORS for test scope and write results back?

**Why third:** This is the "wiring" that makes everything else automatic. Done once, it runs continuously.

**Actions:**
- Select query pattern: requirement-driven selection (query DOORS for untested requirements) vs. change-driven (trigger tests on requirement change)
- Identify the DOORS Next REST API endpoints required
- Create a service account with minimum required ELM licences
- Build and test one pipeline integration: query DNG → execute ETM test → write result back

**Resources:**
- [IBM DOORS / Git Integration via OpsHub](https://www.opshub.com/ibm-doors-integration/ibm-doors-git-integration/)
- [Day 9 — Digital Thread & CI/CD Integration](../daily-learning-guide/day-09.md)

---

### 3B: DXL Scripting (DOORS Classic Only)

**Research question:** Are there bulk operations (import, validation, reporting) that would benefit from DXL automation?

**Why third:** DXL provides automation capabilities specific to DOORS Classic environments. High value if you are still on Classic; lower priority for DOORS Next (use REST API instead).

**Actions:**
- Identify the top 3 manual DOORS Classic tasks that could be automated with DXL
- Develop or adapt DXL scripts for: PDF text import, coverage reporting, attribute bulk-update
- Test scripts on a DOORS Classic sandbox before production

**Resources:**
- [IBM Rational DOORS DXL Reference Manual (PDF)](https://www.ibm.com/docs/en/SSYQBZ_9.6.1/com.ibm.doors.requirements.doc/topics/dxl_reference_manual.pdf)
- [Day 8 — DXL Scripting](../daily-learning-guide/day-08.md)

---

## Priority 4 — Maintenance & Compliance

These topics are important but can follow once the core automation is operational.

### 4A: Baseline Strategy for Automated Testing

**Research question:** What global configuration will CI/CD test runs reference?

**Why fourth:** Important for compliance and reproducibility, but not the first thing to build. Establish baselines once the pipeline is running.

**Actions:**
- Define baseline events (per-sprint, per-milestone, per-release)
- Configure GCM to span DNG and ETM baselines
- Configure CI/CD to accept a global configuration as a pipeline parameter
- Validate: run CI against a historical baseline and confirm correct test set is executed

**Resources:**
- [Baselines with IBM DOORS Next (SodiusWillert)](https://www.sodiuswillert.com/en/blog/best-practices-for-managing-baselines-with-ibm-doors-next)
- [Day 7 — Baseline & Configuration Management](../daily-learning-guide/day-07.md)

---

### 4B: PDF Import Process

**Research question:** What is the standard process for ingesting requirements from PDF documents into DOORS?

**Why fourth:** Important for onboarding new specifications, but not blocking automated testing of requirements already in DOORS.

**Actions:**
- Select the import path appropriate for your document types (see [pdf-import/workarounds.md](../pdf-import/workarounds.md))
- Pilot the process with one real specification document
- Document the standard operating procedure for your project
- For recurring imports: automate using DXL or CSV pipeline

**Resources:**
- [PDF Import Workarounds](../pdf-import/workarounds.md)
- [Day 10 — PDF Import Workflows](../daily-learning-guide/day-10.md)

---

### 4C: DOORS ELM Architecture Governance

**Research question:** Is there an ELM governance structure that supports long-term automation?

**Why fourth:** Governance is the sustainability layer. Without it, the automation deteriorates as configurations drift.

**Actions:**
- Identify the ELM administrator responsible for server configuration
- Document the OSLC integration configuration and keep it up to date
- Establish a process for reviewing and updating the DOORS type system
- Create a runbook for the CI/CD integration: what to do when it breaks

---

## Summary Roadmap

```
Month 1 (Priority 1):
  ├── Audit requirements for testability (1A)
  ├── Design/standardise attribute schema (1B)
  └── Baseline current coverage (1C)

Month 2 (Priority 2):
  ├── Configure DNG–ETM OSLC integration (2A)
  └── Establish link governance process (2B)

Month 3 (Priority 3):
  ├── Build CI/CD pipeline integration (3A)
  └── Develop DXL scripts if Classic (3B)

Month 4+ (Priority 4):
  ├── Implement baseline/GCM strategy (4A)
  ├── Establish PDF import process (4B)
  └── Formalise ELM governance (4C)
```

---

## Key Success Metrics

| Metric | Baseline | Target (Month 6) |
|--------|----------|-----------------|
| Requirements coverage (%) | Measure now | >80% of Critical reqs |
| Verified requirements (%) | Measure now | >60% of Critical reqs |
| Time to verify new requirement | Weeks (manual) | Hours (automated) |
| Suspect links resolved | Unknown | <5% outstanding >48h |
| PDF import time per document | Days (manual) | Hours (Path 1/2) |
