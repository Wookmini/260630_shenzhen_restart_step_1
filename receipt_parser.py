"""
영수증 파서 모듈
OCR 텍스트에서 구조화된 데이터를 정규식 기반으로 추출
중국 영수증 6종 분류 지원
"""
import re
from typing import Optional


# === 계정과목 자동 매핑 규칙 ===
ACCOUNT_RULES = {
    "주유": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "加油": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "汽油": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "柴油": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "成品油": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "톨비": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "通行费": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "过路费": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "주차": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "停车": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "铁路": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "客票": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "火车": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "출장": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "교통": {"major": "여비교통비", "minor": "해외", "code": "51061030"},
    "통신": {"major": "통신비", "minor": "기타", "code": "51071700"},
    "WIFI": {"major": "통신비", "minor": "기타", "code": "51071700"},
    "电信": {"major": "통신비", "minor": "기타", "code": "51071700"},
    "임대": {"major": "지급임차료", "minor": "사무실임차료", "code": "51201020"},
    "租金": {"major": "지급임차료", "minor": "사무실임차료", "code": "51201020"},
    "은행수수료": {"major": "해외지사비", "minor": None, "code": "51321010"},
    "手续费": {"major": "해외지사비", "minor": None, "code": "51321010"},
    "택배": {"major": "해외지사비", "minor": None, "code": "51321010"},
    "快递": {"major": "해외지사비", "minor": None, "code": "51321010"},
    "사무용품": {"major": "해외지사비", "minor": None, "code": "51321010"},
    "办公": {"major": "해외지사비", "minor": None, "code": "51321010"},
}


def clean_amount(amt_str: str) -> Optional[float]:
    """금액 문자열 정제"""
    if not amt_str:
        return None
    cleaned = re.sub(r"[^\d.]", "", amt_str.replace(",", "").replace(" ", ""))
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_receipt(raw_text: str) -> dict:
    """
    OCR 텍스트에서 구조화된 영수증 데이터 추출
    반환: {type, date, amount, currency, seller, description, account_major, account_minor, account_code}
    """
    result = {
        "type": "기타",
        "date": None,
        "amount": None,
        "currency": "CNY",
        "seller": None,
        "description": None,
        "account_major": None,
        "account_minor": None,
        "account_code": None,
    }

    if not raw_text or not raw_text.strip():
        return result

    # === 1. 영수증 유형 식별 및 필드 추출 ===

    # (A) 增值税发票 (VAT Fapiao)
    vat_keywords = ["发票", "购买方", "销售方", "价税合计", "电子", "代码", "识别", "税率"]
    if any(kw in raw_text for kw in vat_keywords):
        result["type"] = "增值税发票"
        _parse_vat_fapiao(raw_text, result)

    # (B) 火车票 (기차표)
    elif any(kw in raw_text for kw in ["铁路", "客票", "火车票"]):
        result["type"] = "火车票"
        _parse_train_ticket(raw_text, result)

    # (C) 加油票 (주유 영수증)
    elif any(kw in raw_text for kw in ["成品油", "汽油", "柴油", "加油"]):
        result["type"] = "加油票"
        _parse_fuel_receipt(raw_text, result)

    # (D) 过路费 (톨비)
    elif any(kw in raw_text for kw in ["广东联合电子", "通行费", "过路费", "高速"]):
        result["type"] = "过路费"
        _parse_toll_receipt(raw_text, result)

    # (E) 银行回单 (은행 전표)
    elif any(kw in raw_text for kw in ["SHINHAN", "网上银行", "银行", "汇款"]):
        result["type"] = "银行回单"
        _parse_bank_receipt(raw_text, result)

    # === 2. 폴백 추출 (유형 미식별 시) ===
    if result["amount"] is None:
        _fallback_amount(raw_text, result)
    if result["date"] is None:
        _fallback_date(raw_text, result)

    # === 3. 자동 계정 분류 ===
    _auto_classify_account(raw_text, result)

    return result


def _parse_vat_fapiao(text: str, result: dict):
    """增值税发票 파싱"""
    # 금액: 价税合计 소문자(小写)
    amt_patterns = [
        r"(?:小\s*写|价税合计).*?[¥￥][ \t]*([\d., ]+)",
        r"(?:小\s*写|价税合计)[ \t]*.*?([\d,]+\.?\d*)",
        r"合\s*计.*?[¥￥][ \t]*([\d., ]+)",
        r"[¥￥][ \t]*([\d,]+\.\d{2})", # 단순히 ¥ 뒤의 금액
    ]
    for pattern in amt_patterns:
        m = re.search(pattern, text)
        if m:
            result["amount"] = clean_amount(m.group(1))
            if result["amount"]:
                break

    # 날짜: 开票日期
    date_patterns = [
        r"开[票标]\s*日\s*期\s*[:：]?\s*(\d{4})\s*[-年/]\s*(\d{1,2})\s*[-月/]\s*(\d{1,2})",
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        r"(\d{4})\s*[年4]\s*0?(\d{1,2})\s*[月H]\s*0?(\d{1,2})", # Tesseract 오류 보정
    ]
    for pattern in date_patterns:
        m = re.search(pattern, text)
        if m:
            result["date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
            break

    # 판매자: 销售方 이후 텍스트
    seller_m = re.search(r"(?:销售方|名\s*称)[^\w]*[:：]*[^\w]*(.+?)(?:\n|$)", text)
    if seller_m:
        val = seller_m.group(1).strip()[:50]
        if len(val) > 2 and "公司" in val:
            result["seller"] = val
    
    if not result["seller"]:
        # 판매자 폴백: '公司'가 포함된 줄을 판매자로 추정
        for line in text.split('\n'):
            if "公司" in line and "发票" not in line:
                cleaned_line = re.sub(r"^[^\w]*명\s*칭[^\w]*", "", line)
                cleaned_line = re.sub(r"^[^\w]*名\s*称[^\w]*", "", cleaned_line)
                result["seller"] = cleaned_line.strip(" :：").strip()[:50]
                break

    # 내역: 项目名称 (Project Name)
    # 중국 증치세 영수증의 항목명은 대체로 '*카테고리*품명' 형태를 띰 (예: *文具*得力纳米净橡皮擦)
    item_pattern = r"\*([^\*]+)\*([^\n]+)"
    desc_matches = re.findall(item_pattern, text)
    if desc_matches:
        # 첫 번째 항목을 대표 내역으로 사용 (예: "文具 - 得力纳米净橡皮擦")
        category, item_name = desc_matches[0]
        result["description"] = f"{category.strip()} - {item_name.strip()}"[:100]
    else:
        # 기존 폴백: "名称" 아래 줄 추출하되 规格型号 등 표 헤더 무시
        desc_m = re.search(r"(?:货物|项目|服务).*?名称.*?\n\s*\*?(?!规格型号|单位|数量)(.+?)(?:\s+\d|\n|$)", text)
        if desc_m:
            result["description"] = desc_m.group(1).strip()[:100]


def _parse_train_ticket(text: str, result: dict):
    """火车票 파싱"""
    amt_m = re.search(r"(?:票价|¥)\s*[:：]?\s*[¥￥]?\s*([\d.,]+)", text, re.IGNORECASE)
    if amt_m:
        result["amount"] = clean_amount(amt_m.group(1))

    date_m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
    if date_m:
        result["date"] = f"{date_m.group(1)}-{int(date_m.group(2)):02d}-{int(date_m.group(3)):02d}"

    result["description"] = "기차표"


def _parse_fuel_receipt(text: str, result: dict):
    """加油票 파싱"""
    amt_patterns = [
        r"(?:小\s*写|价税合计|合计|金额).*?[¥￥]\s*([\d.,]+)",
        r"[¥￥]\s*([\d.,]+)",
    ]
    for pattern in amt_patterns:
        m = re.search(pattern, text)
        if m:
            result["amount"] = clean_amount(m.group(1))
            if result["amount"]:
                break

    _fallback_date(text, result)
    result["description"] = "주유비"


def _parse_toll_receipt(text: str, result: dict):
    """过路费 파싱"""
    amt_m = re.search(r"(?:金额|合计|通行费).*?[¥￥]?\s*([\d.,]+)", text)
    if amt_m:
        result["amount"] = clean_amount(amt_m.group(1))

    _fallback_date(text, result)
    result["description"] = "톨비"


def _parse_bank_receipt(text: str, result: dict):
    """银行回单 파싱"""
    amt_m = re.search(r"(?:交易金额|转账金额|金额)\s*[:：]?\s*(USD|CNY)?\s*[¥￥]?\s*([\d\s.,]+)", text)
    if amt_m:
        result["amount"] = clean_amount(amt_m.group(2))
        if amt_m.group(1):
            result["currency"] = amt_m.group(1).upper()

    date_m = re.search(r"(?:交易日期|日期)\s*[:：]?\s*(\d{4})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{1,2})", text)
    if date_m:
        result["date"] = f"{date_m.group(1)}-{int(date_m.group(2)):02d}-{int(date_m.group(3)):02d}"

    result["description"] = "은행 거래"


def _fallback_amount(text: str, result: dict):
    """폴백 금액 추출"""
    # 1. ¥ 또는 ￥ 가 있는 경우
    m = re.search(r"[¥￥]\s*([\d,]+\.?\d*)", text)
    if m:
        result["amount"] = clean_amount(m.group(1))
        return
    
    # 2. % 뒤에 나타나는 금액 (VAT의 경우)
    m2 = re.search(r"%\n*.*?([\d,]+\.\d{2})", text)
    if m2:
        result["amount"] = clean_amount(m2.group(1))
        return
        
    # 3. 문서 끝부분에 위치한 XX.XX 형태의 금액
    m3 = re.findall(r"([\d,]+\.\d{2})", text)
    if m3:
        # 가장 마지막에 등장하는 소수점 2자리 숫자를 금액으로 추정
        result["amount"] = clean_amount(m3[-1])


def _fallback_date(text: str, result: dict):
    """폴백 날짜 추출"""
    if result["date"]:
        return

    patterns = [
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        r"(\d{4})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{1,2})",
        r"(202\d).*?0?(\d{1,2})\s*[月H]\s*0?(\d{1,2})", # Tesseract 오류 보정
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            result["date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
            return


def _auto_classify_account(text: str, result: dict):
    """키워드 기반 자동 계정 분류"""
    combined = (text + " " + (result.get("description") or "")).lower()
    for keyword, account in ACCOUNT_RULES.items():
        if keyword.lower() in combined:
            result["account_major"] = account["major"]
            result["account_minor"] = account["minor"]
            result["account_code"] = account["code"]
            return
