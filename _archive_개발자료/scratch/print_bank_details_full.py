import json

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))
targets = ['25.pdf', '30.pdf', '37.pdf', '45.pdf', '57.pdf', '60.pdf']

for t in targets:
    lm_item = next((x for x in learning_model if x['pdf_filename'] == t), None)
    if lm_item:
        print(f"=== {t} ===")
        print(lm_item['ocr_pages'][0].strip())
    print("-" * 50)
