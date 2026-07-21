import json

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))
lm_item = next(x for x in learning_model if x['pdf_filename'] == '48.pdf')

for idx, page in enumerate(lm_item['ocr_pages']):
    print(f"=== Page {idx+1} ===")
    lines = page.split('\n')
    for line in lines:
        l = line.strip()
        if not l: continue
        # Print if it contains digits and is short, or has '元', '金额', '号码'
        if any(x in l for x in ['元', '金额', '号码', '代码', '收费员车型']) or len(l) < 30:
            print("  ", l)
    print("-" * 50)
