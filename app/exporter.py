"""Export a Chapter 1 outline to DOCX (editable, for the adviser) or PDF.

Section content uses the small Markdown subset described in engines.base.OutlineEngine.
"""
import io
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from fpdf import FPDF

_NUMBERED = re.compile(r"^(\d+)\.\s+(.*)$")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def parse_blocks(content: str) -> list[tuple[str, str]]:
    """Split content into ("para" | "bullet" | "number", text) blocks; number text keeps its "N. "."""
    blocks = []
    paragraph: list[str] = []

    def flush():
        if paragraph:
            blocks.append(("para", " ".join(paragraph)))
            paragraph.clear()

    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith(("- ", "* ")):
            flush()
            blocks.append(("bullet", line[2:].strip()))
        elif _NUMBERED.match(line):
            flush()
            blocks.append(("number", line))
        else:
            paragraph.append(line)
    flush()
    return blocks


def _runs(text: str) -> list[tuple[str, bool]]:
    """Split text into (segment, is_bold) runs."""
    parts = _BOLD.split(text)
    return [(part, i % 2 == 1) for i, part in enumerate(parts) if part]


def safe_filename(title: str, ext: str) -> str:
    base = re.sub(r"[^A-Za-z0-9]+", "_", title)[:60].strip("_") or "chapter1"
    return f"{base}_Chapter1.{ext}"


# ------------------------------------------------------------------------- DOCX
def to_docx(outline: dict) -> bytes:
    doc = Document()
    for section in doc.sections:
        section.top_margin = section.bottom_margin = Inches(1)
        section.left_margin = Inches(1.5)  # common binding margin for theses
        section.right_margin = Inches(1)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 2.0
    normal.paragraph_format.space_after = Pt(0)

    def centered(text, bold=True, size=12, space_after=0):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(space_after)
        run = p.add_run(text)
        run.bold = bold
        run.font.size = Pt(size)

    centered(outline["title"].upper(), size=12, space_after=12)
    centered("CHAPTER I")
    centered("INTRODUCTION", space_after=12)

    for number, section in enumerate(outline["sections"], 1):
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(12)
        run = heading.add_run(f"1.{number} {section['heading']}")
        run.bold = True
        for kind, text in parse_blocks(section["content"]):
            p = doc.add_paragraph()
            fmt = p.paragraph_format
            if kind == "para":
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                fmt.first_line_indent = Inches(0.5)
            elif kind == "bullet":
                fmt.left_indent = Inches(0.75)
                fmt.first_line_indent = Inches(-0.25)
                p.add_run("•\t")
            else:  # numbered: keep the student's numbering exactly
                fmt.left_indent = Inches(0.75)
                fmt.first_line_indent = Inches(-0.25)
            for segment, bold in _runs(text):
                p.add_run(segment).bold = bold
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# -------------------------------------------------------------------------- PDF
_PDF_REPLACEMENTS = {"–": "-", "—": "-", "‘": "'", "’": "'", "“": '"', "”": '"', "…": "...", "•": "-"}


def _latin1(text: str) -> str:
    """The built-in PDF fonts only support Latin-1; replace typographic characters."""
    for src, dst in _PDF_REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "replace").decode("latin-1")


def to_pdf(outline: dict) -> bytes:
    pdf = FPDF(format="Letter", unit="mm")
    pdf.set_margins(left=38, top=25, right=25)
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    line_h = 8  # roughly double-spaced 12pt
    width = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Times", "B", 12)
    pdf.multi_cell(width, 6, _latin1(outline["title"].upper()), align="C")
    pdf.ln(4)
    pdf.cell(width, line_h, "CHAPTER I", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(width, line_h, "INTRODUCTION", align="C", new_x="LMARGIN", new_y="NEXT")

    for number, section in enumerate(outline["sections"], 1):
        pdf.ln(4)
        pdf.set_font("Times", "B", 12)
        pdf.multi_cell(width, line_h, _latin1(f"1.{number} {section['heading']}"))
        pdf.set_font("Times", "", 12)
        for kind, text in parse_blocks(section["content"]):
            text = _latin1(text)
            if kind == "para":
                pdf.multi_cell(width, line_h, "        " + text, align="J", markdown=True)
            else:
                prefix = "-  " if kind == "bullet" else ""
                pdf.set_x(pdf.l_margin + 8)
                pdf.multi_cell(width - 8, line_h, prefix + text, markdown=True)
    return bytes(pdf.output())
