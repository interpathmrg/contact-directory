"""
Generador de etiquetas de invitación en PDF.
Formato: Avery 5163 — 2 columnas × 5 filas = 10 etiquetas por página (US Letter).

Dimensiones Avery 5163:
  Etiqueta : 4" × 2"
  Margen izq/der : 0.15625" (5/32")
  Gap horizontal : 0.1875"  (3/16")
  Margen top/bot : 0.5"
"""
from __future__ import annotations

import io
from dataclasses import dataclass

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

# ---------------------------------------------------------------------------
# Constantes de layout Avery 5163 (US Letter)
# ---------------------------------------------------------------------------
_COLS = 2
_ROWS = 5
_LABEL_W: float = 4.0 * inch
_LABEL_H: float = 2.0 * inch
_MARGIN_LEFT: float = 0.15625 * inch
_MARGIN_TOP: float = 0.5 * inch
_COL_GAP: float = 0.1875 * inch
_PAGE_W, _PAGE_H = letter  # 612 × 792 pt

# ---------------------------------------------------------------------------
# Estilos de texto
# ---------------------------------------------------------------------------
_STYLE_NAME = ParagraphStyle(
    "label_name",
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    spaceAfter=3,
)
_STYLE_EMPRESA = ParagraphStyle(
    "label_empresa",
    fontName="Helvetica",
    fontSize=10,
    leading=12,
    spaceAfter=2,
)
_STYLE_SOCIEDAD = ParagraphStyle(
    "label_sociedad",
    fontName="Helvetica-Oblique",
    fontSize=9,
    leading=11,
    textColor=(0.3, 0.3, 0.3),  # gris suave
)


@dataclass
class LabelData:
    nombre_completo: str
    empresa: str
    sociedad: str


# ---------------------------------------------------------------------------
# Funciones de dibujo
# ---------------------------------------------------------------------------

def _draw_label(c: Canvas, x: float, y_top: float, label: LabelData) -> None:
    """
    Dibuja una etiqueta. (x, y_top) = esquina superior izquierda.
    En reportlab y crece hacia arriba, por lo que y_top > y_bottom.
    """
    pad_x = 0.15 * inch
    pad_y = 0.20 * inch
    available_w = _LABEL_W - 2 * pad_x
    max_h = _LABEL_H - 2 * pad_y

    # Línea guía entre etiquetas (gris muy claro — comentar para impresión limpia)
    c.saveState()
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.setLineWidth(0.3)
    c.rect(x, y_top - _LABEL_H, _LABEL_W, _LABEL_H)
    c.restoreState()

    cursor_y = y_top - pad_y  # baseline de inicio (parte superior usable)

    def draw_para(text: str, style: ParagraphStyle) -> None:
        nonlocal cursor_y
        if not text:
            return
        p = Paragraph(text, style)
        _w, ph = p.wrapOn(c, available_w, max_h)
        cursor_y -= ph
        p.drawOn(c, x + pad_x, cursor_y)
        cursor_y -= style.spaceAfter  # type: ignore[attr-defined]

    draw_para(label.nombre_completo, _STYLE_NAME)
    draw_para(label.empresa, _STYLE_EMPRESA)
    draw_para(label.sociedad, _STYLE_SOCIEDAD)


def generate_labels_pdf(labels: list[LabelData]) -> bytes:
    """
    Genera un PDF con etiquetas de invitación (Avery 5163).
    Soporta múltiples páginas automáticamente.
    """
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=letter)

    # Metadatos del PDF
    c.setTitle("Etiquetas de Invitación")
    c.setAuthor("Contact Directory")

    per_page = _COLS * _ROWS
    total_pages = max(1, -(-len(labels) // per_page))  # ceil division

    for page_num in range(total_pages):
        page_labels = labels[page_num * per_page : (page_num + 1) * per_page]

        for idx, label in enumerate(page_labels):
            col = idx % _COLS
            row = idx // _COLS

            x = _MARGIN_LEFT + col * (_LABEL_W + _COL_GAP)
            # y_top: desde el tope de la página bajando por margen + filas anteriores
            y_top = _PAGE_H - _MARGIN_TOP - row * _LABEL_H

            _draw_label(c, x, y_top, label)

        if page_num < total_pages - 1:
            c.showPage()

    c.save()
    return buf.getvalue()
