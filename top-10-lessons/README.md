# Top 10 Lessons — IBM DOORS ELM for Systems Architects

These ten lessons distil the most important concepts for a systems architect whose goal is to **introduce automated testing** into a DOORS ELM environment. They are ordered by priority — not complexity. Start with what will unlock the most value for test automation first.

---

## The Top 10 Lessons

### Lesson 1 — Requirements Traceability Fundamentals
**The single most important concept.** Traceability is the chain linking a stakeholder need to a system requirement, to a design artefact, to a test case, to a test result. Without it, automated testing cannot prove coverage.

**Key ideas:**
- Forward traceability (requirement → test)
- Backward traceability (test result → requirement)
- Orphan requirements (no test coverage) and orphan tests (no requirement)
- Coverage matrices and gap analysis

**Why first:** Every subsequent lesson builds on this mental model.

---

### Lesson 2 — Writing Testable Requirements (INCOSE Quality Rules)
**Poorly written requirements cannot be tested.** INCOSE defines 42 quality criteria for requirements. The most automation-critical are: *verifiable*, *unambiguous*, *complete*, *singular* (one requirement per statement), and *implementation-free*.

**Key ideas:**
- SMART requirements (Specific, Measurable, Achievable, Relevant, Testable)
- The INCOSE 42 rules — especially the 8 rules most relevant to testability
- Common anti-patterns: use of "shall/should/may" confusion, compound requirements, undefined quantities
- How a badly-worded requirement causes test case explosion

**Why second:** Automated testing of ambiguous requirements produces meaningless results. Fix the requirements first.

---

### Lesson 3 — DOORS ELM Architecture (Classic vs Next, ELM Suite)
**Understand what you are working with.** DOORS Classic (v9.x) and DOORS Next (v7.x) are substantially different tools sharing a brand name. Many organisations run both.

**Key ideas:**
- DOORS Classic: client-server, DXL scripting, module/object model
- DOORS Next (DNG): web-based, OSLC, artifact/component/stream model
- The Engineering Lifecycle Management (ELM) suite: DNG + ETM + EWM + ELMUE
- Global Configuration Management (GCM) — managing variants across tools
- Jazz.net platform as the integration fabric

**Why third:** Architectural confusion causes misaligned tool configuration. Know which product you are configuring.

---

### Lesson 4 — Attributes, Types & Custom Properties
**Structure your data for automation.** DOORS artifacts carry attributes (fields) that automation tools query to determine test scope, priority, and status. Poorly structured attribute schemas break automation pipelines.

**Key ideas:**
- Built-in vs custom artifact types
- Enumeration attributes (e.g., Priority: High/Medium/Low) vs string/date/link attributes
- Type systems in DOORS Next: artifact types, link types, constraint types
- Designing attribute schemas with automation in mind (consistent naming, controlled vocabularies)
- Attribute-based filtering for test selection

**Why fourth:** Before building any automation, the data model must support it.

---

### Lesson 5 — Requirements Traceability Links & Matrices
**Operationalising traceability.** Once you understand the concept (Lesson 1), this lesson covers how to create, manage, and report on traceability links in DOORS.

**Key ideas:**
- Link types: *satisfies*, *verifies*, *refines*, *derives*, *traces*
- Creating suspect links (flagging requirements that changed after a test was written)
- Generating Traceability Matrices (RTM) in DOORS Next
- Coverage reports: percentage of requirements with test coverage
- Link validity rules and governance

**Why fifth:** The RTM is the primary artefact used by test automation to select test cases.

---

### Lesson 6 — DOORS Next + IBM Engineering Test Management (ETM) Integration
**The core automation integration.** ETM (formerly Rational Quality Manager) is IBM's test management tool. Its OSLC integration with DOORS Next enables test cases to be linked to requirements, and test execution results to flow back as requirement satisfaction evidence.

**Key ideas:**
- OSLC (Open Services for Lifecycle Collaboration) — the integration protocol
- Linking ETM Test Cases to DOORS Next requirements
- Test execution results updating requirement verification status
- Setting up OSLC Friend relationships between servers
- Role-based access configuration for test engineers
- Common integration pitfalls: permission misconfiguration, OSLC consumer keys

**Why sixth:** This is the primary mechanism for automated testing traceability.

---

### Lesson 7 — Baseline & Configuration Management
**Protecting the integrity of your requirements.** A baseline is a snapshot of requirements at a point in time. Without baselines, it is impossible to determine which version of a requirement a test was written against.

**Key ideas:**
- Streams vs baselines in DOORS Next
- Global Configuration Management (GCM): spanning baselines across DNG, ETM, EWM
- Change sets and how requirement changes are tracked
- Suspect links — when a requirement changes after a test is written
- Baseline strategies for regulated industries (DO-178C, IEC 62443, ISO 26262)

**Why seventh:** Automated testing must target a known baseline, not a moving target.

---

### Lesson 8 — DXL Scripting for Automation (DOORS Classic)
**The native automation language.** DXL (DOORS eXtension Language) is the scripting language built into DOORS Classic. It enables bulk operations, custom imports, report generation, and integration hooks.

**Key ideas:**
- DXL syntax and data model (modules, objects, attributes)
- Reading and writing attributes programmatically
- Automating module creation and object linking
- Running DXL as batch scripts or triggered by DOORS menu
- DXL for PDF-to-DOORS import automation (see [pdf-import](../pdf-import/README.md))
- Community DXL resources and script libraries

**Why eighth:** DXL is the primary tool for automating repetitive DOORS Classic workflows, including bulk requirement import.

---

### Lesson 9 — Digital Thread & CI/CD Integration
**Connecting DOORS to your software delivery pipeline.** The "digital thread" is the continuous traceable link from requirement to deployed software. For automated testing, this means connecting DOORS requirement changes to CI/CD pipeline triggers.

**Key ideas:**
- OSLC TRS (Tracked Resource Sets) — event feeds for requirement changes
- Triggering test runs when requirements change (Jenkins, GitHub Actions, Azure DevOps)
- IBM DOORS + Git integration patterns (OpsHub, custom webhooks)
- Compliance-ready traceability: commit → test → requirement
- Licence and access model for CI/CD service accounts in ELM

**Why ninth:** The ultimate goal — requirements changes automatically trigger relevant test suites.

---

### Lesson 10 — PDF Import Workflows
**The practical pain point.** DOORS has no native PDF import. Requirements stored in numbered paragraphs in PDF documents must be converted before import. This lesson covers the reliable approaches.

**Key ideas:**
- Why PDF import does not exist in DOORS (IBM confirmed limitation)
- PDF → Word → DOORS (the standard path)
- PDF → CSV → DOORS (for structured data with metadata)
- PDF → ReqIF → DOORS (standards-based, regulated industries)
- DXL scripting for repeatable automated PDF import
- Preserving paragraph numbering as artifact identifiers

**Why tenth:** Practically, many requirements arrive as PDFs. This lesson is the bridge from real-world documents to a managed DOORS database.

See: [pdf-import/workarounds.md](../pdf-import/workarounds.md) for step-by-step guidance.

---

## Research Priority Map for Automated Testing

The table below groups lessons by their priority for a systems architect whose primary goal is introducing automated testing.

| Priority | Lessons | Focus Area | Why This Priority |
|----------|---------|-----------|-------------------|
| **P1 — Do First** | 1, 2, 4 | Foundations for testable data | Testable requirements + correct attribute schemas are prerequisites for all automation |
| **P2 — Do Second** | 5, 6 | Traceability + ETM integration | The core technical integration between requirements and test execution |
| **P3 — Do Third** | 8, 9 | Scripting + CI/CD | Automating workflows once the data model and integrations are sound |
| **P4 — Do Last** | 3, 7, 10 | Architecture, baselines, PDF import | Context and maintenance concerns; important but not blocking automation delivery |

---

## Quick Reference: Key Terms

| Term | Definition |
|------|-----------|
| DNG | DOORS Next Generation — the web-based version of DOORS |
| ELM | Engineering Lifecycle Management — IBM's suite including DNG, ETM, EWM |
| ETM | Engineering Test Management — IBM's test management tool (was RQM) |
| EWM | Engineering Workflow Management — IBM's work item tracker (was RTC) |
| OSLC | Open Services for Lifecycle Collaboration — the integration standard |
| GCM | Global Configuration Management — managing variants across the ELM suite |
| DXL | DOORS eXtension Language — scripting language for DOORS Classic |
| RTM | Requirements Traceability Matrix — the key artefact linking requirements to tests |
| ReqIF | Requirements Interchange Format — standard XML format for requirements exchange |
| Suspect Link | A traceability link flagged because a linked artifact was modified |
