"""!
@file icons.py
@brief Load the Lucide SVG icons in assets/ as tk.PhotoImage for the UI.
@details Tkinter cannot draw SVG directly, so each icon is rasterized with PyMuPDF
         (the same dependency used for thumbnails). currentColor in the SVG is
         swapped for the requested color, and the result is cached by (name, size,
         color) — the cache also keeps the PhotoImage references alive.
"""
import os
import tkinter as tk

import fitz  # PyMuPDF

from .style import colorBrand

assetsDir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
_cache = {}


def icon(name, size, color=colorBrand):
    """!
    @brief Return a Lucide icon as a square tk.PhotoImage.
    @param name Icon name, e.g. "combine" (matches a file in assets/).
    @param size Width and height of the rasterized icon, in pixels.
    @param color Fill color substituted for currentColor in the SVG.
    @return Cached tk.PhotoImage for (name, size, color).
    """
    key = (name, size, color)
    if key not in _cache:
        with open(os.path.join(assetsDir, f"{name}.svg"), encoding="utf-8") as file:
            svg = file.read().replace("currentColor", color)
        doc = fitz.open(stream=svg.encode("utf-8"), filetype="svg")
        page = doc[0]
        zoom = size / page.rect.width if page.rect.width else 1
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
        doc.close()
        _cache[key] = tk.PhotoImage(data=pix.tobytes("png"))
    return _cache[key]
