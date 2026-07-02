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
        
    # OCR이 콤마를 온점으로 잘못 인식한 경우 복원 (예: 12.405.76 -> 12405.76)
    if amt_str.count('.') >= 2:
        parts = amt_str.rsplit('.', 1)
        if len(parts[1]) == 2:
            amt_str = parts[0].replace('.', '') + '.' + parts[1]

    cleaned = re.sub(r"[^\d.]", "", amt_str.replace(",", "").replace(" ", ""))
    
    # 여전히 소수점이 2개 이상인 경우 오류 방지 (가장 마지막 소수점만 살림)
    if cleaned.count('.') > 1:
        parts = cleaned.rsplit('.', 1)
        cleaned = parts[0].replace('.', '') + '.' + parts[1]
        
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
        "fee_amount": None,
        "tax_code_valid": None,
    }

    if not raw_text or not raw_text.strip():
        return result

    # === 1. 영수증 유형 식별 및 필드 추출 ===

    # (E) 银行回单 (은행 전표) - 가장 구체적이므로 최상위에서 체크
    if any(kw in raw_text for kw in ["SHINHAN", "网上银行", "银行", "汇款", "手续费", "交易金额", "转账", "回单", "交易时间"]):
        result["type"] = "银行回单"
        _parse_bank_receipt(raw_text, result)

    # (A) 增值税发票 (VAT Fapiao)
    elif any(kw in raw_text for kw in ["发票", "购买方", "销售方", "价税合计", "电子", "代码", "识别", "税率"]):
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
        r"(?:小\s*写|价税合计)[ \t]*.*?([\d.,]+\.?\d*)",
        r"合\s*计.*?[¥￥][ \t]*([\d., ]+)",
        r"[¥￥][ \t]*([\d.,]+\.\d{2})", # 단순히 ¥ 뒤의 금액
    ]
    for pattern in amt_patterns:
        m_list = re.findall(pattern, text)
        if m_list:
            amounts = [clean_amount(m) for m in m_list if clean_amount(m) is not None]
            non_zero = [a for a in amounts if a > 0.0]
            if non_zero:
                result["amount"] = max(non_zero)
                break

    # 한자 대문자 금액(价税合计 大写) 검증 및 소수점 인식 오류 보정
    cn_str = extract_cn_amount_string(text)
    if cn_str:
        cn_val = parse_cn_amount(cn_str)
        if cn_val > 0.0:
            if not result.get("amount"):
                result["amount"] = cn_val
            else:
                try:
                    reg_val = float(str(result["amount"]).replace(',', ''))
                    # 소수점 오류 등으로 오차가 큰 경우 대문자 한자 금액으로 보정
                    if abs(reg_val - cn_val) > 1.0:
                        result["amount"] = cn_val
                except:
                    result["amount"] = cn_val

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

    # 세무코드 검증
    target_code = "91440300MAELRTJ5XE"
    result["tax_code_valid"] = (target_code in text)


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
        r"([\d.,]+)\s*元",
    ]
    for pattern in amt_patterns:
        m_list = re.findall(pattern, text)
        if m_list:
            amounts = [clean_amount(m) for m in m_list if clean_amount(m) is not None]
            non_zero = [a for a in amounts if a > 0.0]
            if non_zero:
                result["amount"] = max(non_zero)
                break

    _fallback_date(text, result)
    result["description"] = "주유비"


def _parse_toll_receipt(text: str, result: dict):
    """过路费 파싱"""
    amt_list = re.findall(r"(?:金额|合计|通行费|收费).*?[¥￥]?\s*([\d.,]+)", text)
    if amt_list:
        amounts = [clean_amount(a) for a in amt_list if clean_amount(a) is not None]
        non_zero = [a for a in amounts if a > 0.0]
        if non_zero:
            result["amount"] = max(non_zero)

    _fallback_date(text, result)
    result["description"] = "톨비"


def _parse_bank_receipt(text: str, result: dict):
    """银行回单 파싱"""
    # 1. 거래 통화 및 거래액(amount) 추출
    amt_matches = re.findall(r"(CNY|USD)\s*([\d.,]+\.\d{2})", text, re.IGNORECASE)
    if amt_matches:
        parsed_amounts = []
        for curr, amt_str in amt_matches:
            val = clean_amount(amt_str)
            if val is not None:
                parsed_amounts.append((val, curr, amt_str))
        if parsed_amounts:
            # 거래액은 수수료보다 크므로 가장 큰 금액을 거래액으로 선택
            parsed_amounts.sort(key=lambda x: x[0], reverse=True)
            result["amount"] = clean_amount(parsed_amounts[0][2])
            result["currency"] = parsed_amounts[0][1].upper()
            
    if not result.get("amount"):
        amt_m = re.search(r"(?:交易金额|转账金额|金额)\s*[:：]?\s*(USD|CNY)?\s*[¥￥]?\s*([\d\s.,]+)", text)
        if amt_m:
            result["amount"] = clean_amount(amt_m.group(2))
            if amt_m.group(1):
                result["currency"] = amt_m.group(1).upper()

    # 2. 날짜 추출
    date_m = re.search(r"(?:交易日期|日期)\s*[:：]?\s*(\d{4})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{1,2})", text)
    if date_m:
        result["date"] = f"{date_m.group(1)}-{int(date_m.group(2)):02d}-{int(date_m.group(3)):02d}"
    else:
        _fallback_date(text, result)

    result["description"] = "은행 거래"

    # 급여(工资) 여부 확인
    if "工资" in text or "급여" in text:
        result["description"] = "급여"
        
    # 3. 수수료(手续费) 추출 (모든 은행 이체증명서 공통)
    # 수수료 키워드 위치 기준 위아래 3줄 내에서 단독 소수점 1~2자리 숫자를 탐색
    lines = text.split('\n')
    fee_idx = -1
    for idx, line in enumerate(lines):
        if "手续费" in line:
            fee_idx = idx
            break
            
    if fee_idx != -1:
        start = max(0, fee_idx - 3)
        end = min(len(lines), fee_idx + 4)
        for i in range(start, end):
            cleaned_line = re.sub(r'[¥￥\s]', '', lines[i])
            if re.match(r'^\d+\.\d{1,2}$', cleaned_line):
                try:
                    val = float(cleaned_line)
                    main_val = float(str(result.get("amount", "0")).replace(',', ''))
                    # 수수료는 원금과 다르고 대개 100위안 미만임
                    if abs(val - main_val) > 0.01 and val < 100.0:
                        result["fee_amount"] = val
                        break
                except:
                    pass


def _fallback_amount(text: str, result: dict):
    """폴백 금액 추출"""
    # 1. ¥ 또는 ￥ 가 있는 경우
    m_list = re.findall(r"[¥￥]\s*([\d.,]+\.?\d*)", text)
    if m_list:
        amounts = [clean_amount(m) for m in m_list if clean_amount(m) is not None]
        non_zero = [a for a in amounts if a > 0.0]
        if non_zero:
            result["amount"] = max(non_zero)
            return
    
    # 2. % 뒤에 나타나는 금액 (VAT의 경우)
    m2_list = re.findall(r"%\n*.*?([\d.,]+\.\d{2})", text)
    if m2_list:
        amounts = [clean_amount(m) for m in m2_list if clean_amount(m) is not None]
        non_zero = [a for a in amounts if a > 0.0]
        if non_zero:
            result["amount"] = max(non_zero)
            return
        
    # 3. 문서 끝부분에 위치한 XX.XX 형태의 금액
    m3 = re.findall(r"([\d.,]+\.\d{2})", text)
    if m3:
        amounts = [clean_amount(m) for m in m3 if clean_amount(m) is not None]
        non_zero = [a for a in amounts if a > 0.0]
        if non_zero:
            result["amount"] = non_zero[-1]


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


# === 중국어 한자 대문자 금액(价税合计 大写) 파싱 유틸리티 ===

cn_digits = {'零': 0, '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9, '貮': 2, '两': 2}
cn_units = {'拾': 10, '佰': 100, '仟': 1000, '万': 10000, '亿': 100000000}

def parse_cn_amount(cn_str: str) -> float:
    """한자 대문자 금액 문자열을 float로 변환"""
    valid_chars = set(list(cn_digits.keys()) + list(cn_units.keys()) + ['元', '圆', '角', '分', '整'])
    cleaned = ''.join([c for c in cn_str if c in valid_chars])
    
    if not cleaned:
        return 0.0
        
    yuan_part = cleaned
    jiao_val = 0.0
    fen_val = 0.0
    
    # 1. '角' (Jiao) 추출
    jiao_m = re.search(r'([零壹贰叁肆伍陆柒捌玖])角', yuan_part)
    if jiao_m:
        jiao_val = cn_digits[jiao_m.group(1)] * 0.1
        yuan_part = yuan_part.replace(jiao_m.group(0), '')
        
    # 2. '分' (Fen) 추출
    fen_m = re.search(r'([零壹贰叁肆伍陆柒捌玖])分', yuan_part)
    if fen_m:
        fen_val = cn_digits[fen_m.group(1)] * 0.01
        yuan_part = yuan_part.replace(fen_m.group(0), '')
        
    # 3. 화폐 단위 및 종결 접미사 제거
    yuan_part = re.sub(r'[元圆整]', '', yuan_part)
    
    def parse_section(section_str):
        section_val = 0
        current_digit = 0
        has_digit = False
        for char in section_str:
            if char in cn_digits:
                current_digit = cn_digits[char]
                has_digit = True
            elif char in cn_units:
                unit = cn_units[char]
                if not has_digit:
                    current_digit = 1
                section_val += current_digit * unit
                current_digit = 0
                has_digit = False
        if has_digit:
            section_val += current_digit
        return section_val

    if '万' in yuan_part:
        parts = yuan_part.split('万')
        val = parse_section(parts[0]) * 10000 + parse_section(parts[1])
    else:
        val = parse_section(yuan_part)
        
    return float(val) + jiao_val + fen_val


def extract_cn_amount_string(text: str) -> str:
    """OCR 텍스트에서 한자 대문자 금액 후보 문자열 추출"""
    candidates = re.findall(r'[零壹贰叁肆伍陆柒捌玖拾佰仟万亿元圆角分整]{2,}', text)
    if not candidates:
        return ""
    valid_candidates = []
    for cand in candidates:
        if any(u in cand for u in ['拾', '佰', '仟', '万', '亿', '元', '圆', '整']):
            valid_candidates.append(cand)
    if not valid_candidates:
        return ""
    return max(valid_candidates, key=len)
