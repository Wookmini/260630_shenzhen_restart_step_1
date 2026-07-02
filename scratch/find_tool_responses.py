import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

p = r"C:\Users\20000177\.gemini\antigravity\brain\a9923e8e-cf15-415c-81e7-2cd999fdb2d4\.system_generated\logs\overview.txt"
if os.path.exists(p):
    with open(p, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            try:
                data = json.loads(line)
                if data.get('type') == 'TOOL_RESPONSE' or 'response' in data:
                    print(f"Line {idx}: {line.strip()[:300]}")
            except Exception as e:
                pass
else:
    print("No overview.txt")
