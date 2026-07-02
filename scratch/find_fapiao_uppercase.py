import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/ocr_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

# Chinese uppercase digit map
cn_digits = {'零':0, '壹':1, '贰':2, '叁':3, '肆':4, '伍':5, '陆':6, '柒':7, '捌':8, '玖':9}
cn_units = {'拾':10, '佰':100, '仟':1000, '万':10000, '亿':100000000}

def parse_chinese_money(text):
    # Regex to find uppercase money text
    # e.g., 贰佰玖拾伍圆整, 壹仟贰佰元, etc.
    # We look for a sequence of characters containing cn_digits and cn_units, ending with 圆/元/整
    match = re.search(r'([零壹贰叁肆伍陆柒捌玖拾佰仟万亿元圆角分整]+)', text)
    if not match:
        return None
    # Let's clean the matched sequence to only contain valid financial characters
    # Usually it's in a label like "价税合计（大写） 贰佰玖拾伍圆整"
    lines = text.split('\n')
    for line in lines:
        if '大写' in line or '合计' in line:
            # Look for uppercase sequence in this line or subsequent line
            m = re.search(r'(?:大写|合计).*?([零壹贰叁肆伍陆柒捌玖拾佰仟万亿元圆角分整]{2,})', line)
            if m:
                return m.group(1)
    return None

print("Checking OCR cache for Fapiao uppercase amounts:")
for h, item in cache.items():
    text = item.get('raw_text', '')
    if '发票' in text or '增值税' in text or '成品油' in text:
        uppercase = parse_chinese_money(text)
        print(f"Hash: {h[:10]}... | Uppercase: {uppercase}")
        # print first few lines of text
        print("Lines:")
        for line in text.split('\n')[:15]:
            print(f"  {line}")
        print("-" * 50)
