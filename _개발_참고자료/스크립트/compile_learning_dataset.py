import os
import json
import pandas as pd
import fitz
import re
import sys

sys.path.append(r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1")
from ocr_engine import run_ocr

TARGET_DIR = r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\과거 참고데이터\26년 5월\5월 스캔본_재정비\엑셀 대응"
RULES_JSON_PATH = r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\data\may_learned_rules.json"
LEARNED_MODEL_PATH = r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\data\shenzhen_receipt_learning_model.json"

def compile_learning_model():
    # Load raw rules
    with open(RULES_JSON_PATH, "r", encoding="utf-8") as f:
        rules = json.load(f)
        
    files = sorted(os.listdir(TARGET_DIR))
    pdfs = [f for f in files if f.endswith('.pdf')]
    
    learning_dataset = []
    
    for pdf_name in pdfs:
        print(f"Analyzing {pdf_name} for learning model...")
        pdf_path = os.path.join(TARGET_DIR, pdf_name)
        
        # Determine corresponding proof numbers
        # E.g. '01.pdf' -> ['1'], '61-62.pdf' -> ['61', '62']
        base_name = os.path.splitext(pdf_name)[0]
        if '-' in base_name:
            parts = base_name.split('-')
            proof_nums = [str(int(p)) for p in parts if p.isdigit()]
        else:
            proof_nums = [str(int(base_name))] if base_name.isdigit() else []
            
        associated_rules = []
        for pno in proof_nums:
            if pno in rules:
                associated_rules.extend(rules[pno])
                
        ocr_texts = []
        try:
            doc = fitz.open(pdf_path)
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=200) # Hits cache
                img_bytes = pix.tobytes("png")
                
                ocr_res = run_ocr(img_bytes, f"{pdf_name}_p{i}")
                raw_text = ocr_res.get('raw_text', '')
                ocr_texts.append(raw_text)
            doc.close()
        except Exception as e:
            print(f"Error reading {pdf_name}: {e}")
            
        learning_dataset.append({
            "pdf_filename": pdf_name,
            "proof_numbers": proof_nums,
            "associated_rules": associated_rules,
            "ocr_pages": ocr_texts
        })
        
    with open(LEARNED_MODEL_PATH, "w", encoding="utf-8") as f:
        json.dump(learning_dataset, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated learning database with {len(learning_dataset)} entries at {LEARNED_MODEL_PATH}!")

if __name__ == "__main__":
    compile_learning_model()
