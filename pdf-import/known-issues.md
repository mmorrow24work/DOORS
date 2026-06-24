# PDF Import — Known Issues

## Issue 1: No Native PDF Import Exists

**Severity:** Blocker — no workaround within DOORS itself
**Affected versions:** All DOORS Classic (v9.x) and DOORS Next (v7.x)

IBM DOORS and DOORS Next do not include any native PDF import functionality. This is a confirmed, intentional limitation. IBM has not released any feature to address this and there are no recorded feature requests that have been accepted.

**Source:** [Can DOORS Next Generation import PDF documents? — IBM Jazz Community Forum](https://jazz.net/forum/questions/206870/can-doors-next-generation-import-pdf-documents)

**Workaround:** Convert PDF to an intermediate format before import. See [workarounds.md](workarounds.md).

---

## Issue 2: DOORS Does Not Preserve Numbered Lists

**Severity:** High — affects hierarchy fidelity during import
**Affected versions:** All DOORS Classic and DOORS Next

DOORS does not support numbered lists as a native formatting concept. When importing a Word document that contains numbered lists, DOORS converts them to bullet points. This means:

- Paragraph numbering (1.1, 1.1.2, etc.) must be embedded in the text itself, not relying on Word's auto-numbering
- Section numbers must be stored explicitly in an artifact attribute, not derived from list position
- Any requirement formatted as an auto-numbered list in Word will lose its number on import

**Source:** [DOORS module export to Microsoft Word omits section numbers — IBM Support](https://www.ibm.com/support/pages/doors-module-export-microsoft-word-omits-section-numbers)

**Workaround:** When converting PDF → Word, do not use Word's automatic list numbering. Instead, type the paragraph number directly into the requirement text (e.g., "1.1.2 The system shall..."). Alternatively, store the number in a dedicated `Identifier` attribute during CSV import.

---

## Issue 3: ReqIF Import Fails with Invalid Hyperlinks

**Severity:** Medium — only affects ReqIF import path
**Affected versions:** DOORS Next (multiple versions)
**IBM APAR:** PH30295

When using the PDF → ReqIF → DOORS import path, the ReqIF import in DOORS Next fails silently or with an error if the ReqIF file contains invalid hyperlinks (malformed URLs, broken internal links from the source PDF).

This can happen when:
- The source PDF contains hyperlinks that are not valid URLs
- The intermediate tool (ReqView, Cameo) preserves these hyperlinks in the ReqIF export
- DOORS Next cannot parse the malformed link during import

**Source:** [PH30295: IBM DOORS NEXT GENERATION REQIF IMPORT FAILS WHEN THE FILE HAS INVALID HYPERLINKS — IBM Support](https://www.ibm.com/support/pages/apar/PH30295)

**Workaround:**
1. Before converting PDF → ReqIF, remove all hyperlinks from the source Word document
2. In Word: Home → Find & Replace → More → Format → "Find All" hyperlinks; remove formatting
3. Alternatively: check the ReqIF XML file directly and remove any `<xhtml:a href="...">` elements with malformed URLs

---

## Issue 4: PDF Character Display — Japanese and Chinese Characters

**Severity:** Low (regional — affects CJK character sets)
**Affected versions:** DOORS Next 6.0.5 with Firefox 64-bit or Internet Explorer

When viewing PDFs attached within DOORS Next, Japanese and Simplified Chinese characters may display as blank squares. This affects the display of PDF attachments, not the import of requirements.

**Source:** [Workarounds and Limitations: Known issues in IBM Rational DOORS Next Generation 6.0.5](https://jazz.net/library/article/91116)

**Workaround:**
- Install Adobe Acrobat Reader with the appropriate browser plug-in
- Use 32-bit Firefox instead of 64-bit Firefox
- This issue does not affect DOORS Next 7.x when viewed in Chrome or Edge

---

## Issue 5: PDF ActiveX Viewer Hides Menus in Internet Explorer

**Severity:** Low (browser-specific, legacy)
**Affected versions:** DOORS Next 6.0.6 with Internet Explorer

Menus and controls within DOORS Next may be hidden behind PDF documents when using Internet Explorer's PDF ActiveX Viewer. This is a defect in the PDF ActiveX Viewer, not in DOORS itself.

**Source:** [Workarounds and Limitations: Known issues in IBM Rational DOORS Next Generation 6.0.6](https://jazz.net/library/article/91880)

**Workaround:**
- Remove PDF ActiveX Viewer from Internet Explorer settings
- Use the Embedded Documents feature in DOORS Next instead
- Note: Internet Explorer is no longer a supported browser for DOORS Next — migrate to Chrome or Edge

---

## Issue 6: PDF → Word Conversion Quality Varies

**Severity:** Medium — affects practical usability of all import paths
**Affected versions:** All DOORS versions (not a DOORS defect — a conversion quality issue)

The quality of PDF → Word conversion varies significantly based on the PDF's structure. Problems commonly seen:

| PDF Characteristic | Conversion Problem | Impact on DOORS Import |
|-------------------|-------------------|----------------------|
| Scanned PDF (image-based) | No text layer; OCR required | Entire document appears as images, not text |
| Multi-column layout | Text extracted in wrong reading order | Requirements interleaved incorrectly |
| Complex tables | Table structure lost; becomes plain text | Tabular requirements lose their structure |
| Watermarked PDF | Watermark text appears in body text | False text injected into requirements |
| Headers/footers with numbering | Footer page numbers confused with section numbers | False requirement objects created |
| Protected/encrypted PDF | Conversion tool cannot extract text | Import fails entirely |

**Workaround:** See [workarounds.md — Preparing the Word Document](workarounds.md#preparing-the-word-document) for a checklist to clean up post-conversion before importing.

---

## Issue 7: Section Numbers Lost After Import (DOORS Classic)

**Severity:** Medium — affects requirement traceability
**Affected versions:** DOORS Classic

When importing a text file into DOORS Classic using the plain text import, heading numbers may be captured as part of the heading text rather than as a separate attribute. If the module is later exported and re-imported, the heading numbers may duplicate.

**Source:** [Options for importing plain text files — IBM Documentation](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.2?topic=files-options-importing-plain-text)

**Workaround:**
- Store the paragraph number in a dedicated `Section Number` attribute, not embedded in the heading text
- Use the DXL import path to explicitly control how numbers are extracted and stored
- Set heading number recognition rules correctly in the import options dialog

---

## Summary Table

| Issue | Severity | Affects | Primary Workaround |
|-------|----------|---------|-------------------|
| No native PDF import | Blocker | All versions | Convert to Word/CSV/ReqIF first |
| Numbered lists become bullets | High | All versions | Type numbers explicitly; use CSV import |
| ReqIF fails on invalid hyperlinks | Medium | DOORS Next | Remove hyperlinks before export |
| CJK character display in PDF viewer | Low | DOORS Next 6.0.5 | Use Adobe Acrobat plug-in |
| PDF ActiveX menus hidden | Low | IE only | Remove ActiveX, use embedded docs |
| Poor PDF→Word conversion quality | Medium | All versions | Clean up Word doc before import |
| Section numbers lost | Medium | DOORS Classic | Use dedicated Section Number attribute |
