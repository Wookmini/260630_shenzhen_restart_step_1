import cv2
import pytesseract
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

files = [
    "영수증 보관소/2026-05/Chen Feng Ju/010.png",
    "영수증 보관소/2026-05/Chen Feng Ju/011.png",
    "영수증 보관소/2026-05/Chen Feng Ju/012.png",
    "영수증 보관소/2026-05/신순연/195.png"
]

for p in files:
    if os.path.exists(p):
        print(f"\n=================== OCR for {p} ===================")
        try:
            # Read image using numpy to bypass path encoding bug
            import numpy as np
            with open(p, "rb") as f:
                chunk = f.read()
            img_array = np.frombuffer(chunk, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                print(f"Failed to load {p}")
                continue
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding to bring out faint text
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Run Tesseract
            text = pytesseract.image_to_string(thresh, lang='chi_sim+eng', config='--psm 6')
            
            # Extract possible amounts (lines with numbers or ¥/元)
            import re
            lines = text.split('\n')
            for line in lines:
                if re.search(r'\d', line):
                    print(line.strip())
        except Exception as e:
            print(f"Error: {e}")
