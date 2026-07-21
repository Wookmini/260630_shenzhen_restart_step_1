import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chen_receipts = [r for r in data if r.get('person') == 'Chen Feng Ju']
print(f"Total receipts for Chen Feng Ju: {len(chen_receipts)}")
sum_amt = 0.0
for r in chen_receipts:
    print(f"File: {r.get('file_path')} | Type: {r.get('type')} | Date: {r.get('date')} | Withdrawal Date: {r.get('withdrawal_date')} | Amt: {r.get('amount')} | Desc: {r.get('description')} | Warning: {r.get('validation_warning')}")
    if r.get('description') != '은행수수료' and r.get('amount') is not None:
        sum_amt += float(r.get('amount'))

print(f"Sum of expenses: {sum_amt}")
