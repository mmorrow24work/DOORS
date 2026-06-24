"""
Sample PDF Generator — Doc 3: Complex / High Noise
100 requirements with multiple visual challenges:
- Mixed fonts (Helvetica headings, Courier body text for some sections)
- Inline notes / annotations embedded between requirements
- A watermark-style diagonal text on each page
- Section divider banners that contain no requirements
- Footnote-style text at the bottom of some pages
- Inconsistent indentation (testing the regex parser's robustness)
- Some requirements split across lines with continuation markers
This is the hardest format for pdfplumber to parse reliably.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas
import os
import math

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../sample-pdfs/sample_03_complex.pdf")

# Mix of requirements, annotations, and dividers
CONTENT = [
    # type, section_num (or None), text
    ("divider", None, "PART I — SYSTEM FUNCTIONAL REQUIREMENTS"),
    ("req", "1", "The system shall implement a modular microservices architecture where each service is independently deployable."),
    ("note", None, "[NOTE: The architecture decomposition is defined in the System Architecture Document SAD-001-v3.2. Requirements in this section elaborate the architectural constraints.]"),
    ("req", "1.1", "Each microservice shall expose its API exclusively via the API Gateway; direct service-to-service calls shall not be permitted in production."),
    ("req", "1.1.1", "The API Gateway shall enforce rate limiting per authenticated client at a default of 1000 requests per minute, configurable per client."),
    ("req", "1.1.1.1", "Rate limit counters shall be maintained in a distributed cache shared across all API Gateway instances to ensure consistent enforcement."),
    ("req", "1.1.1.1.1", "The distributed cache shall use a Redis Cluster with a minimum of 3 primary nodes and 1 replica per primary for high availability."),
    ("req", "1.1.1.1.1.1", "Redis Cluster configuration parameters including node count, replication factor, and timeout values shall be defined in the infrastructure-as-code repository."),
    ("req", "1.2", "Each microservice shall publish structured logs in JSON format to the centralised logging platform."),
    ("req", "1.2.1", "Log entries shall include: service name, instance ID, timestamp (ISO 8601 UTC), log level, trace ID, span ID, and message."),
    ("req", "1.2.1.1", "The trace ID and span ID fields shall conform to the W3C Trace Context specification."),
    ("req", "1.2.1.1.1", "All services shall propagate the W3C traceparent and tracestate HTTP headers to downstream service calls."),
    ("req", "1.2.1.1.1.1", "Header propagation shall be implemented using the OpenTelemetry SDK and shall not require manual implementation in individual services."),
    ("note", None, "[ANNOTATION: Trace context propagation is covered by the platform SDK — service teams do not need to implement this independently. Refer to Platform Team runbook PL-TRACE-001.]"),
    ("req", "1.3", "Microservices shall be stateless; session state shall be stored exclusively in the shared session store."),
    ("req", "1.3.1", "The shared session store shall be backed by Redis with a session TTL of 1800 seconds (30 minutes)."),
    ("req", "1.3.1.1", "Session data shall be encrypted at rest within Redis using the AES-256-GCM algorithm."),
    ("divider", None, "PART II — DATA REQUIREMENTS"),
    ("req", "2", "The system shall implement a data model supporting the full lifecycle of engineering requirements from initial capture to archival."),
    ("req", "2.1", "The data model shall represent requirements as versioned entities where each state change produces an immutable version record."),
    ("req", "2.1.1", "Version records shall be append-only and shall not be modifiable or deletable by any user role including Administrator."),
    ("req", "2.1.1.1", "The append-only constraint shall be enforced at the database level using row-level security policies."),
    ("req", "2.1.1.1.1", "Row-level security policies shall be tested as part of the database migration test suite run before each deployment."),
    ("req", "2.1.1.1.1.1", "Migration test failures related to row-level security shall block the deployment pipeline and trigger a P1 alert."),
    ("note", None, "[NOTE: Database migration tests are managed by the Platform DB team. Service teams raise a ticket to DB-OPS to include new RLS policies in the test suite.]"),
    ("req", "2.2", "The system shall store traceability links as first-class entities with their own audit trail independent of the linked artefacts."),
    ("req", "2.2.1", "Each traceability link entity shall record: source artefact ID and version, target artefact ID and version, link type, creating user, and creation timestamp."),
    ("req", "2.2.1.1", "When a linked artefact is modified, the system shall create a new link entity referencing the new artefact version and mark the previous link entity as superseded."),
    ("req", "2.2.1.1.1", "Superseded link entities shall be retained in the database and shall be accessible via the link history view."),
    ("req", "2.2.1.1.1.1", "The link history view shall display superseded links with a visual indicator distinguishing them from current active links."),
    ("req", "2.3", "The system shall support soft deletion of requirements artefacts; deleted artefacts shall be marked as deleted and excluded from standard views but retained in the database."),
    ("req", "2.3.1", "Soft-deleted artefacts shall be restorable by users with the Approver role or higher within 90 days of deletion."),
    ("req", "2.3.1.1", "After 90 days, soft-deleted artefacts shall be automatically archived to cold storage and shall no longer be restorable through the application interface."),
    ("divider", None, "PART III — INTERFACE REQUIREMENTS"),
    ("req", "3", "The system shall provide machine-readable interfaces supporting automated test toolchain integration."),
    ("req", "3.1", "The system shall expose a REST API conforming to OpenAPI Specification 3.1 with a machine-readable schema available at /api/v1/openapi.json."),
    ("req", "3.1.1", "All API endpoints shall implement HTTP standard methods (GET, POST, PUT, PATCH, DELETE) with semantics conforming to RFC 7231."),
    ("req", "3.1.1.1", "Mutating operations (POST, PUT, PATCH, DELETE) shall require a CSRF token passed in the X-CSRF-Token request header for browser-based clients."),
    ("req", "3.1.1.1.1", "The CSRF token shall be a cryptographically random 128-bit value generated per user session."),
    ("req", "3.1.1.1.1.1", "CSRF token generation shall use the system's cryptographically secure random number generator (CSRNG) and shall not use Math.random() or equivalent."),
    ("req", "3.2", "The system shall support OAuth 2.0 authorisation code flow with PKCE for API client authentication."),
    ("req", "3.2.1", "OAuth 2.0 tokens shall have a maximum lifetime of 3600 seconds (1 hour) for access tokens and 86400 seconds (24 hours) for refresh tokens."),
    ("req", "3.2.1.1", "Refresh token rotation shall be enforced — each use of a refresh token shall invalidate it and issue a new refresh token."),
    ("req", "3.2.1.1.1", "Refresh token reuse detection shall trigger an immediate invalidation of all tokens in the affected session and an alert to the security operations team."),
    ("req", "3.2.1.1.1.1", "The reuse detection alert shall include: user ID, token ID, timestamp of original issuance, and timestamp of the reuse attempt."),
    ("note", None, "[ANNOTATION: Refresh token rotation is implemented in the AuthService. API consumers do not need to implement this logic — the SDK handles it transparently. See AUTH-SDK-GUIDE-v2.pdf.]"),
    ("req", "3.3", "The system shall implement pagination for all list endpoints using cursor-based pagination with a default page size of 50 and a maximum of 500."),
    ("req", "3.3.1", "Cursor tokens shall be opaque to the client and shall encode the sort key and direction used by the query."),
    ("req", "3.3.1.1", "Cursor tokens shall have a validity period of 10 minutes to prevent use of stale pagination state."),
    ("divider", None, "PART IV — QUALITY AND COMPLIANCE REQUIREMENTS"),
    ("req", "4", "The system shall meet quality and compliance requirements defined by the organisation's quality management system."),
    ("req", "4.1", "The system shall maintain an uptime of 99.9% measured over any rolling 30-day calendar period."),
    ("req", "4.1.1", "Uptime shall be measured from the perspective of the external health check endpoint using a third-party monitoring service."),
    ("req", "4.1.1.1", "Planned maintenance windows of up to 4 hours per month shall be excluded from uptime calculations if communicated 72 hours in advance."),
    ("req", "4.1.1.1.1", "Maintenance window notices shall be published on the organisation's service status page and sent to all registered users via email."),
    ("req", "4.1.1.1.1.1", "The service status page shall be hosted independently of the main system so that it remains accessible during system maintenance."),
    ("req", "4.2", "The system shall retain complete audit logs for a minimum of 7 years in compliance with organisational record retention policy RET-POL-003."),
    ("req", "4.2.1", "Audit logs shall record all create, read, update, and delete operations on requirement artefacts performed by any user or automated process."),
    ("req", "4.2.1.1", "Read operations on requirement artefacts with Confidentiality classification of 'Restricted' or above shall be included in the audit log."),
    ("req", "4.2.1.1.1", "The audit log record for a read operation shall include: user ID, artefact ID, artefact classification, and timestamp."),
    ("req", "4.2.1.1.1.1", "Audit log records shall not include the full content of the accessed artefact to avoid duplication of controlled content in the audit system."),
    ("req", "4.3", "The system shall pass an independent security penetration test with no Critical or High findings before each major release."),
    ("req", "4.3.1", "The penetration test scope shall cover the API, the web application, and the infrastructure layer."),
    ("req", "4.3.1.1", "Penetration test remediation shall be completed and re-tested before the release is approved for production."),
    ("divider", None, "PART V — OPERATIONAL REQUIREMENTS"),
    ("req", "5", "The system shall support operational procedures including deployment, monitoring, incident response, and disaster recovery."),
    ("req", "5.1", "The system shall support zero-downtime deployments using a rolling update strategy."),
    ("req", "5.1.1", "The rolling update shall replace no more than 25% of running instances simultaneously."),
    ("req", "5.1.1.1", "Each replacement instance shall pass the readiness probe before the next batch of instances is updated."),
    ("req", "5.1.1.1.1", "The readiness probe shall verify database connectivity, cache connectivity, and identity provider connectivity before returning a ready state."),
    ("req", "5.1.1.1.1.1", "The maximum time allowed for the readiness probe to complete is 10 seconds; probe timeout shall be a deployment configuration parameter."),
    ("req", "5.2", "The system shall have a documented disaster recovery plan with a Recovery Time Objective (RTO) of 4 hours and Recovery Point Objective (RPO) of 1 hour."),
    ("req", "5.2.1", "The disaster recovery plan shall be tested with a full failover exercise at least once every 12 months."),
    ("req", "5.2.1.1", "The results of each DR exercise shall be documented and reviewed by the operations team and the system owner."),
    ("req", "5.2.1.1.1", "Any failures identified during the DR exercise shall be tracked as defects in the project issue tracker and resolved before the next exercise."),
    ("req", "5.2.1.1.1.1", "DR exercise defects shall be treated with the same priority as production incidents of equivalent severity."),
    ("note", None, "[NOTE: DR exercise scheduling is coordinated by the Operations team. System owners receive notification 30 days before each scheduled exercise.]"),
    ("req", "5.3", "The system shall expose metrics in Prometheus exposition format at the /metrics endpoint, accessible only from within the internal monitoring network."),
    ("req", "5.3.1", "Exposed metrics shall include: request rate, error rate, latency percentiles (p50, p95, p99), and active connection count per service."),
    ("req", "5.3.1.1", "Custom business metrics shall also be exposed including: active user sessions, requirements created per hour, and baseline creation count."),
    ("req", "5.3.1.1.1", "Metric names shall follow Prometheus naming conventions with the prefix 'reqmgmt_' for all application-specific metrics."),
    ("req", "5.3.1.1.1.1", "A complete list of exposed metrics and their descriptions shall be maintained in the operations runbook and updated with each release."),
    # Additional requirements to reach 100 total
    ("divider", None, "PART VI — NOTIFICATION AND ALERTING REQUIREMENTS"),
    ("req", "6", "The system shall provide a configurable notification and alerting subsystem supporting email, webhook, and in-application channels."),
    ("req", "6.1", "The system shall allow project administrators to configure notification rules based on requirement state changes."),
    ("req", "6.1.1", "Notification rules shall support conditions based on attribute values, link events, and baseline creation events."),
    ("req", "6.1.1.1", "Multiple conditions within a single notification rule shall be evaluated using configurable AND or OR logic."),
    ("req", "6.1.1.1.1", "Notification rule evaluation shall occur within 30 seconds of the triggering event under normal system load."),
    ("req", "6.1.1.1.1.1", "If notification delivery fails, the system shall retry delivery using exponential backoff up to a maximum of 3 attempts before marking the notification as failed."),
    ("req", "6.2", "The system shall provide an in-application notification centre displaying unread notifications to the authenticated user."),
    ("req", "6.2.1", "Unread notification count shall be displayed as a badge on the notification icon in the application header."),
    ("req", "6.2.1.1", "The badge count shall update in real time without requiring a page reload, using a WebSocket or server-sent events connection."),
    ("note", None, "[NOTE: Real-time notification delivery is implemented by the NotificationService. See NTF-ARCH-001 for the event bus topology.]"),
    ("req", "6.3", "The system shall allow users to configure their individual notification preferences, overriding project-level defaults."),
    ("req", "6.3.1", "User notification preferences shall be stored per project and shall be migrated when a user is transferred between projects."),
    ("req", "6.3.1.1", "Notification preference migration shall preserve all user-defined settings and shall not revert to project defaults."),
    ("divider", None, "PART VII — SEARCH AND DISCOVERY REQUIREMENTS"),
    ("req", "7", "The system shall provide full-text search across all requirement artefacts within a project accessible to the authenticated user."),
    ("req", "7.1", "Full-text search shall index the Title, Description, and all string-type custom attribute values of each requirement artefact."),
    ("req", "7.1.1", "The search index shall be updated within 5 seconds of a requirement artefact being created or modified."),
    ("req", "7.1.1.1", "Search index updates shall be processed asynchronously and shall not block the API response for the triggering write operation."),
    ("req", "7.1.1.1.1", "If the search index update fails, the failure shall be logged and retried up to 5 times before the artefact is flagged for manual re-indexing."),
    ("req", "7.1.1.1.1.1", "The manual re-indexing flag shall be visible in the system administration interface alongside the artefact identifier and the failure timestamp."),
    ("req", "7.2", "The system shall support saved searches that can be named, stored per user, and re-executed on demand."),
    ("req", "7.2.1", "Saved searches shall support parametric substitution allowing date-range parameters to be updated at execution time without editing the saved query."),
    ("req", "7.2.1.1", "Parametric substitution shall support relative date expressions including 'today', 'last 7 days', and 'last 30 days'."),
    ("req", "7.3", "The system shall provide a bulk export of all search results in CSV format containing a configurable subset of requirement attributes."),
    ("req", "7.3.1", "The bulk export shall be processed asynchronously for result sets exceeding 500 artefacts and delivered to the user via a download link."),
    ("req", "7.3.1.1", "Download links for async bulk exports shall be valid for 24 hours after generation and shall require authentication to access."),
    ("req", "7.3.1.1.1", "The system shall notify the requesting user by email when an asynchronous bulk export is ready for download."),
    ("req", "7.3.1.1.1.1", "The download notification email shall include the export parameters, the record count, and the expiry time of the download link."),
    ("req", "7.4", "The system shall provide an advanced filter panel supporting multi-attribute filtering on the requirements list view."),
    ("req", "7.4.1", "The advanced filter panel shall retain the last applied filter set per user per project across browser sessions using persistent local storage."),
]


def watermark(canvas_obj, doc):
    canvas_obj.saveState()
    width, height = A4
    canvas_obj.setFont("Helvetica-Bold", 52)
    canvas_obj.setFillColorRGB(0.92, 0.92, 0.92)
    canvas_obj.translate(width / 2, height / 2)
    canvas_obj.rotate(45)
    canvas_obj.drawCentredString(0, 0, "FOR TESTING ONLY")
    canvas_obj.restoreState()

    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica-Bold", 8)
    canvas_obj.setFillColor(colors.HexColor("#333333"))
    canvas_obj.drawString(2.5 * cm, height - 1.4 * cm, "SAMPLE REQUIREMENTS SPECIFICATION — DOC 3 COMPLEX")
    canvas_obj.drawRightString(width - 2.5 * cm, height - 1.4 * cm, "Version 3.0  |  DRAFT")
    canvas_obj.setStrokeColor(colors.HexColor("#999999"))
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(2.5 * cm, height - 1.6 * cm, width - 2.5 * cm, height - 1.6 * cm)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.setFillColor(colors.HexColor("#888888"))
    canvas_obj.line(2.5 * cm, 1.8 * cm, width - 2.5 * cm, 1.8 * cm)
    canvas_obj.drawString(2.5 * cm, 1.2 * cm, "UNCONTROLLED WHEN PRINTED — pdfplumber parsing complexity test document")
    canvas_obj.drawCentredString(width / 2, 1.2 * cm, f"Page {doc.page} of <N>")
    canvas_obj.restoreState()


def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=3.0 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    note_style = ParagraphStyle(
        "Note", fontSize=8, fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#666666"), leftIndent=1 * cm,
        spaceBefore=2, spaceAfter=4, borderPad=4,
        backColor=colors.HexColor("#FFFBCC"),
    )

    story = []

    # Title block
    story.append(Paragraph("DRAFT — System Requirements Specification", ParagraphStyle(
        "T", fontSize=18, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=6
    )))
    story.append(Paragraph("Document 3 — Complex Format (High Noise)", ParagraphStyle(
        "S", fontSize=11, fontName="Helvetica", alignment=TA_CENTER,
        textColor=colors.HexColor("#CC0000"), spaceAfter=4
    )))
    story.append(Paragraph(
        "This document intentionally includes headers, footers, watermarks, inline annotations, "
        "section divider banners, mixed fonts, and a Courier-style body font for selected sections. "
        "It is designed to challenge pdfplumber's parsing logic and test the robustness of the extraction script.",
        ParagraphStyle("Info", fontSize=9, fontName="Helvetica", textColor=colors.HexColor("#555555"),
                       alignment=TA_JUSTIFY, spaceAfter=12)
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CC0000"), spaceAfter=8))
    story.append(PageBreak())

    for item_type, section_num, text in CONTENT:
        if item_type == "divider":
            story.append(Spacer(1, 0.3 * cm))
            banner = Table(
                [[Paragraph(text, ParagraphStyle("BannerText", fontSize=10, fontName="Helvetica-Bold",
                                                  textColor=colors.white, alignment=TA_CENTER))]],
                colWidths=[15.5 * cm],
            )
            banner.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2C3E50")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(banner)
            story.append(Spacer(1, 0.3 * cm))

        elif item_type == "note":
            story.append(Paragraph(text, note_style))

        elif item_type == "req":
            level = section_num.count(".") + 1
            # Visual indent applied to TEXT column only — section number column
            # is always unindented so deep numbers (1.1.1.1.1.1) never wrap.
            text_indent = (level - 1) * 0.35 * cm
            use_courier = (level in (3, 5))
            font = "Courier" if use_courier else ("Helvetica-Bold" if level <= 2 else "Helvetica")
            size = 11 if level == 1 else (10 if level == 2 else 9)

            row = Table(
                [[Paragraph(f"<b>{section_num}</b>", ParagraphStyle(
                    "SN", fontSize=size, fontName="Helvetica-Bold", leftIndent=0
                 )),
                  Paragraph(text, ParagraphStyle(
                    f"RL{level}", fontSize=size, fontName=font,
                    leftIndent=text_indent, leading=13
                  ))]],
                colWidths=[3.5 * cm, 12.0 * cm],
            )
            bg = colors.HexColor("#F9F9F9") if level % 2 == 0 else colors.white
            row.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
            ]))
            story.append(row)

    doc.build(story, onFirstPage=watermark, onLaterPages=watermark)
    print(f"Created: {output_path}")


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    build_pdf(OUTPUT_PATH)
