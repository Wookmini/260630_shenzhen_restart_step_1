import openpyxl
import sys

sys.stdout.reconfigure(encoding='utf-8')

wb = openpyxl.load_workbook('영수증 보관소/2026-05/정산내역_2026-05_v3양식.xlsx', data_only=True)
sheet = wb.active

print("v3 Rows 230-250:")
for row_idx in range(230, 251):
    row_vals = [sheet.cell(row=row_idx, column=col).value for col in range(1, 19)]
    print(f"Row {row_idx}: {row_vals}")
