"""
Sample PDF Generator — Doc 6: Defence Specification Style
~90 requirements across three annexes with restarted numbering.

Key challenges tested:
  - "OFFICIAL SENSITIVE" classification marking repeated in header AND footer
    on every page — high-volume noise that must be filtered.
  - Annex A / Annex B / Annex C structure — each annex restarts at requirement
    1.1, so the section column in the CSV is critical for disambiguation.
  - Deep nesting up to 6 levels (1.1.1.1.1.1).
  - Long requirement text wrapping across multiple lines.
  - Section divider pages between annexes.
  - Mixed formal and technical language (government style).
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../sample-pdfs/sample_06_defence.pdf")
PAGE_W, PAGE_H = A4

CLASSIFICATION = "OFFICIAL SENSITIVE"
DOC_REF = "DEF-SRD-2024-006"
DOC_TITLE = "System Requirements Document — Integrated Command and Control Platform"


def header_footer(canvas, doc):
    """Repeat classification marking in header and footer on every page."""
    canvas.saveState()
    # Classification header
    canvas.setFillColor(colors.HexColor("#8b0000"))
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 1.0 * cm, CLASSIFICATION)
    # Header rule + doc ref
    canvas.setFillColor(colors.HexColor("#333333"))
    canvas.setFont("Helvetica", 8)
    canvas.line(2.5 * cm, PAGE_H - 1.6 * cm, PAGE_W - 2.5 * cm, PAGE_H - 1.6 * cm)
    canvas.drawString(2.5 * cm, PAGE_H - 2.1 * cm, DOC_REF)
    canvas.drawRightString(PAGE_W - 2.5 * cm, PAGE_H - 2.1 * cm, "Issue 1.0")
    # Footer rule + page number
    canvas.line(2.5 * cm, 2.0 * cm, PAGE_W - 2.5 * cm, 2.0 * cm)
    canvas.drawString(2.5 * cm, 1.5 * cm, f"Page {doc.page}")
    canvas.drawRightString(PAGE_W - 2.5 * cm, 1.5 * cm, DOC_REF)
    # Classification footer
    canvas.setFillColor(colors.HexColor("#8b0000"))
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawCentredString(PAGE_W / 2, 0.7 * cm, CLASSIFICATION)
    canvas.restoreState()


def annex_divider(canvas, doc, annex_title):
    """Full-page divider for each annex."""
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#1a3a5c"))
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 24)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 1 * cm, annex_title)
    canvas.setFont("Helvetica", 11)
    canvas.setFillColor(colors.HexColor("#aaccee"))
    canvas.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 0.5 * cm, DOC_TITLE)
    canvas.setFillColor(colors.HexColor("#cc8888"))
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawCentredString(PAGE_W / 2, 2 * cm, CLASSIFICATION)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 2 * cm, CLASSIFICATION)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Requirements content — three annexes, each restarting at 1
# ---------------------------------------------------------------------------

ANNEX_A_REQS = [
    ("1", "Functional Requirements Overview",
     "This annex defines the functional requirements for the Integrated Command and "
     "Control (ICC) Platform. All requirements are mandatory unless explicitly "
     "stated otherwise. Requirements shall be verified by the method indicated in "
     "the Verification Method attribute."),
    ("1.1", "Command and Control Functions",
     "The system shall implement command and control functions that enable authorised "
     "operators to direct and monitor all assigned assets in real time."),
    ("1.1.1", None,
     "The system shall display the current operational status of all assets in the "
     "common operating picture (COP) with a maximum update latency of 2 seconds "
     "from the time of status change at the asset."),
    ("1.1.2", None,
     "The system shall provide a hierarchical command structure that mirrors the "
     "operational chain of command as defined in the current operational order."),
    ("1.1.2.1", None,
     "The command hierarchy shall be configurable by an operator with the System "
     "Administrator role and shall take effect within 60 seconds of configuration "
     "being saved."),
    ("1.1.2.2", None,
     "The system shall enforce that commands are only propagated downward through "
     "the command hierarchy and not laterally between units at the same echelon."),
    ("1.1.3", None,
     "The system shall record all commands issued, acknowledged, and executed, "
     "together with the issuing operator identity, timestamp, and asset "
     "acknowledgement timestamp, in a tamper-evident command log."),
    ("1.1.3.1", None,
     "The command log shall be stored in an append-only data structure and shall "
     "be replicated to the backup system within 5 seconds of each log entry being "
     "written."),
    ("1.1.3.1.1", None,
     "The replication channel shall use mutual TLS authentication and shall be "
     "monitored for availability; any replication failure shall generate a P1 "
     "alert within 30 seconds."),
    ("1.1.3.1.1.1", None,
     "The P1 alert shall be delivered simultaneously to the system duty officer "
     "display terminal, the operations room alarm panel, and the on-call engineer "
     "mobile device, and shall not be dismissible until acknowledged by a duty "
     "officer with an appropriate security clearance level."),
    ("1.2", "Situational Awareness",
     "The system shall aggregate situational awareness data from all connected "
     "sensor systems and present it in a fused, deduplicated common operating "
     "picture."),
    ("1.2.1", None,
     "The system shall accept data feeds from the following sensor categories and "
     "shall process each within the latency tolerance specified:"),
    ("1.2.2", None,
     "Duplicate tracks arising from overlapping sensor coverage shall be fused "
     "within 500ms of the second observation being received, using the track "
     "fusion algorithm specified in the System Design Document."),
    ("1.2.3", None,
     "The system shall permit an operator to manually correlate or de-correlate "
     "tracks and shall record the operator identity and timestamp of each manual "
     "correlation action."),
    ("1.3", "Mission Planning",
     "The system shall provide a mission planning capability enabling authorised "
     "planners to create, edit, and distribute operational plans."),
    ("1.3.1", None,
     "A mission plan shall contain at minimum: mission objective, execution timeline, "
     "asset assignments, rules of engagement reference, and designated communication "
     "channels."),
    ("1.3.2", None,
     "The mission planning module shall enforce version control such that each "
     "saved revision of a plan creates an immutable record accessible to authorised "
     "reviewers."),
    ("1.3.2.1", None,
     "The version history shall be accessible to any operator with at least "
     "Read-Only access to the plan and shall display the author, timestamp, "
     "and change summary for each revision."),
    ("1.3.2.1.1", None,
     "Change summaries shall be mandatory for any revision that modifies asset "
     "assignments, rules of engagement references, or the execution timeline by "
     "more than 30 minutes in either direction."),
    ("1.4", "Communication Management",
     "The system shall manage communications between all nodes in the command "
     "network with priority-based queuing and guaranteed delivery for critical "
     "message types."),
    ("1.4.1", None,
     "Critical messages (FLASH and IMMEDIATE precedence) shall be delivered "
     "within 5 seconds of transmission for all addressees within radio range "
     "or connected via primary data link."),
    ("1.4.2", None,
     "The system shall provide an offline message store-and-forward capability "
     "for addressees that are temporarily out of communication, with automatic "
     "delivery upon reconnection."),
]

ANNEX_B_REQS = [
    ("1", "Interface Requirements Overview",
     "This annex defines the interface requirements for all external and internal "
     "interfaces of the ICC Platform. Interfaces are categorised as: External "
     "(systems outside programme boundary), Internal (between subsystems within "
     "the programme boundary), and Operator (human-machine interfaces)."),
    ("1.1", "External System Interfaces",
     "The system shall implement external interfaces to all systems listed in the "
     "Interface Control Document (ICD-ICC-2024-001) using the protocols and data "
     "formats specified therein."),
    ("1.1.1", None,
     "Each external interface shall have a defined service level agreement covering "
     "minimum bandwidth, maximum latency, and availability, as specified in the ICD."),
    ("1.1.2", None,
     "The system shall monitor the health of each external interface and shall "
     "raise an alert to the duty operator if an interface falls below its defined "
     "service level thresholds."),
    ("1.1.2.1", None,
     "Health monitoring data for external interfaces shall be retained for 30 days "
     "and shall be available to system administrators for capacity planning and "
     "incident investigation."),
    ("1.2", "Internal Subsystem Interfaces",
     "Internal interfaces between ICC Platform subsystems shall comply with the "
     "subsystem interface specifications defined in the System Design Document (SDD)."),
    ("1.2.1", None,
     "All internal interfaces shall use the platform-standard message bus "
     "(Apache Kafka v3.x) and shall conform to the canonical message schemas "
     "defined in the Schema Registry."),
    ("1.2.2", None,
     "Each subsystem shall implement a health endpoint that returns a JSON status "
     "object within 200ms, conforming to the platform health-check schema."),
    ("1.2.2.1", None,
     "The health endpoint shall be polled by the platform orchestration layer at "
     "least every 30 seconds and the results shall be surfaced in the platform "
     "operations dashboard."),
    ("1.3", "Operator Interface",
     "The operator interface shall be designed for use in a high-workload, time-"
     "critical operational environment where errors may have significant consequences."),
    ("1.3.1", None,
     "The interface shall apply the following human factors principles throughout:"),
    ("1.3.2", None,
     "Critical actions (issue command, approve mission plan, modify rules of engagement) "
     "shall require a mandatory confirmation step before execution. The confirmation "
     "dialogue shall state the action to be performed and its immediate consequences."),
    ("1.3.3", None,
     "The interface shall provide keyboard shortcuts for all primary operator "
     "functions and shall make these shortcuts visible in the interface at all times."),
    ("1.4", "Data Exchange Formats",
     "All data exchanged with external systems shall use the formats specified "
     "in the ICD and shall conform to relevant NATO STANAG data standards where "
     "applicable."),
    ("1.4.1", None,
     "Track data exchanged via the tactical data link interface shall conform "
     "to STANAG 5516 Link 16 message format."),
    ("1.4.2", None,
     "Position reporting data shall conform to STANAG 4677 Friendly Force "
     "Tracking (FFT) message format."),
    ("1.4.2.1", None,
     "Where a connected system cannot produce STANAG 4677 compliant output, "
     "the system shall implement a translation layer as specified in the relevant "
     "Legacy Interface Supplement."),
]

ANNEX_C_REQS = [
    ("1", "Performance Requirements Overview",
     "The performance requirements in this annex are binding service level "
     "requirements. Failure to meet any mandatory performance requirement "
     "constitutes a non-conformance and shall be raised as a defect in the "
     "project issue register."),
    ("1.1", "Latency Requirements",
     "The system shall meet the following end-to-end latency requirements for "
     "data flowing from sensor input to operator display."),
    ("1.1.1", None,
     "Track data from all sensor inputs shall be processed and displayed on the "
     "COP within 2 seconds of receipt at the system ingress point, measured end-to-end "
     "under normal load conditions."),
    ("1.1.2", None,
     "Command messages issued by an operator shall be transmitted to the target "
     "asset command receiver within 500ms of the operator pressing the 'Send' button, "
     "measured under normal RF conditions."),
    ("1.1.3", None,
     "The mission planning module shall render a mission plan containing up to 500 "
     "waypoints and 200 asset assignments within 3 seconds of opening."),
    ("1.2", "Throughput Requirements",
     "The system shall sustain the following minimum throughput levels under peak "
     "operational load, defined as 150 simultaneous operator sessions with all "
     "subsystems active."),
    ("1.2.1", None,
     "Track processing throughput: minimum 10,000 track updates per minute."),
    ("1.2.2", None,
     "Command message throughput: minimum 500 command messages per minute system-wide."),
    ("1.2.3", None,
     "COP display refresh rate: minimum 1 Hz (one full screen update per second) "
     "for all connected operator terminals under peak load."),
    ("1.3", "Availability and Resilience",
     "The system shall achieve a minimum operational availability of 99.9% measured "
     "over any 30-day operational period."),
    ("1.3.1", None,
     "The system shall implement N+1 redundancy for all critical subsystems. "
     "The failure of any single component shall not result in loss of any primary "
     "operational capability."),
    ("1.3.2", None,
     "Automatic failover between redundant components shall complete within 30 "
     "seconds of a primary component failure being detected by the health monitoring "
     "subsystem."),
    ("1.3.2.1", None,
     "Failover events shall not result in loss of any command log entries or mission "
     "plan data. In-flight transactions interrupted by a failover shall be recovered "
     "using the transaction log within 60 seconds of failover completion."),
    ("1.4", "Capacity",
     "The system shall be designed to accommodate the following capacity requirements "
     "for an initial 5-year operational life."),
    ("1.4.1", None,
     "Maximum concurrent operator sessions: 200."),
    ("1.4.2", None,
     "Maximum tracked entities in the common operating picture: 50,000 simultaneous "
     "tracks without performance degradation below the thresholds specified in 1.1."),
    ("1.4.3", None,
     "Maximum stored mission plans: 10,000 plans with full version history retained "
     "for the operational life of the system."),
    ("1.4.3.1", None,
     "Mission plan storage shall be designed to scale beyond 10,000 plans by "
     "adding storage capacity without architectural change, up to a maximum of "
     "100,000 plans."),
    ("1.4.3.1.1", None,
     "Scaling beyond 10,000 plans shall be achievable without system downtime "
     "using the storage expansion procedures defined in the Operations Manual."),
    ("1.4.3.1.1.1", None,
     "The Operations Manual storage expansion procedure shall be tested and "
     "validated as part of the pre-deployment acceptance test, with evidence of "
     "a successful test retained in the project quality records."),
]

ANNEXES = [
    ("Annex A — Functional Requirements", ANNEX_A_REQS),
    ("Annex B — Interface Requirements", ANNEX_B_REQS),
    ("Annex C — Performance Requirements", ANNEX_C_REQS),
]


def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=3.0 * cm,
        bottomMargin=3.0 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("T", parent=styles["Heading1"], fontSize=16,
                                 spaceAfter=6, fontName="Helvetica-Bold",
                                 alignment=TA_CENTER)
    subtitle_style = ParagraphStyle("ST", parent=styles["Normal"], fontSize=10,
                                    spaceAfter=4, alignment=TA_CENTER,
                                    textColor=colors.HexColor("#555555"))
    annex_header = ParagraphStyle("AH", parent=styles["Heading1"], fontSize=14,
                                  spaceBefore=0, spaceAfter=10,
                                  fontName="Helvetica-Bold",
                                  textColor=colors.white,
                                  backColor=colors.HexColor("#1a3a5c"),
                                  borderPad=6)
    req_style = ParagraphStyle("R", parent=styles["Normal"], fontSize=10,
                               fontName="Helvetica", leading=14, spaceAfter=5)

    story = []

    # Title page
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(f"<font color='#8b0000'><b>{CLASSIFICATION}</b></font>",
                            ParagraphStyle("CL", parent=styles["Normal"], fontSize=11,
                                           alignment=TA_CENTER, spaceAfter=16)))
    story.append(Paragraph(DOC_TITLE, title_style))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(DOC_REF, subtitle_style))
    story.append(Paragraph("Issue 1.0 — RESTRICTED CIRCULATION", subtitle_style))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        "This document is issued under authority of the Programme Director. "
        "It contains requirements that shall be met by the contractor. "
        "Contents are classified as " + CLASSIFICATION + " and must not be "
        "disclosed to persons without appropriate authorisation and need-to-know.",
        ParagraphStyle("D", parent=styles["Normal"], fontSize=9,
                       textColor=colors.HexColor("#555555"))
    ))
    story.append(PageBreak())

    # Annexes
    for annex_name, reqs in ANNEXES:
        story.append(Paragraph(annex_name, annex_header))
        story.append(Spacer(1, 0.3 * cm))

        for req_num, _heading, text in reqs:
            level = req_num.count(".") + 1 if "." in req_num else 1
            indent = (level - 1) * 0.4 * cm

            r = ParagraphStyle(
                f"RL{level}",
                parent=req_style,
                leftIndent=indent,
                fontName="Helvetica-Bold" if level <= 2 else "Helvetica",
                fontSize=10 if level <= 2 else 9,
            )
            story.append(Paragraph(f"<b>{req_num}</b>&nbsp;&nbsp;{text}", r))

        story.append(Spacer(1, 0.8 * cm))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Created: {output_path}")


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    build_pdf(OUTPUT_PATH)
