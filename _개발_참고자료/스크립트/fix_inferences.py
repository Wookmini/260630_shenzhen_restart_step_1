import os
import json
import pandas as pd
import fitz
import re
import sys

sys.path.append(r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1")
from ocr_engine import run_ocr

TARGET_DIR = r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\과거 참고데이터\26년 5월\5월 스캔본_재정비\엑셀 대응"
EXCEL_PATH = os.path.join(TARGET_DIR, "추론값.xlsx")

def extract_fee(raw_text):
    for line in raw_text.split('\n'):
        if "手续费" in line or "수수료" in line or "CHARGE" in line.upper():
            m = re.search(r"([\d,]+\.\d{2})", line)
            if m: return float(m.group(1).replace(',', ''))
            m = re.search(r"([\d,]+)", line)
            if m: return float(m.group(1).replace(',', ''))
    return None

def extract_amount(raw_text):
    def to_float(val):
        try: return float(val.strip().replace(' ', '').replace(',', ''))
        except: return None
        
    m = re.search(r"(?:小\s*写|价税合计).*?[¥￥][ \t]*([\d., \n]+\.\d{2})", raw_text)
    if m: 
        res = to_float(m.group(1))
        if res: return res
        
    m = re.search(r"(?:交易金额|转账金额|金额)\s*[:：]?\s*(?:USD|CNY)?\s*[¥￥]?\s*([\d\s.,\n]+\.\d{2})", raw_text)
    if m: 
        res = to_float(m.group(1))
        if res: return res
        
    m = re.search(r"[¥￥]\s*([\d,\n]+\.\d{2})", raw_text)
    if m: 
        res = to_float(m.group(1))
        if res: return res
    
    m = re.search(r"￥\s*(-\s*[\d,\n]+\.\d{2})", raw_text)
    if m: 
        res = to_float(m.group(1))
        if res: return res
    
    return None

def infer_description(raw_text):
    text_nospace = raw_text.replace(" ", "")
    
    m = re.search(r"\*([^\*]+)\*([^\n]+)", raw_text)
    if m:
        cat = m.group(1).strip()
        item = m.group(2).strip()
        korean_cat = "기타 항목"
        if "旅游" in cat or "签证" in item: korean_cat = "비자/여행 서비스"
        elif "餐饮" in cat: korean_cat = "식대"
        elif "住宿" in cat: korean_cat = "숙박비"
        elif "运输" in cat or "客运" in item: korean_cat = "택시/여객 요금"
        elif "经纪代理" in cat: korean_cat = "대행 서비스 요금"
        elif "保险" in cat: korean_cat = "보험료"
        elif "电信" in cat: korean_cat = "통신 요금"
        elif "租赁" in cat: korean_cat = "렌트비/임차료"
        elif "快递" in cat: korean_cat = "택배비"
        elif "软件" in cat: korean_cat = "소프트웨어 요금"
        elif "服务" in cat: korean_cat = "서비스 요금"
        elif "汽油" in cat: korean_cat = "주유비"
        return f"{korean_cat} (*{cat}*{item})"
    
    if "SHINHAN" in raw_text.upper() or "网上银行" in raw_text or "银行回单" in raw_text:
        return "은행 계좌 이체"
        
    if "滴滴" in raw_text: return "택시 (滴滴) 요금"
    if "通行费" in raw_text or "联合电子" in raw_text: return "톨비 (通行费)"
    if "出租车" in raw_text or "TAXI" in raw_text.upper(): return "택시비"
    if "餐饮" in raw_text or "菜" in raw_text: return "식대"
    if "京东" in raw_text: return "징동 쇼핑 (사무용품 등)"
    if "跨行POS" in raw_text: return "타행 POS 소비"
    if "天福" in raw_text: return "편의점 (天福) 결제"
    
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    if len(lines) > 1:
        for l in lines:
            if not re.match(r'^\d+$', l) and "PiaoMei" not in l and "PIno" not in l and "GlobalChip" not in l and "Thisisthe" not in l.replace(" ", ""):
                return l[:30]
    return "알 수 없는 항목"

def fix_pdfs():
    # Read up to 19.pdf which we know are correct
    df = pd.read_excel(EXCEL_PATH, header=None, names=["파일명", "추론결과"])
    
    # Keep 01 to 19
    good_files = [f"{i:02d}.pdf" for i in range(1, 20)]
    df_good = df[df["파일명"].isin(good_files)].copy()
    
    files = sorted(os.listdir(TARGET_DIR))
    pdfs = [f for f in files if f.endswith('.pdf')]
    
    new_rows = []
    
    for pdf_name in pdfs:
        if pdf_name in good_files:
            continue
            
        print(f"Fixing {pdf_name}...")
        pdf_path = os.path.join(TARGET_DIR, pdf_name)
        
        try:
            doc = fitz.open(pdf_path)
            page_summaries = []
            
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=200) # Hits cache
                img_bytes = pix.tobytes("png")
                
                ocr_res = run_ocr(img_bytes, f"{pdf_name}_p{i}")
                raw_text = ocr_res.get('raw_text', '')
                
                is_shinhan = "SHINHAN" in raw_text.upper() or "网上银行" in raw_text
                amount = None
                
                if is_shinhan:
                    fee_amt = extract_fee(raw_text)
                    if fee_amt is not None:
                        desc = "계좌 이체 수수료"
                        amount = fee_amt
                    else:
                        desc = "계좌 이체 내역"
                        amount = extract_amount(raw_text)
                else:
                    desc = infer_description(raw_text)
                    amount = extract_amount(raw_text)
                
                if amount is not None:
                    amt_str = f"{amount:,.2f}위안"
                else:
                    amt_str = "금액 미상"
                    
                page_summaries.append(f"{i+1}페이지: {desc} / {amt_str}")
            
            doc.close()
            final_str = "   ".join(page_summaries) if page_summaries else "인식된 내역 없음"
            
            new_rows.append({"파일명": pdf_name, "추론결과": final_str})
            
        except Exception as e:
            print(f"Error {pdf_name}: {e}")

    df_new = pd.DataFrame(new_rows)
    df_combined = pd.concat([df_good, df_new], ignore_index=True)
    df_combined.to_excel(EXCEL_PATH, index=False, header=False)
    print("Fixed formatting for 20-62!")

if __name__ == "__main__":
    fix_pdfs()
