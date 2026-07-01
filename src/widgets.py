"""!
@file widgets.py
@brief Reusable Tkinter widgets and small UI helpers for BoaPDF.
"""
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

from .style import (colorBg, colorCard, colorInk, colorMuted, colorBrand, colorBrandDark, colorTint, colorLine, colorGreen,
                    colorDisabled, colorGhost, colorGhostHover, fontFamily, radiusButton, radiusCard)
from .icons import icon


def roundRect(canvas, x1, y1, x2, y2, radius, **kw):
    """!
    @brief Draw a rounded rectangle on a canvas as a smooth polygon.
    @param canvas Target tk.Canvas.
    @param x1 Left coordinate.
    @param y1 Top coordinate.
    @param x2 Right coordinate.
    @param y2 Bottom coordinate.
    @param radius Corner radius.
    @return The canvas item id of the created polygon.
    """
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kw)


class FlatButton(tk.Canvas):
    """!
    @brief A rounded, styled button drawn on a Canvas (colors handled manually).
    @param master Parent widget.
    @param text Button label.
    @param command Callable invoked on click.
    @param kind "primary", "ghost" or "link" — controls the color scheme.
    """

    def __init__(self, master, text, command, kind="primary", **kw):
        surface = master.cget("bg")
        if kind == "primary":
            self._bg, self._fg, self._hover = colorBrand, "#ffffff", colorBrandDark
        elif kind == "ghost":
            self._bg, self._fg, self._hover = colorGhost, colorInk, colorGhostHover
        else:  # link
            self._bg, self._fg, self._hover = surface, colorMuted, surface
        self._font = tkfont.Font(family=fontFamily, size=11, weight="bold")
        padX, padY = 22, 11
        width = self._font.measure(text) + padX * 2
        height = self._font.metrics("linespace") + padY * 2
        super().__init__(master, width=width, height=height, bg=surface,
                         highlightthickness=0, bd=0, **kw)
        self._text = text
        self._command = command
        self._enabled = True
        self._render(self._bg)
        self.config(cursor="hand2")
        self.bind("<Button-1>", self._onClick)
        self.bind("<Enter>", lambda e: self._enabled and self._render(self._hover))
        self.bind("<Leave>", lambda e: self._enabled and self._render(self._bg))

    def _render(self, fill):
        self.delete("all")
        width = int(self["width"])
        height = int(self["height"])
        roundRect(self, 1, 1, width - 1, height - 1, radiusButton, fill=fill, outline=fill)
        self.create_text(width // 2, height // 2 + 1, text=self._text,
                         fill=self._fg, font=self._font)

    def _onClick(self, _event):
        if self._enabled and self._command:
            self._command()

    def setEnabled(self, enabled):
        self._enabled = enabled
        if enabled:
            self._render(self._bg)
            self.config(cursor="hand2")
        else:
            self._render(colorDisabled)
            self.config(cursor="arrow")


class Segmented(tk.Frame):
    """!
    @brief A pill-style single-choice control (replaces native radio buttons).
    @param master Parent widget.
    @param options Iterable of (value, label) pairs.
    @param variable tk.Variable bound to the selected value.
    @param command Optional callable invoked when the selection changes.
    """

    def __init__(self, master, options, variable, command=None, **kw):
        super().__init__(master, bg=master.cget("bg"), **kw)
        self._var = variable
        self._command = command
        self._font = tkfont.Font(family=fontFamily, size=10, weight="bold")
        self._buttons = {}
        for value, text in options:
            button = self._makeSegment(text, value)
            button.pack(side="left", padx=(0, 8))
            self._buttons[value] = button
        self._render()

    def _makeSegment(self, text, value):
        padX, padY = 16, 8
        width = self._font.measure(text) + padX * 2
        height = self._font.metrics("linespace") + padY * 2
        segment = tk.Canvas(self, width=width, height=height, bg=self.cget("bg"),
                            highlightthickness=0, bd=0, cursor="hand2")
        segment.label = text
        segment.bind("<Button-1>", lambda e, v=value: self._select(v))
        return segment

    def _select(self, value):
        self._var.set(value)
        self._render()
        if self._command:
            self._command()

    def _render(self):
        current = self._var.get()
        for value, segment in self._buttons.items():
            selected = value == current
            width = int(segment["width"])
            height = int(segment["height"])
            fill = colorBrand if selected else colorGhost
            fg = "#ffffff" if selected else colorInk
            segment.delete("all")
            roundRect(segment, 1, 1, width - 1, height - 1, height // 2, fill=fill, outline=fill)
            segment.create_text(width // 2, height // 2 + 1, text=segment.label,
                                fill=fg, font=self._font)


class ScrollFrame(tk.Frame):
    """!
    @brief A vertically scrollable container, used to display many thumbnails.
    @param master Parent widget.
    """

    def __init__(self, master, **kw):
        super().__init__(master, bg=colorBg, **kw)
        self.canvas = tk.Canvas(self, bg=colorBg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=colorBg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._window, width=e.width))
        self.canvas.bind_all("<MouseWheel>", self._onWheel)
        self.bind("<Destroy>", self._onDestroy)

    def _onWheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def _onDestroy(self, event):
        """!
        @brief Remove the app-wide mouse-wheel binding once this frame is destroyed.
        @param event Tkinter <Destroy> event.
        @details bind_all() registers the wheel handler at the application level, so
                 without this cleanup it keeps firing after the frame (and its canvas)
                 are gone, raising TclError: invalid command name.
        """
        if event.widget is self:
            self.canvas.unbind_all("<MouseWheel>")

    def clear(self):
        for child in self.inner.winfo_children():
            child.destroy()


class RoundedCard(tk.Canvas):
    """!
    @brief A card with rounded corners, drawn on a Canvas with content placed inside.
    @param master Parent widget.
    @param padx Horizontal padding applied to the inner content frame.
    @param pady Vertical padding applied to the inner content frame.
    """

    def __init__(self, master, padx=22, pady=22, **kw):
        super().__init__(master, bg=master.cget("bg"), highlightthickness=0, bd=0, **kw)
        self._padx = padx
        self._pady = pady
        self._fill = colorCard
        self._outline = colorLine
        self.inner = tk.Frame(self, bg=colorCard)
        self._win = self.create_window(0, 0, window=self.inner, anchor="nw")
        self.bind("<Configure>", self._onResize)

    def _onResize(self, event=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 2 or h < 2:
            return
        self.delete("bg")
        roundRect(self, 1, 1, w - 1, h - 1, radiusCard,
                  fill=self._fill, outline=self._outline, tags="bg")
        self.tag_lower("bg")
        self.itemconfig(self._win, width=w - 2, height=h - 2)
        self.coords(self._win, 1, 1)
        self.inner.config(padx=self._padx, pady=self._pady)

    def setColors(self, fill, outline):
        self._fill = fill
        self._outline = outline
        self._onResize()
        self.inner.config(bg=fill)
        for widget in self.inner.winfo_children():
            try:
                widget.config(bg=fill)
            except tk.TclError:
                pass


def toolHeader(parent, iconName, title, subtitle):
    """!
    @brief Build the common header (back link + title + subtitle) for a tool screen.
    @param parent Parent widget to attach the header to.
    @param iconName Lucide icon name shown next to the title.
    @param title Screen title text.
    @param subtitle Screen subtitle text.
    @return The header tk.Frame.
    """
    app = parent.winfo_toplevel()
    head = tk.Frame(parent, bg=colorBg)
    head.pack(fill="x", padx=40, pady=(18, 4))
    back = tk.Label(head, text="←  Back", bg=colorBg, fg=colorMuted, font=(fontFamily, 10, "bold"), cursor="hand2")
    back.pack(anchor="w")
    back.bind("<Button-1>", lambda e: app.showHome())
    titleRow = tk.Frame(head, bg=colorBg)
    titleRow.pack(pady=(8, 2))
    tk.Label(titleRow, image=icon(iconName, 24), bg=colorBg).pack(side="left", padx=(0, 8))
    tk.Label(titleRow, text=title, bg=colorBg, fg=colorInk, font=(fontFamily, 18, "bold")).pack(side="left")
    tk.Label(head, text=subtitle, bg=colorBg, fg=colorMuted, font=(fontFamily, 10)).pack()
    return head


def statusLabel(parent):
    """!
    @brief Create a status label used to show progress / success / error messages.
    @param parent Parent widget to attach the label to.
    @return The created tk.Label.
    """
    label = tk.Label(parent, text="", bg=colorBg, fg=colorMuted, font=(fontFamily, 10, "bold"))
    label.pack(pady=6)
    return label


def setStatus(label, text, kind="info"):
    """!
    @brief Update a status label's text and color.
    @param label Target tk.Label, normally created by statusLabel().
    @param text Message to display.
    @param kind "info", "ok" or "err" — selects the label color.
    """
    color = {"info": colorMuted, "ok": colorGreen, "err": colorBrand}[kind]
    label.config(text=text, fg=color)
    label.update_idletasks()
