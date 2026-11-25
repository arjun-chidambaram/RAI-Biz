import io
import datetime
import re
from typing import Optional, Any, List
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)

from ..models import Assessment, Business, AIApplication, Risk, Recommendation, FairnessResult, PrivacyFinding, SustainabilityResult

def clean_for_reportlab(text: Any) -> str:
    """
    Converts arbitrary text (with potential HTML tags, markdown, or unescaped characters)
    into safe, valid ReportLab XML paragraph markup.
    - Strips unsupported HTML tags.
    - Converts supported tags (b, strong, i, em, u, br, font).
    - Converts markdown **bold** and *italic*.
    - Converts newlines to <br/>.
    - Safely escapes raw ampersands and angle brackets.
    - Guarantees NO literal HTML tags are shown as raw characters.
    """
    if text is None:
        return ""
    s = str(text).strip()
    if not s:
        return ""

    s = s.replace("\r\n", "\n").replace("\r", "\n")

    # 1. Convert markdown bold and italic
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", s)

    # 2. Tokenize allowed tags to protect them from tag stripping and character escaping
    font_tokens = {}
    def font_sub(m):
        tok = f"___FONT_{len(font_tokens)}___"
        font_tokens[tok] = m.group(0)
        return tok

    s = re.sub(r"<font\b[^>]*>", font_sub, s, flags=re.I)
    s = re.sub(r"</font>", "___FONT_END___", s, flags=re.I)
    s = re.sub(r"<(b|strong)\b[^>]*>", "___B_START___", s, flags=re.I)
    s = re.sub(r"</(b|strong)>", "___B_END___", s, flags=re.I)
    s = re.sub(r"<(i|em)\b[^>]*>", "___I_START___", s, flags=re.I)
    s = re.sub(r"</(i|em)>", "___I_END___", s, flags=re.I)
    s = re.sub(r"<u\b[^>]*>", "___U_START___", s, flags=re.I)
    s = re.sub(r"</u>", "___U_END___", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", "___BR___", s, flags=re.I)
    s = re.sub(r"</p>", "___BR___", s, flags=re.I)
    s = re.sub(r"<p\b[^>]*>", "", s, flags=re.I)

    # 3. Strip any other HTML tags with tag names
    s = re.sub(r"</?[a-zA-Z][a-zA-Z0-9:-]*\b[^>]*>", "", s)

    # 4. Escape raw XML special characters (&, <, >)
    s = re.sub(r"&(?!([a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);)", "&amp;", s)
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    s = s.replace("\n", "<br/>")

    # 5. Restore allowed tokens
    s = s.replace("___B_START___", "<b>").replace("___B_END___", "</b>")
    s = s.replace("___I_START___", "<i>").replace("___I_END___", "</i>")
    s = s.replace("___U_START___", "<u>").replace("___U_END___", "</u>")
    s = s.replace("___BR___", "<br/>")
    for tok, orig in font_tokens.items():
        s = s.replace(tok, orig)
    s = s.replace("___FONT_END___", "</font>")

    # 6. Normalize excessive consecutive line breaks
    s = re.sub(r"(<br/>\s*){3,}", "<br/><br/>", s)
    return s


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass ReportLab canvas that calculates the exact total page count
    and draws professional running headers and footers on every page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header on page 2 and beyond
        if self._pageNumber > 1:
            self.drawString(36, 764, "RAI-Biz — Responsible AI Governance Audit Report")
            self.drawRightString(576, 764, "Executive Summary & Audit Trail")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.6)
            self.line(36, 758, 576, 758)

        # Running footer on all pages
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(36, 22, "CONFIDENTIAL & PROPRIETARY — RAI-BIZ GOVERNANCE PLATFORM")
        self.drawRightString(576, 22, page_str)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.6)
        self.line(36, 32, 576, 32)
        self.restoreState()


def generate_assessment_pdf(db: Session, assessment_id: int) -> bytes:
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise ValueError("Assessment not found")

    business = db.query(Business).filter(Business.id == assessment.business_id).first()
    application = db.query(AIApplication).filter(AIApplication.id == assessment.application_id).first()
    risks = db.query(Risk).filter(Risk.application_id == assessment.application_id).all()
    recommendations = db.query(Recommendation).filter(Recommendation.application_id == assessment.application_id).all()
    fairness = db.query(FairnessResult).filter(FairnessResult.application_id == assessment.application_id).order_by(FairnessResult.created_at.desc()).first()
    privacy = db.query(PrivacyFinding).filter(PrivacyFinding.application_id == assessment.application_id).order_by(PrivacyFinding.created_at.desc()).first()
    sustainability = db.query(SustainabilityResult).filter(SustainabilityResult.application_id == assessment.application_id).order_by(SustainabilityResult.created_at.desc()).first()

    buffer = io.BytesIO()
    # Printable area: Letter 8.5 x 11 inches (612 x 792 pt).
    # Margins: 36 pt left & right -> printable width = 540 pt (7.5 inches).
    # Top & bottom margins: 42 pt.
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Brand Color Palette
    PRIMARY = colors.HexColor("#0B1528")      # Deep Navy
    ACCENT = colors.HexColor("#0284c7")       # Tech Blue
    TEAL = colors.HexColor("#0d9488")         # Teal
    SUCCESS = colors.HexColor("#059669")      # Emerald
    WARNING = colors.HexColor("#d97706")      # Amber
    DANGER = colors.HexColor("#e11d48")       # Crimson / Rose
    LIGHT_BG = colors.HexColor("#f8fafc")     # Light Slate Background
    BORDER_COLOR = colors.HexColor("#cbd5e1") # Border Slate

    # Typography & Paragraph Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=ACCENT,
        alignment=2 # Right align
    )
    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=PRIMARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#334155")
    )
    disclaimer_style = ParagraphStyle(
        'DisclaimerCustom',
        parent=styles['Italic'],
        fontName='Helvetica-Oblique',
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#64748b")
    )

    # Table Header & Cell Styles
    th_teal_style = ParagraphStyle(
        'THTeal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=0
    )
    th_teal_center = ParagraphStyle(
        'THTealCenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1
    )
    th_navy_style = ParagraphStyle(
        'THNavy',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=0
    )
    th_navy_center = ParagraphStyle(
        'THNavyCenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1
    )
    td_style = ParagraphStyle(
        'TDNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#1e293b")
    )
    td_bold_style = ParagraphStyle(
        'TDBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#0f172a")
    )
    td_center_style = ParagraphStyle(
        'TDCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#1e293b"),
        alignment=1
    )

    elements = []

    # 1. Header / Title Banner Table
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    header_data = [
        [
            Paragraph("<b>RAI-Biz Governance Audit Report</b>", title_style),
            Paragraph(
                f"<b>Generated:</b> {now_utc.strftime('%Y-%m-%d %H:%M UTC')}<br/>"
                f"<b>Audit Reference:</b> #{assessment.id}",
                subtitle_style
            )
        ]
    ]
    t_header = Table(header_data, colWidths=[4.7 * inch, 2.8 * inch])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(t_header)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceBefore=8, spaceAfter=10))

    # 2. Business Profile & AI Application Metadata Grid
    biz_name = clean_for_reportlab(business.name if business else 'N/A')
    app_name = clean_for_reportlab(application.name if application else 'N/A')
    biz_ind = clean_for_reportlab(f"{business.industry if business else 'N/A'} ({business.size if business else 'N/A'} employees)")
    app_func = clean_for_reportlab(application.business_function if application else 'N/A')
    biz_loc = clean_for_reportlab(business.location if business else 'N/A')
    app_impact = clean_for_reportlab(f"Impact: {application.automated_decision_impact if application else 'High'} | Oversight: {application.human_oversight if application else 'None'}")

    meta_table_data = [
        [
            Paragraph(f"<b>SME Organization:</b> {biz_name}", body_style),
            Paragraph(f"<b>Target AI System:</b> {app_name}", body_style)
        ],
        [
            Paragraph(f"<b>Industry / Size:</b> {biz_ind}", body_style),
            Paragraph(f"<b>Business Function:</b> {app_func}", body_style)
        ],
        [
            Paragraph(f"<b>Jurisdiction:</b> {biz_loc}", body_style),
            Paragraph(f"<b>Decision Parameters:</b> {app_impact}", body_style)
        ]
    ]
    t_meta = Table(meta_table_data, colWidths=[3.75 * inch, 3.75 * inch])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 10))

    # 3. Executive Scorecard
    elements.append(Paragraph("1. Executive Responsible AI Scorecard", h2_style))
    score_rows = [
        [
            Paragraph("Governance Dimension", th_navy_style),
            Paragraph("Score / 100", th_navy_center),
            Paragraph("Risk Tier", th_navy_center),
            Paragraph("Evaluation Summary", th_navy_style)
        ],
        [
            Paragraph("Fairness & Demographic Equity", td_bold_style),
            Paragraph(f"{assessment.fairness_score:.1f}", td_center_style),
            Paragraph(
                f"<font color='{'#059669' if assessment.fairness_score >= 80 else ('#d97706' if assessment.fairness_score >= 60 else '#be123c')}'><b>"
                f"{'Compliant' if assessment.fairness_score >= 80 else ('Moderate' if assessment.fairness_score >= 60 else 'High Risk')}</b></font>",
                td_center_style
            ),
            Paragraph("Pre-deployment demographic parity & algorithmic bias testing.", td_style)
        ],
        [
            Paragraph("Transparency & Explainability", td_bold_style),
            Paragraph(f"{assessment.transparency_score:.1f}", td_center_style),
            Paragraph(
                f"<font color='{'#059669' if assessment.transparency_score >= 80 else ('#d97706' if assessment.transparency_score >= 60 else '#be123c')}'><b>"
                f"{'Compliant' if assessment.transparency_score >= 80 else ('Moderate' if assessment.transparency_score >= 60 else 'High Risk')}</b></font>",
                td_center_style
            ),
            Paragraph("Decision records, human sign-off & SHAP model explanations.", td_style)
        ],
        [
            Paragraph("Data Privacy & Governance", td_bold_style),
            Paragraph(f"{assessment.privacy_score:.1f}", td_center_style),
            Paragraph(
                f"<font color='{'#059669' if assessment.privacy_score >= 80 else ('#d97706' if assessment.privacy_score >= 60 else '#be123c')}'><b>"
                f"{'Compliant' if assessment.privacy_score >= 80 else ('Moderate' if assessment.privacy_score >= 60 else 'High Risk')}</b></font>",
                td_center_style
            ),
            Paragraph("PII minimization, encryption controls & retention schedule.", td_style)
        ],
        [
            Paragraph("Green AI & Sustainability", td_bold_style),
            Paragraph(f"{assessment.sustainability_score:.1f}", td_center_style),
            Paragraph(
                f"<font color='{'#059669' if assessment.sustainability_score >= 80 else ('#d97706' if assessment.sustainability_score >= 60 else '#be123c')}'><b>"
                f"{'Compliant' if assessment.sustainability_score >= 80 else ('Moderate' if assessment.sustainability_score >= 60 else 'High Risk')}</b></font>",
                td_center_style
            ),
            Paragraph("Compute runtime energy tracking & regional carbon intensity.", td_style)
        ],
        [
            Paragraph("<b>OVERALL RESPONSIBLE AI INDEX</b>", td_bold_style),
            Paragraph(f"<b>{assessment.overall_score:.1f}</b>", td_center_style),
            Paragraph(
                f"<font color='{'#059669' if assessment.overall_score >= 80 else ('#d97706' if assessment.overall_score >= 60 else '#be123c')}'><b>"
                f"{'ENTERPRISE READY' if assessment.overall_score >= 80 else ('REMEDIATION NEEDED' if assessment.overall_score >= 60 else 'CRITICAL DEFICIENCIES')}</b></font>",
                td_center_style
            ),
            Paragraph("Composite arithmetic mean across all 4 governance pillars.", td_bold_style)
        ]
    ]
    t_scores = Table(score_rows, colWidths=[2.30 * inch, 1.10 * inch, 1.60 * inch, 2.50 * inch], repeatRows=1)
    t_scores.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e0f2fe")),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_scores)
    elements.append(Spacer(1, 8))

    # 4. Deep Analytical Findings & Verification
    elements.append(Paragraph("2. Deep Analytical Findings & Verification", h2_style))
    analysis_items = []
    
    if fairness:
        dp_diff = fairness.demographic_parity_diff
        dp_ratio = fairness.demographic_parity_ratio
        sens_attr = clean_for_reportlab(fairness.sensitive_attribute)
        risk_lvl = clean_for_reportlab(fairness.risk_level)
        rule_eval = "EEOC 4/5ths Rule VIOLATED" if dp_ratio < 0.80 else "EEOC 4/5ths Rule SATISFIED"
        analysis_items.append(
            f"<b>Fairness &amp; Disparity Audit:</b> Demographic Parity Difference = {dp_diff:.3f}, "
            f"Parity Ratio = {dp_ratio:.3f}. <b>{rule_eval}</b> "
            f"across sensitive attribute '{sens_attr}'. Disparate impact risk evaluated as <b>{risk_lvl}</b>."
        )
    else:
        analysis_items.append("<b>Fairness Audit:</b> Synthetic/uploaded benchmark dataset not yet linked to this assessment.")

    if privacy:
        analysis_items.append(
            f"<b>Privacy &amp; PII Screening:</b> {privacy.pii_detected_count} unredacted direct identifiers detected out of {privacy.total_records_scanned} records scanned. "
            f"Overall Privacy Governance Risk evaluated as <b>{clean_for_reportlab(privacy.risk_level)}</b>."
        )
    else:
        analysis_items.append("<b>Privacy Screening:</b> No raw dataset PII screening performed on current run.")

    if sustainability:
        reg_name = clean_for_reportlab(sustainability.region_name)
        analysis_items.append(
            f"<b>Green AI &amp; Energy Modeling:</b> Estimated compute runtime of {sustainability.compute_duration_hours}h at {sustainability.power_draw_kw} kW "
            f"consumed {sustainability.energy_kwh} kWh, generating ~{sustainability.estimated_co2e_kg:.2f} kg CO2e in '{reg_name}'."
        )
    else:
        analysis_items.append("<b>Green AI Footprint:</b> Baseline energy tracking not yet registered for this model.")

    for item in analysis_items:
        elements.append(Paragraph(f"• {item}", body_style))
        elements.append(Spacer(1, 3))

    elements.append(Spacer(1, 6))

    # 5. Central Risk Center Summary Table
    elements.append(Paragraph(f"3. Active Risks Register ({len(risks)} Identified)", h2_style))
    risk_rows = [
        [
            Paragraph("Severity", th_navy_center),
            Paragraph("Score", th_navy_center),
            Paragraph("Risk Title, Business Impact &amp; Evidence Source", th_navy_style),
            Paragraph("Status &amp; Lifecycle", th_navy_style)
        ]
    ]

    for r in risks:
        score_display = f"{r.risk_score:.0f}/100" if r.risk_score is not None else "N/A"
        sev_upper = (r.severity or 'MEDIUM').upper()
        sev_color = "#be123c" if sev_upper == "CRITICAL" else ("#c2410c" if sev_upper == "HIGH" else ("#b45309" if sev_upper == "MEDIUM" else "#047857"))
        
        clean_title = clean_for_reportlab(r.title)
        clean_impact = clean_for_reportlab(r.business_impact)
        source_name = clean_for_reportlab(r.evidence_source or 'Self-reported assessment')
        verified_tag = " • Verified" if r.is_verified else " • Unverified"
        clean_status = clean_for_reportlab(r.status or 'Open')
        clean_lifecycle = clean_for_reportlab(r.lifecycle_status or 'New')

        details_markup = (
            f"<b>{clean_title}</b><br/>"
            f"<font color='#334155'>{clean_impact}</font><br/>"
            f"<font color='#64748b'>[Source: {source_name}{verified_tag}]</font>"
        )

        lifecycle_markup = (
            f"<b>{clean_status}</b><br/>"
            f"<font color='#64748b'>{clean_lifecycle}</font>"
        )

        risk_rows.append([
            Paragraph(f"<font color='{sev_color}'><b>{sev_upper}</b></font>", td_center_style),
            Paragraph(score_display, td_center_style),
            Paragraph(details_markup, td_style),
            Paragraph(lifecycle_markup, td_style)
        ])

    if len(risks) == 0:
        risk_rows.append([
            Paragraph("NONE", td_center_style),
            Paragraph("0", td_center_style),
            Paragraph("No open risk deficiencies registered.", td_style),
            Paragraph("Verified", td_style)
        ])

    t_risks = Table(risk_rows, colWidths=[0.85 * inch, 0.75 * inch, 4.50 * inch, 1.40 * inch], repeatRows=1)
    t_risks.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_risks)
    elements.append(Spacer(1, 8))

    # 6. Actionable AI Recommendations Table
    elements.append(Paragraph(f"4. Actionable Remediation Roadmap ({len(recommendations)} Recommendations)", h2_style))
    rec_rows = [
        [
            Paragraph("Priority", th_teal_center),
            Paragraph("Responsible Team", th_teal_style),
            Paragraph("Recommended Action Plan", th_teal_style),
            Paragraph("Expected Business Benefit", th_teal_style)
        ]
    ]

    for rec in recommendations:
        prio_upper = (rec.priority or 'MEDIUM').upper()
        prio_color = "#be123c" if prio_upper == "CRITICAL" else ("#c2410c" if prio_upper == "HIGH" else ("#b45309" if prio_upper == "MEDIUM" else "#047857"))
        
        clean_team = clean_for_reportlab(rec.responsible_team or 'Engineering')
        clean_problem = clean_for_reportlab(rec.problem)
        clean_action = clean_for_reportlab(rec.action)
        clean_benefit = clean_for_reportlab(rec.expected_business_benefit)

        action_plan_markup = (
            f"<b>{clean_problem}</b><br/>"
            f"<font color='#334155'>{clean_action}</font>"
        )

        rec_rows.append([
            Paragraph(f"<font color='{prio_color}'><b>{prio_upper}</b></font>", td_center_style),
            Paragraph(f"<b>{clean_team}</b>", td_style),
            Paragraph(action_plan_markup, td_style),
            Paragraph(clean_benefit, td_style)
        ])

    if len(recommendations) == 0:
        rec_rows.append([
            Paragraph("INFO", td_center_style),
            Paragraph("Engineering", td_style),
            Paragraph("Complete initial governance assessment to unlock automated remediation recommendations.", td_style),
            Paragraph("N/A", td_style)
        ])

    t_recs = Table(rec_rows, colWidths=[0.85 * inch, 1.25 * inch, 3.40 * inch, 2.00 * inch], repeatRows=1)
    t_recs.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_recs)
    elements.append(Spacer(1, 8))

    # 7. Statutory & Epistemological Disclaimer
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#94a3b8"), spaceBefore=4, spaceAfter=6))
    disclaimer_text = (
        "<b>LEGAL NOTICE &amp; STATUTORY AUDIT DISCLAIMER:</b> This report is generated by the RAI-Biz Governance Engine "
        "as a self-reported assessment and heuristic technical screening for Small and Medium Enterprises. It does NOT "
        "constitute an official regulatory certificate, statutory conformity attestation under the EU AI Act, formal ISO/IEC 42001 certification, "
        "or legally binding advice. Feature importances and SHAP values quantify empirical model correlation and do not establish causal relationships. "
        "Deploying organizations remain exclusively responsible for autonomous model decisions and regulatory compliance."
    )
    elements.append(Paragraph(disclaimer_text, disclaimer_style))

    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
