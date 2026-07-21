import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

branch_receipts = [r for r in data if r.get('person') == '심천지사']
print(f"Total receipts for 심천지사: {len(branch_receipts)}")
total_sum = 0.0
for r in sorted(branch_receipts, key=lambda x: x.get('file_path')):
    file_no = r.get('file_path').split('/')[-1]
    amt = r.get('amount')
    desc = r.get('description')
    print(f"File: {file_no} | Amt: {amt} | Desc: {desc}")
    if desc != '은행수수료' and amt is not None:
        total_sum += float(amt)

print(f"Total Sum of non-fee expenses: {total_sum}")
