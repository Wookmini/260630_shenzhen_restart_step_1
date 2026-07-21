import json

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))
targets = ['25.pdf', '30.pdf', '37.pdf', '45.pdf', '57.pdf', '60.pdf']

for t in targets:
    lm_item = next((x for x in learning_model if x['pdf_filename'] == t), None)
    if lm_item:
        print(f"=== {t} ===")
        # Print lines that look like payment purpose or notes (e.g. 附言, 户名, 收款, etc.)
        lines = lm_item['ocr_pages'][0].split('\n')
        for line in lines:
            line_str = line.strip()
            if any(x in line_str for x in ['附言', '收款方', '付款方', '户名', '转账', '手续费', '金额']):
                print("  ", line_str)
    print("-" * 50)
