import easyocr
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# Initialize reader for Chinese and English
print("Initializing EasyOCR reader...")
reader = easyocr.Reader(['ch_sim', 'en'])
print("EasyOCR reader initialized.")

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
        print(f"\n=================== OCR for {label} ===================")
        try:
            results = reader.readtext(p)
            for bbox, text, prob in results:
                print(f"  {text} (prob: {prob:.2f})")
        except Exception as e:
            print(f"Error reading {label}: {e}")
    else:
        print(f"File not found: {p}")
