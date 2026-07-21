"""
SROT — 심천지사 영수증 OCR 변환 웹앱
FastAPI 메인 서버 (Phase 2 - 월별 정산 연동 고도화)
"""
import os
import sys
import json
import re
import shutil
import datetime
from datetime import timedelta
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

# UTF-8 콘솔 출력
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from excel_exporter import export_to_excel

app = FastAPI(title="SROT - 심천지사 영수증 OCR 변환 웹앱")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "작업장소 (영수증 보관)")

# === 마스터 데이터 ===
ACCOUNT_MASTER = [
    {"code": "51131050", "major": "업무추진비", "minor": "일반"},
    {"code": "51061030", "major": "여비교통비", "minor": "해외"},
    {"code": "51201020", "major": "지급임차료", "minor": "사무실임차료"},
    {"code": "51201030", "major": "지급임차료", "minor": "차량임차료"},
    {"code": "51071700", "major": "통신비", "minor": "기타"},
    {"code": "51321010", "major": "해외지사비", "minor": None},
    {"code": "52981010", "major": "(-)잡이익(50)", "minor": "(-)잡이익"},
    {"code": "51031020", "major": "급여(incentive)", "minor": "포상금"},
]

MEMBERS = [
    "신순연", "김명관", "권유석",
    "Zhang Liang", "Lin Jieting", "Lin WeiJian",
    "Piao Mei Ling", "Xiong Feng",
    "Chen Guo Liang", "Liu Ming Liang", "Chen Feng Ju",
]

AUTHORIZED_USERS = {
    "20000243": "PiaoMeiLing",
    "20000001": "이현주",
    "20000117": "김수민",
    "20000177": "정영욱"
}

# --- 접속 세션(Lock) 관리 ---
ACTIVE_SESSION = {
    "emp_id": None,
    "name": None,
    "last_active": None
}

# === Pydantic 모델 ===
class LoginRequest(BaseModel):
    emp_id: str
    name: str

class ReceiptUpdate(BaseModel):
    withdrawal_date: Optional[str] = None
    date: Optional[str] = None
    receipt_number: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    person: Optional[str] = None
    account_major: Optional[str] = None
    account_minor: Optional[str] = None
    account_code: Optional[str] = None
    type: Optional[str] = None
    remark: Optional[str] = None

# === 헬퍼 함수 ===
def get_month_dir(month_str: str) -> str:
    """특정 월의 보관소 디렉토리 경로 반환 및 생성"""
    if not re.match(r'^\d{4}-\d{2}$', month_str):
        raise HTTPException(status_code=400, detail="올바르지 않은 월 형식입니다. (YYYY-MM 필요)")
    month_dir = os.path.join(STORAGE_DIR, month_str)
    os.makedirs(month_dir, exist_ok=True)
    return month_dir

def load_month_receipts(month_str: str) -> list:
    """특정 월의 data.json 로드"""
    month_dir = get_month_dir(month_str)
    db_path = os.path.join(month_dir, "data.json")
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_month_receipts(month_str: str, receipts: list):
    """특정 월의 data.json 저장"""
    month_dir = get_month_dir(month_str)
    db_path = os.path.join(month_dir, "data.json")
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(receipts, f, ensure_ascii=False, indent=2)

def regenerate_excel_sync(month_str: str, receipts: list):
    """특정 월의 엑셀 파일을 심천지사 전도금 정산 양식_{month_str}.xlsx로 자동 재생성"""
    month_dir = get_month_dir(month_str)
    excel_path = os.path.join(month_dir, f"심천지사 전도금 정산 양식_{month_str}.xlsx")
    
    # 템플릿 사용 (없으면 기본 생성)
    # excel_exporter는 ROOT의 TEMPLATE_PATH를 바라봄
    try:
        export_to_excel(receipts, month_label=month_str, output_path=excel_path)
        print(f"[Sync] Regenerated excel sheet: {excel_path}")
    except Exception as e:
        print(f"[Sync Error] Failed to regenerate excel: {e}")

# === API 엔드포인트 ===

@app.post("/api/login")
def login(req: LoginRequest):
    global ACTIVE_SESSION
    
    # 1. 자격 증명 확인
    if req.emp_id not in AUTHORIZED_USERS or AUTHORIZED_USERS[req.emp_id].replace(" ", "").lower() != req.name.replace(" ", "").lower():
        return {"success": False, "message": "사번 또는 이름이 일치하지 않습니다."}

    # 2. 동시 접속(Lock) 확인
    now = datetime.datetime.now()
    if ACTIVE_SESSION["emp_id"] is not None and ACTIVE_SESSION["emp_id"] != req.emp_id:
        # 다른 사람이 접속 중인 경우, 마지막 활동 시간이 60초 이내인지 확인
        if ACTIVE_SESSION["last_active"] and (now - ACTIVE_SESSION["last_active"]) < timedelta(seconds=60):
            current_user = ACTIVE_SESSION["name"]
            return {"success": False, "message": f"현재 <span class='highlight-name'>{current_user}</span>님이 접속 중입니다.<br>동시 접속은 불가합니다."}
            
    # 3. 로그인 성공 및 Lock 획득
    ACTIVE_SESSION["emp_id"] = req.emp_id
    ACTIVE_SESSION["name"] = AUTHORIZED_USERS[req.emp_id]
    ACTIVE_SESSION["last_active"] = now
    
    return {"success": True, "message": "로그인 성공"}

@app.post("/api/heartbeat")
def heartbeat(req: LoginRequest):
    global ACTIVE_SESSION
    now = datetime.datetime.now()
    # 하트비트를 보낸 사람이 현재 세션 소유자라면 시간 갱신
    if ACTIVE_SESSION["emp_id"] == req.emp_id:
        ACTIVE_SESSION["last_active"] = now
        return {"success": True}
    return {"success": False, "message": "세션 만료"}

@app.post("/api/logout")
def logout(req: LoginRequest):
    global ACTIVE_SESSION
    if ACTIVE_SESSION["emp_id"] == req.emp_id:
        ACTIVE_SESSION["emp_id"] = None
        ACTIVE_SESSION["name"] = None
        ACTIVE_SESSION["last_active"] = None
    return {"success": True}

@app.get("/api/months")
def get_months():
    """작업장소 (영수증 보관) 하위의 월별 폴더 목록 조회"""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    dirs = []
    for item in os.listdir(STORAGE_DIR):
        if os.path.isdir(os.path.join(STORAGE_DIR, item)):
            if re.match(r'^\d{4}-\d{2}$', item):
                dirs.append(item)
    dirs.sort(reverse=True) # 최신 월이 위로
    return dirs

@app.get("/api/months/{month_str}/receipts")
def get_month_receipts(month_str: str):
    """특정 월의 영수증 목록 조회"""
    return load_month_receipts(month_str)

@app.put("/api/months/{month_str}/receipts/{evidence_no}")
def update_month_receipt(month_str: str, evidence_no: int, update: ReceiptUpdate):
    """특정 월의 특정 영수증 데이터 수정"""
    receipts = load_month_receipts(month_str)
    target_idx = -1
    for idx, r in enumerate(receipts):
        if r.get("evidence_no") == evidence_no:
            target_idx = idx
            break
            
    if target_idx == -1:
        raise HTTPException(status_code=404, detail="해당 영수증을 찾을 수 없습니다.")

    receipt = receipts[target_idx]
    old_person = receipt.get("person")
    update_data = update.model_dump(exclude_none=True)
    
    # 데이터 병합
    receipt.update(update_data)
    
    # 대계정을 수동 지정했으므로 매핑 성공 처리
    if "account_major" in update_data and update_data["account_major"]:
        receipt["is_mapped"] = True
    
    new_person = receipt.get("person")
    
    # 담당자(Person) 변경 시 영수증 파일 이동 처리
    file_path = receipt.get("file_path")
    if file_path and old_person != new_person and new_person:
        month_dir = get_month_dir(month_str)
        # old path: 작업장소 (영수증 보관)/2026-06/이몽룡/001.png
        old_full_path = os.path.join(BASE_DIR, file_path)
        
        if os.path.exists(old_full_path):
            filename = os.path.basename(old_full_path)
            # Preserve subfolder structure when moving to new person
            rel_to_person = os.path.relpath(old_full_path, os.path.join(month_dir, old_person))
            new_person_dir = os.path.join(month_dir, new_person)
            new_full_path = os.path.join(new_person_dir, rel_to_person)
            
            os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
            shutil.move(old_full_path, new_full_path)
            
            # file_path 필드도 갱신
            receipt["file_path"] = os.path.relpath(new_full_path, BASE_DIR).replace('\\', '/')
            
            # 이전 담당자 폴더가 비어 있으면 폴더 제거
            old_person_dir = os.path.dirname(old_full_path)
            if os.path.exists(old_person_dir) and not os.listdir(old_person_dir):
                try:
                    os.rmdir(old_person_dir)
                except Exception:
                    pass

    save_month_receipts(month_str, receipts)
    regenerate_excel_sync(month_str, receipts)
    
    return {"status": "success", "receipt": receipt}

@app.delete("/api/months/{month_str}/receipts/{evidence_no}")
def delete_month_receipt(month_str: str, evidence_no: int):
    """특정 월의 특정 영수증 삭제 및 증빙 번호/파일명 재정렬"""
    receipts = load_month_receipts(month_str)
    target_idx = -1
    for idx, r in enumerate(receipts):
        if r.get("evidence_no") == evidence_no:
            target_idx = idx
            break
            
    if target_idx == -1:
        raise HTTPException(status_code=404, detail="해당 영수증을 찾을 수 없습니다.")
        
    target_receipt = receipts[target_idx]
    
    # 1. 파일 삭제
    file_path = target_receipt.get("file_path")
    if file_path:
        full_path = os.path.join(BASE_DIR, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            # 폴더 비어 있으면 제거
            parent_dir = os.path.dirname(full_path)
            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                try:
                    os.rmdir(parent_dir)
                except Exception:
                    pass
                    
    # 2. 목록에서 제거
    receipts.pop(target_idx)
    
    # 3. 정렬 및 순차 재배치
    receipts.sort(key=lambda x: x.get("evidence_no", 9999))
    
    month_dir = get_month_dir(month_str)
    for i, r in enumerate(receipts):
        new_no = i + 1
        old_no = r.get("evidence_no")
        r["evidence_no"] = new_no
        
        # 파일명도 00X.png 형태로 순차 리네이밍
        fpath = r.get("file_path")
        person = r.get("person", "Unknown")
        
        if fpath:
            old_full_path = os.path.join(BASE_DIR, fpath)
            if os.path.exists(old_full_path):
                ext = os.path.splitext(old_full_path)[1].lower()
                new_filename = f"{new_no:03d}{ext}"
                
                old_dir = os.path.dirname(old_full_path)
                new_full_path = os.path.join(old_dir, new_filename)
                
                if old_full_path != new_full_path:
                    shutil.move(old_full_path, new_full_path)
                    
                # 필드 갱신
                r["file_path"] = os.path.relpath(new_full_path, BASE_DIR).replace('\\', '/')

    # 4. 저장 및 엑셀 싱크
    save_month_receipts(month_str, receipts)
    regenerate_excel_sync(month_str, receipts)
    
    return {"status": "success", "message": f"{evidence_no}번 영수증 삭제 및 리네이밍 완료"}

@app.get("/api/months/{month_str}/images/{assignee}/{filename}")
def serve_month_image(month_str: str, assignee: str, filename: str):
    """(하위 호환용) 특정 월의 영수증 이미지 파일 서빙"""
    fpath = os.path.join(STORAGE_DIR, month_str, assignee, filename)
    if os.path.exists(fpath):
        ext = os.path.splitext(fpath)[1].lower()
        media_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif",
            ".webp": "image/webp", ".pdf": "application/pdf",
        }
        media_type = media_map.get(ext, "application/octet-stream")
        return FileResponse(fpath, media_type=media_type)
    raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다.")

@app.get("/api/images/{file_path:path}")
def serve_image_by_path(file_path: str):
    """임의 깊이의 하위 폴더 구조를 모두 지원하는 이미지 서빙 라우트"""
    fpath = os.path.join(BASE_DIR, file_path)
    # 보안: BASE_DIR 외부 접근 차단
    if not os.path.abspath(fpath).startswith(os.path.abspath(STORAGE_DIR)):
        raise HTTPException(status_code=403, detail="접근이 거부되었습니다.")
        
    if os.path.exists(fpath):
        ext = os.path.splitext(fpath)[1].lower()
        media_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif",
            ".webp": "image/webp", ".pdf": "application/pdf",
        }
        media_type = media_map.get(ext, "application/octet-stream")
        return FileResponse(fpath, media_type=media_type)
    raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다.")

@app.get("/api/months/{month_str}/export")
def download_month_excel(month_str: str):
    """특정 월의 정산 엑셀 파일 다운로드"""
    month_dir = get_month_dir(month_str)
    excel_path = os.path.join(month_dir, f"심천지사 전도금 정산 양식_{month_str}.xlsx")
    
    if not os.path.exists(excel_path):
        # 엑셀 파일이 없으면 재생성 시도
        receipts = load_month_receipts(month_str)
        if not receipts:
            raise HTTPException(status_code=404, detail="해당 월의 정산 데이터가 없습니다.")
        regenerate_excel_sync(month_str, receipts)
        
    if os.path.exists(excel_path):
        filename = f"심천지사 전도금 정산 양식_{month_str}.xlsx"
        return FileResponse(
            excel_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    raise HTTPException(status_code=404, detail="엑셀 파일을 찾을 수 없습니다.")

@app.get("/api/accounts")
def get_accounts():
    """계정과목 마스터 데이터 조회"""
    return ACCOUNT_MASTER

@app.get("/api/members")
def get_members():
    """담당자 목록 조회"""
    return MEMBERS

@app.post("/api/months/{month_str}/save")
def save_month_excel(month_str: str):
    """현재 data.json 기반으로 엑셀 정산 파일 즉시 덮어쓰기 저장"""
    receipts = load_month_receipts(month_str)
    if not receipts:
        raise HTTPException(status_code=404, detail="해당 월의 정산 데이터가 없습니다.")
    regenerate_excel_sync(month_str, receipts)
    saved_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return {"status": "success", "message": f"엑셀 정산 파일 저장 완료 ({saved_at})"}

@app.post("/api/months/{month_str}/reprocess")
def reprocess_month(month_str: str):
    """수정된 엑셀 데이터를 바탕으로 파이썬 batch_processor를 재실행하여 검증 결과를 최신화"""
    import subprocess
    try:
        script_path = os.path.join(BASE_DIR, "_시스템_코어", "batch_processor.py")
        subprocess.run([sys.executable, script_path, month_str], check=True)
        return {"status": "success", "message": f"{month_str} 월 시스템 판독(검증) 재가동 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"배치 처리 중 오류 발생: {str(e)}")

@app.post("/api/months/{month_str}/close")
def close_month(month_str: str):
    """특정 월의 정산 데이터를 마감(Closing)하여 영구 보존 데이터로 저장"""
    if ACTIVE_SESSION["name"] not in ["정영욱", "김수민"]:
        raise HTTPException(status_code=403, detail="마감 권한이 없습니다.")
        
    closing_path = os.path.join(STORAGE_DIR, month_str, "closing.json")
    if os.path.exists(closing_path):
        raise HTTPException(status_code=409, detail="이미 확정한 데이터가 있습니다.\n새로 확정하고자 하시면,\n피플팀 관리자에게 문의해 주세요.")
        
    receipts = load_month_receipts(month_str)
    if not receipts:
        raise HTTPException(status_code=404, detail="마감할 정산 데이터가 없습니다.")
        
    closing_data = []
    for r in receipts:
        if r.get("receipt_number"):
            closing_data.append({
                "evidence_no": r.get("evidence_no"),
                "receipt_number": r.get("receipt_number"),
                "month": month_str
            })
            
    closing_path = os.path.join(STORAGE_DIR, month_str, "closing.json")
    try:
        with open(closing_path, 'w', encoding='utf-8') as f:
            json.dump(closing_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"마감 파일 저장 중 오류 발생: {str(e)}")
        
    return {"status": "success", "message": f"{month_str} 월 데이터 마감 완료. 총 {len(closing_data)}건의 증빙번호 영구 보존됨."}

@app.get("/logo.png")
def serve_logo():
    """회사 로고 이미지 서빙"""
    logo_path = os.path.join(BASE_DIR, "static", "logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="로고 파일을 찾을 수 없습니다.")

# === 정적 파일 서빙 ===
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
