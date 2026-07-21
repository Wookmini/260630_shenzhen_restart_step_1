import json

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))
lm_item = next(x for x in learning_model if x['pdf_filename'] == '27.pdf')

for p in [5, 6, 7]:
    print(f"=== Page {p+1} ===")
    print(lm_item['ocr_pages'][p].strip())
    print("-" * 50)
