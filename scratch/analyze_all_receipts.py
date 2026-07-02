import json, os, re

# Load files
learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))
data = json.load(open('영수증 보관소/2026-05/data.json', encoding='utf-8'))

# Map evidence_no to original pdf & page
target_dir = os.path.abspath('영수증 보관소/2026-05')
images = []
for item in os.listdir(target_dir):
    a_dir = os.path.join(target_dir, item)
    if os.path.isdir(a_dir):
        for file in os.listdir(a_dir):
            if file.endswith('.pdf.processed'):
                # Read page count from processed file (or just match in learning_model)
                pdf_name = file[:-10]
                lm_item = next((x for x in learning_model if x['pdf_filename'] == pdf_name), None)
                if lm_item:
                    for page_num in range(len(lm_item['ocr_pages'])):
                        images.append({
                            'assignee': item,
                            'original_pdf': pdf_name,
                            'page_num': page_num,
                            'file_name': f'{pdf_name[:-4]}_p{page_num}.png'
                        })
images.sort(key=lambda x: (x['assignee'], x['file_name']))
mapping = {i+1: (img['original_pdf'], img['page_num'], img['assignee']) for i, img in enumerate(images)}

# Group data by PDF
grouped_data = {}
for item in data:
    ev_no = item['evidence_no']
    if ev_no in mapping:
        pdf, page, assignee = mapping[ev_no]
        grouped_data.setdefault(pdf, {})[page] = item

# Now analyze from 07.pdf to 61-62.pdf
out_file = 'scratch/receipts_ocr_summary.txt'
with open(out_file, 'w', encoding='utf-8') as f:
    for item in learning_model:
        pdf = item['pdf_filename']
        num_part = pdf.replace('.pdf', '')
        # We start from 07.pdf
        if num_part.isdigit() and int(num_part) < 7:
            continue
        if num_part == '01' or num_part == '02' or num_part == '03' or num_part == '04' or num_part == '05' or num_part == '06':
            continue
            
        f.write(f"=========================================\n")
        f.write(f"PDF: {pdf}\n")
        f.write(f"Rules: {item['associated_rules']}\n")
        
        ocr_pages = item['ocr_pages']
        pdf_data = grouped_data.get(pdf, {})
        
        for idx, ocr in enumerate(ocr_pages):
            page_num = idx + 1
            f.write(f"  --- Page {page_num} ---\n")
            # Get data.json values
            page_data = pdf_data.get(idx, {})
            f.write(f"    Data.json Amount: {page_data.get('amount')}, Desc: {page_data.get('description')}, Seller: {page_data.get('seller')}, Type: {page_data.get('type')}\n")
            
            # Print cleaned OCR lines
            lines = [l.strip() for l in ocr.split('\n') if l.strip()]
            f.write(f"    OCR snippet:\n")
            for line in lines[:15]:
                f.write(f"      {line}\n")
            if len(lines) > 15:
                f.write(f"      ... ({len(lines)-15} more lines)\n")
        f.write("\n")

print(f"Analysis written to {out_file}")
