import cv2
import numpy as np
import pytesseract
import mss
import os
from utils import TESS_PATH, MINING_DATA

pytesseract.pytesseract.tesseract_cmd = os.path.join(TESS_PATH, "tesseract.exe")

MONITOR = 1

ROI_X_START = 0.30
ROI_X_END   = 0.70
ROI_Y_START = 0.20
ROI_Y_END   = 0.45

SIG_MIN = 1500
SIG_MAX = 100000

BINARIZE_THRESHOLDS = [150, 120, 180]


class OcrScanner:
    def __init__(self, debug=False):
        self.debug = debug
        self.last_sig_position = None

    def get_screen_frame(self):
        with mss.mss() as sct:
            mon = sct.monitors[MONITOR]
            area = {"top": 0, "left": 0, "width": mon["width"], "height": mon["height"]}
            sct_img = sct.grab(area)
            frame = np.array(sct_img)
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    def get_roi(self, frame):
        """Returns the cropped ROI image and its top-left offset (x, y) in the full frame."""
        h, w = frame.shape[:2]
        x1 = int(w * ROI_X_START)
        x2 = int(w * ROI_X_END)
        y1 = int(h * ROI_Y_START)
        y2 = int(h * ROI_Y_END)
        return frame[y1:y2, x1:x2], x1, y1

    def _scan_roi_for_signature(self, roi):
        """
        Searches the ROI for a number matching a valid signature range.
        Returns (value, x, y) relative to the ROI, or None if nothing is found.
        """
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        if self.debug:
            cv2.imshow("ROI gray", gray)
            cv2.waitKey(1)

        for thresh_val in BINARIZE_THRESHOLDS:
            candidates = self._extract_numbers_from_gray(gray, thresh_val)
            for val, x, y in candidates:
                if SIG_MIN <= val <= SIG_MAX:
                    return val, x, y

        return None

    def _extract_numbers_from_gray(self, gray, threshold):
        """
        Binarizes the image and runs OCR to extract all numbers with their positions.
        Returns a list of (int_value, x, y).
        """
        scaled = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

        _, thresh = cv2.threshold(scaled, threshold, 255, cv2.THRESH_BINARY_INV)

        # Try both the inverted and non-inverted version to handle light and dark HUDs
        versions = [thresh, cv2.bitwise_not(thresh)]
        candidates = []

        for img in versions:
            kernel = np.ones((2, 2), np.uint8)
            img = cv2.dilate(img, kernel, iterations=1)

            config = r"--oem 3 --psm 11 -c tessedit_char_whitelist=0123456789.,"
            data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)

            for i, text in enumerate(data["text"]):
                digits = "".join(filter(str.isdigit, text))
                if not digits:
                    continue
                try:
                    val = int(digits)
                except ValueError:
                    continue
                if val < SIG_MIN or val > SIG_MAX:
                    continue
                # Convert coordinates back to original scale before the x3 upscale
                x = data["left"][i] // 3
                y = data["top"][i] // 3
                candidates.append((val, x, y))

        return candidates

    def scan_frame(self, frame):
        """
        Main method. Returns (signature_value, crop_image) or (None, None) if not found.
        """
        roi, roi_x, roi_y = self.get_roi(frame)
        result = self._scan_roi_for_signature(roi)
        if result is None:
            return None, None
        val, x, y = result
        abs_x = roi_x + x
        abs_y = roi_y + y
        crop = frame[max(0, abs_y - 5):abs_y + 40, abs_x:abs_x + 120]
        return val, crop

    def calibrate_roi(self, frame):
        h, w = frame.shape[:2]
        x1 = int(w * ROI_X_START)
        x2 = int(w * ROI_X_END)
        y1 = int(h * ROI_Y_START)
        y2 = int(h * ROI_Y_END)
        preview = frame.copy()
        cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.imshow("ROI calibration (press any key to close)", preview)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def read_from_file(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            return None
        val, _ = self.scan_frame(img)
        return val

    def scan_folder(self, folder_path):
        for filename in os.listdir(folder_path):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                full_path = os.path.join(folder_path, filename)
                value = self.read_from_file(full_path)
                print("File:", filename, "Value:", value)


if __name__ == "__main__":
    scanner = OcrScanner()
    frame = scanner.get_screen_frame()
    scanner.calibrate_roi(frame)