import os
import sys
import pandas as pd
import fitz
import re

sys.path.append(r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1")
from ocr_engine import run_ocr
from receipt_parser import parse_receipt
from receipt_mapper import map_receipt_data

TARGET_DIR = r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\과거 참고데이터\26년 5월\5월 스캔본_재정비\엑셀 대응"
EXCEL_PATH = os.path.join(TARGET_DIR, "추론값.xlsx")

def extract_fee(raw_text):
    """Extract transfer fee from text. Usually looks like 手续费 or 수수료 followed by amount."""
    for line in raw_text.split('\n'):
        if "手续费" in line or "수수료" in line or "CHARGE" in line.upper():
            # Find the first number that looks like an amount
            m = re.search(r"([\d,]+\.\d{2})", line)
            if m:
                return float(m.group(1).replace(',', ''))
            # Sometimes it's just an integer
            m = re.search(r"([\d,]+)", line)
            if m:
                return float(m.group(1).replace(',', ''))
    return None

def process_pdfs():
    # Read existing Excel to see which files are already processed
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, header=None, names=["파일명", "추론결과"])
    else:
        df = pd.DataFrame(columns=["파일명", "추론결과"])

    processed_files = set(df["파일명"].dropna().tolist())
    
    files = sorted(os.listdir(TARGET_DIR))
    pdfs = [f for f in files if f.endswith('.pdf')]
    
    # We want to process from 07.pdf upwards, so skip any that are already in processed_files 
    # and explicitly skip 01 to 06 as per user instruction just in case.
    skip_list = {'01.pdf', '02.pdf', '03.pdf', '04.pdf', '05.pdf', '06.pdf'}
    
    for pdf_name in pdfs:
        if pdf_name in processed_files or pdf_name in skip_list:
            continue
            
        print(f"\nProcessing {pdf_name}...")
        pdf_path = os.path.join(TARGET_DIR, pdf_name)
        
        try:
            doc = fitz.open(pdf_path)
            page_summaries = []
            
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")
                
                # Run OCR
                ocr_res = run_ocr(img_bytes, f"{pdf_name}_p{i}")
                raw_text = ocr_res.get('raw_text', '')
                
                # Parse
                parsed = parse_receipt(raw_text)
                amount = parsed.get("amount")
                seller = parsed.get("seller", "")
                
                # Determine if Shinhan Bank transfer
                is_shinhan = False
                if "SHINHAN" in raw_text.upper() or "INWARD REMITTANCE" in raw_text.upper() or parsed.get("type") == "银行回单":
                    is_shinhan = True
                
                # Map standard description
                mapped = map_receipt_data(raw_text, seller)
                desc = mapped.get("standard_desc")
                
                if is_shinhan:
                    fee_amt = extract_fee(raw_text)
                    if fee_amt is not None:
                        # Only write the transfer fee
                        desc = f"{desc} 계좌 이체 수수료" if desc else "계좌 이체 수수료"
                        amount = fee_amt
                    else:
                        desc = "해외 송금 입금 내역 (Inward Remittance)" if "INWARD" in raw_text.upper() else "은행 계좌 이체"
                        # If no fee found but we have an amount, use the amount (it might be the main remittance)
                        # but user asked: "신한은행 이체 영수증일경우, 밑에 이체수수료만 기재"
                        # If there is no fee, maybe it's the main transfer. The user wrote for 01.pdf: 
                        # "1페이지: 해외 송금 입금 내역 (Inward Remittance) / 35,488.17위안"
                        # So if we can't find a fee, just use the main amount and description.
                else:
                    if not desc:
                        desc = parsed.get("description", "기타 항목")
                
                # Format
                if amount is not None:
                    amt_str = f"{amount:,.2f}위안"
                else:
                    amt_str = "금액 미상"
                    
                page_summaries.append(f"{i+1}페이지: {desc} / {amt_str}")
                print(f"  -> {page_summaries[-1]}")
            
            doc.close()
            
            final_str = "   ".join(page_summaries) if page_summaries else "인식된 내역 없음"
            
            # Append immediately to df and save
            new_row = pd.DataFrame([{"파일명": pdf_name, "추론결과": final_str}])
            df = pd.concat([df, new_row], ignore_index=True)
            
            # Save using pandas without header
            df.to_excel(EXCEL_PATH, index=False, header=False)
            
        except Exception as e:
            print(f"Error processing {pdf_name}: {e}")

if __name__ == "__main__":
    process_pdfs()
