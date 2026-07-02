import json, re

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))

def analyze_pdf_amounts(pdf_filename):
    lm_item = next(x for x in learning_model if x['pdf_filename'] == pdf_filename)
    print(f"=== {pdf_filename} ===")
    for p_idx, page in enumerate(lm_item['ocr_pages']):
        # Find all numbers like XX.00 or XX元 or similar in the text
        amounts = []
        # We can extract all patterns like \b\d+(?:\.\d{2})?\b and filter
        # Let's search for lines containing money terms
        lines = page.split('\n')
        for line in lines:
            # Match digits followed by '元' or '元整' or starting with '￥' or '-'
            matches = re.findall(r'[-￥¥]?\b\d+(?:\.\d{1,2})?\b(?:元|元整)?', line)
            if matches:
                # clean matches
                cleaned = []
                for m in matches:
                    clean_m = m.replace('元整', '').replace('元', '').replace('￥', '').replace('¥', '')
                    try:
                        val = float(clean_m)
                        if val > 0 and val < 500: # exclude large phone numbers or invoice numbers
                            cleaned.append(val)
                    except ValueError:
                        pass
                if cleaned:
                    print(f"  Page {p_idx+1}: {line.strip()} -> {cleaned}")

analyze_pdf_amounts('48.pdf')
analyze_pdf_amounts('50.pdf')
analyze_pdf_amounts('55.pdf')
