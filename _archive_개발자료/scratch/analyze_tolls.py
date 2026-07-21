import json, re

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))

def parse_tolls(pdf_name):
    lm_item = next(x for x in learning_model if x['pdf_filename'] == pdf_name)
    print(f"================ {pdf_name} ================")
    for p_idx, page in enumerate(lm_item['ocr_pages']):
        print(f"--- Page {p_idx+1} ---")
        # Find all numbers that look like currency or amounts (e.g. 13.00, 13元, 13, -13.00, etc.)
        # Also print lines that say "发票号码", "发票代码", "金额"
        lines = page.split('\n')
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if any(x in line_str for x in ['金额', '元', '¥', '￥', '通行费', '支付', '实付', '收费']):
                print("  ", line_str)

parse_tolls('48.pdf')
parse_tolls('50.pdf')
parse_tolls('55.pdf')
