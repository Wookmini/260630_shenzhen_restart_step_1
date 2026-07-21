import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

branch_receipts = [r for r in data if r.get('person') == '심천지사']
for r in sorted(branch_receipts, key=lambda x: int(x.get('evidence_no') or 0)):
    ev = int(r.get('evidence_no') or 0)
    if ev <= 208:
        print(f"EvNo: {r.get('evidence_no')} | File: {r.get('file_path').split('/')[-1]} | Type: {r.get('type')} | Date: {r.get('date')} | Withdrawal Date: {r.get('withdrawal_date')} | Amt: {r.get('amount')} | Desc: {r.get('description')} | Warning: {r.get('validation_warning')}")
