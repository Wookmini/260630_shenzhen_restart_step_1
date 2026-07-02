import json
import hashlib
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/Chen Feng Ju/001.png', 'rb') as f:
    img_bytes = f.read()

img_hash = hashlib.sha256(img_bytes).hexdigest()
print("Hash calculated:", img_hash)

with open('data/ocr_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

res = cache.get(img_hash)
if res:
    print("TEXT:")
    print(res.get('raw_text', ''))
else:
    print("Hash not found in cache!")
