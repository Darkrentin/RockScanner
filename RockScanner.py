import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps
import cv2
import time

from utils import Style, LOGO_PATH, MINING_DATA, ICON_PATH
from scanner import OcrScanner

WIN_H = 150
WIN_W = 450

TARGET_THRESHOLD = 0.25
NUMBER_THRESHOLD = 1000
LOOP_DELAY = 600
MOVE_DELAY = 0.05


class RockScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RockScanner")
        self.iconbitmap(ICON_PATH)
        self.geometry(str(WIN_W)+"x"+str(WIN_H))
        self.config(bg=Style.BG_COLOR)
        self.attributes("-topmost", True)
        self.current_img_ref = None
        
        self.last_move_time = 0
        self.bind("<Configure>", self.on_window_move)
        
        # Check if logo exists before starting
        if not os.path.exists(LOGO_PATH):
            messagebox.showerror("Error", "Logo file missing")
            self.destroy()
            return
            
        self.scanner = OcrScanner(LOGO_PATH)
        self.setup_ui()
        self.scan_loop()
    
    def on_window_move(self, event):
        self.last_move_time = time.time()

    def setup_ui(self):
        # Label for scan status
        self.status_label = tk.Label(self, text="SEARCHING", fg="#555", bg=Style.BG_COLOR, font=(Style.FONT_FAMILY, 12))
        self.status_label.pack(pady=5)

        # Frame for top information
        self.header = tk.Frame(self, bg=Style.BG_COLOR)
        self.header.pack(fill=tk.X, padx=20, pady=10)
        self.header.columnconfigure(0, weight=1)
        self.header.columnconfigure(1, weight=1)

        # Label for the found number
        self.ocr_label = tk.Label(self.header, text="---", font=(Style.FONT_FAMILY, 24, "bold"), fg=Style.GOLD_COLOR, bg=Style.BG_COLOR)
        self.ocr_label.grid(row=0, column=0, sticky="w")

        # Container for the image preview
        self.img_border = tk.Frame(self.header, bg=Style.BLOCK_COLOR, bd=1, relief="solid")
        self.img_border.grid(row=0, column=1, sticky="e")
        self.image_display = tk.Label(self.img_border, bg=Style.BLOCK_COLOR, text="OFFLINE", fg="#444", font=(Style.FONT_FAMILY, 12))
        self.image_display.pack(padx=2, pady=2)

        # Bottom area for result text
        self.results_area = tk.Frame(self, bg=Style.BG_COLOR)
        self.results_area.pack(fill=tk.X, padx=20, pady=5)

    def scan_loop(self):
        if time.time() - self.last_move_time < MOVE_DELAY:
            self.status_label.config(text="PAUSED (MOVING)", fg=Style.ACCENT_COLOR)
            self.after(LOOP_DELAY, self.scan_loop)
            return

        try:
            # Capture and search for logo
            frame = self.scanner.get_screen_frame()
            min_v, max_v, min_l, max_l = self.scanner.find_target(frame)

            if max_v > TARGET_THRESHOLD:
                # Target found
                self.status_label.config(text="LOCKED", fg="#00FF00")
                x, y = max_l
                # Cut the number area next to the logo
                crop = frame[max(0, y-3) : y+self.scanner.t_h+3, x+self.scanner.t_w : x+self.scanner.t_w+85]
                val = self.scanner.read_number(crop)
                
                # Check mining database
                results = []
                if val and val > NUMBER_THRESHOLD:
                    for base, name in MINING_DATA.items():
                        if val % base == 0:
                            results.append({"name": name, "mult": val // base, "sig": base})
                
                results.sort(key=lambda x: x["mult"], reverse=True)
                # Show results in interface
                self.update_display(val, results, crop)
            else:
                # Target not found
                self.status_label.config(text="SCANNING", fg="#FF3B30")
                self.update_display(None, [], None)

        except Exception as e:
            print(e)
            
        self.after(LOOP_DELAY, self.scan_loop)

    def update_display(self, number, results, cv_img):
        # Update preview image
        if cv_img is not None:
            img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            resized = ImageOps.contain(pil_img, (150, 50))
            tk_photo = ImageTk.PhotoImage(resized)
            self.image_display.config(image=tk_photo, text="")
            self.current_img_ref = tk_photo
        else:
            self.image_display.config(image="", text="OFFLINE")

        # Update number text
        self.ocr_label.config(text=str(number) if number else "-----")

        # Update result labels
        for w in self.results_area.winfo_children():
            w.destroy()

        if results:
            best = results[0]
            line = tk.Frame(self.results_area, bg=Style.BLOCK_COLOR, padx=12, pady=10)
            line.pack(fill=tk.X)
            tk.Label(line, text=f"{best['mult']}x {best['name'].upper()}", fg=Style.GOLD_COLOR, bg=Style.BLOCK_COLOR, font=(Style.FONT_FAMILY, 14, "bold")).pack(side=tk.LEFT)
            tk.Label(line, text=f"Sig: {best['sig']}", fg=Style.ACCENT_COLOR, bg=Style.BLOCK_COLOR, font=(Style.FONT_FAMILY, 10)).pack(side=tk.RIGHT)
        else:
            # Show default text if nothing is found
            tk.Label(self.results_area, text="// Undefined //", fg="#444", bg=Style.BLOCK_COLOR, font=(Style.FONT_FAMILY, 11, "italic"), padx=12, pady=10).pack(fill=tk.X)

import os
if __name__ == "__main__":
    app = RockScannerApp()
    app.mainloop()