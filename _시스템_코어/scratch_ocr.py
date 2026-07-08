import os, json
import sys
sys.path.append(os.path.dirname(__file__))
from ocr_engine import run_ocr

base_path = r"c:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1"
img_path = os.path.join(base_path, "작업장소 (영수증 보관)", "2026-06", "Lin Wei Jian", "001-여비교통비-284.7.jpg")

with open(img_path, 'rb') as f:
    data = f.read()

res = run_ocr(data, '001.jpg')
print(res['raw_text'])
