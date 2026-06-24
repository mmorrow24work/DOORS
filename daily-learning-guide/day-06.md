# Day 6 — DOORS Next + IBM Engineering Test Management Integration

**Bloom's Level:** Apply → Analyse
**Estimated Time:** 90 minutes

---

## Learning Objectives

By the end of today you will be able to:
- [ ] Describe how OSLC enables DOORS Next to link to ETM test cases
- [ ] Identify the configuration steps required to activate the DNG–ETM integration
- [ ] Explain the flow from requirement change to suspect link to test execution
- [ ] Diagnose the most common integration configuration failures

---

## Core Concept (15 min)

### How OSLC Integration Works

IBM Engineering Test Management (ETM) and DOORS Next (DNG) communicate using **OSLC** — a REST-based web standard that allows tools to link to each other's artefacts as if they were hyperlinks.

The integration works as follows:

```
DNG (Requirements)          ETM (Tests)
┌─────────────────┐         ┌──────────────────┐
│  Requirement    │◄────────│  Test Case       │
│  REQ-001        │Validates│  TC-042          │
│  Status: Not    │         │  Status: Passed  │
│  Verified       │────────►│                  │
└─────────────────┘  OSLC   └──────────────────┘
        │                           │
        └─── Suspect Link ──────────┘
             (when REQ-001 changes)
```

When a test case in ETM is linked to a requirement in DNG:
1. The test case appears in the DNG requirement's "Validated By" section
2. When the test passes in ETM, DNG shows the requirement as satisfied
3. When the requirement is modified in DNG, the link is marked suspect in ETM
4. ETM can alert test engineers that the linked test needs review

### Configuration Steps

Setting up the DNG–ETM integration requires these steps (performed by an ELM administrator):

**Step 1: Register ETM as a Friend of DNG** (and vice versa)
- In DNG project settings: add ETM server URL as a trusted consumer
- In ETM project settings: add DNG server URL as a trusted consumer
- This establishes mutual trust using OSLC consumer keys

**Step 2: Configure Project Associations**
- Link a DNG project area to an ETM project area
- Both must be on the same Jazz server (or federated Jazz servers)
- Without this, DNG artifacts cannot be discovered from ETM

**Step 3: Enable Link Type Definitions**
- Ensure "Validates" link type is enabled in both project type systems
- Add custom link types if needed (e.g., "Acceptance Tests", "Regression Tests")

**Step 4: Verify OSLC Rootservices**
- Confirm both servers expose their OSLC rootservices endpoint
- URL: `https://yourserver/rm/rootservices` (DNG) and `https://yourserver/qm/rootservices` (ETM)
- These are the discovery endpoints tools use to find each other

### The Automated Testing Flow

Once configured, the full automated testing flow looks like:

```
1. Engineer creates requirement in DNG (REQ-001, Priority: Critical)
2. Test engineer creates test case in ETM (TC-042)
3. TC-042 is linked to REQ-001 via OSLC Validates link
4. CI pipeline queries DNG: "find all Critical requirements not yet Verified"
5. DNG returns REQ-001; CI retrieves TC-042 from the link
6. CI executes TC-042; result: Pass
7. ETM writes result back: TC-042 = Passed
8. DNG updates: REQ-001 Verification Status = Verified
```

### Common Integration Failures

| Failure | Symptom | Fix |
|---------|---------|-----|
| OSLC consumer keys not set up | "Cannot connect to requirements provider" in ETM | Re-register Friend relationship with correct keys |
| Project areas not associated | DNG requirements not discoverable from ETM | Add project association in both tools |
| Wrong server URL in Friend config | Timeout when browsing for requirements | Check URL format: `https://server:port/rm` |
| Firewall blocking OSLC ports | Links work in UI but fail in CI/CD | Open required ports (typically 9443) |
| Role misconfiguration | User can see link but cannot create it | Assign correct ELM role to test engineers |
| GCM not configured | Links break when switching streams/baselines | Configure GCM project areas to span DNG and ETM |

---

## Key Definitions

| Term | Definition |
|------|-----------|
| **ETM** | Engineering Test Management — IBM's test planning and execution tool |
| **OSLC Friend** | A trusted server relationship that allows OSLC links between two tools |
| **Consumer key** | A credential pair that authorises OSLC communication between tools |
| **Project association** | The configuration linking a DNG project to an ETM project |
| **Rootservices** | An OSLC discovery endpoint that exposes a server's capabilities |
| **Validated By** | The backlink shown in DNG when an ETM test case links to a requirement |
| **Suspect link** | In ETM: a link to a DNG requirement that was modified after the link was created |

---

## Practical Exercise (30 min)

**Option A (if you have ELM access):**
1. Open DNG and locate a functional requirement
2. Open ETM and find or create a test case for that requirement
3. In ETM, create an OSLC link from the test case to the DNG requirement (use "Validates")
4. Return to DNG and confirm the backlink ("Validated By: TC-xxx") appears
5. Modify the requirement text in DNG
6. Return to ETM and confirm the link is now marked as suspect

**Option B (if you do not have ELM access):**
1. Review the DOORS Next + ETM integration documentation: https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.2?topic=integrating-doors-engineering-test-management
2. Draw the integration configuration diagram: servers, Friend relationships, project associations
3. For each of the 6 common failures in the table above, write one line describing how you would diagnose it in your environment

---

## Connection to Automated Testing

The DNG–ETM integration is the **technical backbone** of automated testing traceability. Without it, test results are stored in ETM but requirements in DNG have no knowledge of whether they have been verified. With it, every test execution writes evidence back into the requirements database — creating the audit trail that compliance frameworks require.

For a systems architect, the key insight is: the integration configuration is a one-time infrastructure cost. Once set up, every automated test run automatically maintains requirement verification status with no manual effort.

---

## Reflection Prompts

1. Is the OSLC Friend relationship between DNG and ETM currently active in your organisation? If not, who would need to approve and configure it?
2. What would it take to get the first DNG requirement linked to an ETM test case in your environment?
3. In your current testing process, how does a test result make its way back to a requirements document? How many manual steps are involved?

---

## Further Reading

- [IBM DOORS / ETM Integration — Official Documentation](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.2?topic=integrating-doors-engineering-test-management)
- [ETM and DOORS Integration — Jazz.net Reference](https://jazz.net/help-dev/clm/topic/com.ibm.rational.test.qm.doc/topics/c_int_rqm_doors.html)
- [IBM Engineering Test Management Overview](https://www.ibm.com/products/ibm-engineering-test-management)

---

## Tomorrow's Preview

**Day 7** covers baseline and configuration management — the mechanism that ensures your automated tests always run against a known, stable version of requirements, not a moving target. Before tomorrow, ask: *when a requirement changes in your project today, who is notified, and how do they know which tests are affected?*
