import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps
import cv2
import time
import os
import threading
import queue

from utils import Style, MINING_DATA, ICON_PATH, VERSION

from scanner import OcrScanner

WIN_H = 215
WIN_W = 450

NUMBER_THRESHOLD = 1000
LOOP_DELAY = 200
MOVE_DELAY = 0.05


class RockScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RockScanner v" + VERSION)
        self.iconbitmap(ICON_PATH)
        self.geometry(str(WIN_W) + "x" + str(WIN_H))
        self.config(bg=Style.BG_COLOR)
        self.attributes("-topmost", True)
        self.current_img_ref = None
        self.scanning_active = False

        self.last_move_time = 0
        self.bind("<Configure>", self.on_window_move)

        self.result_queue = queue.Queue()

        self.scanner = OcrScanner(debug=False)
        self.setup_ui()

        self.ocr_label.grid_remove()
        self.ocr_entry.grid(row=0, column=0, sticky="w")
        self.status_label.config(text="MANUAL", fg=Style.ACCENT_COLOR)
        self.ocr_entry.focus_set()

        self._scan_thread = threading.Thread(target=self._scan_worker, daemon=True)
        self._scan_thread.start()

        self._poll_results()

    def on_window_move(self, event):
        self.last_move_time = time.time()

    def toggle_scan(self):
        self.scanning_active = not self.scanning_active
        if self.scanning_active:
            self._draw_toggle(active=True)
            self.status_label.config(text="SCANNING", fg="#FF3B30")
            self.ocr_entry.grid_remove()
            self.ocr_label.grid(row=0, column=0, sticky="w")
            self.ocr_label.config(text="-----")
            self._update_results_only(None, [])
        else:
            self._draw_toggle(active=False)
            self.status_label.config(text="MANUAL", fg=Style.ACCENT_COLOR)
            self.ocr_label.grid_remove()
            self.ocr_entry.grid(row=0, column=0, sticky="w")
            self._manual_var.set("")
            self._update_results_only(None, [])
            self.ocr_entry.focus_set()

    def setup_ui(self):
        top_bar = tk.Frame(self, bg=Style.BG_COLOR)
        top_bar.pack(fill=tk.X, padx=20, pady=(10, 0))

        self.toggle_canvas = tk.Canvas(
            top_bar, width=52, height=26,
            bg=Style.BG_COLOR, highlightthickness=0, cursor="hand2"
        )
        self.toggle_canvas.pack(side=tk.LEFT, padx=(0, 10))
        self.toggle_canvas.bind("<Button-1>", lambda e: self.toggle_scan())
        self._draw_toggle(active=False)

        self.status_label = tk.Label(
            top_bar, text="IDLE", fg="#555",
            bg=Style.BG_COLOR, font=(Style.FONT_FAMILY, 12)
        )
        self.status_label.pack(side=tk.LEFT)

        self.header = tk.Frame(self, bg=Style.BG_COLOR)
        self.header.pack(fill=tk.X, padx=20, pady=10)
        self.header.columnconfigure(0, weight=1)
        self.header.columnconfigure(1, weight=1)

        self.ocr_label = tk.Label(
            self.header, text="---",
            font=(Style.FONT_FAMILY, 24, "bold"),
            fg=Style.GOLD_COLOR, bg=Style.BG_COLOR
        )
        self.ocr_label.grid(row=0, column=0, sticky="w")

        self._manual_var = tk.StringVar()
        self._manual_var.trace_add("write", self._on_manual_input)
        self.ocr_entry = tk.Entry(
            self.header,
            textvariable=self._manual_var,
            font=(Style.FONT_FAMILY, 24, "bold"),
            fg=Style.GOLD_COLOR, bg=Style.BG_COLOR,
            insertbackground=Style.ACCENT_COLOR,
            relief="flat", bd=0,
            highlightthickness=0,
            width=8,
            disabledforeground="#555",
            disabledbackground=Style.BG_COLOR,
        )

        self.img_border = tk.Frame(self.header, bg=Style.BLOCK_COLOR, bd=1, relief="solid")
        self.img_border.grid(row=0, column=1, sticky="e")
        self.image_display = tk.Label(
            self.img_border, bg=Style.BLOCK_COLOR,
            text="OFFLINE", fg="#444", font=(Style.FONT_FAMILY, 12)
        )
        self.image_display.pack(padx=2, pady=2)

        self.results_area = tk.Frame(self, bg=Style.BG_COLOR)
        self.results_area.pack(fill=tk.X, padx=20, pady=5)

    def _draw_toggle(self, active):
        """Draw a hardware-style ON/OFF toggle switch on the canvas."""
        c = self.toggle_canvas
        c.delete("all")
        W, H = 52, 26
        R = H // 2

        track_color = "#00BFFF" if active else "#3A3A3C"
        c.create_arc(0, 0, H, H, start=90, extent=180, fill=track_color, outline=track_color)
        c.create_arc(W - H, 0, W, H, start=270, extent=180, fill=track_color, outline=track_color)
        c.create_rectangle(R, 0, W - R, H, fill=track_color, outline=track_color)

        knob_x = W - R - 2 if active else R + 2

        if active:
            c.create_oval(
                knob_x - R + 1, 1, knob_x + R - 3, H - 1,
                fill="#005f7a", outline=""
            )

        # Knob
        knob_color = "#FFFFFF" if active else "#8E8E93"
        c.create_oval(
            knob_x - R + 3, 3, knob_x + R - 5, H - 3,
            fill=knob_color, outline=""
        )

    def _on_manual_input(self, *_):
        if self.scanning_active:
            return
        raw = self._manual_var.get().strip()
        digits = "".join(filter(str.isdigit, raw))
        if not digits:
            self.status_label.config(text="MANUAL", fg=Style.ACCENT_COLOR)
            self._update_results_only(None, [])
            return
        try:
            val = int(digits)
        except ValueError:
            self._update_results_only(None, [])
            return
        results = []
        if val > NUMBER_THRESHOLD:
            for base, name in MINING_DATA.items():
                if val % base == 0:
                    results.append({"name": name, "mult": val // base, "sig": base})
        results.sort(key=lambda x: x["mult"], reverse=True)
        if results:
            self.status_label.config(text="LOCKED", fg="#00FF00")
        else:
            self.status_label.config(text="MANUAL", fg=Style.ACCENT_COLOR)
        self._update_results_only(val, results)

    def _update_results_only(self, number, results):
        for w in self.results_area.winfo_children():
            w.destroy()
        if results:
            for i, match in enumerate(results):
                fg_name   = Style.GOLD_COLOR  if i == 0 else "#AAAAAA"
                fg_sig    = Style.ACCENT_COLOR if i == 0 else "#555555"
                font_size = 14 if i == 0 else 11
                line = tk.Frame(self.results_area, bg=Style.BLOCK_COLOR, padx=12, pady=6)
                line.pack(fill=tk.X, pady=(0, 2))
                tk.Label(line, text=f"{match['mult']}x {match['name'].upper()}",
                    fg=fg_name, bg=Style.BLOCK_COLOR,
                    font=(Style.FONT_FAMILY, font_size, "bold")).pack(side=tk.LEFT)
                tk.Label(line, text=f"Sig: {match['sig']}",
                    fg=fg_sig, bg=Style.BLOCK_COLOR,
                    font=(Style.FONT_FAMILY, 10)).pack(side=tk.RIGHT)
        else:
            tk.Label(self.results_area, text="// Undefined //",
                fg="#444", bg=Style.BLOCK_COLOR,
                font=(Style.FONT_FAMILY, 11, "italic"),
                padx=12, pady=10).pack(fill=tk.X)
        self.update_idletasks()
        new_h = max(WIN_H, self.winfo_reqheight())
        self.geometry(f"{WIN_W}x{new_h}")

    def _scan_worker(self):
        while True:
            time.sleep(LOOP_DELAY / 1000)

            if not self.scanning_active:
                continue

            if time.time() - self.last_move_time < MOVE_DELAY:
                self.result_queue.put(("paused", None, None))
                continue

            try:
                frame = self.scanner.get_screen_frame()
                val, crop = self.scanner.scan_frame(frame)

                if val is not None:
                    results = []
                    if val > NUMBER_THRESHOLD:
                        for base, name in MINING_DATA.items():
                            if val % base == 0:
                                results.append({
                                    "name": name,
                                    "mult": val // base,
                                    "sig": base
                                })
                    results.sort(key=lambda x: x["mult"], reverse=True)
                    self.result_queue.put(("locked", val, results, crop))
                else:
                    self.result_queue.put(("scanning", None, None))

            except Exception as e:
                print(e)

    def _poll_results(self):
        try:
            while True:
                item = self.result_queue.get_nowait()

                if not self.scanning_active:
                    continue

                status = item[0]

                if status == "paused":
                    self.status_label.config(text="PAUSED (MOVING)", fg=Style.ACCENT_COLOR)

                elif status == "locked":
                    _, val, results, crop = item
                    self.status_label.config(text="LOCKED", fg="#00FF00")
                    self.update_display(val, results, crop)

                elif status == "scanning":
                    self.status_label.config(text="SCANNING", fg="#FF3B30")
                    self.update_display(None, [], None)

        except queue.Empty:
            pass

        self.after(50, self._poll_results)

    def update_display(self, number, results, cv_img):
        if cv_img is not None and cv_img.size > 0:
            img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            resized = ImageOps.contain(pil_img, (150, 50))
            tk_photo = ImageTk.PhotoImage(resized)
            self.image_display.config(image=tk_photo, text="")
            self.current_img_ref = tk_photo
        else:
            self.image_display.config(image="", text="OFFLINE")

        self.ocr_label.config(text=str(number) if number else "-----")

        for w in self.results_area.winfo_children():
            w.destroy()

        if results:
            for i, match in enumerate(results):
                fg_name   = Style.GOLD_COLOR  if i == 0 else "#AAAAAA"
                fg_sig    = Style.ACCENT_COLOR if i == 0 else "#555555"
                font_size = 14 if i == 0 else 11
 
                line = tk.Frame(self.results_area, bg=Style.BLOCK_COLOR, padx=12, pady=6)
                line.pack(fill=tk.X, pady=(0, 2))
                tk.Label(
                    line,
                    text=f"{match['mult']}x {match['name'].upper()}",
                    fg=fg_name, bg=Style.BLOCK_COLOR,
                    font=(Style.FONT_FAMILY, font_size, "bold")
                ).pack(side=tk.LEFT)
                tk.Label(
                    line,
                    text=f"Sig: {match['sig']}",
                    fg=fg_sig, bg=Style.BLOCK_COLOR,
                    font=(Style.FONT_FAMILY, 10)
                ).pack(side=tk.RIGHT)
        else:
            tk.Label(
                self.results_area,
                text="// Undefined //",
                fg="#444", bg=Style.BLOCK_COLOR,
                font=(Style.FONT_FAMILY, 11, "italic"),
                padx=12, pady=10
            ).pack(fill=tk.X)


if __name__ == "__main__":
    app = RockScannerApp()
    app.mainloop()