import json

with open("data/ocr_cache.json", encoding="utf-8") as f:
    d = json.load(f)

for v in d.values():
    if v.get("filename") == "219.png":
        with open("scratch/219_ocr_text.txt", "w", encoding="utf-8") as out:
            out.write(v.get("raw_text", ""))
