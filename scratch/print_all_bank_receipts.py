import json

with open('data/ocr_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

with open('scratch/all_bank_ocr_texts.txt', 'w', encoding='utf-8') as out:
    for h, data in cache.items():
        text = data.get('raw_text', '')
        if any(kw in text for kw in ["SHINHAN", "网上银行", "电子回单"]):
            out.write(f"--- HASH: {h} ---\n")
            out.write(text)
            out.write("\n\n")
