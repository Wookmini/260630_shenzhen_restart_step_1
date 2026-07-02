import json
import sys
import os

sys.path.append(r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1")
from excel_exporter import export_to_excel

data_json_path = r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\영수증 보관소\2026-05\data.json"
excel_path = r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\영수증 보관소\2026-05\정산내역_2026-05_v2.xlsx"

with open(data_json_path, "r", encoding="utf-8") as f:
    d = json.load(f)

# Find evidence_no 219 and split it
new_data = []
for item in d:
    if item.get("evidence_no") == 219:
        # Create Item 1: 급여
        item1 = item.copy()
        item1["amount"] = 280937.55
        item1["description"] = "급여"
        item1["account_major"] = "해외지사비"
        item1["account_minor"] = None
        new_data.append(item1)
        
        # Create Item 2: 은행수수료
        item2 = item.copy()
        item2["amount"] = 12.0
        item2["description"] = "은행수수료"
        item2["account_major"] = "해외지사비"
        item2["account_minor"] = None
        new_data.append(item2)
    else:
        new_data.append(item)

# Save back to data.json
with open(data_json_path, "w", encoding="utf-8") as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

# Export to excel
export_to_excel(new_data, "2026-05", excel_path)
print("Successfully split evidence_no 219 and generated new Excel.")
