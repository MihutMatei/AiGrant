# -------------------------------------------------
# generate_presentation_formal_utf8.py
# -------------------------------------------------
import json
import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from pathlib import Path

# ----------------------------
# Register UTF-8 fonts
# ----------------------------
BASE_DIR = Path(__file__).resolve().parents[0]

pdfmetrics.registerFont(TTFont("DejaVu", BASE_DIR / "DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", BASE_DIR / "DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Italic", BASE_DIR / "DejaVuSerif-Italic.ttf"))

CURRENT_DATE = datetime.now().strftime("%B %d, %Y")


# ----------------------------
# Page number drawing
# ----------------------------
def _draw_page_number(canvas_obj, doc):
    page_num = canvas_obj.getPageNumber()
    if page_num > 1:  # skip title page
        canvas_obj.setFont("DejaVu", 10)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawRightString(
            doc.rightMargin + doc.width, doc.bottomMargin / 2, f"Page {page_num - 1}"
        )


# ----------------------------
# Title page drawing
# ----------------------------
def _draw_title_page(canvas_obj, doc, company_name, tagline, logo_path=None):
    """Draws the title page centered with optional logo."""
    width, height = letter
    y = height / 2 + 60

    # Draw logo if provided
    if logo_path and os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=2 * inch, height=2 * inch)
            img.drawOn(canvas_obj, (width - 2 * inch) / 2, y)
            y -= 80
        except Exception:
            # ignore logo loading errors
            pass

    # Draw company name
    canvas_obj.setFont("DejaVu-Bold", 36)
    canvas_obj.setFillColor(colors.HexColor("#1a3c6e"))
    canvas_obj.drawCentredString(width / 2, y, company_name or "")

    # Draw tagline
    y -= 50
    canvas_obj.setFont("DejaVu", 16)
    canvas_obj.setFillColor(colors.HexColor("#2c5282"))
    canvas_obj.drawCentredString(width / 2, y, tagline or "")

    # Draw date
    y -= 40
    canvas_obj.setFont("DejaVu-Italic", 14)
    canvas_obj.setFillColor(colors.grey)
    canvas_obj.drawCentredString(width / 2, y, CURRENT_DATE)


# ----------------------------
# PDF generator
# ----------------------------
def generate_presentation(
    json_file: str, pdf_file: str, logo_path: str = None, registry_json_path: str = None
):
    """Generates a company presentation PDF from JSON input."""
    try:
        # Load main JSON
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return 0

    registry_data = {}
    if registry_json_path:
        try:
            with open(registry_json_path, "r", encoding="utf-8") as f2:
                registry_data = json.load(f2)
        except Exception:
            # skip if registry JSON not found
            registry_data = {}

    company_name = registry_data.get("denumire") or data.get("company_name") or ""
    tagline = data.get("tagline", "")
    sections = data.get("sections", [])

    # PDF setup
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    # ----------------------------
    # Styles
    # ----------------------------
    section_title_style = ParagraphStyle(
        "SectionTitle",
        fontName="DejaVu-Bold",
        fontSize=22,
        leading=28,  # slightly larger than fontSize to give breathing room
        textColor=colors.HexColor("#1a3c6e"),
        spaceBefore=20,
        spaceAfter=24,
    )
    body_style = ParagraphStyle(
        "Body", fontName="DejaVu", fontSize=12, leading=22, spaceAfter=14, alignment=4
    )
    detail_style = ParagraphStyle(
        "Detail",
        fontName="DejaVu",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#2d3748"),
    )

    content = []

    # -----------------------------
    # 1. Company details (page 2)
    # -----------------------------
    details_raw = [
        ("Company Name", registry_data.get("denumire")),
        ("Motto", tagline),
        ("Address", data.get("address") or registry_data.get("adresa")),
        ("Phone", data.get("phone") or registry_data.get("telefon")),
        ("Email", data.get("email")),
        ("Website", data.get("website")),
        ("CUI", registry_data.get("cif")),
        ("Trade Register No.", registry_data.get("numar_reg_com")),
        ("VAT Starting Date", registry_data.get("tva")),
        ("CAEN", registry_data.get("caen_code")),
    ]
    # Keep only non-empty/non-null values
    details = [
        (label, str(value))
        for label, value in details_raw
        if value not in (None, "", "null")
    ]

    if details:
        table = Table(details, colWidths=[2 * inch, 4.7 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f7fafc")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2d3748")),
                    ("FONTNAME", (0, 0), (0, -1), "DejaVu-Bold"),
                    ("FONTSIZE", (0, 0), (0, -1), 11),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (1, 0), (1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("BACKGROUND", (1, 0), (1, -1), colors.white),
                ]
            )
        )

        content += [
            PageBreak(),  # start second page
            Paragraph("Company Details", section_title_style),
            Spacer(1, 12),
            table,
            Spacer(1, 20),
        ]

    # -----------------------------
    # 2. Sections (continuous with widow/orphan control)
    # -----------------------------
    for sec in sections:
        body_text = sec["body"].replace("\n", "<br/><br/>")
        body_para = Paragraph(body_text, body_style)
        content.append(
            KeepTogether(
                [Paragraph(sec["title"], section_title_style), Spacer(1, 24), body_para]
            )
        )

    # -----------------------------
    # Build PDF
    # -----------------------------
    try:
        doc.build(
            content,
            onFirstPage=lambda canvas_obj, doc: _draw_title_page(
                canvas_obj, doc, company_name, tagline, logo_path
            ),
            onLaterPages=_draw_page_number,
        )
        return 1  # success
    except Exception:
        return 0  # error


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    if len(sys.argv) <= 3:
        print(
            f"Usage: {sys.argv[0]} <json_text> <json_date_firma> <output_pdf_name>\nAlso logo.png/jpg/jpeg will be auto-detected if present."
        )
        sys.exit(0)

    json_path = sys.argv[1]
    registry = sys.argv[2]
    pdf_path = sys.argv[3]

    # Automatically detect logo
    logo = None
    for ext in ["png", "jpg", "jpeg"]:
        if os.path.exists(f"logo.{ext}"):
            logo = f"logo.{ext}"
            break

    sys.exit(generate_presentation(json_path, pdf_path, logo, registry))
