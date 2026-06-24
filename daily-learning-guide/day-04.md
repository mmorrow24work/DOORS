# Day 4 — Attributes, Types & Custom Properties

**Bloom's Level:** Understand → Apply
**Estimated Time:** 90 minutes

---

## Learning Objectives

By the end of today you will be able to:
- [ ] Distinguish between built-in and custom artifact attributes in DOORS Next
- [ ] Design a minimal attribute schema that supports automated test selection
- [ ] Define controlled vocabularies for enumeration attributes
- [ ] Explain why inconsistent attribute naming breaks automation pipelines

---

## Core Concept (15 min)

### What Are Attributes?

In DOORS, every requirement is an *artifact* (DOORS Next) or *object* (DOORS Classic). Each artifact carries a set of **attributes** — fields that store metadata about the requirement.

Think of attributes as columns in a database table. The requirement text is one column; all other fields (priority, status, owner, component, test coverage) are attributes.

### Built-In Attributes (DOORS Next)

Every artifact in DOORS Next has these by default:

| Attribute | Type | Example |
|-----------|------|---------|
| Identifier | String (auto) | REQ-001 |
| Name | String | Login response time |
| Primary Text | Rich text | "The system shall respond to login requests within 2 seconds..." |
| Created By | User | john.smith |
| Created On | Date | 2024-01-15 |
| Modified On | Date | 2024-03-01 |
| Artifact Type | Type | Functional Requirement |

### Custom Attributes — The Power of DOORS

Custom attributes let you extend every artifact with domain-specific fields. These are essential for automation:

| Attribute Name | Type | Purpose |
|---------------|------|---------|
| Priority | Enumeration (Critical/High/Medium/Low) | Test prioritisation |
| Verification Status | Enumeration (Not Verified/In Progress/Verified/Waived) | Coverage tracking |
| Verification Method | Enumeration (Test/Analysis/Inspection/Demonstration) | Determines whether automated test applies |
| Component | String | Which subsystem this requirement belongs to |
| Safety Critical | Boolean | Flags requirements needing extra test rigour |
| Allocated To | String (team/sprint) | Used by CI/CD to scope test runs |

### Artifact Types

DOORS Next supports multiple artifact types within a project. This allows you to model a requirement hierarchy:

```
StakeholderNeed (top level)
  └── SystemRequirement (verified by tests)
        └── SubsystemRequirement (allocated to teams)
              └── DesignConstraint (verified by inspection)
```

Each type can have a different set of attributes. A *Design Constraint* may not need a *Verification Status* attribute; a *Functional Requirement* always does.

### Designing for Automation

The attribute schema must be designed with automation in mind from day one. Key principles:

1. **Use controlled vocabularies** — never free-text fields for values that automation will query. Use enumerations. `Priority = "High"` is queryable; `Priority = "hi!!"` causes pipeline failures.
2. **Be consistent across the schema** — if one artifact type uses "Verified" and another uses "Complete", your queries will miss records.
3. **Add automation-specific attributes** — `Automation ID` (the test case ID in your CI system), `Last Verified Date`, `Verified By Build` (the CI build number).
4. **Don't over-engineer** — start with 5–7 custom attributes. More attributes = more governance overhead. Add only when a concrete automation need justifies it.

### Example Minimal Schema for Automated Testing

```
Artifact Type: Functional Requirement
├── Identifier (auto)
├── Name
├── Primary Text
├── Priority               [Critical | High | Medium | Low]
├── Verification Method    [Test | Analysis | Inspection | Demonstration]
├── Verification Status    [Not Verified | In Progress | Verified | Waived]
├── Component              [controlled list of subsystem names]
└── Automation Test ID     [string — e.g., "TC-0042" in your CI system]
```

---

## Key Definitions

| Term | Definition |
|------|-----------|
| **Attribute** | A metadata field on a DOORS artifact (e.g., Priority, Status) |
| **Artifact Type** | A named category of artifact with its own attribute set (e.g., Functional Requirement) |
| **Enumeration** | An attribute restricted to a fixed set of values — critical for automation |
| **Controlled vocabulary** | A defined list of allowed values; prevents free-text inconsistency |
| **Verification Method** | How a requirement will be verified: Test, Analysis, Inspection, or Demonstration |
| **Verification Status** | The current verification state of a requirement |
| **Type system** | The set of artifact types, link types, and attribute definitions for a project |

---

## Practical Exercise (30 min)

**Goal:** Design the attribute schema for your project's primary requirement type.

1. Identify your most common requirement type (e.g., Functional Requirement)
2. List every piece of information that an automated test pipeline would need to know about this requirement
3. For each piece, decide:
   - Attribute name (be exact — this is what your API queries will use)
   - Type: String / Enumeration / Boolean / Date / Integer / User
   - For enumerations: list every allowed value
   - Is this mandatory or optional?
4. Review against this checklist:
   - [ ] Is there an attribute that identifies verification method?
   - [ ] Is there an attribute that tracks verification status?
   - [ ] Is there an attribute for priority (for test ordering)?
   - [ ] Is there an attribute that links to a CI system test case ID?
   - [ ] Are all enumeration values consistent with other tools in your pipeline?
5. Write a one-paragraph justification for why each attribute is needed

---

## Connection to Automated Testing

The attribute schema is the **contract between DOORS and your test automation pipeline**. Your CI/CD system will query DOORS for requirements that match certain attribute values (e.g., `Priority = "Critical" AND Verification Status = "Not Verified"`), retrieve the linked test cases, and execute them.

If the schema is inconsistent or uses free-text where enumerations are needed, the query fails silently — no error, just missing requirements. This is one of the most common causes of automated testing gaps that only appear at audit time.

---

## Reflection Prompts

1. What attributes do you currently capture for requirements (in whatever tool you use today)?
2. Which of those attributes does your test team actually use when writing test cases? Which are ignored?
3. If your CI system could query DOORS right now, what is the first filter it would apply to find requirements that need test runs?

---

## Further Reading

- [Complete Guide: Requirements Management with DOORS Next](https://mgtechsoft.com/blog/requirements-management-with-doors-next-a-complete-guide/)
- [IBM DOORS Next 101 Community Hub](https://www.ibm.com/community/101/engineering/ibm-engineering-requirements-management-doors-next-101/)
- [IBM DOORS Next Training Videos — Attributes (Official Playlist)](https://www.youtube.com/playlist?list=PLbFaBJSLVSlxcGJefBDHSSoAPhH8YzCnT)

---

## Tomorrow's Preview

**Day 5** turns attributes into traceability links. You will set up the links that connect your requirements to test cases and generate the Requirements Traceability Matrix (RTM). Before tomorrow, think: *between your requirements and your test cases, does a link exist today? If so, where does it live — in a spreadsheet, in a test tool, or nowhere?*
