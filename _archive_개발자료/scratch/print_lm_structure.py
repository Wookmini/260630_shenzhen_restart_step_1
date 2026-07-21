import json

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))
print(f"Total items in learning model: {len(learning_model)}")
print("First item keys:", learning_model[0].keys())
print("First item values:")
for k, v in learning_model[0].items():
    if k != 'ocr_pages':
        print(f"  {k}: {v}")
    else:
        print(f"  ocr_pages (count): {len(v)}")
