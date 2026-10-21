"""Export PDF de l'agenda : affiche A4 prête à imprimer, événements regroupés par jour."""

from collections import defaultdict
from datetime import date
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.models import Event

GREEN = colors.HexColor("#4a7a1a")
LIME = colors.HexColor("#7ec843")
INK = colors.HexColor("#111827")
GREY = colors.HexColor("#6b7280")
LIGHT = colors.HexColor("#f3f4f6")
LOGO = Path(__file__).resolve().parent.parent / "assets" / "logo-rodez.png"

MONTHS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]  # fmt: skip
DAYS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
WIDTH, HEIGHT = A4
MARGIN = 16 * mm
BANNER = 46 * mm


def period_label(start: date | None, end: date | None) -> str:
    """Intitulé de la période : « Novembre 2026 » pour un mois, sinon « du … au … »."""
    if start and (end is None or (end.year, end.month) == (start.year, start.month)):
        return f"{MONTHS[start.month - 1].capitalize()} {start.year}"
    if start and end:
        return f"Du {start.day} {MONTHS[start.month - 1]} au {end.day} {MONTHS[end.month - 1]}"
    return "Prochains événements"


def _first_page(canvas, doc):
    """Bandeau vert avec le titre, la période et le logo (première page)."""
    canvas.saveState()
    canvas.setFillColor(GREEN)
    canvas.rect(0, HEIGHT - BANNER, WIDTH, BANNER, stroke=0, fill=1)
    canvas.setFillColor(LIME)
    canvas.rect(0, HEIGHT - BANNER - 2.5 * mm, WIDTH, 2.5 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 13)
    canvas.drawString(MARGIN, HEIGHT - 17 * mm, "AGENDA")
    canvas.setFont("Helvetica-Bold", 30)
    canvas.drawString(MARGIN, HEIGHT - 31 * mm, doc.period)
    canvas.setFont("Helvetica", 10)
    canvas.drawString(MARGIN, HEIGHT - 40 * mm, "Maison de l'Économie · Rodez Agglomération")
    if LOGO.exists():
        box_w, box_h = 52 * mm, 24 * mm
        x, y = WIDTH - MARGIN - box_w, HEIGHT - BANNER + (BANNER - box_h) / 2
        canvas.setFillColor(colors.white)
        canvas.roundRect(x, y, box_w, box_h, 2 * mm, stroke=0, fill=1)
        canvas.drawImage(
            str(LOGO), x + 3 * mm, y + 2 * mm, width=box_w - 6 * mm, height=box_h - 4 * mm,
            preserveAspectRatio=True, mask="auto",
        )  # fmt: skip
    _footer(canvas, doc)
    canvas.restoreState()


def _later_pages(canvas, doc):
    """Fin de bandeau discret et pied de page (pages suivantes)."""
    canvas.saveState()
    canvas.setFillColor(GREEN)
    canvas.rect(0, HEIGHT - 9 * mm, WIDTH, 9 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(MARGIN, HEIGHT - 6 * mm, f"AGENDA · {doc.period}")
    _footer(canvas, doc)
    canvas.restoreState()


def _footer(canvas, doc):
    """Pied de page : mention d'édition et numéro de page."""
    canvas.setStrokeColor(LIGHT)
    canvas.line(MARGIN, 14 * mm, WIDTH - MARGIN, 14 * mm)
    canvas.setFillColor(GREY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(MARGIN, 9 * mm, f"Édité le {date.today():%d/%m/%Y} · portailMDE")
    canvas.drawRightString(WIDTH - MARGIN, 9 * mm, f"Page {doc.page}")


def _styles() -> dict[str, ParagraphStyle]:
    """Styles de texte de l'affiche."""
    return {
        "day": ParagraphStyle("day", fontName="Helvetica-Bold", fontSize=26, leading=26,
                              textColor=GREEN, alignment=1),
        "weekday": ParagraphStyle("weekday", fontName="Helvetica", fontSize=9, leading=11,
                                  textColor=GREY, alignment=1),
        "time": ParagraphStyle("time", fontName="Helvetica-Bold", fontSize=10, leading=13,
                               textColor=GREEN),
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=12.5, leading=15,
                                textColor=INK),
        "desc": ParagraphStyle("desc", fontName="Helvetica", fontSize=9.5, leading=12.5,
                               textColor=GREY),
        "empty": ParagraphStyle("empty", fontName="Helvetica", fontSize=12, leading=16,
                                textColor=GREY, alignment=1),
    }  # fmt: skip


def _esc(text: str) -> str:
    """Échappe le texte pour les paragraphes ReportLab (balises XML)."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _event_cell(event: Event, styles) -> list:
    """Contenu d'un événement : heure, titre et description."""
    when = event.event_time.strftime("%H h %M") if event.event_time else "Toute la journée"
    cell = [Paragraph(when, styles["time"]), Paragraph(_esc(event.title), styles["title"])]
    if event.description:
        cell.append(Paragraph(_esc(event.description).replace("\n", "<br/>"), styles["desc"]))
    return cell


def _day_block(day: date, events: list[Event], styles) -> KeepTogether:
    """Bloc d'un jour : date à gauche, événements en cartes à droite."""
    left = [
        Paragraph(str(day.day), styles["day"]),
        Paragraph(DAYS[day.weekday()], styles["weekday"]),
    ]
    rows = [[left, _event_cell(events[0], styles)]]
    rows += [["", _event_cell(e, styles)] for e in events[1:]]
    table = Table(rows, colWidths=[26 * mm, WIDTH - 2 * MARGIN - 26 * mm])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("SPAN", (0, 0), (0, -1)),
                ("BACKGROUND", (1, 0), (1, -1), LIGHT),
                ("LINEBEFORE", (1, 0), (1, -1), 2.2, LIME),
                ("LINEBELOW", (1, 0), (1, -2), 0.6, colors.white),
                ("LEFTPADDING", (1, 0), (1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return KeepTogether([table, Spacer(1, 4 * mm)])


def build_agenda_pdf(events: list[Event], start: date | None, end: date | None) -> bytes:
    """Génère l'affiche PDF (A4 portrait) des événements fournis, groupés par jour."""
    buffer = BytesIO()
    doc = BaseDocTemplate(
        buffer, pagesize=A4, title=f"Agenda – {period_label(start, end)}",
        author="Maison de l'Économie", leftMargin=MARGIN, rightMargin=MARGIN,
    )  # fmt: skip
    doc.period = period_label(start, end)
    first = Frame(MARGIN, 20 * mm, WIDTH - 2 * MARGIN, HEIGHT - BANNER - 32 * mm, id="first")
    later = Frame(MARGIN, 20 * mm, WIDTH - 2 * MARGIN, HEIGHT - 36 * mm, id="later")
    doc.addPageTemplates(
        [
            PageTemplate(
                id="first", frames=[first], onPage=_first_page, autoNextPageTemplate="later"
            ),
            PageTemplate(id="later", frames=[later], onPage=_later_pages),
        ]
    )
    styles = _styles()
    by_day: dict[date, list[Event]] = defaultdict(list)
    for event in sorted(events, key=lambda e: (e.event_date, e.event_time is None, e.event_time)):
        by_day[event.event_date].append(event)
    story: list = [_day_block(day, items, styles) for day, items in by_day.items()]
    if not story:
        story = [
            Spacer(1, 40 * mm),
            Paragraph("Aucun événement prévu sur cette période.", styles["empty"]),
        ]
    doc.build(story)
    return buffer.getvalue()
