import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

cn_digits = {'零': 0, '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9, '貮': 2, '两': 2}
cn_units = {'拾': 10, '佰': 100, '仟': 1000, '万': 10000, '亿': 100000000}

def parse_cn_amount(cn_str: str) -> float:
    valid_chars = set(list(cn_digits.keys()) + list(cn_units.keys()) + ['元', '圆', '角', '分', '整'])
    cleaned = ''.join([c for c in cn_str if c in valid_chars])
    
    if not cleaned:
        return 0.0
        
    yuan_part = cleaned
    jiao_val = 0.0
    fen_val = 0.0
    
    # Extract Jiao (角)
    jiao_m = re.search(r'([零壹贰叁肆伍陆柒捌玖])角', yuan_part)
    if jiao_m:
        jiao_val = cn_digits[jiao_m.group(1)] * 0.1
        yuan_part = yuan_part.replace(jiao_m.group(0), '')
        
    # Extract Fen (分)
    fen_m = re.search(r'([零壹贰叁肆伍陆柒捌玖])分', yuan_part)
    if fen_m:
        fen_val = cn_digits[fen_m.group(1)] * 0.01
        yuan_part = yuan_part.replace(fen_m.group(0), '')
        
    # Remove remaining suffix characters
    yuan_part = re.sub(r'[元圆整]', '', yuan_part)
    
    def parse_section(section_str):
        section_val = 0
        current_digit = 0
        has_digit = False
        for char in section_str:
            if char in cn_digits:
                current_digit = cn_digits[char]
                has_digit = True
            elif char in cn_units:
                unit = cn_units[char]
                # If there's no digit before unit (e.g. 拾元 -> 10 yuan), default to 1
                if not has_digit:
                    current_digit = 1
                section_val += current_digit * unit
                current_digit = 0
                has_digit = False
        if has_digit:
            section_val += current_digit
        return section_val

    if '万' in yuan_part:
        parts = yuan_part.split('万')
        val = parse_section(parts[0]) * 10000 + parse_section(parts[1])
    else:
        val = parse_section(yuan_part)
        
    return float(val) + jiao_val + fen_val

def extract_cn_amount_string(text: str) -> str:
    candidates = re.findall(r'[零壹贰叁肆伍陆柒捌玖拾佰仟万亿元圆角分整]{2,}', text)
    if not candidates:
        return ""
    valid_candidates = []
    for cand in candidates:
        if any(u in cand for u in ['拾', '佰', '仟', '万', '亿', '元', '圆', '整']):
            valid_candidates.append(cand)
    if not valid_candidates:
        return ""
    return max(valid_candidates, key=len)

with open('data/ocr_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

for h, item in cache.items():
    text = item.get('raw_text', '')
    if any(kw in text for kw in ['发票', '增值税', '成品油', '过路费', '加油票', '客运资金']):
        cn_str = extract_cn_amount_string(text)
        if cn_str:
            parsed = parse_cn_amount(cn_str)
            print(f"Hash: {h[:10]}... | Extracted CN: {cn_str} | Parsed Num: {parsed}")
