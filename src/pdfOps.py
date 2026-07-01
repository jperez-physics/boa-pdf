"""!
@file pdfOps.py
@brief Core PDF operations and thumbnail rendering for BoaPDF.
@details All functions here are UI-agnostic (except that thumbnails are returned as
         tk.PhotoImage so they can be shown directly). They are kept separate from the
         screens so the logic can be tested on its own.
@author Jaime
"""
import os
import tkinter as tk

import fitz  # PyMuPDF

from .style import thumbWidth


def openPdf(path):
    """!
    @brief Open a PDF document.
    @param path Path to the PDF file.
    @return The opened fitz.Document.
    @exception ValueError If the file is missing or password protected.
    """
    doc = fitz.open(path)
    if doc.needs_pass:
        doc.close()
        raise ValueError("The PDF is password protected.")
    return doc


def renderThumb(page, width=thumbWidth):
    """!
    @brief Render a PDF page as a thumbnail image.
    @param page A fitz.Page to rasterize.
    @param width Target thumbnail width in pixels.
    @return tk.PhotoImage thumbnail of the page.
    """
    zoom = width / page.rect.width if page.rect.width else 1
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return tk.PhotoImage(data=pix.tobytes("png"))


def rotatePhoto(img, degrees):
    """!
    @brief Rotate a tk.PhotoImage by a multiple of 90 degrees (no extra deps).
    @param img Source tk.PhotoImage.
    @param degrees Rotation angle; only multiples of 90 are meaningful.
    @return A new, rotated tk.PhotoImage.
    """
    degrees %= 360
    if degrees == 0:
        return img
    width, height = img.width(), img.height()
    if degrees == 180:
        out = tk.PhotoImage(width=width, height=height)
        for x in range(width):
            for y in range(height):
                out.put("#%02x%02x%02x" % img.get(x, y), (width - 1 - x, height - 1 - y))
        return out
    out = tk.PhotoImage(width=height, height=width)  # 90 / 270 swap the axes
    for x in range(width):
        for y in range(height):
            color = "#%02x%02x%02x" % img.get(x, y)
            if degrees == 90:
                out.put(color, (height - 1 - y, x))
            else:  # 270
                out.put(color, (y, width - 1 - x))
    return out


def parseRanges(spec, total):
    """!
    @brief Parse a page-range spec into 0-based index pairs.
    @param spec Range spec, e.g. "1-3, 5, 8-10".
    @param total Total page count of the document, used to validate bounds.
    @return List of (startIndex, endIndex) 0-based pairs.
    @exception ValueError If a range is malformed or out of bounds.
    """
    groups = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            first, last = chunk.split("-", 1)
            start, end = int(first), int(last)
        else:
            start = end = int(chunk)
        if start < 1 or end > total or start > end:
            raise ValueError(f"Invalid range: '{chunk}' (the PDF has {total} pages).")
        groups.append((start - 1, end - 1))
    if not groups:
        raise ValueError("Enter at least one page range.")
    return groups


def mergePdfs(paths, outPath):
    """!
    @brief Merge the given PDF files, in order, into a single document.
    @param paths Ordered list of source PDF paths.
    @param outPath Destination path for the merged PDF.
    @exception ValueError If any source PDF is password protected.
    """
    out = fitz.open()
    try:
        for path in paths:
            src = fitz.open(path)
            if src.needs_pass:
                raise ValueError(f"'{os.path.basename(path)}' is password protected.")
            out.insert_pdf(src)
            src.close()
        out.save(outPath)
    finally:
        out.close()


pageSizes = {
    "original": None,
    "a4":     (595.28, 841.89),
    "letter": (612, 792),
}
margin = 36  # 0.5 inch in points
gap = 18     # space between images on multi-image pages


def _validateImage(path):
    """!
    @brief Check that a file is a readable image.
    @param path Path to the candidate image file.
    @exception ValueError If the file is not a supported, readable image.
    """
    try:
        fitz.Pixmap(path)
    except Exception:
        raise ValueError(f"'{os.path.basename(path)}' is not a supported image.")


def _fitRect(imgW, imgH, cellW, cellH):
    """!
    @brief Compute a rect that centers an image inside a cell, preserving aspect ratio.
    @param imgW Source image width.
    @param imgH Source image height.
    @param cellW Target cell width.
    @param cellH Target cell height.
    @return fitz.Rect centered within the cell.
    """
    scale = min(cellW / imgW, cellH / imgH)
    w, h = imgW * scale, imgH * scale
    x = (cellW - w) / 2
    y = (cellH - h) / 2
    return fitz.Rect(x, y, x + w, y + h)


def imagesToPdf(paths, outPath, pageSize="original", perPage=1):
    """!
    @brief Combine one or more images into a single PDF.
    @param paths Ordered list of image file paths.
    @param outPath Destination path for the generated PDF.
    @param pageSize "original" keeps each image's native size; "a4" or "letter"
           fits images onto that paper size.
    @param perPage How many images per page (1, 2 or 4). Ignored when pageSize is "original".
    @exception ValueError If paths is empty or an image is not supported/readable.
    """
    if not paths:
        raise ValueError("Add at least one image.")
    for path in paths:
        _validateImage(path)

    out = fitz.open()
    try:
        if pageSize == "original":
            for path in paths:
                img = fitz.open(path)
                pdfBytes = img.convert_to_pdf()
                img.close()
                imgPdf = fitz.open("pdf", pdfBytes)
                out.insert_pdf(imgPdf)
                imgPdf.close()
        else:
            pw, ph = pageSizes[pageSize]
            cols = 2 if perPage >= 4 else 1
            rows = 2 if perPage >= 2 else 1
            usableW = pw - margin * 2 - gap * (cols - 1)
            usableH = ph - margin * 2 - gap * (rows - 1)
            cellW = usableW / cols
            cellH = usableH / rows

            for i in range(0, len(paths), perPage):
                batch = paths[i:i + perPage]
                page = out.new_page(width=pw, height=ph)
                for slot, path in enumerate(batch):
                    col = slot % cols
                    row = slot // cols
                    originX = margin + col * (cellW + gap)
                    originY = margin + row * (cellH + gap)
                    pix = fitz.Pixmap(path)
                    fit = _fitRect(pix.width, pix.height, cellW, cellH)
                    fit = fit + fitz.Rect(originX, originY, originX, originY)
                    page.insert_image(fit, filename=path)

        out.save(outPath)
    finally:
        out.close()


def extractToFile(doc, groups, outPath):
    """!
    @brief Write a single PDF containing the pages from the given groups.
    @param doc Source fitz.Document.
    @param groups List of (startIndex, endIndex) 0-based page-range pairs.
    @param outPath Destination path for the resulting PDF.
    """
    out = fitz.open()
    try:
        for start, end in groups:
            out.insert_pdf(doc, from_page=start, to_page=end)
        out.save(outPath)
    finally:
        out.close()


def splitRangesToFolder(doc, groups, folder, baseName):
    """!
    @brief Write one PDF per (start, end) page-range group.
    @param doc Source fitz.Document.
    @param groups List of (startIndex, endIndex) 0-based page-range pairs.
    @param folder Destination folder for the generated PDFs.
    @param baseName Base file name used to build each output file name.
    @return Number of files written.
    """
    for index, (start, end) in enumerate(groups, start=1):
        out = fitz.open()
        out.insert_pdf(doc, from_page=start, to_page=end)
        out.save(os.path.join(folder, f"{baseName}_part_{index}.pdf"))
        out.close()
    return len(groups)


def splitEachToFolder(doc, folder, baseName):
    """!
    @brief Write one PDF per page of the source document.
    @param doc Source fitz.Document.
    @param folder Destination folder for the generated PDFs.
    @param baseName Base file name used to build each output file name.
    @return Number of files written.
    """
    for index in range(doc.page_count):
        out = fitz.open()
        out.insert_pdf(doc, from_page=index, to_page=index)
        out.save(os.path.join(folder, f"{baseName}_page_{index + 1}.pdf"))
        out.close()
    return doc.page_count


def buildOrganized(doc, items, outPath):
    """!
    @brief Rebuild a PDF following the order, rotation and kept pages in items.
    @param doc Source fitz.Document.
    @param items List of dicts {"index": originalPageIndex, "rotate": degrees}.
    @param outPath Destination path for the rebuilt PDF.
    """
    out = fitz.open()
    try:
        for item in items:
            out.insert_pdf(doc, from_page=item["index"], to_page=item["index"])
            if item["rotate"]:
                page = out[out.page_count - 1]
                page.set_rotation((page.rotation + item["rotate"]) % 360)
        out.save(outPath)
    finally:
        out.close()
