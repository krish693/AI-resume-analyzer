import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)


def generate_ats_pdf_report(candidate_name: str, job_title: str, analysis_data: dict, formatting_data: dict = None) -> bytes:
    """
    Builds an executive-level, professional ATS evaluation PDF report.
    Returns bytes buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A")
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B")
    )

    h2_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )

    bullet_style = ParagraphStyle(
        "BulletItem",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B")
    )

    story = []

    # 1. Header Banner
    header_data = [
        [
            Paragraph("<b>AI RESUME ANALYZER PRO</b><br/><font size='8' color='#64748B'>Executive ATS Compatibility & Evaluation Report</font>", title_style),
            Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}<br/><b>Status:</b> ATS Screened", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[380, 160])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3B82F6"), spaceAfter=12))

    # 2. Candidate & Job Profile Card
    ats_score = analysis_data.get("ats_score", 0)
    score_color = "#10B981" if ats_score >= 80 else ("#F59E0B" if ats_score >= 60 else "#EF4444")

    candidate_card_data = [
        [
            Paragraph(f"<b>Candidate:</b> {candidate_name or 'Anonymous Candidate'}", body_style),
            Paragraph(f"<b>Target Role:</b> {job_title or 'Target Job Role'}", body_style),
            Paragraph(f"<font size='16' color='{score_color}'><b>{ats_score}%</b></font><br/><font size='7' color='#64748B'>ATS MATCH SCORE</font>", body_style)
        ]
    ]
    card_table = Table(candidate_card_data, colWidths=[200, 220, 120])
    card_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
    ]))
    story.append(card_table)
    story.append(Spacer(1, 12))

    # 3. Candidate Summary
    story.append(Paragraph("Executive Candidate Summary", h2_style))
    summary_text = analysis_data.get("candidate_summary", "No candidate summary provided.")
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))

    # 4. Skills Breakdown (Side-by-Side: Matched vs Missing)
    story.append(Paragraph("Skills Match & Gap Breakdown", h2_style))
    matched_skills = analysis_data.get("matched_skills", [])
    missing_skills = analysis_data.get("missing_skills", [])

    matched_content = "<br/>".join([f"<font color='#059669'><b>[+]</b></font> {s}" for s in matched_skills[:12]]) or "No verified skill matches."
    missing_content = "<br/>".join([f"<font color='#DC2626'><b>[-]</b></font> {s}" for s in missing_skills[:12]]) or "No major missing requirements."

    skills_table_data = [
        [
            Paragraph("<b>MATCHED SKILLS (PRESENT)</b>", ParagraphStyle("H_Green", parent=body_style, textColor=colors.HexColor("#065F46"))),
            Paragraph("<b>MISSING SKILLS (JD REQUIREMENTS)</b>", ParagraphStyle("H_Red", parent=body_style, textColor=colors.HexColor("#991B1B")))
        ],
        [
            Paragraph(matched_content, bullet_style),
            Paragraph(missing_content, bullet_style)
        ]
    ]
    skills_table = Table(skills_table_data, colWidths=[270, 270])
    skills_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#ECFDF5")),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#FEF2F2")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(skills_table)
    story.append(Spacer(1, 12))

    # 5. Strengths & Weaknesses
    story.append(Paragraph("Strengths & Risk Factors", h2_style))
    strengths = analysis_data.get("strengths", [])
    weaknesses = analysis_data.get("weaknesses", [])

    strengths_html = "<br/>".join([f"• <b>{st}</b>" for st in strengths[:4]]) or "None noted."
    weaknesses_html = "<br/>".join([f"• <i>{wk}</i>" for wk in weaknesses[:4]]) or "None noted."

    sw_table_data = [
        [Paragraph("<b>Key Strengths</b>", body_style), Paragraph("<b>Identified Weaknesses / Gaps</b>", body_style)],
        [Paragraph(strengths_html, bullet_style), Paragraph(weaknesses_html, bullet_style)]
    ]
    sw_table = Table(sw_table_data, colWidths=[270, 270])
    sw_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(sw_table)
    story.append(Spacer(1, 12))

    # 6. Actionable Resume Improvements
    story.append(Paragraph("High-Priority Resume Improvements", h2_style))
    improvements = analysis_data.get("resume_improvements", [])
    for idx, imp in enumerate(improvements[:5], start=1):
        story.append(Paragraph(f"<b>{idx}.</b> {imp}", bullet_style))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 8))

    # 7. Recommended Interview Questions
    story.append(Paragraph("Tailored Interview Preparation Questions", h2_style))
    questions = analysis_data.get("interview_questions", [])
    for idx, q in enumerate(questions[:6], start=1):
        story.append(Paragraph(f"<b>Q{idx}:</b> {q}", bullet_style))
        story.append(Spacer(1, 3))

    # 8. Footer Note
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=6))
    footer_text = Paragraph(
        "<font size='7' color='#94A3B8'>Confidential Candidate Assessment Report • Generated via AI Resume Analyzer Pro • Powered by Groq LLM & Streamlit Cloud</font>",
        ParagraphStyle("Footer", parent=styles["Normal"], alignment=1)
    )
    story.append(footer_text)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
