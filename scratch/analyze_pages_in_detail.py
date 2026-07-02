import json

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))

targets = {
    '27.pdf': [5, 6, 7],
    '41.pdf': [5],
    '42.pdf': [3],
    '47.pdf': [0, 1],
    '48.pdf': [0, 1, 2, 3, 4, 5],
    '50.pdf': [0, 1, 2, 3, 4, 5]
}

for pdf, pages in targets.items():
    lm_item = next((x for x in learning_model if x['pdf_filename'] == pdf), None)
    if not lm_item:
        print(f"PDF {pdf} not found in learning model")
        continue
    for p in pages:
        if p < len(lm_item['ocr_pages']):
            print(f"=== {pdf} Page {p+1} ===")
            print(lm_item['ocr_pages'][p].strip())
            print("-" * 40)
