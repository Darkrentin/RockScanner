import cv2
import pytesseract
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def debug_display_img(gray, thresh):
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.title("1. Original")
    plt.imshow(gray, cmap='gray')
    
    plt.subplot(1, 2, 2)
    plt.title("2. OCR Input")
    plt.imshow(thresh, cmap='gray')
    
    plt.show()

def simple_ocr_pipeline(image_path):
    img = cv2.imread(image_path)
    
    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    
    _, thresh = cv2.threshold(gray, 125, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones((2, 2), np.uint8)
    thresh = cv2.dilate(thresh, kernel, iterations=1)

    # OCR
    custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.,'
    text_found = pytesseract.image_to_string(thresh, config=custom_config)
    
    only_digits = "".join(filter(str.isdigit, text_found))
    
    try:
        number = int(only_digits)
    except ValueError:
        number = None

    debug_display_img(gray, thresh)

    return number

def test_data():
    dir = Path('data')

    exts = ['*.png', '*.jpg', '*.jpeg']
    images = []
    for ext in exts:
        images.extend(dir.glob(ext))
    
    for i in images:
        value = simple_ocr_pipeline(str(i))
        print(f"File : {i.name} | find : {value}")

if __name__ == '__main__':
    test_data()