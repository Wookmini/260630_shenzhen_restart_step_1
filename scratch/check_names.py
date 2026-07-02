import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

names = set(r.get('person') for r in results)
print("Unique names:", names)

print("\nAll items with warnings:")
for r in results:
    warn = r.get('validation_warning')
    if warn and "불일치" in warn:
        print(f"[{r.get('person')}] Ev {r.get('evidence_no')}: {warn}")
