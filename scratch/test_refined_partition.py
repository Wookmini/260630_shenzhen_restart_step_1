import json
from collections import defaultdict
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Sort all by evidence_no to ensure order
data.sort(key=lambda x: int(x.get('evidence_no') or 0))

# Pre-process: fix the 201.png amount if it was parsed as 19.23 but the lowercase says 79.23
# Let's see: in data.json, we can simulate what our updated parser would do.
for r in data:
    if r.get('file_path') == '영수증 보관소/2026-05/심천지사/201.png':
        r['amount'] = 79.23
    # Simulating commission fee extraction for 199.png and 203.png
    if r.get('file_path') == '영수증 보관소/2026-05/심천지사/199.png':
        r['amount'] = 10.0
        r['description'] = 'USD입금 and RMB 환전'
    if r.get('file_path') == '영수증 보관소/2026-05/심천지사/203.png':
        r['amount'] = 25.0
        r['description'] = 'USD입금 and RMB 환전'

# Group by person
person_groups = defaultdict(list)
for r in data:
    person_groups[r.get('person')].append(r)

for person, person_receipts in person_groups.items():
    if person == '권유석':
        continue
    
    # Sort bank fee receipts
    bank_receipts = [r for r in person_receipts if r.get('is_bank_fee_receipt')]
    bank_receipts.sort(key=lambda x: int(x.get('evidence_no') or 0))
    
    if not bank_receipts:
        print(f"Person: {person} has no bank receipts")
        continue
        
    print(f"\n=== Person: {person} ({len(bank_receipts)} bank receipts) ===")
    
    # Map each receipt to its corresponding bank receipt
    br_to_receipts = defaultdict(list)
    for r in person_receipts:
        desc = r.get('description') or ''
        # Exclude inward remittance from bank receipt matching
        if '입금' in desc or '환전' in desc:
            r['withdrawal_date'] = r.get('date')
            continue
            
        # Find matched bank receipt
        matched_br = None
        r_ev = int(r.get('evidence_no') or 0)
        for br in bank_receipts:
            br_ev = int(br.get('evidence_no') or 0)
            if br_ev >= r_ev:
                matched_br = br
                break
        if not matched_br:
            matched_br = bank_receipts[-1]
            
        br_to_receipts[id(matched_br)].append(r)
        
    for br in bank_receipts:
        matched_list = br_to_receipts[id(br)]
        # Filter out bank fee receipt from calculation
        exp_list = [r for r in matched_list if not r.get('is_bank_fee_receipt')]
        
        # Auto-fill logic: if exactly one expense has None/0 amount
        if len(exp_list) == 1:
            exp_r = exp_list[0]
            if exp_r.get('amount') is None or exp_r.get('amount') == 0.0:
                principal = br.get('principal_amount')
                try:
                    principal_float = float(str(principal).replace(',', ''))
                except:
                    principal_float = 0.0
                exp_r['amount'] = principal_float
                print(f"    [Auto-filled Amount] File: {exp_r.get('file_path')} filled with {principal_float} from Bank Receipt EvNo: {br.get('evidence_no')}")
        
        sum_expenses = 0.0
        for r in exp_list:
            if r.get('amount') is not None:
                sum_expenses += float(r.get('amount'))
        
        principal = br.get('principal_amount')
        try:
            principal_float = float(str(principal).replace(',', ''))
        except:
            principal_float = 0.0
            
        diff = abs(sum_expenses - principal_float)
        status = "금액 일치" if diff <= 1.0 else f"불일치 (이체:{principal_float} vs 영수증:{sum_expenses})"
        
        print(f"  Bank Fee Receipt EvNo: {br.get('evidence_no')} (File: {br.get('file_path')})")
        print(f"    Date: {br.get('date')} | Fee: {br.get('amount')} | Principal: {principal_float}")
        print(f"    Matched expenses count: {len(exp_list)} | Sum: {sum_expenses}")
        print(f"    Result: {status}")
