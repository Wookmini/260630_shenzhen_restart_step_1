import json, os

data = json.load(open('영수증 보관소/2026-05/data.json', encoding='utf-8'))
learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))

for item in data:
    # Liu Ming Liang is assignee. Let's find ev numbers for 50.pdf
    pass

images = []
target_dir = os.path.abspath('영수증 보관소/2026-05')
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
for i, img in enumerate(images):
    if img['original_pdf'] == '50.pdf':
        ev_no = i + 1
        item_in_data = next((x for x in data if x.get('evidence_no') == ev_no), None)
        amt = item_in_data.get('amount') if item_in_data else None
        desc = item_in_data.get('description') if item_in_data else None
        print(f"ev={ev_no:03d}.png, pdf={img['original_pdf']}, page={img['page_num']+1}, assignee={img['assignee']}, amount={amt}, desc={desc}")
