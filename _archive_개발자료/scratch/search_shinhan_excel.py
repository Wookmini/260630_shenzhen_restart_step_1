import json, openpyxl

wb = openpyxl.load_workbook('과거 참고데이터/26년 5월/5월 스캔본_재정비/엑셀 대응/추론값.xlsx')
ws = wb.active

for r in range(7, ws.max_row+1):
    val_a = ws.cell(row=r, column=1).value
    val_b = ws.cell(row=r, column=2).value or ''
    # If the file exists in the directory, let's print some examples of row 1 to 20
    if r < 15:
        print(f"Row {r}: {val_a} -> {val_b}")
