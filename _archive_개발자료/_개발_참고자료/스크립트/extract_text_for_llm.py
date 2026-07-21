import os
import fitz
import json
import sys
sys.path.append(r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1")
from ocr_engine import run_ocr

TARGET_DIR = r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\과거 참고데이터\26년 5월\5월 스캔본_재정비\엑셀 대응"

def main():
    results = {}
    files = sorted(os.listdir(TARGET_DIR))
    pdfs = [f for f in files if f.endswith('.pdf')]
    
    # Filter only 07.pdf to 61-62.pdf (or those not 01 to 06)
    skip_list = ['01.pdf', '02.pdf', '03.pdf', '04.pdf', '05.pdf', '06.pdf']
    target_pdfs = [f for f in pdfs if f not in skip_list and f != '추론값.xlsx']
    
    for pdf_name in target_pdfs:
        print(f"Processing {pdf_name}...")
        pdf_path = os.path.join(TARGET_DIR, pdf_name)
        try:
            doc = fitz.open(pdf_path)
            pages_text = []
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=150) # lower dpi for faster OCR since we just need text
                img_bytes = pix.tobytes("png")
                ocr_res = run_ocr(img_bytes, f"{pdf_name}_p{i}")
                raw_text = ocr_res.get('raw_text', '')
                pages_text.append(raw_text)
            doc.close()
            results[pdf_name] = pages_text
        except Exception as e:
            print(f"Failed {pdf_name}: {e}")
            results[pdf_name] = [f"ERROR: {e}"]
            
    out_path = os.path.join(r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1", "scratch_ocr_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Done. Saved to scratch_ocr_results.json")

if __name__ == "__main__":
    main()
