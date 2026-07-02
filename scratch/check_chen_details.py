import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chen_receipts = [r for r in data if r.get('person') == 'Chen Feng Ju']
print(f"Total receipts for Chen Feng Ju: {len(chen_receipts)}")
for r in sorted(chen_receipts, key=lambda x: x.get('file_path')):
    file_no = r.get('file_path').split('/')[-1]
    print(f"File: {file_no} | Amt: {r.get('amount')} | Desc: {r.get('description')} | Date: {r.get('date')}")
