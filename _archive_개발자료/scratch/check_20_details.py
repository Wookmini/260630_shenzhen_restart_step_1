import json, os

learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))
lm_item = next(x for x in learning_model if x['pdf_filename'] == '20.pdf')
ocr_pages = lm_item['ocr_pages']

# Find ev mapping
target_dir = os.path.abspath('영수증 보관소/2026-05')
images = []
for item in os.listdir(target_dir):
    a_dir = os.path.join(target_dir, item)
    if os.path.isdir(a_dir):
        for file in os.listdir(a_dir):
            if file.endswith('.pdf.processed'):
                pdf_name = file[:-10]
                lm_it = next((x for x in learning_model if x['pdf_filename'] == pdf_name), None)
                if lm_it:
                    for page_num in range(len(lm_it['ocr_pages'])):
                        images.append({
                            'assignee': item,
                            'original_pdf': pdf_name,
                            'page_num': page_num,
                            'file_name': f'{pdf_name[:-4]}_p{page_num}.png'
                        })
images.sort(key=lambda x: (x['assignee'], x['file_name']))
mapping = {i+1: (img['original_pdf'], img['page_num'], img['assignee']) for i, img in enumerate(images)}

data = json.load(open('영수증 보관소/2026-05/data.json', encoding='utf-8'))
mapped_data = {}
for item in data:
    ev = item['evidence_no']
    if ev in mapping:
        pdf, page, assignee = mapping[ev]
        if pdf == '20.pdf':
            mapped_data[page] = (ev, item)

for page_idx in range(16):
    ev, item = mapped_data.get(page_idx, (None, None))
    ocr = ocr_pages[page_idx]
    print(f"=== Page {page_idx+1} (ev={ev:03d}.png) ===")
    if item:
        print(f"  data.json: amount={item.get('amount')}, desc={item.get('description')}, type={item.get('type')}, seller={item.get('seller')}")
    # print all lines containing numbers or currency symbols or specific patterns
    lines = [l.strip() for l in ocr.split('\n') if l.strip()]
    print(f"  OCR snippets:")
    for line in lines:
        if any(c.isdigit() or c in '¥￥$Rp' for c in line) or '发票' in line or '金额' in line or '合计' in line or '费' in line or '票' in line:
            print(f"    {line}")
