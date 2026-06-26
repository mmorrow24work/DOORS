"""
Sample PDF Generator — Doc 4: Table of Contents + Multi-Annex
~100 requirements across 3 main sections and 2 annexes.
Requirement numbers restart at 1.x in each section and annex.

Key challenges tested:
  - Table of Contents: entries that match SECTION_PATTERN (number + space + text)
    but must NOT become requirements. Dot-leaders and page numbers identify them.
  - Section/annex tracking: requirement 1.1 appears in Section 1, Section 2,
    Annex A, and Annex B — the section column in the CSV must keep them distinct.
  - Bullet sub-items within requirements (mix of • and - styles).
  - Em dashes in section names (cp1252 mojibake candidate).
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../sample-pdfs/sample_04_toc_annex.pdf")

PAGE_W, PAGE_H = A4

DOC_NUM = "SRS-2024-004"
DOC_TITLE = "System Requirements Specification — Platform Architecture"


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(2.5 * cm, PAGE_H - 1.8 * cm, DOC_NUM)
    canvas.drawRightString(PAGE_W - 2.5 * cm, PAGE_H - 1.8 * cm, DOC_TITLE)
    canvas.line(2.5 * cm, PAGE_H - 2.0 * cm, PAGE_W - 2.5 * cm, PAGE_H - 2.0 * cm)
    canvas.drawString(2.5 * cm, 1.4 * cm, "INTERNAL USE ONLY")
    canvas.drawRightString(PAGE_W - 2.5 * cm, 1.4 * cm, f"Page {doc.page}")
    canvas.line(2.5 * cm, 1.8 * cm, PAGE_W - 2.5 * cm, 1.8 * cm)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

# Table of Contents entries — these match SECTION_PATTERN but should be
# ignored because they are followed by dot-leaders and page numbers.
TOC_ENTRIES = [
    ("1", "System Overview"),
    ("1.1", "Scope and Purpose"),
    ("1.2", "System Context"),
    ("1.3", "Definitions and Abbreviations"),
    ("2", "Functional Requirements"),
    ("2.1", "User Interface"),
    ("2.2", "Business Logic"),
    ("2.3", "Reporting"),
    ("3", "Data Requirements"),
    ("3.1", "Data Storage"),
    ("3.2", "Data Integrity"),
    ("Annex A", "Security Requirements"),
    ("Annex B", "Performance Requirements"),
]

SECTION_1 = [
    ("1", "System Overview",
     "The system shall provide an enterprise-grade platform for managing programme "
     "delivery, resource allocation, and stakeholder reporting across multiple "
     "concurrent projects."),
    ("1.1", "Scope and Purpose",
     "The system shall serve as the single authoritative source of truth for all "
     "programme-level requirements, decisions, and delivery artefacts."),
    ("1.1.1", None,
     "The system shall be accessible to all authorised users within the enterprise "
     "network without requiring local software installation beyond a supported "
     "web browser."),
    ("1.1.2", None,
     "The system shall support the following user roles and their associated permissions:\n"
     "BULLET: Programme Manager\n"
     "BULLET: Project Manager\n"
     "BULLET: Business Analyst\n"
     "BULLET: Read-Only Viewer"),
    ("1.2", "System Context",
     "The system shall integrate with the following enterprise systems via published APIs:\n"
     "BULLET: Enterprise Resource Planning (ERP)\n"
     "BULLET: Human Resources Information System (HRIS)\n"
     "BULLET: Document Management System (DMS)"),
    ("1.2.1", None,
     "Integration with the ERP system shall use the REST API documented in "
     "ERP-API-SPEC-v3.2, with OAuth 2.0 authentication."),
    ("1.2.2", None,
     "The system shall synchronise user account data from HRIS on a scheduled "
     "basis no less frequently than every 4 hours during business hours."),
    ("1.3", "Definitions and Abbreviations",
     "All abbreviations used in this document shall be defined in the Glossary at "
     "Annex A of the project's Document Management Plan."),
    ("1.3.1", None,
     "Where a term used in a requirement has a specific technical meaning that "
     "differs from its common English meaning, the technical definition shall take "
     "precedence and shall be referenced explicitly."),
]

SECTION_2 = [
    ("1", "Functional Requirements",
     "The system shall implement all functional requirements described in this section "
     "as mandatory capabilities for the initial system release."),
    ("1.1", "User Interface",
     "The user interface shall comply with WCAG 2.1 Level AA accessibility standards "
     "throughout all screens and user workflows."),
    ("1.1.1", None,
     "The interface shall support keyboard-only navigation for all primary user "
     "functions without requiring mouse interaction."),
    ("1.1.2", None,
     "The interface shall be responsive and shall display correctly on screen widths "
     "from 1024px to 3840px without horizontal scrolling."),
    ("1.1.3", None,
     "The interface shall provide the following view modes for requirement lists:\n"
     "BULLET: Flat list sorted by requirement number\n"
     "BULLET: Hierarchical tree view\n"
     "BULLET: Filter view (filter by status, owner, priority)\n"
     "BULLET: Traceability matrix view"),
    ("1.2", "Business Logic",
     "The system shall enforce all business rules defined in the Business Rules "
     "Register (BRR-2024-001) without exception."),
    ("1.2.1", None,
     "The system shall prevent a requirement from being set to status 'Approved' "
     "unless all mandatory attributes have been populated."),
    ("1.2.2", None,
     "Mandatory attributes for approval shall include:\n"
     "BULLET: Title (non-empty string, max 200 characters)\n"
     "BULLET: Description (non-empty string)\n"
     "BULLET: Priority (one of: Critical, High, Medium, Low)\n"
     "BULLET: Owner (a valid user account)\n"
     "BULLET: Verification Method (one of: Test, Inspection, Analysis, Demonstration)"),
    ("1.2.3", None,
     "The system shall generate an audit log entry for every state transition "
     "of a requirement, recording the user, timestamp, previous state, new state, "
     "and an optional comment."),
    ("1.3", "Reporting",
     "The system shall provide a built-in reporting module with at minimum the "
     "standard reports defined in Annex B."),
    ("1.3.1", None,
     "All reports shall be exportable in the following formats:\n"
     "BULLET: PDF (using the organisation standard report template)\n"
     "BULLET: Microsoft Excel (.xlsx)\n"
     "BULLET: CSV (UTF-8 encoded)"),
    ("1.3.2", None,
     "Reports shall be generated on-demand and shall reflect the current live "
     "data at the moment the report is run."),
    ("1.3.3", None,
     "The system shall support scheduled report generation with delivery by "
     "email to a configured distribution list."),
]

SECTION_3 = [
    ("1", "Data Requirements",
     "All data stored and processed by the system shall comply with the "
     "organisation's Data Classification Policy and applicable data protection "
     "legislation."),
    ("1.1", "Data Storage",
     "All persistent data shall be stored in the organisation-approved relational "
     "database, which shall be hosted in the primary data centre."),
    ("1.1.1", None,
     "The database shall be configured with daily full backups and continuous "
     "transaction log backups retained for a minimum of 90 days."),
    ("1.1.2", None,
     "Data at rest shall be encrypted using AES-256 or stronger with key management "
     "performed by the enterprise key management service."),
    ("1.2", "Data Integrity",
     "The system shall implement controls to ensure the integrity of all stored data "
     "including referential integrity, constraint validation, and audit trails."),
    ("1.2.1", None,
     "The system shall perform referential integrity checks before committing any "
     "transaction that modifies parent-child relationships between artefacts."),
    ("1.2.2", None,
     "The system shall maintain an immutable audit trail for all modifications to "
     "requirements, links, and configuration settings."),
    ("1.2.3", None,
     "The audit trail shall record the following for each event:\n"
     "BULLET: Event type and timestamp\n"
     "BULLET: User identity (username and display name)\n"
     "BULLET: Source IP address\n"
     "BULLET: Object identifier and type\n"
     "BULLET: Previous and new values for changed attributes"),
]

ANNEX_A = [
    ("1", "Security Requirements",
     "All security requirements in this annex are mandatory and shall be "
     "implemented prior to any production deployment of the system."),
    ("1.1", "Authentication",
     "The system shall implement multi-factor authentication (MFA) as the default "
     "and mandatory authentication method for all user accounts."),
    ("1.1.1", None,
     "Supported second factors shall include at minimum:\n"
     "BULLET: Time-based one-time password (TOTP) via authenticator app\n"
     "BULLET: Hardware security key (FIDO2/WebAuthn)"),
    ("1.1.2", None,
     "The system shall enforce a minimum password complexity policy:\n"
     "BULLET: Minimum 14 characters\n"
     "BULLET: At least one uppercase, one lowercase, one digit, one special character\n"
     "BULLET: Not matching any of the previous 24 passwords"),
    ("1.1.3", None,
     "Service accounts shall use certificate-based authentication and shall not "
     "be permitted to use password-based authentication."),
    ("1.2", "Authorisation",
     "The system shall implement Role-Based Access Control (RBAC) with the principle "
     "of least privilege applied to all roles."),
    ("1.2.1", None,
     "Role assignments shall be reviewed by the system administrator no less than "
     "every 90 days and any inactive accounts shall be disabled."),
    ("1.2.2", None,
     "Access to sensitive data classifications shall require explicit role "
     "assignment and shall not be inherited from parent roles."),
    ("1.3", "Cryptography",
     "All cryptographic operations shall use algorithms and key lengths approved "
     "in the organisation's Cryptographic Standards document (SEC-STD-003)."),
    ("1.3.1", None,
     "Deprecated algorithms (MD5, SHA-1, DES, 3DES, RC4) shall not be used "
     "in any new system component."),
    ("1.3.2", None,
     "TLS 1.3 shall be the minimum version for all external connections; "
     "TLS 1.2 is permitted for internal connections pending legacy system migration."),
    ("1.4", "Vulnerability Management",
     "The system shall be subject to regular security assessments as part of the "
     "organisation's vulnerability management programme."),
    ("1.4.1", None,
     "The system shall undergo a full penetration test prior to initial production "
     "deployment and annually thereafter."),
    ("1.4.2", None,
     "Critical and High severity findings from penetration tests and vulnerability "
     "scans shall be remediated within the following timeframes:\n"
     "BULLET: Critical — within 7 calendar days of identification\n"
     "BULLET: High — within 30 calendar days of identification\n"
     "BULLET: Medium — within 90 calendar days of identification"),
]

ANNEX_B = [
    ("1", "Performance Requirements",
     "The performance requirements in this annex define the measurable service "
     "levels that the system shall achieve under normal and peak load conditions."),
    ("1.1", "Response Time",
     "The system shall meet the following response time requirements under normal "
     "load conditions (defined as up to 200 concurrent active users)."),
    ("1.1.1", None,
     "Page load time for all primary user interface screens shall not exceed 2 "
     "seconds at the 95th percentile."),
    ("1.1.2", None,
     "API responses for read operations shall complete within 500ms at the 95th "
     "percentile and within 2 seconds at the 99th percentile."),
    ("1.1.3", None,
     "Report generation for standard reports covering up to 10,000 requirements "
     "shall complete within 30 seconds."),
    ("1.2", "Throughput",
     "The system shall support a minimum throughput of 1,000 requirement "
     "read/write operations per minute under normal load."),
    ("1.2.1", None,
     "Batch import operations shall support ingestion of at least 5,000 "
     "requirements per hour without degradation of interactive user performance."),
    ("1.3", "Availability",
     "The system shall achieve an availability of 99.5% measured over any "
     "rolling 30-day period, excluding planned maintenance windows."),
    ("1.3.1", None,
     "Planned maintenance windows shall not exceed 4 hours per calendar month "
     "and shall be scheduled outside core business hours (08:00–18:00 local time, "
     "Monday to Friday)."),
    ("1.3.2", None,
     "The system shall implement automatic failover to the secondary data centre "
     "within 15 minutes of a primary data centre failure being detected."),
    ("1.4", "Scalability",
     "The system architecture shall support horizontal scaling to accommodate "
     "growth in user numbers and data volumes without architectural rework."),
    ("1.4.1", None,
     "The system shall scale to support at least 2,000 concurrent active users "
     "by adding application server capacity without database schema changes."),
    ("1.4.2", None,
     "Data storage shall scale to accommodate a minimum of 1,000,000 requirement "
     "artefacts without performance degradation beyond the thresholds in 1.1."),
]

SECTIONS = [
    ("Section 1 — System Overview", SECTION_1),
    ("Section 2 — Functional Requirements", SECTION_2),
    ("Section 3 — Data Requirements", SECTION_3),
    ("Annex A — Security Requirements", ANNEX_A),
    ("Annex B — Performance Requirements", ANNEX_B),
]


def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("T", parent=styles["Heading1"], fontSize=18,
                                 spaceAfter=6, fontName="Helvetica-Bold", alignment=TA_CENTER)
    sub_style = ParagraphStyle("S", parent=styles["Normal"], fontSize=11,
                               spaceAfter=4, alignment=TA_CENTER)
    section_banner = ParagraphStyle("SB", parent=styles["Heading1"], fontSize=13,
                                    spaceBefore=12, spaceAfter=8,
                                    fontName="Helvetica-Bold",
                                    textColor=colors.HexColor("#1a3a5c"),
                                    borderPad=4)
    toc_style = ParagraphStyle("TOC", parent=styles["Normal"], fontSize=10,
                               fontName="Helvetica", spaceAfter=3)
    req_style = ParagraphStyle("R", parent=styles["Normal"], fontSize=10,
                               fontName="Helvetica", leading=14, spaceAfter=5)
    bullet_style = ParagraphStyle("BL", parent=styles["Normal"], fontSize=10,
                                  fontName="Helvetica", leading=13, spaceAfter=2,
                                  leftIndent=1.2 * cm)

    story = []

    # Title page
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph(DOC_TITLE, title_style))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(DOC_NUM, sub_style))
    story.append(Paragraph("Version 2.1 | INTERNAL USE ONLY", sub_style))
    story.append(PageBreak())

    # Table of Contents — entries match SECTION_PATTERN but should not become reqs
    story.append(Paragraph("Table of Contents", styles["Heading1"]))
    story.append(Spacer(1, 0.3 * cm))
    for num, title in TOC_ENTRIES:
        dots = "." * max(5, 60 - len(num) - len(title))
        story.append(Paragraph(f"{num}&nbsp;&nbsp;{title}{dots}1", toc_style))
    story.append(PageBreak())

    # Requirements sections
    for section_name, reqs in SECTIONS:
        story.append(Paragraph(section_name, section_banner))
        story.append(Spacer(1, 0.2 * cm))

        for req_num, _heading, text in reqs:
            level = req_num.count(".") + 1 if "." in req_num else 1
            indent = (level - 1) * 0.5 * cm

            r_style = ParagraphStyle(
                f"RL{level}",
                parent=req_style,
                leftIndent=indent,
                fontName="Helvetica-Bold" if level == 1 else "Helvetica",
            )

            # Split out BULLET: lines
            lines = text.split("\n")
            main_text = lines[0]
            bullets = [l.replace("BULLET: ", "") for l in lines[1:] if l.startswith("BULLET:")]

            story.append(Paragraph(f"<b>{req_num}</b>&nbsp;&nbsp;{main_text}", r_style))

            for b in bullets:
                story.append(Paragraph(f"• {b}", bullet_style))

        story.append(Spacer(1, 0.5 * cm))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Created: {output_path}")


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    build_pdf(OUTPUT_PATH)
