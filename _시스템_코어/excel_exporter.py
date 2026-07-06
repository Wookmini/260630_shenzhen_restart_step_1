"""
엑셀 내보내기 모듈
관리 양식 템플릿(26.06 시트)에 맞게 OCR 데이터를 매핑하여 엑셀 생성
"""
import os
import shutil
import datetime
import openpyxl
from openpyxl.styles import PatternFill
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(
    BASE_DIR, "작업장소 (영수증 보관)", "심천지사 전도금 정산 양식_YYYY-MM.xlsx"
)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def ensure_output_dir():
    """출력 디렉토리 생성"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def export_to_excel(receipts: List[Dict[str, Any]], month_label: str = "26.06", output_path: str = None) -> str:
    """
    영수증 데이터 목록을 관리 양식 엑셀로 내보내기

    Args:
        receipts: 영수증 데이터 리스트 (각각 date, description, person, amount 등 포함)
        month_label: 대상 시트명 (기본: 26.06)

    Returns:
        생성된 엑셀 파일 경로

    26.06 시트 컬럼 매핑 (행 19~20 헤더 기준):
        B열(2): 출금일자
        C열(3): 증빙일자
        D열(4): 증빙번호(뒤5자리)
        E열(5): 내역
        F열(6): 담당자
        G열(7): 증빙번호
        H열(8): 대계정
        I열(9): 소계정
        J열(10): 입금 CNY
        K열(11): 입금 환산요율
        L열(12): 입금 USD
        M열(13): 출금 CNY
        N열(14): 출금 환산요율
        O열(15): 출금 USD
        P열(16): 잔액 CNY
        Q열(17): 잔액 USD
        R열(18): 이체증빙(비고)
        S열(19): 지출증빙(비고)
    """
    if not output_path:
        ensure_output_dir()
        # 타임스탬프 포함 출력 파일명
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"정산_export_{ts}.xlsx"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

    if os.path.exists(TEMPLATE_PATH):
        # 템플릿 복사 후 데이터 삽입
        shutil.copyfile(TEMPLATE_PATH, output_path)
        wb = openpyxl.load_workbook(output_path)
    else:
        # 템플릿이 없으면 새 워크북 생성
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = month_label
        # 헤더 작성
        headers_row19 = {2: "날짜", 5: "내역", 6: "담당자", 7: "증빙번호",
                         8: "대계정", 9: "소계정", 10: "입금", 13: "출금", 16: "잔액"}
        headers_row20 = {2: "출금일자", 3: "증빙일자", 4: "증빙번호(뒤5자리)",
                         5: "내역", 6: "담당자", 7: "증빙번호",
                         8: "대계정", 9: "소계정",
                         10: "CNY", 11: "환산요율", 12: "USD",
                         13: "CNY", 14: "환산요율", 15: "USD",
                         16: "CNY", 17: "USD", 18: "비고", 19: "항목"}
        for col, val in headers_row19.items():
            ws.cell(row=19, column=col, value=val)
        for col, val in headers_row20.items():
            ws.cell(row=20, column=col, value=val)

    # 대상 시트 접근
    if month_label in wb.sheetnames:
        ws = wb[month_label]
    else:
        ws = wb.active
        ws.title = month_label

    # Clear existing data rows starting from row 21 to allow clean overwrite/regeneration
    # We restrict the clearing loop to 1000 rows to prevent extreme lag from large ws.max_row (e.g. 490k rows)
    max_clear_row = min(max(ws.max_row + 1, 500), 1000)
    for r in range(22, max_clear_row):
        for c in range(1, min(ws.max_column + 1, 35)):
            cell = ws.cell(row=r, column=c)
            if cell.value is not None or (cell.fill and cell.fill.fill_type is not None):
                cell.value = None
                cell.fill = openpyxl.styles.PatternFill(fill_type=None)

    start_row = 22

    # 영수증 데이터 삽입
    for idx, receipt in enumerate(receipts):
        r = start_row + idx
        evidence_no = receipt.get("evidence_no", idx + 1)

        # B열: 출금일자 (은행 이체증명서 기준 일괄 적용된 날짜)
        withdrawal_date_val = receipt.get("withdrawal_date")
        if withdrawal_date_val and isinstance(withdrawal_date_val, datetime.datetime):
            withdrawal_date_val = withdrawal_date_val.strftime("%Y-%m-%d")
        elif withdrawal_date_val and isinstance(withdrawal_date_val, str):
            # 문자열이라도 yyyy-mm-dd 형태로 유지
            if len(withdrawal_date_val) > 10:
                withdrawal_date_val = withdrawal_date_val[:10]
        ws.cell(row=r, column=2, value=withdrawal_date_val)

        # C열: 증빙일자 (OCR 추출 원본 날짜)
        date_val = receipt.get("date")
        if date_val and isinstance(date_val, datetime.datetime):
            date_val = date_val.strftime("%Y-%m-%d")
        elif date_val and isinstance(date_val, str):
            if len(date_val) > 10:
                date_val = date_val[:10]
        ws.cell(row=r, column=3, value=date_val)

        # D열: 증빙번호 (파표일 경우에만)
        if receipt.get("type") == "增值税发票":
            ws.cell(row=r, column=4, value=receipt.get("receipt_number", ""))
        else:
            ws.cell(row=r, column=4, value="")

        # E열: 내역
        desc_cell = ws.cell(row=r, column=5, value=receipt.get("description", ""))

        # F열: 담당자
        ws.cell(row=r, column=6, value=receipt.get("person", ""))

        # G열: 증빙번호
        ws.cell(row=r, column=7, value=evidence_no)

        # H열: 대계정
        major_cell = ws.cell(row=r, column=8, value=receipt.get("account_major", ""))

        # I열: 소계정
        minor_cell = ws.cell(row=r, column=9, value=receipt.get("account_minor", ""))
        
        # 맵핑 실패(Unknown) 시 빨간색 배경 적용
        if receipt.get("is_mapped") is False:
            red_fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
            desc_cell.fill = red_fill
            major_cell.fill = red_fill
            minor_cell.fill = red_fill

        # J열: 입금 CNY
        deposit_cny = receipt.get("deposit_cny")
        if deposit_cny is not None:
            ws.cell(row=r, column=10, value=deposit_cny)

        # K열: 입금 환산요율
        deposit_rate = receipt.get("deposit_rate")
        if deposit_rate is not None:
            ws.cell(row=r, column=11, value=deposit_rate)

        # L열: 입금 USD
        deposit_usd = receipt.get("deposit_usd")
        if deposit_usd is not None:
            ws.cell(row=r, column=12, value=deposit_usd)

        # M열: 출금 CNY
        amount = receipt.get("amount")
        if amount is not None:
            ws.cell(row=r, column=13, value=amount)

        # N열: 환산요율 (환율표 참조 수식)
        ws.cell(row=r, column=14, value=f"='통장내역(환율표)'!$D$88")

        # O열: 출금 USD (= CNY / 환율)
        ws.cell(row=r, column=15, value=f"=M{r}/N{r}")

        # P열: 잔액 CNY (입금 가산, 출금 차감)
        ws.cell(row=r, column=16, value=f"=P{r-1}+J{r}-M{r}")

        # Q열: 잔액 USD (입금 가산, 출금 차감)
        ws.cell(row=r, column=17, value=f"=Q{r-1}+L{r}-O{r}")

        # R열: 비고 (통합) - 수기 기재 또는 웹앱 비고란
        remark_text = receipt.get("remark")
        if remark_text:
            ws.cell(row=r, column=18, value=remark_text)

        # S열: 항목 - 시스템 자동 판독 결과 및 경고 (은행/파표 등)
        # S열: 항목 - 시스템 자동 판독 결과 및 경고 (은행/파표 등)
        warning = receipt.get("validation_warning")
        system_remarks = []
        
        if warning:
            system_remarks.append(f"[{warning}]")
            
        if receipt.get("type") == "增值税发票":
            if not receipt.get("tax_code_valid"):
                system_remarks.append("파표 회사코드 불일치/누락")
        elif receipt.get("type") and receipt.get("type") != "银行回单":
            system_remarks.append("파표 외 영수증")
                
        if system_remarks:
            from openpyxl.styles import Font
            item_cell = ws.cell(row=r, column=19, value=" / ".join(system_remarks))
            item_cell.font = Font(color="FF0000")

    wb.save(output_path)
    return output_path


def get_available_exports() -> list:
    """생성된 엑셀 파일 목록 반환"""
    ensure_output_dir()
    files = []
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".xlsx"):
            filepath = os.path.join(OUTPUT_DIR, f)
            files.append({
                "filename": f,
                "path": filepath,
                "size": os.path.getsize(filepath),
                "created": datetime.datetime.fromtimestamp(
                    os.path.getctime(filepath)
                ).isoformat()
            })
    files.sort(key=lambda x: x["created"], reverse=True)
    return files
