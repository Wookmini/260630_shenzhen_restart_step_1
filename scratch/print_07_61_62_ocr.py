import json

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))

for pdf in ['07.pdf', '61-62.pdf']:
    lm_item = next((x for x in learning_model if x['pdf_filename'] == pdf), None)
    if lm_item:
        print(f"=== {pdf} ===")
        for i, page in enumerate(lm_item['ocr_pages']):
            print(f"--- Page {i+1} ---")
            print(page.strip())
    print("-" * 50)
