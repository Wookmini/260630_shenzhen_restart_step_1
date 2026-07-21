import sys

for lib in ['PIL', 'easyocr', 'pytesseract', 'cv2', 'pdf2image', 'fitz', 'openpyxl']:
    try:
        __import__(lib)
        print(f"{lib}: available")
    except ImportError:
        print(f"{lib}: NOT available")
