import json
import hashlib

def compute_image_hash(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()

with open('영수증 보관소/2026-05/Chen Feng Ju/014.png', 'rb') as f:
    img_bytes = f.read()

img_hash = compute_image_hash(img_bytes)
print("Hash calculated:", img_hash)

with open('data/ocr_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

res = cache.get(img_hash)
with open('scratch/ocr_text_output.txt', 'w', encoding='utf-8') as out:
    if res:
        out.write(f"HASH: {img_hash}\n")
        out.write(f"TEXT:\n{res.get('raw_text', '')}\n")
    else:
        out.write("Hash not found in cache!\n")
