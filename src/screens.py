"""!
@file screens.py
@brief The five screens of BoaPDF: Home, Merge, Split, Organize and Image to PDF.
"""
import os
import tkinter as tk
from tkinter import filedialog

from .style import colorBg, colorCard, colorInk, colorMuted, colorBrand, colorTint, colorLine, colorDisabled, fontFamily, gridCols
from .widgets import (FlatButton, Segmented, RoundedCard, ScrollFrame,
                      toolHeader, statusLabel, setStatus)
from .icons import icon
from . import pdfOps


# --------------------------------------------------------------------------- #
# Home
# --------------------------------------------------------------------------- #
class HomeScreen(tk.Frame):
    """!
    @brief Landing screen with the four feature cards (Merge, Split, Organize, Image to PDF).
    @param master Parent widget.
    """

    def __init__(self, master):
        super().__init__(master, bg=colorBg)
        self.pack(fill="both", expand=True)
        app = self.winfo_toplevel()

        wrap = tk.Frame(self, bg=colorBg)
        wrap.pack(fill="both", expand=True, padx=56, pady=(44, 28))

        tk.Label(wrap, text="All your PDF tools in one place",
                 bg=colorBg, fg=colorInk, font=(fontFamily, 22, "bold")).pack()
        tk.Label(wrap, text="Choose a tool to get started.",
                 bg=colorBg, fg=colorMuted, font=(fontFamily, 11)).pack(pady=(4, 28))

        # Feature cards (2×2 grid)
        cards = tk.Frame(wrap, bg=colorBg)
        cards.pack(fill="both", expand=True)
        cards.columnconfigure((0, 1), weight=1, uniform="c")
        cards.rowconfigure((0, 1), weight=1, uniform="r")
        data = [
            ("combine", "Merge PDF", "Combine several PDFs into a single document, in the order you choose.", app.showMerge),
            ("scissors", "Split PDF", "Split a PDF into several files or extract just the pages you need.", app.showSplit),
            ("files", "Organize PDF", "Reorder, rotate and delete pages of a PDF.", app.showOrganize),
            ("file-image", "Image to PDF", "Turn JPG, PNG and other images into a single PDF document.", app.showImageToPdf),
        ]
        for index, (iconName, title, desc, command) in enumerate(data):
            self.makeCard(cards, iconName, title, desc, command).grid(
                row=index // 2, column=index % 2, sticky="nsew", padx=10, pady=8)

    def makeCard(self, master, iconName, title, desc, command):
        card = RoundedCard(master)
        pad = card.inner
        tk.Label(pad, image=icon(iconName, 34), bg=colorCard).pack(anchor="w")
        tk.Label(pad, text=title, bg=colorCard, fg=colorInk, font=(fontFamily, 14, "bold")).pack(anchor="w", pady=(12, 5))
        tk.Label(pad, text=desc, bg=colorCard, fg=colorMuted, font=(fontFamily, 10), justify="left",
                 wraplength=230).pack(anchor="w")
        surfaces = [card, pad] + list(pad.winfo_children())

        def hover(active):
            card.setColors(colorTint if active else colorCard, colorBrand if active else colorLine)

        for widget in surfaces:
            widget.config(cursor="hand2")
            widget.bind("<Button-1>", lambda e: command())
            widget.bind("<Enter>", lambda e: hover(True))
            widget.bind("<Leave>", lambda e: hover(False))
        return card


# --------------------------------------------------------------------------- #
# Merge
# --------------------------------------------------------------------------- #
class MergeScreen(tk.Frame):
    """!
    @brief Screen for combining several PDFs, in a chosen order, into one document.
    @param master Parent widget.
    @param preload Optional list of file paths to pre-populate the merge list.
    """

    def __init__(self, master, preload=None):
        super().__init__(master, bg=colorBg)
        self.pack(fill="both", expand=True)
        self.files = []  # ordered paths

        toolHeader(self, "combine", "Merge PDF",
                   "Combine several PDFs into one. Order the list before merging.")

        body = tk.Frame(self, bg=colorBg)
        body.pack(fill="both", expand=True, padx=40, pady=(8, 0))

        bar = tk.Frame(body, bg=colorBg)
        bar.pack(fill="x")
        FlatButton(bar, "+ Add PDF", self.addFiles, kind="ghost").pack(side="left")

        self.listbox = tk.Listbox(body, font=(fontFamily, 11), activestyle="none", bg=colorCard, fg=colorInk,
                                  selectbackground="#d4f0e2", selectforeground=colorInk,
                                  highlightthickness=1, highlightbackground=colorLine, bd=0, height=10)
        self.listbox.pack(fill="both", expand=True, pady=12)

        controls = tk.Frame(body, bg=colorBg)
        controls.pack(fill="x")
        for text, command in (("↑ Up", lambda: self.move(-1)),
                              ("↓ Down", lambda: self.move(1)),
                              ("✕ Remove", self.remove)):
            FlatButton(controls, text, command, kind="ghost").pack(side="left", padx=(0, 8))
        self.goButton = FlatButton(controls, "Merge PDF", self.merge)
        self.goButton.pack(side="right")

        self.status = statusLabel(body)

        if preload:
            self.files = list(preload)
            self.refresh()

    def refresh(self):
        self.listbox.delete(0, "end")
        for path in self.files:
            self.listbox.insert("end", "   " + os.path.basename(path))
        self.goButton.setEnabled(len(self.files) >= 2)
        if len(self.files) == 1:
            setStatus(self.status, "Add at least one more PDF to merge.")
        else:
            setStatus(self.status, "")

    def addFiles(self):
        files = filedialog.askopenfilenames(title="Add PDF", filetypes=[("PDF", "*.pdf")])
        self.files.extend(files)
        self.refresh()

    def selectedIndex(self):
        selection = self.listbox.curselection()
        return selection[0] if selection else None

    def move(self, delta):
        index = self.selectedIndex()
        if index is None:
            return
        target = index + delta
        if 0 <= target < len(self.files):
            self.files[index], self.files[target] = self.files[target], self.files[index]
            self.refresh()
            self.listbox.selection_set(target)

    def remove(self):
        index = self.selectedIndex()
        if index is not None:
            self.files.pop(index)
            self.refresh()

    def merge(self):
        if len(self.files) < 2:
            return
        outPath = filedialog.asksaveasfilename(
            title="Save merged PDF", defaultextension=".pdf",
            initialfile="boapdf_merged.pdf", filetypes=[("PDF", "*.pdf")])
        if not outPath:
            return
        setStatus(self.status, "Merging...")
        try:
            pdfOps.mergePdfs(self.files, outPath)
        except Exception as error:
            setStatus(self.status, str(error), "err")
            return
        setStatus(self.status, f"✓ Saved to {outPath}", "ok")


# --------------------------------------------------------------------------- #
# Split
# --------------------------------------------------------------------------- #
class SplitScreen(tk.Frame):
    """!
    @brief Screen for splitting a PDF by ranges, extracting pages, or separating every page.
    @param master Parent widget.
    """

    def __init__(self, master):
        super().__init__(master, bg=colorBg)
        self.pack(fill="both", expand=True)
        self.path = None
        self.doc = None
        self.thumbs = []

        toolHeader(self, "scissors", "Split PDF",
                   "Split by ranges, extract pages or separate every page.")

        body = tk.Frame(self, bg=colorBg)
        body.pack(fill="both", expand=True, padx=40, pady=(8, 0))

        top = tk.Frame(body, bg=colorBg)
        top.pack(fill="x")
        FlatButton(top, "Load PDF", self.loadPdf, kind="ghost").pack(side="left")
        self.docName = tk.Label(top, text="No file loaded", bg=colorBg, fg=colorMuted, font=(fontFamily, 10))
        self.docName.pack(side="left", padx=12)

        options = tk.Frame(body, bg=colorBg)
        options.pack(fill="x", pady=(12, 4))
        self.mode = tk.StringVar(value="ranges")
        Segmented(options, (("ranges", "Split by ranges"),
                            ("extract", "Extract pages (1 PDF)"),
                            ("each", "Separate all pages")),
                  self.mode, command=self.toggleRanges).pack(side="left")

        self.rangeRow = tk.Frame(body, bg=colorBg)
        self.rangeRow.pack(fill="x")
        tk.Label(self.rangeRow, text="Pages / ranges:", bg=colorBg, fg=colorInk, font=(fontFamily, 10)).pack(side="left")
        self.rangesEntry = tk.Entry(self.rangeRow, font=(fontFamily, 11), width=24, bg=colorCard,
                                    highlightthickness=1, highlightbackground=colorLine, bd=0)
        self.rangesEntry.pack(side="left", padx=8, ipady=4)
        tk.Label(self.rangeRow, text="e.g.  1-3, 5, 8-10", bg=colorBg, fg=colorMuted, font=(fontFamily, 9)).pack(side="left")

        self.gridArea = ScrollFrame(body)
        self.gridArea.pack(fill="both", expand=True, pady=12)

        bottom = tk.Frame(body, bg=colorBg)
        bottom.pack(fill="x")
        self.goButton = FlatButton(bottom, "Split PDF", self.process)
        self.goButton.pack(side="right")
        self.goButton.setEnabled(False)
        self.status = statusLabel(bottom)

    def toggleRanges(self):
        if self.mode.get() == "each":
            self.rangeRow.pack_forget()
        else:
            self.rangeRow.pack(fill="x", after=self.gridArea.master.winfo_children()[1])

    def loadPdf(self):
        path = filedialog.askopenfilename(title="Load PDF", filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            doc = pdfOps.openPdf(path)
        except Exception as error:
            setStatus(self.status, str(error), "err")
            return
        if self.doc:
            self.doc.close()
        self.doc, self.path = doc, path
        self.docName.config(text=f"{os.path.basename(path)} · {doc.page_count} page(s)", fg=colorInk)
        self.showPages()
        self.goButton.setEnabled(True)
        setStatus(self.status, "")

    def showPages(self):
        self.gridArea.clear()
        self.thumbs = []
        for index, page in enumerate(self.doc):
            img = pdfOps.renderThumb(page)
            self.thumbs.append(img)
            cell = tk.Frame(self.gridArea.inner, bg=colorCard, highlightbackground=colorLine, highlightthickness=1)
            cell.grid(row=index // gridCols, column=index % gridCols, padx=6, pady=6)
            tk.Label(cell, image=img, bg=colorCard).pack(padx=6, pady=(6, 2))
            tk.Label(cell, text=f"Page {index + 1}", bg=colorCard, fg=colorMuted, font=(fontFamily, 8, "bold")).pack(pady=(0, 6))

    def process(self):
        if not self.doc:
            return
        mode = self.mode.get()
        total = self.doc.page_count
        try:
            if mode == "extract":
                groups = pdfOps.parseRanges(self.rangesEntry.get(), total)
                outPath = filedialog.asksaveasfilename(
                    title="Save cropped PDF", defaultextension=".pdf",
                    initialfile="boapdf_cropped.pdf", filetypes=[("PDF", "*.pdf")])
                if not outPath:
                    return
                pdfOps.extractToFile(self.doc, groups, outPath)
                setStatus(self.status, f"✓ Saved to {outPath}", "ok")
                return

            # 'ranges' and 'each' produce several files -> choose a folder
            folder = filedialog.askdirectory(title="Folder to save the PDFs")
            if not folder:
                return
            baseName = os.path.splitext(os.path.basename(self.path))[0]
            if mode == "each":
                count = pdfOps.splitEachToFolder(self.doc, folder, baseName)
            else:  # ranges
                groups = pdfOps.parseRanges(self.rangesEntry.get(), total)
                count = pdfOps.splitRangesToFolder(self.doc, groups, folder, baseName)
            setStatus(self.status, f"✓ {count} file(s) saved to {folder}", "ok")
        except ValueError as error:
            setStatus(self.status, str(error), "err")
        except Exception as error:
            setStatus(self.status, f"Error: {error}", "err")


# --------------------------------------------------------------------------- #
# Organize
# --------------------------------------------------------------------------- #
class OrganizeScreen(tk.Frame):
    """!
    @brief Screen for reordering, rotating and deleting pages of a PDF before saving it.
    @param master Parent widget.
    """

    def __init__(self, master):
        super().__init__(master, bg=colorBg)
        self.pack(fill="both", expand=True)
        self.path = None
        self.doc = None
        self.baseThumbs = []     # original thumbnail per page
        self.items = []          # [{index, rotate}] in current order
        self.photoCache = {}     # (index, rotate) -> PhotoImage

        toolHeader(self, "files", "Organize PDF",
                   "Reorder with ◀ ▶, rotate with ⟳ and delete with ✕.")

        body = tk.Frame(self, bg=colorBg)
        body.pack(fill="both", expand=True, padx=40, pady=(8, 0))

        top = tk.Frame(body, bg=colorBg)
        top.pack(fill="x")
        FlatButton(top, "Load PDF", self.loadPdf, kind="ghost").pack(side="left")
        self.docName = tk.Label(top, text="No file loaded", bg=colorBg, fg=colorMuted, font=(fontFamily, 10))
        self.docName.pack(side="left", padx=12)

        self.gridArea = ScrollFrame(body)
        self.gridArea.pack(fill="both", expand=True, pady=12)

        bottom = tk.Frame(body, bg=colorBg)
        bottom.pack(fill="x")
        self.goButton = FlatButton(bottom, "Save PDF", self.save)
        self.goButton.pack(side="right")
        self.goButton.setEnabled(False)
        self.status = statusLabel(bottom)

    def loadPdf(self):
        path = filedialog.askopenfilename(title="Load PDF", filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            doc = pdfOps.openPdf(path)
        except Exception as error:
            setStatus(self.status, str(error), "err")
            return
        if self.doc:
            self.doc.close()
        self.doc, self.path = doc, path
        self.docName.config(text=f"{os.path.basename(path)} · {doc.page_count} page(s)", fg=colorInk)
        self.baseThumbs = [pdfOps.renderThumb(page) for page in doc]
        self.items = [{"index": i, "rotate": 0} for i in range(doc.page_count)]
        self.photoCache = {}
        self.render()
        self.goButton.setEnabled(True)
        setStatus(self.status, "")

    def photoFor(self, index, rotate):
        key = (index, rotate)
        if key not in self.photoCache:
            self.photoCache[key] = pdfOps.rotatePhoto(self.baseThumbs[index], rotate)
        return self.photoCache[key]

    def render(self):
        self.gridArea.clear()
        for pos, item in enumerate(self.items):
            img = self.photoFor(item["index"], item["rotate"])
            cell = tk.Frame(self.gridArea.inner, bg=colorCard, highlightbackground=colorLine, highlightthickness=1)
            cell.grid(row=pos // gridCols, column=pos % gridCols, padx=6, pady=6)

            tools = tk.Frame(cell, bg=colorCard)
            tools.pack(fill="x", padx=4, pady=(4, 0))
            self.miniButton(tools, "◀", lambda p=pos: self.move(p, -1)).pack(side="left")
            self.miniButton(tools, "⟳", lambda p=pos: self.rotate(p)).pack(side="left")
            self.miniButton(tools, "✕", lambda p=pos: self.delete(p), danger=True).pack(side="left")
            self.miniButton(tools, "▶", lambda p=pos: self.move(p, 1)).pack(side="right")

            tk.Label(cell, image=img, bg=colorCard).pack(padx=6, pady=2)
            tk.Label(cell, text=f"Page {item['index'] + 1}", bg=colorCard, fg=colorMuted,
                     font=(fontFamily, 8, "bold")).pack(pady=(0, 6))
        self.goButton.setEnabled(bool(self.items))
        if not self.items:
            setStatus(self.status, "No pages left. Load a PDF again.", "err")

    def miniButton(self, master, text, command, danger=False):
        label = tk.Label(master, text=text, bg=colorCard, fg=(colorBrand if danger else colorMuted),
                         font=(fontFamily, 10, "bold"), cursor="hand2", padx=3)
        label.bind("<Button-1>", lambda e: command())
        label.bind("<Enter>", lambda e: label.config(fg=colorBrand))
        label.bind("<Leave>", lambda e: label.config(fg=(colorBrand if danger else colorMuted)))
        return label

    def move(self, pos, delta):
        target = pos + delta
        if 0 <= target < len(self.items):
            self.items[pos], self.items[target] = self.items[target], self.items[pos]
            self.render()

    def rotate(self, pos):
        self.items[pos]["rotate"] = (self.items[pos]["rotate"] + 90) % 360
        self.render()

    def delete(self, pos):
        self.items.pop(pos)
        self.render()

    def save(self):
        if not self.items:
            return
        outPath = filedialog.asksaveasfilename(
            title="Save organized PDF", defaultextension=".pdf",
            initialfile="boapdf_organized.pdf", filetypes=[("PDF", "*.pdf")])
        if not outPath:
            return
        setStatus(self.status, "Saving...")
        try:
            pdfOps.buildOrganized(self.doc, self.items, outPath)
        except Exception as error:
            setStatus(self.status, f"Error: {error}", "err")
            return
        setStatus(self.status, f"✓ Saved to {outPath}", "ok")


# --------------------------------------------------------------------------- #
# Image to PDF
# --------------------------------------------------------------------------- #
imageTypes = [
    ("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.pnm *.webp"),
    ("All files", "*.*"),
]


class ImageToPdfScreen(tk.Frame):
    """!
    @brief Screen for combining images into a PDF, with page-size and layout options.
    @param master Parent widget.
    """

    def __init__(self, master):
        super().__init__(master, bg=colorBg)
        self.pack(fill="both", expand=True)
        self.files = []  # ordered image paths

        toolHeader(self, "file-image", "Image to PDF",
                   "Turn JPG, PNG and other images into a PDF document.")

        body = tk.Frame(self, bg=colorBg)
        body.pack(fill="both", expand=True, padx=40, pady=(8, 0))

        # Options row
        optionsRow = tk.Frame(body, bg=colorBg)
        optionsRow.pack(fill="x", pady=(0, 8))

        tk.Label(optionsRow, text="Page size", bg=colorBg, fg=colorInk,
                 font=(fontFamily, 10, "bold")).pack(side="left", padx=(0, 8))
        self.pageSize = tk.StringVar(value="a4")
        Segmented(optionsRow, (("original", "Original"),
                               ("a4", "A4"),
                               ("letter", "Letter")),
                  self.pageSize, command=self.onPageSizeChange).pack(side="left")

        self.perPageFrame = tk.Frame(optionsRow, bg=colorBg)
        self.perPageFrame.pack(side="left")
        tk.Label(self.perPageFrame, text="Images per page", bg=colorBg, fg=colorInk,
                 font=(fontFamily, 10, "bold")).pack(side="left", padx=(24, 8))
        self.perPage = tk.StringVar(value="1")
        Segmented(self.perPageFrame, (("1", "1"), ("2", "2"), ("4", "4")),
                  self.perPage).pack(side="left")

        bar = tk.Frame(body, bg=colorBg)
        bar.pack(fill="x")
        FlatButton(bar, "+ Add images", self.addFiles, kind="ghost").pack(side="left")

        self.listbox = tk.Listbox(body, font=(fontFamily, 11), activestyle="none", bg=colorCard, fg=colorInk,
                                  selectbackground="#d4f0e2", selectforeground=colorInk,
                                  highlightthickness=1, highlightbackground=colorLine, bd=0, height=10)
        self.listbox.pack(fill="both", expand=True, pady=12)

        controls = tk.Frame(body, bg=colorBg)
        controls.pack(fill="x")
        for text, command in (("↑ Up", lambda: self.move(-1)),
                              ("↓ Down", lambda: self.move(1)),
                              ("✕ Remove", self.remove)):
            FlatButton(controls, text, command, kind="ghost").pack(side="left", padx=(0, 8))
        self.goButton = FlatButton(controls, "Create PDF", self.convert)
        self.goButton.pack(side="right")

        self.status = statusLabel(body)
        self.refresh()

    def onPageSizeChange(self):
        if self.pageSize.get() != "original":
            self.perPageFrame.pack(side="left")
        else:
            self.perPageFrame.pack_forget()

    def refresh(self):
        self.listbox.delete(0, "end")
        for path in self.files:
            self.listbox.insert("end", "   " + os.path.basename(path))
        self.goButton.setEnabled(len(self.files) >= 1)
        if not self.files:
            setStatus(self.status, "Add one or more images to create a PDF.")
        else:
            setStatus(self.status, "")

    def addFiles(self):
        files = filedialog.askopenfilenames(title="Add images", filetypes=imageTypes)
        self.files.extend(files)
        self.refresh()

    def selectedIndex(self):
        selection = self.listbox.curselection()
        return selection[0] if selection else None

    def move(self, delta):
        index = self.selectedIndex()
        if index is None:
            return
        target = index + delta
        if 0 <= target < len(self.files):
            self.files[index], self.files[target] = self.files[target], self.files[index]
            self.refresh()
            self.listbox.selection_set(target)

    def remove(self):
        index = self.selectedIndex()
        if index is not None:
            self.files.pop(index)
            self.refresh()

    def convert(self):
        if not self.files:
            return
        outPath = filedialog.asksaveasfilename(
            title="Save PDF", defaultextension=".pdf",
            initialfile="boapdf_images.pdf", filetypes=[("PDF", "*.pdf")])
        if not outPath:
            return
        setStatus(self.status, "Creating PDF...")
        ps = self.pageSize.get()
        pp = int(self.perPage.get()) if ps != "original" else 1
        try:
            pdfOps.imagesToPdf(self.files, outPath, pageSize=ps, perPage=pp)
        except ValueError as error:
            setStatus(self.status, str(error), "err")
            return
        except Exception as error:
            setStatus(self.status, f"Error: {error}", "err")
            return
        setStatus(self.status, f"✓ Saved to {outPath}", "ok")