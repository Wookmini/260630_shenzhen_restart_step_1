import json
data=json.load(open('c:/Users/20000177/Desktop/Wooktigravity/260630_shenzhen_restart_step_1/작업장소 (영수증 보관)/2026-05/data.json', encoding='utf-8'))
val = [r.get('validation_warning') for r in data if r.get('evidence_no') == 31]
with open('c:/Users/20000177/Desktop/Wooktigravity/260630_shenzhen_restart_step_1/scratch/test_out.txt', 'w', encoding='utf-8') as f:
    f.write(repr(val))
