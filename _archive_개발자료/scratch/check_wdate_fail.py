import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\영수증 보관소\2026-05\data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for person in set(d['person'] for d in data if d.get('person')):
    if person == '권유석': continue
    receipts = [d for d in data if d.get('person') == person and not d.get('is_bank_fee_receipt')]
    
    # Check if for all general receipts, withdrawal_date == date
    all_same = True
    for r in receipts:
        if r.get('withdrawal_date') != r.get('date'):
            all_same = False
            break
    
    if all_same and len(receipts) > 0:
        print(f"FAILED PERSON: {person} - All withdrawal dates are equal to receipt dates!")

