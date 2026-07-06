import os
import json
import pandas as pd
from receipt_parser import parse_receipt
from receipt_mapper import map_receipt_data

def process_results():
    with open("scratch_ocr_results.json", "r", encoding="utf-8") as f:
        results = json.load(f)
        
    excel_path = r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\과거 참고데이터\26년 5월\5월 스캔본_재정비\엑셀 대응\추론값.xlsx"
    
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path)
    else:
        df = pd.DataFrame(columns=["파일명", "추론결과"])

    new_rows = []
    
    for pdf_name, pages_text in results.items():
        page_summaries = []
        for i, text in enumerate(pages_text):
            if "ERROR" in text:
                continue
            
            parsed = parse_receipt(text)
            amount = parsed.get("amount")
            
            # Shinhan Bank Transfer rule
            if "SHINHAN" in text or "Inward Remittance" in text or parsed.get("type") == "银行回单":
                # Need to find transfer fee. Usually "手续费" or "수수료"
                # If there's a specific amount for fee
                # Simplified: let's try to extract from map_receipt_data or look for small amounts
                is_shinhan = True
            else:
                is_shinhan = False
            
            mapped = map_receipt_data(text, parsed.get("seller", ""))
            desc = mapped.get("standard_desc")
            
            if is_shinhan:
                # Need to find transfer fee in text
                lines = text.split("\n")
                fee_amt = None
                for line in lines:
                    if "手续费" in line or "수수료" in line or "CHARGE" in line.upper():
                        import re
                        m = re.search(r"[\d.,]+", line)
                        if m:
                            fee_amt = m.group(0)
                if fee_amt:
                    desc = f"{desc} 계좌 이체 수수료" if desc else "계좌 이체 수수료"
                    amount = float(fee_amt.replace(",", ""))
                else:
                    # fallback to small amount logic if bank receipt
                    if amount and amount > 1000:
                        # Probably the main amount, so skip it or just write fee if we know it is usually 3-15 RMB
                        desc = "계좌 이체 (수수료 미상)"
            else:
                # If it's normal fapiao, we already have mapped desc and amount
                if not desc:
                    desc = parsed.get("description", "기타 항목")
            
            if amount is not None:
                amt_str = f"{amount:,.2f}위안"
            else:
                amt_str = "금액 미상"
                
            page_summaries.append(f"{i+1}페이지: {desc} / {amt_str}")
        
        if page_summaries:
            final_str = "   ".join(page_summaries)
        else:
            final_str = "인식된 내역 없음"
            
        new_rows.append({"파일명": pdf_name, "추론결과": final_str})
        
    df_new = pd.DataFrame(new_rows)
    df_combined = pd.concat([df, df_new], ignore_index=True)
    df_combined.to_excel(excel_path, index=False)
    print(f"Updated {excel_path} with {len(new_rows)} new files.")

if __name__ == "__main__":
    process_results()
