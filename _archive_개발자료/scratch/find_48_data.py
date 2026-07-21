import json

data = json.load(open('영수증 보관소/2026-05/data.json', encoding='utf-8'))
for item in data:
    if item.get('evidence_no') in range(165, 172) or '48.pdf' in str(item.get('evidence_no')):
        # Let's just print all items that have "通行费" or "톨비" or are in Chen Guo Liang
        pass

# Let's print items with evidence_no between 150 and 190 to check Chen Guo Liang's items
# Chen Guo Liang is assignee for 46 (주유비), 47 (주차비), 48 (톨비), 49 (은행수수료)
# Let's find ev numbers for 48.pdf
import os, fitz
learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))
targets = ['46.pdf', '47.pdf', '48.pdf', '49.pdf']
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
    if img['original_pdf'] in targets:
        ev_no = i + 1
        item_in_data = next((x for x in data if x.get('evidence_no') == ev_no), None)
        amt = item_in_data.get('amount') if item_in_data else None
        desc = item_in_data.get('description') if item_in_data else None
        print(f"ev={ev_no:03d}.png, pdf={img['original_pdf']}, page={img['page_num']+1}, assignee={img['assignee']}, amount={amt}, desc={desc}")
