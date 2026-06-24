# Day 7 — Baseline & Configuration Management

**Bloom's Level:** Analyse
**Estimated Time:** 90 minutes

---

## Learning Objectives

By the end of today you will be able to:
- [ ] Explain the difference between a stream and a baseline in DOORS Next
- [ ] Describe how Global Configuration Management (GCM) spans the full ELM suite
- [ ] Identify when suspect links arise and what action they require
- [ ] Design a baseline strategy appropriate for a system under test

---

## Core Concept (15 min)

### The Problem Without Baselines

Without configuration management, requirements are a moving target. A test passes today against requirement REQ-001 version 3. Tomorrow, a designer modifies REQ-001 to version 4. The CI system reports "all tests passing" — but the passing tests were written against a requirement that no longer exists. The product may not meet the current requirement at all.

Baselines solve this by recording *"which version of which requirements were active at this point in time"*.

### Streams and Baselines in DOORS Next

DOORS Next uses a Git-like versioning model:

```
          Initial                  Version 2
          Baseline                 Baseline
              │                       │
Stream ───────●──────────────────────●────────►
              │                       │
         (locked)               (locked — immutable)
              │
         Working Set
         (current mutable state)
```

| Concept | Description |
|---------|-------------|
| **Stream** | A mutable branch of requirements — the active working version |
| **Baseline** | An immutable snapshot of the stream at a point in time |
| **Change Set** | A set of changes to requirements that can be reviewed before merging |
| **Component** | A grouping of modules within a stream — reusable across projects |

Key rule: **baselines are immutable**. Once created, no one can change a baseline. This is what makes them trustworthy for compliance.

### Global Configuration Management (GCM)

The problem with per-tool baselines: a DNG baseline doesn't know which ETM baseline it was tested against. GCM solves this by creating a **global configuration** — a named collection of baselines from DNG, ETM, and EWM that together represent a consistent state of the entire engineering programme.

```
Global Configuration: "Release 2.0 Candidate"
├── DNG Baseline: "Requirements v2.0 RC1"
├── ETM Baseline: "Test Plan v2.0 RC1"  
└── EWM Baseline: "Sprint 8 Complete"
```

With GCM:
- Automated tests run against a declared global configuration
- Traceability links are consistent across the entire suite
- Compliance evidence references the global configuration, not individual tool snapshots

### Suspect Links and Change Control

When a requirement in a DNG stream is modified after a test case links to it, the link becomes **suspect**. This is DOORS' built-in change notification for test engineers.

For automated testing, suspect links should be surfaced as:
- **Build warnings** (for low-priority requirements)
- **Build failures** (for Critical/Safety-Critical requirements)
- **Jira/EWM work items** (for test case review tasks)

### Baseline Strategies

Different project types call for different baseline approaches:

| Strategy | When to Use | How Often |
|----------|-------------|-----------|
| Milestone baselines | Traditional waterfall | At each phase gate |
| Sprint baselines | Agile/iterative | End of every sprint |
| Release baselines | All projects | Before every customer release |
| Regulatory baselines | Safety-critical (DO-178C, ISO 26262) | As required by standard |

For automated testing: create a baseline **before** running a formal test cycle. Tests are always run against a baseline, never against the live stream.

---

## Key Definitions

| Term | Definition |
|------|-----------|
| **Stream** | A mutable branch of requirements in DOORS Next |
| **Baseline** | An immutable, named snapshot of a stream at a point in time |
| **Change Set** | A named, reviewable set of changes to a stream |
| **GCM** | Global Configuration Management — spanning baselines across DNG, ETM, EWM |
| **Global Configuration** | A named collection of per-tool baselines representing a coherent state |
| **Suspect link** | A traceability link invalidated by a subsequent change to a linked artifact |
| **Configuration context** | The active stream or baseline being viewed/queried |

---

## Practical Exercise (30 min)

**Goal:** Design a baseline strategy for your project.

1. Define the baseline events for your project lifecycle:
   - What are your project milestones or sprint boundaries?
   - At what points would you need a "frozen" requirements snapshot?
   - Are there regulatory requirements that mandate specific baselines?

2. Fill in this baseline planning table:

   ```
   Baseline Name | Trigger Event | DNG Component(s) | ETM Component | Owner
   ```

3. Answer these questions:
   - Who has permission to create baselines in your project?
   - Who can approve/reject a change set before it is merged to the stream?
   - What happens when a Critical requirement is modified mid-sprint?

4. Draft a one-paragraph "baseline policy" for your project: when are baselines created, who creates them, and what testing runs against each one?

---

## Connection to Automated Testing

Baselines are the foundation of **repeatable** automated testing. Without them:
- Tests pass or fail against an undefined version of requirements
- Compliance evidence is contestable ("which requirements did this test verify?")
- Regression testing has no stable reference point

With baselines:
- Every CI run specifies its target global configuration
- Test results are stored against that configuration
- Auditors can review exactly which requirements were tested by which test against which version

The practical implementation: configure your CI/CD pipeline to specify a GCM global configuration as a parameter of each test run. ETM will record results against that configuration.

---

## Reflection Prompts

1. In your current project, is there a point in time you could point to and say "this is the requirements baseline we tested against for our last release"? If not, what would it take to create one?
2. Who would need to be involved in approving a change set (requirements change) in your organisation?
3. Would a CI build failure triggered by a suspect link (requirement changed) be acceptable to your team, or would it need to be a warning first?

---

## Further Reading

- [Best Practices for Managing Baselines with IBM DOORS Next (SodiusWillert)](https://www.sodiuswillert.com/en/blog/best-practices-for-managing-baselines-with-ibm-doors-next)
- [IBM DOORS Next Master Documentation — Configuration Management Section](https://www.ibm.com/docs/en/SSUVLZ_7.0.2/pdf/doorsnext_master_702.pdf)
- [IBM ELM License Types & Best Practices (covers GCM licensing)](https://www.ibm.com/support/pages/ibm-engineering-lifecycle-management-elm-license-types-capabilities-and-best-practices)

---

## Tomorrow's Preview

**Day 8** teaches DXL — the DOORS Classic scripting language that enables bulk operations, automated imports, and custom reporting. Even if you are primarily using DOORS Next, understanding DXL is valuable because many organisations still run DOORS Classic for their legacy requirements. Before tomorrow, consider: *are there any repetitive tasks in your DOORS workflow (bulk status updates, report generation, import/export) that you currently do manually?*
