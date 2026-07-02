import shutil
import os
import json
import hashlib

dst_dir = r"C:\Users\20000177\.gemini\antigravity\brain\a9923e8e-cf15-415c-81e7-2cd999fdb2d4\browser"
os.makedirs(dst_dir, exist_ok=True)

# Helper to compute SHA256 hash
def compute_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

# Copy 008, 009, 014 to browser
for fn in ["008.png", "009.png", "014.png"]:
    src = os.path.join("영수증 보관소/2026-05/Chen Feng Ju", fn)
    dst = os.path.join(dst_dir, fn)
    shutil.copy(src, dst)
    print("Copied Chen Feng Ju:", fn)

with open('data/ocr_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

for fn in ["008.png", "009.png", "014.png"]:
    p = os.path.join("영수증 보관소/2026-05/Chen Feng Ju", fn)
    h = compute_hash(p)
    ocr = cache.get(h, {}).get('raw_text', '')
    print(f"\n=== OCR for {fn} ===")
    print(ocr)
