import json
with open(r'C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\영수증 보관소\2026-05\data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for d in data:
    if d.get("withdrawal_date") is None:
        print(f"None WDate! Person: {d.get('person')} | Ev: {d.get('evidence_no')} | Date: {d.get('date')}")
