import json

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))
lm_item = next(x for x in learning_model if x['pdf_filename'] == '50.pdf')

for i in [0, 1, 2, 3]:
    print(f"=== Page {i+1} ===")
    print(lm_item['ocr_pages'][i].strip())
    print("-" * 50)
