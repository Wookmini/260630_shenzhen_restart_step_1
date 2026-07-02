import os
import sys
sys.path.append(r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1")
from ocr_engine import run_ocr_from_file

file_path = r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\영수증 보관소\2026-05\심천지사\219.png"
result = run_ocr_from_file(file_path)
with open("scratch/real_219_text.txt", "w", encoding="utf-8") as f:
    f.write(result.get("raw_text", ""))
