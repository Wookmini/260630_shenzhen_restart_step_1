import json
import hashlib
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Helper to compute SHA256 hash
def compute_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

with open('data/ocr_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

for fn in ['008.png', '010.png', '011.png', '012.png']:
    h = compute_hash(f'영수증 보관소/2026-05/Chen Feng Ju/{fn}')
    ocr = cache.get(h, {}).get('raw_text', '')
    print(f"=== File: {fn} ===")
    print(ocr)
