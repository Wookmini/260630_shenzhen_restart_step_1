import json, os, fitz, hashlib
target_dir = os.path.abspath('영수증 보관소/2026-05')
ocr_cache = json.load(open('data/ocr_cache.json', encoding='utf-8'))

images = []
for item in os.listdir(target_dir):
    a_dir = os.path.join(target_dir, item)
    if os.path.isdir(a_dir):
        for file in os.listdir(a_dir):
            if file.endswith('.pdf.processed'):
                doc = fitz.open(os.path.join(a_dir, file))
                for page_num in range(len(doc)):
                    images.append({'assignee': item, 'original_pdf': file[:-10], 'page_num': page_num, 'file_name': f'{file[:-10]}_p{page_num}.png'})
images.sort(key=lambda x: (x['assignee'], x['file_name']))
mapping = {i+1: (img['original_pdf'], img['page_num'], img['assignee']) for i, img in enumerate(images)}

data = json.load(open('영수증 보관소/2026-05/data.json', encoding='utf-8'))
for item in data:
    pdf, page, assignee = mapping[item['evidence_no']]
    if pdf == '20.pdf':
        img_path = os.path.join(target_dir, assignee, f"{item['evidence_no']:03d}.png")
        h = hashlib.sha256(open(img_path, 'rb').read()).hexdigest()
        raw_text = ocr_cache.get(h, {}).get('raw_text', '')
        print(f"=== PAGE {page+1} ===")
        print(raw_text.replace('\n', ' | '))
