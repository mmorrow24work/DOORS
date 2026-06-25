"""
Sample PDF Generator — Doc 5: Bullet-Heavy Requirements
~30 requirements, most with 2-6 bullet sub-items.

Key challenges tested:
  - Three mixed bullet styles: • (U+2022 rendered as CID), - (hyphen-minus), – (en dash)
  - Bullet markers placed in a narrow table column separate from the text column,
    causing pdfplumber to sometimes extract marker and text on different y-bands
    (the "orphaned bullet marker" scenario)
  - Requirements where the entire substantive content is in the bullet list
  - Requirements that mix free-text prose and bulleted sub-items
  - CID glyph reference (cid:127): reportlab embeds U+2022 in Helvetica without
    a ToUnicode map entry, so pdfplumber extracts it as (cid:127) rather than •
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_LEFT

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../sample-pdfs/sample_05_bullets.pdf")
PAGE_W, PAGE_H = A4
DOC_NUM = "SEC-CTL-005"
DOC_TITLE = "Platform Security Controls Specification"


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.HexColor("#c00000"))
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 1.6 * cm, "CONFIDENTIAL")
    canvas.setFillColor(colors.HexColor("#444444"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2.5 * cm, PAGE_H - 2.0 * cm, DOC_NUM)
    canvas.drawRightString(PAGE_W - 2.5 * cm, PAGE_H - 2.0 * cm, DOC_TITLE)
    canvas.line(2.5 * cm, PAGE_H - 2.2 * cm, PAGE_W - 2.5 * cm, PAGE_H - 2.2 * cm)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.HexColor("#c00000"))
    canvas.drawCentredString(PAGE_W / 2, 1.2 * cm, "CONFIDENTIAL")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#444444"))
    canvas.drawRightString(PAGE_W - 2.5 * cm, 1.6 * cm, f"Page {doc.page}")
    canvas.line(2.5 * cm, 1.9 * cm, PAGE_W - 2.5 * cm, 1.9 * cm)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Bullet styles to cycle through — tests all four variants
# ---------------------------------------------------------------------------
BULLET_STYLES = ["•", "-", "–", "-"]  # •(→CID), -, –, - (▪ omitted: unreliable in Helvetica)


def bullets(items, style_index=0):
    """Return list of (marker, text) tuples cycling through bullet styles."""
    marker = BULLET_STYLES[style_index % len(BULLET_STYLES)]
    return [(marker, item) for item in items]


# ---------------------------------------------------------------------------
# Requirements content
# ---------------------------------------------------------------------------

REQUIREMENTS = [
    # Section 1 — Identity and Access Management
    ("1", "Identity and Access Management",
     "The system shall implement identity and access management controls "
     "in accordance with ISO/IEC 27001:2022 Annex A controls 5.15 through 5.18.",
     [], 0),
    ("1.1", "User Provisioning",
     "The system shall enforce a formal user provisioning process that includes "
     "approval, documentation, and periodic review.",
     ["New accounts shall require line manager and information security approval before activation.",
      "Account provisioning requests shall be logged with the requester, approver, timestamp, and business justification.",
      "Accounts shall be provisioned with the minimum permissions required for the stated business purpose."],
     0),
    ("1.1.1", None,
     "The provisioning workflow shall enforce the following sequence without exception:",
     ["Request submitted by requester via the identity management portal.",
      "Automatic policy check against role catalogue.",
      "Line manager approval via email workflow.",
      "Information security review for privileged access requests.",
      "Account creation and confirmation email to requester."],
     1),
    ("1.1.2", None,
     "The system shall not permit self-approval of access requests under any circumstances.",
     [], 0),
    ("1.2", "User Deprovisioning",
     "The system shall implement automated deprovisioning to ensure timely removal "
     "of access when no longer required.",
     ["Accounts shall be disabled automatically upon receipt of a leaver notification from HR.",
      "Disabled accounts shall be fully deleted after 90 days.",
      "Access tokens and API keys associated with a disabled account shall be revoked immediately."],
     2),
    ("1.2.1", None,
     "The deprovisioning process shall complete within the following timeframes after trigger:",
     ["Standard leavers: account disabled within 1 business day of the leaver date.",
      "Disciplinary terminations: account disabled within 1 hour of HR notification.",
      "Contractor off-boarding: access removed on or before the contract end date."],
     3),
    ("1.3", "Privileged Access Management",
     "Privileged access (administrative, service, and system accounts) shall be "
     "subject to additional controls beyond those applied to standard user accounts.",
     ["Privileged accounts shall be distinct from standard user accounts and shall not be used for day-to-day activities.",
      "All privileged session activity shall be recorded using the organisation-approved privileged access management (PAM) tool.",
      "Privileged credentials shall be rotated at least every 90 days and immediately after any suspected compromise."],
     0),
    ("1.3.1", None,
     "Break-glass emergency accounts shall be subject to the following controls:",
     ["Credentials shall be stored in a sealed physical envelope in the information security safe.",
      "Use of a break-glass account shall automatically trigger an incident in the SIEM.",
      "Credentials shall be changed immediately after any use of a break-glass account.",
      "Break-glass account use shall be reviewed by the CISO within 24 hours."],
     1),
    # Section 2 — Network Security Controls
    ("2", "Network Security Controls",
     "The system shall implement network security controls to protect all components "
     "from unauthorised network access and data interception.",
     [], 0),
    ("2.1", "Network Segmentation",
     "All system components shall be deployed within appropriately segmented "
     "network zones based on their function and data classification.",
     ["Presentation tier (web servers) — DMZ network zone.",
      "Application tier (app servers) — Application network zone.",
      "Data tier (databases, file stores) — Data network zone.",
      "Management components — Out-of-band management network zone."],
     2),
    ("2.1.1", None,
     "Inter-zone traffic shall be controlled by the following rules:",
     ["All inter-zone traffic shall pass through a next-generation firewall with application-layer inspection.",
      "Default-deny rules shall be applied and only explicitly permitted traffic shall flow between zones.",
      "Firewall rules shall be reviewed and re-certified every 6 months."],
     3),
    ("2.2", "Perimeter Protection",
     "The system shall implement perimeter protection controls to prevent "
     "unauthorised external access.",
     [], 0),
    ("2.2.1", None,
     "The following perimeter controls shall be deployed and maintained:",
     ["Web Application Firewall (WAF) in front of all public-facing endpoints.",
      "DDoS mitigation service with automatic traffic scrubbing for attacks exceeding 1 Gbps.",
      "Intrusion Prevention System (IPS) inline on all external network paths.",
      "Rate limiting on all public API endpoints (max 100 requests/minute per source IP by default)."],
     0),
    ("2.3", "Encryption in Transit",
     "All data transmitted between system components and between the system and "
     "external parties shall be encrypted in transit.",
     ["TLS 1.3 shall be used for all external connections.",
      "TLS 1.2 with strong cipher suites is permitted for internal service-to-service communication pending migration.",
      "Unencrypted protocols (HTTP, FTP, Telnet, SNMP v1/v2) shall not be used on any production network path."],
     1),
    # Section 3 — Endpoint Protection
    ("3", "Endpoint and Server Protection",
     "The system shall implement endpoint and server protection controls on all "
     "components deployed in the production environment.",
     [], 0),
    ("3.1", "Antimalware",
     "All servers and endpoints shall run organisation-approved antimalware software "
     "with up-to-date definitions.",
     ["Signature updates shall be applied within 4 hours of release.",
      "Scheduled full-system scans shall run at least weekly outside business hours.",
      "Real-time scanning shall be enabled at all times and shall not be disabled without change management approval."],
     2),
    ("3.2", "Endpoint Detection and Response",
     "The system shall deploy Endpoint Detection and Response (EDR) tooling on all "
     "servers within the production environment.",
     ["– Defender for Endpoint",
      "– Defender for Servers",
      "– Defender for Cloud",
      "– Threat intelligence, automated response and advanced reporting"],
     3),
    ("3.2.1", None,
     "EDR alerts at Critical or High severity shall be triaged within the following timeframes:",
     ["Critical — acknowledged within 15 minutes, contained within 1 hour.",
      "High — acknowledged within 1 hour, contained within 4 hours.",
      "Medium — acknowledged within 4 hours, remediated within 24 hours."],
     0),
    ("3.3", "Patch Management",
     "All system components shall be subject to the organisation's patch management "
     "process with the following mandatory timelines.",
     [], 0),
    ("3.3.1", None,
     "Operating system and middleware patches shall be applied within the following timeframes:",
     ["Critical (CVSS ≥ 9.0) — emergency patching within 72 hours of vendor release.",
      "High (CVSS 7.0–8.9) — patching within 14 days of vendor release.",
      "Medium (CVSS 4.0–6.9) — patching within 30 days.",
      "Low (CVSS < 4.0) — patching in the next scheduled maintenance window."],
     1),
    # Section 4 — Logging and Monitoring
    ("4", "Logging and Monitoring",
     "The system shall implement comprehensive logging and monitoring to support "
     "security incident detection, investigation, and regulatory compliance.",
     [], 0),
    ("4.1", "Security Event Logging",
     "The following events shall be logged by all system components and forwarded "
     "to the centralised SIEM within 60 seconds of occurrence.",
     [], 0),
    ("4.1.1", None,
     "Authentication events to be logged include:",
     ["▪ Successful and failed login attempts (username, timestamp, source IP, MFA result).",
      "▪ Account lockouts.",
      "▪ Password changes and resets.",
      "▪ MFA bypass or fallback use."],
     2),
    ("4.1.2", None,
     "Authorisation events to be logged include:",
     ["▪ Access grants and denials for sensitive data.",
      "▪ Privilege escalation events.",
      "▪ Role assignment changes.",
      "▪ Policy rule changes."],
     3),
    ("4.2", "Log Retention",
     "Security event logs shall be retained in accordance with the following policy.",
     ["Online (queryable) retention: 90 days minimum.",
      "Archived retention: 12 months minimum.",
      "Long-term archive (for regulated data): 7 years minimum."],
     0),
    ("4.3", "Security Monitoring",
     "The SIEM shall be configured with detection rules covering at minimum the "
     "following threat scenarios.",
     ["Brute-force and credential stuffing attacks.",
      "Anomalous login times or geographic locations.",
      "Lateral movement indicators.",
      "Data exfiltration patterns (large outbound transfers).",
      "Ransomware indicators (high-volume file modifications)."],
     1),
    # Section 5 — Incident Response
    ("5", "Incident Response",
     "The system shall support the organisation's incident response capability "
     "through automated detection, alerting, and containment functions.",
     [], 0),
    ("5.1", "Automated Response",
     "The system shall implement automated response actions for specific "
     "high-confidence threat scenarios without requiring manual authorisation.",
     ["Automatically isolate a compromised endpoint from the network when EDR confidence exceeds 90%.",
      "Automatically revoke active sessions for an account when credential compromise is confirmed.",
      "Automatically block a source IP exhibiting brute-force behaviour after 10 failed attempts in 60 seconds."],
     2),
    ("5.2", "Incident Classification",
     "Security incidents shall be classified using the following severity levels, "
     "each with defined response timelines.",
     ["P1 Critical: system breach with data exfiltration confirmed or suspected.",
      "P2 High: active attack in progress but contained within a single system.",
      "P3 Medium: suspicious activity requiring investigation.",
      "P4 Low: policy violation or anomaly without evidence of attack."],
     3),
    ("5.2.1", None,
     "Incident response timelines by severity:",
     ["P1 Critical — CISO notification within 30 minutes; regulatory authority notification within 72 hours.",
      "P2 High — Incident Response Team assembled within 1 hour.",
      "P3 Medium — investigation commenced within 4 hours.",
      "P4 Low — reviewed in the next scheduled security operations meeting."],
     0),
]


def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.8 * cm,
        bottomMargin=2.8 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("T", parent=styles["Heading1"], fontSize=16,
                                 spaceAfter=8, fontName="Helvetica-Bold")
    req_normal = ParagraphStyle("RN", parent=styles["Normal"], fontSize=10,
                                fontName="Helvetica", leading=14, spaceAfter=4)
    req_bold = ParagraphStyle("RB", parent=styles["Normal"], fontSize=10,
                              fontName="Helvetica-Bold", leading=14, spaceAfter=4)

    story = []

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(DOC_TITLE, title_style))
    story.append(Paragraph(f"Document Reference: {DOC_NUM}", styles["Normal"]))
    story.append(Spacer(1, 0.8 * cm))

    current_section_num = None

    for req_num, heading, text, bullet_items, bullet_style_idx in REQUIREMENTS:
        level = req_num.count(".") + 1 if "." in req_num else 1
        indent = (level - 1) * 0.5 * cm

        r_style = ParagraphStyle(
            f"L{level}",
            parent=req_bold if level == 1 else req_normal,
            leftIndent=indent,
        )

        story.append(Paragraph(f"<b>{req_num}</b>&nbsp;&nbsp;{text}", r_style))

        # Bullet items rendered in a two-column table to stress pdfplumber
        # y-coordinate extraction: bullet marker column (narrow) + text column (wide)
        if bullet_items:
            marker = BULLET_STYLES[bullet_style_idx % len(BULLET_STYLES)]
            table_data = [[marker, item] for item in bullet_items]
            bullet_table = Table(
                table_data,
                colWidths=[0.6 * cm, 12.5 * cm],
                hAlign="LEFT",
            )
            bullet_table.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), indent + 0.4 * cm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("FONT", (0, 0), (0, -1), "Helvetica", 10),
                ("FONT", (1, 0), (1, -1), "Helvetica", 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(bullet_table)

        story.append(Spacer(1, 0.15 * cm))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Created: {output_path}")


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    build_pdf(OUTPUT_PATH)
