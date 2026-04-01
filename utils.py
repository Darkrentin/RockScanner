import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

TESS_PATH = resource_path("tesseract")
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