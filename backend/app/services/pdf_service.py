import io
import datetime
from typing import Optional
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)

from ..models import Assessment, Business, AIApplication, Risk, Recommendation, FairnessResult, PrivacyFinding, SustainabilityResult

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
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0B1528")      # Deep Navy
    ACCENT = colors.HexColor("#0284c7")       # Tech Blue
    TEAL = colors.HexColor("#0d9488")         # Teal
    SUCCESS = colors.HexColor("#10b981")      # Emerald Green
    WARNING = colors.HexColor("#f59e0b")      # Amber
    DANGER = colors.HexColor("#e11d48")       # Crimson / Rose
    LIGHT_BG = colors.HexColor("#f8fafc")     # Light Slate
    BORDER_COLOR = colors.HexColor("#e2e8f0") # Border

    # Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=PRIMARY
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=ACCENT
    )
    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155")
    )
    disclaimer_style = ParagraphStyle(
        'DisclaimerCustom',
        parent=styles['Italic'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b")
    )

    elements = []

    # Header / Title Banner
    header_data = [
        [
            Paragraph("<b>RAI-Biz Governance Audit Report</b>", title_style),
            Paragraph(f"<b>Generated:</b> {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}<br/><b>Audit ID:</b> #{assessment.id}", subtitle_style)
        ]
    ]
    t_header = Table(header_data, colWidths=[4.2 * inch, 2.8 * inch])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(t_header)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceBefore=10, spaceAfter=14))

    # Business Profile & AI Application Grid
    meta_table_data = [
        [
            Paragraph(f"<b>SME Organization:</b> {business.name if business else 'N/A'}", body_style),
            Paragraph(f"<b>Target AI System:</b> {application.name if application else 'N/A'}", body_style)
        ],
        [
            Paragraph(f"<b>Industry / Size:</b> {business.industry if business else 'N/A'} ({business.size if business else 'N/A'} employees)", body_style),
            Paragraph(f"<b>Business Function:</b> {application.business_function if application else 'N/A'}", body_style)
        ],
        [
            Paragraph(f"<b>Jurisdiction:</b> {business.location if business else 'N/A'}", body_style),
            Paragraph(f"<b>Decision Impact:</b> {application.automated_decision_impact if application else 'High'} | <b>Human Oversight:</b> {application.human_oversight if application else 'None'}", body_style)
        ]
    ]
    t_meta = Table(meta_table_data, colWidths=[3.5 * inch, 3.5 * inch])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 14))

    # Executive Scorecard
    elements.append(Paragraph("1. Executive Responsible AI Scorecard", h2_style))
    score_rows = [
        ["Governance Dimension", "Score / 100", "Risk Tier", "Evaluation Summary"],
        ["Fairness & Demographic Equity", f"{assessment.fairness_score:.1f}", "Compliant" if assessment.fairness_score >= 80 else ("Moderate" if assessment.fairness_score >= 60 else "High Risk"), "Pre-deployment parity & bias testing"],
        ["Transparency & Explainability", f"{assessment.transparency_score:.1f}", "Compliant" if assessment.transparency_score >= 80 else ("Moderate" if assessment.transparency_score >= 60 else "High Risk"), "Decision records & SHAP model explanations"],
        ["Data Privacy & Governance", f"{assessment.privacy_score:.1f}", "Compliant" if assessment.privacy_score >= 80 else ("Moderate" if assessment.privacy_score >= 60 else "High Risk"), "PII minimization & retention schedule"],
        ["Green AI & Sustainability", f"{assessment.sustainability_score:.1f}", "Compliant" if assessment.sustainability_score >= 80 else ("Moderate" if assessment.sustainability_score >= 60 else "High Risk"), "Compute energy & carbon intensity"],
        ["OVERALL RESPONSIBLE AI INDEX", f"{assessment.overall_score:.1f}", "ENTERPRISE READY" if assessment.overall_score >= 80 else ("REMEDIATION NEEDED" if assessment.overall_score >= 60 else "CRITICAL DEFICIENCIES"), "Composite arithmetic mean of 4 dimensions"]
    ]
    t_scores = Table(score_rows, colWidths=[2.2 * inch, 1.1 * inch, 1.5 * inch, 2.2 * inch])
    t_scores.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (2, -1), 'CENTER'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e0f2fe")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_scores)
    elements.append(Spacer(1, 14))

    # Analytical Findings (Fairness, Privacy, Green AI)
    elements.append(Paragraph("2. Deep Analytical Findings & Verification", h2_style))
    analysis_items = []
    
    if fairness:
        analysis_items.append(
            f"<b>Fairness & Disparity Audit:</b> Demographic Parity Difference = {fairness.demographic_parity_diff:.3f}, "
            f"Parity Ratio = {fairness.demographic_parity_ratio:.3f}. "
            f"{'EEOC 4/5ths Rule VIOLATED' if fairness.demographic_parity_ratio < 0.80 else 'EEOC 4/5ths Rule SATISFIED'} "
            f"across sensitive attribute '{fairness.sensitive_attribute}'. Disparate impact risk evaluated as <b>{fairness.risk_level}</b>."
        )
    else:
        analysis_items.append("<b>Fairness Audit:</b> Synthetic/uploaded benchmark dataset not yet linked to this assessment.")

    if privacy:
        analysis_items.append(
            f"<b>Privacy & PII Screening:</b> {privacy.pii_detected_count} unredacted direct identifiers detected out of {privacy.total_records_scanned} records scanned. "
            f"Overall Privacy Governance Risk evaluated as <b>{privacy.risk_level}</b>."
        )
    else:
        analysis_items.append("<b>Privacy Screening:</b> No raw dataset PII screening performed on current run.")

    if sustainability:
        analysis_items.append(
            f"<b>Green AI & Energy Modeling:</b> Estimated compute runtime of {sustainability.compute_duration_hours}h at {sustainability.power_draw_kw} kW "
            f"consumed {sustainability.energy_kwh} kWh, generating ~{sustainability.estimated_co2e_kg:.2f} kg CO2e in '{sustainability.region_name}'."
        )
    else:
        analysis_items.append("<b>Green AI Footprint:</b> Baseline energy tracking not yet registered for this model.")

    for item in analysis_items:
        elements.append(Paragraph(f"• {item}", body_style))
        elements.append(Spacer(1, 4))

    elements.append(Spacer(1, 10))

    # Central Risk Center Summary Table
    elements.append(Paragraph(f"3. Active Risks Register ({len(risks)} Identified)", h2_style))
    risk_rows = [["Severity", "Score", "Risk Title & Evidence Source", "Lifecycle / Status"]]
    for r in risks[:6]:
        score_display = f"{r.risk_score:.0f}/100" if r.risk_score is not None else "N/A"
        evidence_tag = f"<br/><font color='#64748b'>[Source: {r.evidence_source or 'Assessment'}{' • Verified' if r.is_verified else ''}]</font>"
        lifecycle_tag = f"<b>{r.status}</b><br/><font color='#64748b'>{r.lifecycle_status or 'New'}</font>"
        risk_rows.append([
            r.severity.upper(),
            score_display,
            Paragraph(f"<b>{r.title}</b><br/>{r.business_impact[:95]}...{evidence_tag}", body_style),
            Paragraph(lifecycle_tag, body_style)
        ])
    if len(risks) == 0:
        risk_rows.append(["None", "0", Paragraph("No open risk deficiencies registered.", body_style), Paragraph("Verified", body_style)])

    t_risks = Table(risk_rows, colWidths=[0.9 * inch, 0.7 * inch, 4.2 * inch, 1.2 * inch])
    t_risks.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#334155")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_risks)
    elements.append(Spacer(1, 14))

    # Actionable AI Recommendations Table
    elements.append(Paragraph(f"4. Actionable Remediation Roadmap ({len(recommendations)} Recommendations)", h2_style))
    rec_rows = [["Priority", "Responsible Team", "Recommended Action Plan", "Expected Benefit"]]
    for rec in recommendations[:5]:
        rec_rows.append([
            rec.priority.upper(),
            rec.responsible_team,
            f"<b>{rec.problem}</b><br/>{rec.action}",
            rec.expected_business_benefit
        ])
    if len(recommendations) == 0:
        rec_rows.append(["None", "Engineering", "Complete initial governance assessment to unlock recommendations.", "N/A"])

    t_recs = Table(rec_rows, colWidths=[0.9 * inch, 1.3 * inch, 3.2 * inch, 1.6 * inch])
    t_recs.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_recs)
    elements.append(Spacer(1, 16))

    # Legal Disclaimer & Governance Limitations
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#94a3b8"), spaceBefore=6, spaceAfter=8))
    disclaimer_text = (
        "<b>LEGAL NOTICE & STATUTORY AUDIT DISCLAIMER:</b> This report is generated by the RAI-Biz Governance Engine "
        "as a self-reported assessment and heuristic technical screening for Small and Medium Enterprises. It does NOT "
        "constitute an official regulatory certificate, statutory conformity attestation under the EU AI Act, legal advice, "
        "or formal ISO/IEC 42001 certification. Organizations remain exclusively liable for their deployment decisions."
    )
    elements.append(Paragraph(disclaimer_text, disclaimer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
