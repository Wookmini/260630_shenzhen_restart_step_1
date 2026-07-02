import os, json

target_dir = '영수증 보관소/2026-05'
learning_model = json.load(open('data/shenzhen_receipt_learning_model.json', encoding='utf-8'))

images = []
for item in os.listdir(target_dir):
    assignee_dir = os.path.join(target_dir, item)
    if os.path.isdir(assignee_dir):
        for file in os.listdir(assignee_dir):
            if file.endswith('.pdf.processed'):
                pdf_name = file[:-10]
                lm_it = next((x for x in learning_model if x['pdf_filename'] == pdf_name), None)
                if lm_it:
                    for page_num in range(len(lm_it['ocr_pages'])):
                        images.append({
                            'assignee': item,
                            'pdf_name': pdf_name,
                            'page_num': page_num,
                            'orig_filename': f"{pdf_name[:-4]}_p{page_num}.png"
                        })

images.sort(key=lambda x: (x['assignee'], x['orig_filename']))

print(f"Reconstructed {len(images)} pages.")
for idx, img in enumerate(images[:10]):
    print(f"ev_no={idx+1:03d} -> assignee={img['assignee']}, pdf={img['pdf_name']}, page={img['page_num']+1}")
