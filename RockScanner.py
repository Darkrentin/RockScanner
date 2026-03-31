import tkinter as tk
from tkinter import messagebox
import pytesseract
from PIL import Image, ImageTk, ImageOps
import mss
import cv2
import numpy as np
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

TESS_FOLDER = resource_path("tesseract")
pytesseract.pytesseract.tesseract_cmd = os.path.join(TESS_FOLDER, "tesseract.exe")
LOGO_PATH = resource_path("logo.png")

MINING_DATA = {
    3170: "Quantainium", 
    3185: "Stileron",
    3200: "Savrilium", 
    3370: "Ouratite",
    3385: "Riccite", 
    3400: "Lindinium",
    3540: "Beryl",
    3555: "Taranite",
    3570: "Borase",
    3585: "Gold", 
    3600: "Bexalite", 
    3825: "Laranite",
    3840: "Aslarite", 
    3855: "Titanium", 
    3870: "Tungsten", 
    3885: "Agricium",
    3900: "Torite", 
    4180: "Hephestanite", 
    4195: "Tin", 
    4210: "Quartz",
    4225: "Corundum",
    4240: "Copper", 
    4255: "Silicon", 
    4270: "Iron",
    4285: "Aluminium", 
    4300: "Ice", 
    2000: "Ship wrecks",
    3000: "FPS Mineables",
    4000: "Ground Vehicule Deposits"
}

class Style:
    BG_COLOR = "#1C1C1E"
    ACCENT_COLOR = "#00BFFF"
    TEXT_COLOR = "#E5E5E5"
    GOLD_COLOR = "#FFD700"
    BLOCK_COLOR = "#2C2C2E"
    FONT_FAMILY = "Consolas"

class RockScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RockScanner")
        self.geometry("450x150")
        self.config(bg=Style.BG_COLOR)
        self.attributes('-topmost', True)
        self.current_img_ref = None
        
        if not os.path.exists(LOGO_PATH):
            messagebox.showerror("Error", "Logo file missing")
            self.destroy()
            return
            
        template_raw = cv2.imread(LOGO_PATH, cv2.IMREAD_GRAYSCALE)
        self.template_edges = cv2.Canny(template_raw, 50, 150)
        self.t_h, self.t_w = self.template_edges.shape

        self.setup_ui()
        self.scan_loop()

    def setup_ui(self):
        # Top status
        self.status_label = tk.Label(self, text="SEARCHING...", fg="#555", bg=Style.BG_COLOR, font=(Style.FONT_FAMILY, 12))
        self.status_label.pack(pady=(5, 0))

        # Main Header Frame
        self.header_frame = tk.Frame(self, bg=Style.BG_COLOR)
        self.header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.header_frame.columnconfigure(0, weight=1)
        self.header_frame.columnconfigure(1, weight=1)

        # LEFT SLOT: OCR Number
        self.ocr_label = tk.Label(self.header_frame, text="---", font=(Style.FONT_FAMILY, 24, "bold"), 
                                  fg=Style.GOLD_COLOR, bg=Style.BG_COLOR)
        self.ocr_label.grid(row=0, column=0, sticky="w")

        # RIGHT SLOT: Image Container
        self.img_border = tk.Frame(self.header_frame, bg=Style.BLOCK_COLOR, bd=1, relief="solid")
        self.img_border.grid(row=0, column=1, sticky="e")
        
        self.current_image_label = tk.Label(self.img_border, bg=Style.BLOCK_COLOR, text="OFFLINE", fg="#444", font=(Style.FONT_FAMILY, 12))
        self.current_image_label.pack(padx=2, pady=2)

        self.results_container = tk.Frame(self, bg=Style.BG_COLOR)
        self.results_container.pack(fill=tk.X, padx=20, pady=(0, 15))

    def process_ocr(self, cv_img):
        if cv_img is None: return None
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(gray, 125, 255, cv2.THRESH_BINARY_INV)
        kernel = np.ones((2, 2), np.uint8)
        thresh = cv2.dilate(thresh, kernel, iterations=1)
        
        config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.,'
        text = pytesseract.image_to_string(thresh, config=config)
        digits = "".join(filter(str.isdigit, text))
        try: return int(digits) if digits else None
        except ValueError: return None

    def scan_loop(self):
        try:
            with mss.mss() as sct:
                mon = sct.monitors[1]
                search_area = {"top": mon["height"]//4, "left": mon["width"]//4, "width": mon["width"]//2, "height": mon["height"]//2}
                
                sct_img = sct.grab(search_area)
                frame = np.array(sct_img)
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                gray_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
                edges_frame = cv2.Canny(gray_frame, 50, 150)

                res = cv2.matchTemplate(edges_frame, self.template_edges, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if max_val > 0.25:
                    self.status_label.config(text=f"LOCKED ({int(max_val*100)}%)", fg="#00FF00")
                    x, y = max_loc
                    crop_x, crop_y = x + self.t_w, y - 3
                    crop_w, crop_h = 85, self.t_h + 6
                    crop_img = frame_bgr[max(0,crop_y):crop_y+crop_h, crop_x:crop_x+crop_w]
                    val = self.process_ocr(crop_img)
                    
                    possibilities = []
                    if val and val > 100:
                        for sig_base, name in MINING_DATA.items():
                            if val % sig_base == 0:
                                possibilities.append({"name": name, "mult": val // sig_base, "sig": sig_base})
                    
                    possibilities.sort(key=lambda x: x['mult'], reverse=True)
                    img_display = cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB)
                    self.display_results(val, possibilities, Image.fromarray(img_display))
                else:
                    self.status_label.config(text="SCANNING HUD...", fg="#FF3B30")
                    self.display_results(None, [], None)

        except Exception as e: print(f"Error: {e}")
        self.after(600, self.scan_loop)

    def display_results(self, raw_number, results, pil_img):
        if pil_img:
            resized = ImageOps.contain(pil_img, (150, 50))
            tk_photo = ImageTk.PhotoImage(resized)
            self.current_image_label.config(image=tk_photo, text="")
            self.current_img_ref = tk_photo
        else:
            self.current_image_label.config(image="", text="OFFLINE")

        self.ocr_label.config(text=f"{raw_number if raw_number else '-----'}")

        for widget in self.results_container.winfo_children():
            widget.destroy()

        if results:
            best = results[0]
            line = tk.Frame(self.results_container, bg=Style.BLOCK_COLOR, padx=12, pady=10, bd=1, relief="flat")
            line.pack(fill=tk.X)
            
            tk.Label(line, text=f"{best['mult']}x {best['name'].upper()}", 
                     fg=Style.GOLD_COLOR, bg=Style.BLOCK_COLOR, 
                     font=(Style.FONT_FAMILY, 14, "bold")).pack(side=tk.LEFT)
            
            tk.Label(line, text=f"Sig: {best['sig']}", 
                     fg=Style.ACCENT_COLOR, bg=Style.BLOCK_COLOR, 
                     font=(Style.FONT_FAMILY, 10)).pack(side=tk.RIGHT)
        else:
            tk.Label(self.results_container, text="// --- Undefined --- //", 
                     fg="#444", bg=Style.BLOCK_COLOR, 
                     font=(Style.FONT_FAMILY, 11, "italic"), padx=12, pady=10, bd=1, relief="flat").pack(fill=tk.X)

if __name__ == "__main__":
    app = RockScannerApp()
    app.mainloop()