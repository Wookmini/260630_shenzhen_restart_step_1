import json
with open("영수증 보관소/2026-05/data.json", encoding="utf-8") as f:
    d = json.load(f)
with open("scratch/last_entries.txt", "w", encoding="utf-8") as out:
    for item in d[-5:]:
        out.write(json.dumps(item, ensure_ascii=False) + "\n")
