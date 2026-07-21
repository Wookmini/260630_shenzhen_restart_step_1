import json

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))
lm_item = next(x for x in learning_model if x['pdf_filename'] == '20.pdf')

print("=== Page 13 ===")
print(lm_item['ocr_pages'][12].strip())
