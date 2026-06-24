# Day 9 — Digital Thread & CI/CD Integration

**Bloom's Level:** Evaluate → Create
**Estimated Time:** 90 minutes

---

## Learning Objectives

By the end of today you will be able to:
- [ ] Describe the concept of a digital thread across the full engineering lifecycle
- [ ] Identify the technical components needed to connect DOORS Next to a CI/CD pipeline
- [ ] Design a requirement-driven test pipeline that queries DOORS for test scope
- [ ] Evaluate the access and licensing considerations for CI/CD service accounts

---

## Core Concept (15 min)

### The Digital Thread

The **digital thread** is the unbroken, traceable connection linking every engineering artefact from initial stakeholder need through to deployed, verified product.

```
Stakeholder Need (Word/PDF/Interviews)
     │
     ▼
System Requirement [DNG]
     │ (satisfies)
     ▼
Design Artefact [EWM / Model-Based Engineering]
     │ (implements)
     ▼
Source Code Commit [Git]
     │ (tested by)
     ▼
Test Case [ETM]
     │ (executed by)
     ▼
CI/CD Build [Jenkins / GitHub Actions / Azure DevOps]
     │ (result written back to)
     ▼
Verification Status [DNG → REQ-001: Verified ✓]
```

Every arrow is a traceable link. Break any one link and the digital thread is severed.

### Key Integration Points

For a CI/CD pipeline to interact with DOORS Next, it needs:

1. **DOORS Next REST API** — query requirements, read attributes, update verification status
2. **ETM REST API** — create test runs, record execution results
3. **OSLC TRS (Tracked Resource Sets)** — subscribe to requirement change events
4. **Service Account** — a dedicated ELM user with the right permissions and CAL licence

### Pattern 1: Requirement-Driven Test Selection

```
CI Pipeline Start
      │
      ▼
Query DNG (REST): requirements where
  - Priority = "Critical"
  - Verification Status = "Not Verified" OR Suspect Link = True
      │
      ▼
For each requirement: retrieve linked ETM test case IDs via OSLC
      │
      ▼
Execute test cases in test runner
      │
      ▼
For each result: POST result to ETM (PASS/FAIL)
      │
      ▼
ETM updates DNG requirement: Verification Status = "Verified" (if pass)
      │
      ▼
DNG: requirement coverage report updated automatically
```

### Pattern 2: Requirement Change as Build Trigger

```
Engineer modifies REQ-001 in DNG
      │
      ▼
DNG generates OSLC TRS event: "REQ-001 modified"
      │
      ▼
CI pipeline subscribes to TRS; receives event
      │
      ▼
CI retrieves test cases linked to REQ-001 via "Validates" links
      │
      ▼
CI queues a targeted test run for TC-042, TC-043
      │
      ▼
Results written back to ETM → DNG
```

### DOORS Next REST API — Key Endpoints

| Operation | Endpoint (example) | Method |
|-----------|-------------------|--------|
| Query requirements | `/rm/views?projectURL=...&oslc.query=...` | GET |
| Get requirement details | `/rm/resources/{artifact-id}` | GET |
| Update attribute | `/rm/resources/{artifact-id}` | PUT |
| Get outbound links | `/rm/links?sourceURL=...` | GET |
| Create test result | `/qm/executionresults` | POST |

All endpoints require HTTP Basic Auth or OAuth2 with a valid ELM service account.

### Licensing Considerations

IBM ELM uses **Concurrent Access Licences (CALs)** — a named user or service account consumes a licence slot when connected. For CI/CD:
- The service account must have a valid **DNG Reader** licence (to query requirements) and **ETM Analyst** licence (to write test results)
- Licence consumption is concurrent — if the CI system holds a connection during a long build, it occupies a licence slot
- Design CI/CD queries to open and close connections quickly; avoid long-polling

---

## Key Definitions

| Term | Definition |
|------|-----------|
| **Digital thread** | The unbroken traceable chain from stakeholder need to verified product |
| **OSLC TRS** | Tracked Resource Sets — OSLC event feed for monitoring resource changes |
| **REST API** | The programmatic interface to DOORS Next / ETM — used by CI/CD pipelines |
| **CAL** | Concurrent Access Licence — IBM ELM's licencing model |
| **Service account** | A dedicated non-human ELM user for CI/CD automation |
| **OSLC query** | A structured URL-based query against a DOORS Next project |

---

## Practical Exercise (30 min)

**Goal:** Design the CI/CD integration architecture for your project.

1. Draw the integration diagram: CI tool → DNG → ETM → back to CI
2. For each integration step, identify:
   - What credentials/licences are needed?
   - What network connectivity is required?
   - What is the API call or protocol?
3. Answer these architecture questions:
   - Should your CI pipeline trigger tests on every commit, or only when requirements change?
   - How will you handle test failures — update DNG immediately, or only after investigation?
   - How will you surface suspect links in your build dashboard?
4. Draft a one-page "CI/CD Integration Runbook" describing how a new test run is triggered, executed, and recorded

**Stretch goal:** Write pseudocode (not real code) for the requirement-driven test selection pattern described above, using your organisation's specific attribute names from Day 4.

---

## Connection to Automated Testing

This lesson is the culmination of all previous lessons. The digital thread only has value when it is maintained automatically — not by engineers manually updating spreadsheets after each test run.

The architecture described here enables:
- **Continuous requirement verification**: every code change is immediately traced to requirements
- **Automated compliance evidence**: test results are continuously written to the requirements database
- **Zero-gap coverage reporting**: DNG always reflects current, accurate verification status

---

## Reflection Prompts

1. What is the biggest obstacle to implementing the digital thread in your organisation today — technical, organisational, or financial?
2. Is your CI/CD tool (Jenkins, GitHub Actions, etc.) able to make REST API calls to your ELM server? Are there network/firewall barriers?
3. Who would own the service account and CI/CD integration in your organisation — the requirements team, the test team, or DevOps?

---

## Further Reading

- [IBM DOORS / Git Integration via OpsHub — Compliance-Ready Traceability](https://www.opshub.com/ibm-doors-integration/ibm-doors-git-integration/)
- [IBM DOORS & EWM Integration via OSLC (MGTech Soft)](https://mgtechsoft.com/blog/integrating-ibm-engineering-requirements-management-doors-and-engineering-workflow-management-ewm-using-oslc/)
- [IBM Engineering Test Management — Product Overview](https://www.ibm.com/products/ibm-engineering-test-management)

---

## Tomorrow's Preview

**Day 10** tackles the most practical challenge in the programme: importing requirements from PDF documents with numbered paragraphs. After 9 days of foundations and integrations, you will apply everything you have learned to solve a real-world data ingestion problem. Before tomorrow, gather: *a sample PDF with numbered requirements paragraphs (redacted if needed). You will use it in the exercise.*
