import cv2
import numpy as np
import pytesseract
import mss
import os
from utils import TESS_PATH

pytesseract.pytesseract.tesseract_cmd = os.path.join(TESS_PATH, "tesseract.exe")

MONITOR = 1

class OcrScanner:
    def __init__(self, logo_path, debug = False):
        # Load the logo and prepare edge detection
        template_raw = cv2.imread(logo_path, cv2.IMREAD_GRAYSCALE)
        self.template_edges = cv2.Canny(template_raw, 50, 150)
        self.t_h, self.t_w = self.template_edges.shape
        self.debug = debug

    def get_screen_frame(self):
        with mss.mss() as sct:
            mon = sct.monitors[MONITOR]
            area = {
                "top": mon["height"] // 4,
                "left": mon["width"] // 4,
                "width": mon["width"] // 2,
                "height": mon["height"] // 2
            }
            sct_img = sct.grab(area)
            frame = np.array(sct_img)
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    def find_target(self, frame_bgr):
        # Convert frame to grayscale and find edges
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        # Match the logo edges with the screen edges
        res = cv2.matchTemplate(edges, self.template_edges, cv2.TM_CCOEFF_NORMED)
        return cv2.minMaxLoc(res)

    def read_number(self, cv_img, save_name = "debug_bin.png"):
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(gray, 125, 255, cv2.THRESH_BINARY_INV)
        kernel = np.ones((2, 2), np.uint8)
        thresh = cv2.dilate(thresh, kernel, iterations=1)

        if self.debug:
            cv2.imshow("thresh", thresh)
            cv2.waitKey(0)
            cv2.imwrite(save_name, thresh)

        config = r"--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.,"
        text = pytesseract.image_to_string(thresh, config=config)
        digits = "".join(filter(str.isdigit, text))
        try:
            return int(digits)
        except ValueError:
            return None
        
    def read_from_file(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            return None
        name = "data/debug/debug_" + os.path.basename(image_path)
        return self.read_number(img, save_name=name)
    
    def scan_folder(self, folder_path):
        for filename in os.listdir(folder_path):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                full_path = os.path.join(folder_path, filename)
                value = self.read_from_file(full_path)
                print("File:", filename, "Value:", value)

if __name__ == "__main__":
    scanner = OcrScanner("logo.png", True)
    scanner.scan_folder("data")