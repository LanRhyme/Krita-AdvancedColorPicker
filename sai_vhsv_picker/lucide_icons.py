# -*- coding: utf-8 -*-
"""Lucide Icons renderer for sai_vhsv_picker"""

from .qt_compat import QIcon, QPixmap, QPainter, QColor, QByteArray, QSvgRenderer

_LUCIDE_SVGS = {
    "shield": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>""",
    "lock": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>""",
    "unlock": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg>""",
    "sliders": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="1" x2="7" y1="14" y2="14"/><line x1="9" x2="15" y1="8" y2="8"/><line x1="17" x2="23" y1="16" y2="16"/></svg>""",
    "palette": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/><circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/><circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/><circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.92 0 1.7-.72 1.7-1.65 0-.43-.17-.83-.44-1.12-.27-.29-.44-.7-.44-1.13 0-.93.77-1.7 1.7-1.7h2.48c2.76 0 5-2.24 5-5 0-5.52-4.48-10-10-10Z"/></svg>"""
}

_PIXMAP_CACHE = {}

def get_lucide_pixmap(name, color="#e0e0e0", size=16):
    cache_key = (name, color, size)
    cached = _PIXMAP_CACHE.get(cache_key)
    if cached is not None:
        return cached

    svg_raw = _LUCIDE_SVGS.get(name, _LUCIDE_SVGS["shield"])
    colored_svg = svg_raw.replace('currentColor', color)

    renderer = QSvgRenderer(QByteArray(colored_svg.encode('utf-8')))
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(RenderHint_Antialiasing, True)
    painter.setRenderHint(RenderHint_SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()

    _PIXMAP_CACHE[cache_key] = pixmap
    return pixmap

def get_lucide_icon(name, color="#e0e0e0", size=16):
    return QIcon(get_lucide_pixmap(name, color=color, size=size))
