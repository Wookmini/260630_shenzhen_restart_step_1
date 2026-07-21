import json
import re
import fitz
import os

BASE_DIR = os.path.abspath('.')
target_dir = os.path.join(BASE_DIR, '영수증 보관소', '2026-05')

# Reconstruct PDF image mappings
images = []
for item in os.listdir(target_dir):
    assignee_dir = os.path.join(target_dir, item)
    if os.path.isdir(assignee_dir):
        for file in os.listdir(assignee_dir):
            if file.endswith('.pdf.processed'):
                doc = fitz.open(os.path.join(assignee_dir, file))
                pdf_basename = file[:-10]
                for page_num in range(len(doc)):
                    png_name = f"{os.path.splitext(pdf_basename)[0]}_p{page_num}.png"
                    images.append({
                        'assignee': item,
                        'original_pdf': pdf_basename,
                        'page_num': page_num,
                        'file_name': png_name
                    })
                doc.close()

images.sort(key=lambda x: (x['assignee'], x['file_name']))
mapping = {}
for i, img in enumerate(images):
    ev_no = i + 1
    mapping[ev_no] = (img['original_pdf'], img['page_num'], img['assignee'])

# Load ocr cache and learning model
ocr_cache = json.load(open('data/ocr_cache.json', encoding='utf-8'))
learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))
lm_dict = {item['pdf_filename']: item for item in learning_model}

# Load data.json
with open('영수증 보관소/2026-05/data.json', encoding='utf-8') as f:
    data = json.load(f)

# Group by PDF
grouped = {}
for item in data:
    ev_no = item.get('evidence_no')
    if ev_no in mapping:
        pdf, page, assignee = mapping[ev_no]
        grouped.setdefault(pdf, []).append((page, item, assignee))

# Output details for analysis
out_path = 'scratch/pdf_pages_analysis.txt'
with open(out_path, 'w', encoding='utf-8') as out:
    pdf_list = sorted(grouped.keys(), key=lambda x: [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', x)])
    for pdf in pdf_list:
        pages = sorted(grouped[pdf], key=lambda x: x[0])
        lm_item = lm_dict.get(pdf, {})
        rules = lm_item.get('associated_rules', [])
        out.write(f"=== {pdf} ===\n")
        out.write(f"Rules: {rules}\n")
        for page, item, assignee in pages:
            # get ocr text
            img_path = os.path.join(target_dir, assignee, f"{item.get('evidence_no'):03d}.png")
            import hashlib
            h = hashlib.sha256(open(img_path, 'rb').read()).hexdigest()
            raw_text = ocr_cache.get(h, {}).get('raw_text', '')
            # Clean up white space in raw_text for easy reading
            text_snippet = " | ".join([line.strip() for line in raw_text.split("\n") if line.strip()][:15])
            out.write(f"  Page {page+1} (ev={item.get('evidence_no')}): amount={item.get('amount')}, type={item.get('type')}, seller={item.get('seller')}, desc={item.get('description')}\n")
            out.write(f"    OCR Snippet: {text_snippet[:300]}\n")
        out.write("\n")

print("Done. Output written to scratch/pdf_pages_analysis.txt")
