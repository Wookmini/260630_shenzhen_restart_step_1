import json
import sys

# Reconfigure stdout to use utf-8 to avoid encoding errors in terminal output
sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

cfj = [r for r in data if r.get('person') == 'Chen Feng Ju']
print("Chen Feng Ju receipts:")
for r in cfj:
    print(f"File: {r.get('file_path')} | Date: {r.get('date')} | Amt: {r.get('amount')} | Desc: {r.get('description')} | IsBankFee: {r.get('is_bank_fee_receipt')}")

total_non_fee = sum(float(str(r.get('amount') or 0).replace(',', '')) for r in cfj if r.get('description') != '은행수수료')
print("Total non-fee:", total_non_fee)
