import json
import os

from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PAGE_SIZE = landscape(A3)   # 1190.55 × 841.89 pt
PAGE_W, PAGE_H = PAGE_SIZE
MARGIN = 10 * mm
GUTTER = 4 * mm


def _abs(root, rel_path):
    return os.path.normpath(os.path.join(root, rel_path))


def _best_path(photo, root):
    """Preferisce la versione ottimizzata, ricade sull'originale."""
    for key in ('optimized_path', 'original_path'):
        if photo[key]:
            p = _abs(root, photo[key])
            if os.path.exists(p):
                return p
    return None


def _draw_background(c, rel_path, root):
    abs_path = _abs(root, rel_path)
    if os.path.exists(abs_path):
        c.drawImage(abs_path, 0, 0, PAGE_W, PAGE_H,
                    preserveAspectRatio=False, mask='auto')


def _draw_grid(c, photos, root):
    """Layout automatico 2×2 (max 4 foto per pagina)."""
    cols, rows = 2, 2
    cell_w = (PAGE_W - 2 * MARGIN) / cols
    cell_h = (PAGE_H - 2 * MARGIN) / rows

    for i, photo in enumerate(photos[:cols * rows]):
        path = _best_path(photo, root)
        if not path:
            continue
        col = i % cols
        row = i // cols
        x = MARGIN + col * cell_w + GUTTER
        y = PAGE_H - MARGIN - (row + 1) * cell_h + GUTTER
        c.drawImage(path, x, y,
                    width=cell_w - 2 * GUTTER,
                    height=cell_h - 2 * GUTTER,
                    preserveAspectRatio=True, anchor='c', mask='auto')


def _draw_positioned(c, photo, root):
    """Posizionamento preciso tramite position_data (valori 0-1 relativi alla pagina)."""
    path = _best_path(photo, root)
    if not path:
        return
    try:
        pos = json.loads(photo['position_data'])
        c.drawImage(path,
                    x=pos['x'] * PAGE_W,
                    y=pos['y'] * PAGE_H,
                    width=pos['w'] * PAGE_W,
                    height=pos['h'] * PAGE_H,
                    preserveAspectRatio=True, anchor='c', mask='auto')
    except (json.JSONDecodeError, KeyError, TypeError):
        pass


def export_project_pdf(project, photos, template_components, output_path, root):
    """
    Genera il PDF del fotolibro.

    Struttura:
    - Pagina 1: copertina (template cover, se presente)
    - Pagine successive:
        * foto con position_data → layout manuale, raggruppate per page_number
        * foto senza position_data → auto-grid 2×2
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cover = next((tc for tc in template_components if tc['component_type'] == 'cover'), None)
    inner = next((tc for tc in template_components if tc['component_type'] == 'inner'), None)

    c = canvas.Canvas(output_path, pagesize=PAGE_SIZE)
    total_pages = 0

    # --- Cover ---
    if cover:
        _draw_background(c, cover['file_path'], root)
    c.showPage()
    total_pages += 1

    # --- Pagine con posizionamento manuale ---
    positioned = [p for p in photos if p['position_data']]
    if positioned:
        by_page = {}
        for photo in positioned:
            key = photo['page_number'] or 1
            by_page.setdefault(key, []).append(photo)

        for page_num in sorted(by_page):
            if inner:
                _draw_background(c, inner['file_path'], root)
            for photo in by_page[page_num]:
                _draw_positioned(c, photo, root)
            c.showPage()
            total_pages += 1

    # --- Pagine auto-grid ---
    auto = [p for p in photos if not p['position_data']]
    for i in range(0, len(auto), 4):
        if inner:
            _draw_background(c, inner['file_path'], root)
        _draw_grid(c, auto[i:i + 4], root)
        c.showPage()
        total_pages += 1

    c.save()
    return total_pages
