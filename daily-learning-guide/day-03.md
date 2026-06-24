# Day 3 — DOORS ELM Architecture: Classic vs Next

**Bloom's Level:** Understand
**Estimated Time:** 90 minutes

---

## Learning Objectives

By the end of today you will be able to:
- [ ] Describe the key architectural difference between DOORS Classic and DOORS Next
- [ ] Name the four tools in the IBM ELM suite and their roles
- [ ] Explain what OSLC is and why it matters for tool integration
- [ ] Identify which DOORS version your organisation uses and what that means for automation

---

## Core Concept (15 min)

### The ELM Suite

IBM's **Engineering Lifecycle Management (ELM)** suite is a collection of tools that together cover the full engineering lifecycle:

```
┌─────────────────────────────────────────────────────────┐
│                    IBM ELM Suite                        │
│                                                         │
│  DNG (DOORS Next)     ETM                  EWM          │
│  Requirements    →  Test Cases    →   Work Items        │
│  Management         & Execution       (Defects, Tasks)  │
│                                                         │
│              GCM (Global Configuration Mgmt)            │
│         Manages variants across DNG + ETM + EWM         │
└─────────────────────────────────────────────────────────┘
                         │
                    Jazz.net Platform
                (shared auth, OSLC, links)
```

| Tool | Full Name | Role |
|------|-----------|------|
| **DNG** | Engineering Requirements Management DOORS Next | Requirements |
| **ETM** | Engineering Test Management | Test planning & execution |
| **EWM** | Engineering Workflow Management | Work items, defects, sprints |
| **GCM** | Global Configuration Management | Version control spanning all three tools |

### DOORS Classic (v9.x) Architecture

DOORS Classic is a **client-server** application installed on Windows. Engineers run a desktop client that connects to a shared DOORS server.

Key characteristics:
- **Module/Object model**: requirements live in *modules* (like files), each *object* is a requirement
- **DXL scripting**: a built-in scripting language for automation, reporting, and import
- **Formal modules**: formal and informal modules (formal = numbered, mandatory structure)
- **Integration**: file-based export/import; integration via DXL or third-party connectors
- **Status**: still widely used in defence and aerospace; IBM has stated it will be maintained but no major new features

### DOORS Next / DNG (v7.x) Architecture

DOORS Next is a **web application** running on IBM's Jazz server platform.

Key characteristics:
- **Artifact model**: requirements are *artifacts* within *modules* within *components*
- **Streams and baselines**: change management built in (like Git for requirements)
- **OSLC integration**: links to ETM, EWM, and third-party tools via open standards
- **Project areas and components**: hierarchical organisation for large programmes
- **REST API**: full programmatic access — critical for automation
- **Deployment**: on-premise (Jazz server) or IBM Engineering Lifecycle Management SaaS

### The OSLC Standard — Why It Matters

**OSLC (Open Services for Lifecycle Collaboration)** is an open standard that allows different tools to link to each other's artefacts using HTTP links.

In practice, this means:
- An ETM test case can carry a live link to a DNG requirement
- When a test executes and passes, ETM can update the satisfaction status in DNG
- A change to a DNG requirement automatically flags linked ETM test cases as *suspect*

OSLC is the foundation of automated testing integration with DOORS Next. Without it, test-to-requirement traceability requires manual updates.

### Which Version Do You Have?

| Indicator | DOORS Classic | DOORS Next |
|-----------|--------------|------------|
| Access method | Desktop client | Web browser |
| URL in address bar | N/A | `https://yourserver/rm/...` |
| Server product | DOORS Server | Jazz Team Server |
| Scripting | DXL menus in client | REST API / OSLC |
| Configuration management | Baselines only | Streams + baselines + GCM |

---

## Key Definitions

| Term | Definition |
|------|-----------|
| **ELM** | Engineering Lifecycle Management — IBM's integrated suite |
| **DNG** | DOORS Next — the web-based requirements management component |
| **ETM** | Engineering Test Management — IBM's test tool (was Rational Quality Manager) |
| **EWM** | Engineering Workflow Management — IBM's work item tool (was Rational Team Concert) |
| **GCM** | Global Configuration Management — versioning across the whole ELM suite |
| **OSLC** | Open Services for Lifecycle Collaboration — the integration protocol |
| **Jazz Platform** | The shared server infrastructure underlying DNG, ETM, and EWM |
| **Stream** | A mutable branch of requirements in DOORS Next |
| **Baseline** | An immutable snapshot of requirements at a point in time |

---

## Practical Exercise (30 min)

**Goal:** Map your organisation's current tool landscape against the ELM model.

1. Draw the ELM suite diagram (DNG, ETM, EWM, GCM) on paper
2. For each box, write: *a) do we have this tool? b) what version? c) who owns it?*
3. For each integration line (DNG→ETM, ETM→EWM, etc.), write: *a) is this integration active? b) is it manual or automated?*
4. Mark the gaps — where is the digital thread broken in your organisation today?
5. Identify your single highest-value integration to establish first

*If you don't have access to the tools yet: do this exercise based on conversations with your team or your organisation's IT / tools team.*

---

## Connection to Automated Testing

The architecture determines what automation is possible:

| Architecture | Automation Approach |
|-------------|---------------------|
| DOORS Classic only | DXL scripting; file-based test tool integration; limited real-time feedback |
| DOORS Next only | OSLC links to ETM; REST API for CI/CD; real-time status updates |
| Both Classic + Next | Migration path needed; automation must account for both data models |
| Full ELM suite (DNG + ETM + EWM + GCM) | Full digital thread; automated suspect link detection; compliance-ready traceability |

Your architecture determines which lessons in this guide are most immediately relevant.

---

## Reflection Prompts

1. Does your organisation use DOORS Classic, DOORS Next, or both? What does this mean for your automation roadmap?
2. Is OSLC currently configured between your DNG and ETM instances? If not, what would it take to enable it?
3. Who in your organisation owns the decision about ELM architecture? Is there an ELM administrator?

---

## Further Reading

- [IBM ELM Overview — Full Architecture Documentation](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.1?topic=overview-elm)
- [Complete Overview of IBM Rational DOORS Next Generation (Proexcellency)](https://www.proexcellency.com/blogs/sap-online-training/a-complete-overview-of-ibm-rational-doors-next-generation-for-requirements-engineers)
- [IBM DOORS Next Tutorial For Beginners (YouTube)](https://www.youtube.com/watch?v=bIk33ca0oWQ)

---

## Tomorrow's Preview

**Day 4** gets practical: you will design the attribute schema that makes your requirements queryable by automated tools. Before tomorrow, think: *what fields (besides the requirement text itself) would an automated test system need to know to decide which tests to run?* Priority? Status? Component? Write down your best guess.
