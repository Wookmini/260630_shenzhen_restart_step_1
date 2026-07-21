import json, re

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))
lm_item = next(x for x in learning_model if x['pdf_filename'] == '20.pdf')

for idx, page in enumerate(lm_item['ocr_pages']):
    print(f"=== Page {idx+1} ===")
    lines = page.split('\n')
    for line in lines:
        l = line.strip()
        if not l: continue
        # Find amounts
        matches = re.findall(r'[-￥¥]?\b\d+(?:\.\d{1,2})?\b(?:元|元整)?', l)
        cleaned = []
        for m in matches:
            clean_m = m.replace('元整', '').replace('元', '').replace('￥', '').replace('¥', '')
            try:
                val = float(clean_m)
                if val > 0 and val < 10000:
                    cleaned.append(val)
            except ValueError:
                pass
        if cleaned:
            print("  ", l, "->", cleaned)
