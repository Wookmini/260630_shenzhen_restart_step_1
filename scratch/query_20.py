import json, os, fitz
target_dir = os.path.abspath('영수증 보관소/2026-05')
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
for i, img in enumerate(images):
    if img['original_pdf'] == '20.pdf':
        print(f"ev={i+1:03d}.png, page={img['page_num']+1}, assignee={img['assignee']}")
