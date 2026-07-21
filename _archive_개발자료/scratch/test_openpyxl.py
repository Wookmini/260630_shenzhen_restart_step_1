import openpyxl
import time
import os

TEMPLATE_PATH = r"c:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\26년_6월 심천지사 전도금 정산(데이터 양식 변경).xlsx"
output_path = r"c:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\scratch_test.xlsx"

t0 = time.time()
print("Loading workbook...")
wb = openpyxl.load_workbook(TEMPLATE_PATH)
print(f"Loaded in {time.time() - t0:.2f} seconds")

t1 = time.time()
print("Saving workbook...")
wb.save(output_path)
print(f"Saved in {time.time() - t1:.2f} seconds")

if os.path.exists(output_path):
    os.remove(output_path)
