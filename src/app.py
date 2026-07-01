"""!
@file app.py
@brief Main application window for BoaPDF (top bar + screen switching).
"""
import tkinter as tk

from .style import colorBg, colorCard, colorBrand, colorInk, colorLine, fontFamily
from .screens import (HomeScreen, MergeScreen, SplitScreen, OrganizeScreen,
                      ImageToPdfScreen)


class BoaPdf(tk.Tk):
    """!
    @brief Root application window: builds the header bar and swaps screens.
    """

    def __init__(self):
        super().__init__()
        self.title("BoaPDF")
        self.geometry("980x740")
        self.minsize(820, 600)
        self.configure(bg=colorBg)

        self.buildHeader()
        self.container = tk.Frame(self, bg=colorBg)
        self.container.pack(fill="both", expand=True)
        self.showHome()

    def buildHeader(self):
        bar = tk.Frame(self, bg=colorCard, height=62)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Frame(self, bg=colorLine, height=1).pack(fill="x")  # hairline under the bar

        logoFrame = tk.Frame(bar, bg=colorCard, cursor="hand2")
        logoFrame.pack(side="left", padx=28)
        logoFont = (fontFamily, 18, "bold")
        logoBoa = tk.Label(logoFrame, text="Boa", bg=colorCard, fg=colorInk, font=logoFont, cursor="hand2")
        logoBoa.pack(side="left")
        logoPdf = tk.Label(logoFrame, text="PDF", bg=colorCard, fg=colorBrand, font=logoFont, cursor="hand2")
        logoPdf.pack(side="left")
        for widget in (logoFrame, logoBoa, logoPdf):
            widget.bind("<Button-1>", lambda e: self.showHome())

    def swap(self, builder):
        for child in self.container.winfo_children():
            child.destroy()
        builder(self.container)

    def showHome(self):
        self.swap(HomeScreen)

    def showMerge(self, files=None):
        self.swap(lambda master: MergeScreen(master, preload=files))

    def showSplit(self):
        self.swap(SplitScreen)

    def showOrganize(self):
        self.swap(OrganizeScreen)

    def showImageToPdf(self):
        self.swap(ImageToPdfScreen)
