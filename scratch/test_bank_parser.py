import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def parse_bank_receipt_test(text: str) -> dict:
    result = {"amount": None, "currency": "CNY", "date": None, "fee_amount": None}
    
    # 1. Main Amount
    amt_matches = re.findall(r"(CNY|USD)\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if amt_matches:
        parsed_amounts = []
        for curr, amt_str in amt_matches:
            try:
                val = float(amt_str.replace(',', ''))
                parsed_amounts.append((val, curr, amt_str))
            except:
                pass
        if parsed_amounts:
            parsed_amounts.sort(key=lambda x: x[0], reverse=True)
            result["amount"] = parsed_amounts[0][2]
            result["currency"] = parsed_amounts[0][1].upper()
            
    if not result["amount"]:
        amt_m = re.search(r"(?:交易金额|转账金额|金额)\s*[:：]?\s*(USD|CNY)?\s*[¥￥]?\s*([\d\s.,]+)", text)
        if amt_m:
            result["amount"] = amt_m.group(2).strip().replace(' ', '')
            if amt_m.group(1):
                result["currency"] = amt_m.group(1).upper()
                
    # 2. Date
    date_m = re.search(r"(?:交易日期|日期)\s*[:：]?\s*(\d{4})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{1,2})", text)
    if date_m:
        result["date"] = f"{date_m.group(1)}-{int(date_m.group(2)):02d}-{int(date_m.group(3)):02d}"
    else:
        # Fallback date
        patterns = [
            r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
            r"(\d{4})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{1,2})",
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                result["date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
                break
                
    # 3. Fee
    lines = text.split('\n')
    fee_idx = -1
    for idx, line in enumerate(lines):
        if "手续费" in line:
            fee_idx = idx
            break
            
    if fee_idx != -1:
        start = max(0, fee_idx - 3)
        end = min(len(lines), fee_idx + 4)
        for i in range(start, end):
            cleaned_line = re.sub(r'[¥￥\s]', '', lines[i])
            if re.match(r'^\d+\.\d{1,2}$', cleaned_line):
                try:
                    val = float(cleaned_line)
                    main_val = float(str(result.get("amount", "0")).replace(',', ''))
                    if abs(val - main_val) > 0.01 and val < 100.0:
                        result["fee_amount"] = cleaned_line
                        break
                except:
                    pass
                    
    return result

with open('data/ocr_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

for h, item in cache.items():
    text = item.get('raw_text', '')
    if any(kw in text for kw in ["SHINHAN", "网上银行", "电子回单"]):
        res = parse_bank_receipt_test(text)
        print(f"Hash: {h[:10]}... | Amt: {res['amount']} | Curr: {res['currency']} | Date: {res['date']} | Fee: {res['fee_amount']}")
