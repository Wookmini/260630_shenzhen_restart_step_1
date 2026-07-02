import pytesseract
import sys
import os
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

print("Initializing Pytesseract OCR...")
# Path to tesseract executable if needed, but usually it's in the PATH on this system

files_to_ocr = [
    ("Chen Feng Ju/008.png", "영수증 보관소/2026-05/Chen Feng Ju/008.png"),
    ("Chen Feng Ju/009.png", "영수증 보관소/2026-05/Chen Feng Ju/009.png"),
    ("Chen Feng Ju/010.png", "영수증 보관소/2026-05/Chen Feng Ju/010.png"),
    ("Chen Feng Ju/011.png", "영수증 보관소/2026-05/Chen Feng Ju/011.png"),
    ("Chen Feng Ju/012.png", "영수증 보관소/2026-05/Chen Feng Ju/012.png"),
    ("신순연/195.png", "영수증 보관소/2026-05/신순연/195.png")
]

for label, p in files_to_ocr:
    if os.path.exists(p):
        print(f"\n=================== Pytesseract OCR for {label} ===================")
        try:
            img = Image.open(p)
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            print(text)
        except Exception as e:
            print(f"Error reading {label}: {e}")
    else:
        print(f"File not found: {p}")
