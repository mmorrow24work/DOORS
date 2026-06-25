"""
Sample PDF Generator — Doc 7: Requirements Table (module-style)

Simulates a client document whose requirements are stored in a table rather
than numbered flowing paragraphs.  The table uses the column layout:

  Module Requirement ID | Source of Requirement | Module Requirement Acceptance Criterion | Rationale/Supporting information

This is the exact structure the pdfplumber script must handle via
TABLE_EXTRACTION_ENABLED and TABLE_COLUMN_MAP.
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

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../sample-pdfs/sample_07_table.pdf")
PAGE_W, PAGE_H = A4
DOC_NUM = "SEC-IF-007"
DOC_TITLE = "Interface Control Document — Module Requirements"


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.HexColor("#004080"))
    canvas.drawString(2.5 * cm, PAGE_H - 1.8 * cm, DOC_NUM)
    canvas.drawRightString(PAGE_W - 2.5 * cm, PAGE_H - 1.8 * cm, DOC_TITLE)
    canvas.line(2.5 * cm, PAGE_H - 2.1 * cm, PAGE_W - 2.5 * cm, PAGE_H - 2.1 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#444444"))
    canvas.drawCentredString(PAGE_W / 2, 1.3 * cm, f"Page {doc.page}")
    canvas.line(2.5 * cm, 1.8 * cm, PAGE_W - 2.5 * cm, 1.8 * cm)
    canvas.restoreState()


REQS = [
    # (id, source, criterion_text, rationale)
    (
        "MR-001",
        "SYS-SPEC-001 §3.1",
        "The module shall accept digital input signals in the range 0 V to 3.3 V "
        "with a maximum input impedance of 10 kΩ.",
        "Compatibility with existing 3.3 V logic families in the platform.",
    ),
    (
        "MR-002",
        "SYS-SPEC-001 §3.2",
        "The module shall provide galvanic isolation of at least 1500 V AC RMS "
        "between input and output circuits.",
        "Safety requirement to protect downstream logic from power-line transients.",
    ),
    (
        "MR-003",
        "SYS-SPEC-002 §4.1",
        "The module shall operate within the temperature range −40 °C to +85 °C "
        "without performance degradation.",
        "Deployed in outdoor enclosures subject to wide ambient temperature variation.",
    ),
    (
        "MR-004",
        "SYS-SPEC-002 §4.2",
        "The module shall maintain its rated accuracy after 1000 thermal cycles "
        "from −40 °C to +85 °C.",
        "Long-term reliability requirement for 10-year service life.",
    ),
    (
        "MR-005",
        "SYS-SPEC-003 §2.1",
        "The module shall communicate over CAN bus at 500 kbit/s in accordance "
        "with ISO 11898-2.",
        "CAN is the standard bus for this vehicle platform; 500 kbit/s is mandated by "
        "the platform integration specification.",
    ),
    (
        "MR-006",
        "SYS-SPEC-003 §2.2",
        "The module shall respond to a CAN wake-up frame within 5 ms of receipt.",
        "Response latency budget allocated by the system power-management specification.",
    ),
    (
        "MR-007",
        "SYS-SPEC-004 §5.1",
        "The module firmware shall be updateable in the field via the CAN bootloader "
        "interface without removal from the enclosure.",
        "Reduces field maintenance cost; a physical removal risk was identified in "
        "the maintenance hazard analysis.",
    ),
    (
        "MR-008",
        "SYS-SPEC-004 §5.2",
        "The module shall report a CRC failure and revert to the previous firmware "
        "image if a firmware update checksum does not match.",
        "Prevents bricking of deployed units due to corrupted update packages.",
    ),
    (
        "MR-009",
        "SYS-SPEC-005 §6.1",
        "The module shall draw no more than 150 mA from the 5 V supply rail under "
        "maximum load conditions.",
        "Power budget constraint allocated in the system power distribution analysis.",
    ),
    (
        "MR-010",
        "SYS-SPEC-005 §6.2",
        "The module shall tolerate supply voltage variations from 4.5 V to 5.5 V "
        "without entering an error state.",
        "Accounts for voltage drop across connectors and wiring harness under "
        "worst-case resistance.",
    ),
    (
        "MR-011",
        "SYS-SPEC-006 §7.1",
        "The module shall conform to IPC-A-610 Class 3 workmanship standards for "
        "all solder joints and component placements.",
        "Class 3 is required for safety-critical automotive applications per the "
        "quality assurance plan.",
    ),
    (
        "MR-012",
        "SYS-SPEC-006 §7.2",
        "The module shall pass EMC testing to CISPR 25 Class 5 limits for radiated "
        "and conducted emissions.",
        "Regulatory and customer requirement for use in passenger vehicles.",
    ),
]


def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=3.0 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_s = ParagraphStyle("T", parent=styles["Heading1"], fontSize=14,
                             fontName="Helvetica-Bold", spaceAfter=6)
    section_s = ParagraphStyle("S", parent=styles["Heading2"], fontSize=11,
                               fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=10)
    body_s = ParagraphStyle("B", parent=styles["Normal"], fontSize=9,
                            fontName="Helvetica", leading=12)
    cell_s = ParagraphStyle("C", parent=styles["Normal"], fontSize=8,
                            fontName="Helvetica", leading=10)
    hdr_s = ParagraphStyle("H", parent=styles["Normal"], fontSize=8,
                           fontName="Helvetica-Bold", leading=10,
                           textColor=colors.white)

    story = []

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(DOC_TITLE, title_s))
    story.append(Paragraph(f"Document Reference: {DOC_NUM}", body_s))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("1  Introduction", section_s))
    story.append(Paragraph(
        "This document specifies the module-level requirements for the Interface "
        "Control Module (ICM).  Requirements are captured in tabular form with the "
        "acceptance criterion and rationale for each requirement.",
        body_s,
    ))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("2  Module Requirements", section_s))
    story.append(Paragraph(
        "The following table defines all module requirements.  Each row constitutes "
        "a single traceable requirement.",
        body_s,
    ))
    story.append(Spacer(1, 0.25 * cm))

    col_widths = [2.2 * cm, 2.6 * cm, 7.0 * cm, 5.0 * cm]

    # Header row — multi-line to simulate the exact wrapping in the client document
    header_cells = [
        Paragraph("Module\nRequirement\nID", hdr_s),
        Paragraph("Source of\nRequirement", hdr_s),
        Paragraph("Module Requirement\nAcceptance Criterion", hdr_s),
        Paragraph("Rationale/\nSupporting\ninformation", hdr_s),
    ]

    data = [header_cells]
    for req_id, source, criterion, rationale in REQS:
        data.append([
            Paragraph(req_id, cell_s),
            Paragraph(source, cell_s),
            Paragraph(criterion, cell_s),
            Paragraph(rationale, cell_s),
        ])

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#004080")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  8),
        ("ALIGN",        (0, 0), (-1, 0),  "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF4FB")]),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("FONTSIZE",     (0, 1), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("3  Verification Summary", section_s))
    story.append(Paragraph(
        "Each requirement in Section 2 shall be verified by test in accordance with "
        "the Module Verification Plan (MVP-ICM-001).  Traceability between requirements "
        "and verification activities is maintained in the Requirements Traceability Matrix.",
        body_s,
    ))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Created: {output_path}")


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    build_pdf(OUTPUT_PATH)
