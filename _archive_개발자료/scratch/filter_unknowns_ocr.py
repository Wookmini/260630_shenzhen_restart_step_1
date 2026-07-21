import json

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))

targets = {
    '27.pdf': [5, 6, 7],
    '41.pdf': [5],
    '42.pdf': [3],
    '47.pdf': [0, 1],
    '48.pdf': [0, 1, 2, 3, 4, 5]
}

for pdf, pages in targets.items():
    lm_item = next((x for x in learning_model if x['pdf_filename'] == pdf), None)
    if not lm_item:
        print(f"PDF {pdf} not found in learning model")
        continue
    for p in pages:
        if p < len(lm_item['ocr_pages']):
            print(f"=== {pdf} Page {p+1} ===")
            lines = [l.strip() for l in lm_item['ocr_pages'][p].split('\n') if l.strip()]
            for line in lines:
                # print lines that are likely to contain amounts, transaction ids, dates, or payment details
                if any(c.isdigit() or c in '¥￥$Rp' for c in line) or '订单' in line or '合计' in line or '金额' in line or '费' in line or '收款' in line:
                    print("  ", line)
            print("-" * 40)
