"""
create_sample_pdf.py

Generates a fake "Q3 Financial Report" PDF and saves it to data/sample_report.pdf.
Run this script once to create test data before running the RAG pipeline.

Usage:
    python create_sample_pdf.py
"""

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

OUTPUT_PATH = "data/sample_report.pdf"


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=LETTER,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"], fontSize=20, spaceAfter=12
    )
    heading_style = ParagraphStyle(
        "Heading", parent=styles["Heading2"], fontSize=13, spaceBefore=16, spaceAfter=6
    )
    body_style = styles["BodyText"]
    body_style.spaceAfter = 8
    body_style.leading = 16

    story = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("Acme Corporation", styles["Heading1"]))
    story.append(Paragraph("Q3 2024 Financial Report", title_style))
    story.append(Paragraph("For the quarter ended September 30, 2024", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # ── Executive Summary ─────────────────────────────────────────────────────
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(
        "Acme Corporation delivered strong results in the third quarter of 2024, "
        "with total revenue reaching $4.7 million, representing a 23% increase "
        "year-over-year. Net income grew to $820,000, up from $610,000 in Q3 2023. "
        "These results were driven by robust performance in our SaaS product line "
        "and expanded enterprise contracts signed during the quarter.",
        body_style,
    ))
    story.append(Paragraph(
        "Operating expenses increased modestly to $3.1 million, primarily due to "
        "planned headcount additions in the engineering and sales departments. "
        "Despite higher costs, our operating margin improved to 34%, compared to "
        "29% in the same period last year, reflecting improved operational efficiency "
        "and economies of scale.",
        body_style,
    ))

    # ── Revenue Breakdown ─────────────────────────────────────────────────────
    story.append(Paragraph("Revenue Breakdown by Segment", heading_style))
    story.append(Paragraph(
        "Our three core business segments all posted positive growth in Q3 2024. "
        "The SaaS segment remained our largest revenue contributor, accounting for "
        "58% of total revenue at $2.73 million. Professional services contributed "
        "$1.12 million (24%), while hardware sales brought in $850,000 (18%).",
        body_style,
    ))

    # Revenue table
    table_data = [
        ["Segment", "Q3 2024 Revenue", "Q3 2023 Revenue", "YoY Growth"],
        ["SaaS Products", "$2,730,000", "$2,100,000", "+30%"],
        ["Professional Services", "$1,120,000", "$980,000", "+14%"],
        ["Hardware Sales", "$850,000", "$730,000", "+16%"],
        ["Total", "$4,700,000", "$3,810,000", "+23%"],
    ]
    table = Table(table_data, colWidths=[2.2 * inch, 1.5 * inch, 1.5 * inch, 1.2 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor("#F2F3F4"), colors.white]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#D5E8D4")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.15 * inch))

    # ── Regional Performance ──────────────────────────────────────────────────
    story.append(Paragraph("Regional Performance", heading_style))
    story.append(Paragraph(
        "North America continued to be our strongest market, contributing $2.9 million "
        "in revenue, a 19% increase over Q3 2023. The EMEA region showed the highest "
        "growth rate at 41%, reaching $1.1 million, buoyed by the expansion of our "
        "London and Frankfurt offices. Asia-Pacific revenue grew 18% to $700,000, "
        "with particularly strong demand from enterprise clients in Singapore and Japan.",
        body_style,
    ))

    # ── Key Operating Metrics ─────────────────────────────────────────────────
    story.append(Paragraph("Key Operating Metrics", heading_style))
    story.append(Paragraph(
        "Annual Recurring Revenue (ARR) reached $10.9 million at the end of Q3, "
        "representing a 27% increase year-over-year. Monthly Recurring Revenue (MRR) "
        "stood at $910,000, up from $717,000 at the same point in 2023. Customer "
        "churn remained low at 1.8% monthly, well below the industry average of 3.2%.",
        body_style,
    ))
    story.append(Paragraph(
        "We added 47 new enterprise customers during the quarter, bringing the total "
        "enterprise customer count to 312. Average Contract Value (ACV) for new "
        "enterprise deals reached $85,000, up 12% from the prior year. Net Revenue "
        "Retention (NRR) remained strong at 118%, indicating healthy expansion "
        "revenue from existing customers.",
        body_style,
    ))

    # ── Expenses & Headcount ──────────────────────────────────────────────────
    story.append(Paragraph("Expenses and Headcount", heading_style))
    story.append(Paragraph(
        "Total operating expenses for Q3 2024 were $3.1 million, compared to "
        "$2.7 million in Q3 2023. Research and development spending increased to "
        "$980,000 (21% of revenue) as we accelerated investment in our next-generation "
        "AI-powered analytics platform, scheduled for general availability in Q1 2025.",
        body_style,
    ))
    story.append(Paragraph(
        "Sales and marketing expenses totalled $1.05 million, representing a customer "
        "acquisition cost (CAC) of $22,300 per enterprise customer — a 7% improvement "
        "from Q2 2024. General and administrative costs were $1.07 million. "
        "Total headcount at quarter-end was 184 full-time employees, an increase of "
        "21 from the start of the year.",
        body_style,
    ))

    # ── Outlook ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Q4 2024 Outlook", heading_style))
    story.append(Paragraph(
        "For the fourth quarter of 2024, Acme Corporation expects total revenue in "
        "the range of $5.1 million to $5.4 million, implying full-year revenue of "
        "approximately $17.8 million. We anticipate continued momentum in our SaaS "
        "segment, supported by a healthy pipeline of enterprise deals expected to "
        "close before year-end.",
        body_style,
    ))
    story.append(Paragraph(
        "Operating expenses are expected to increase modestly to $3.3–$3.4 million "
        "as we complete hiring for the product and engineering teams. Management "
        "remains committed to achieving positive free cash flow for the full year "
        "and reaffirms its long-term target of 40% operating margins by 2026.",
        body_style,
    ))

    doc.build(story)
    print(f"PDF created: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
