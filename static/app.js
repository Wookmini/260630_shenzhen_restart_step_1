/**
 * SROT — 심천지사 영수증 OCR 변환 웹앱
 * 프론트엔드 인터랙션 로직 (Phase 2 - 월별 정산 대시보드)
 */

// === 상태 관리 ===
const state = {
  months: [],
  currentMonth: "",
  receipts: [],
  currentIndex: 0,
  accounts: [],
  members: [],
  imageZoom: 1,
  imageRotation: 0,
};

// === 초기화 ===
document.addEventListener("DOMContentLoaded", async () => {
  initTabs();
  initViewerControls();
  initFormActions();
  await loadMasterData();
  await initMonthSelector();
});

// === 탭 전환 ===
function initTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`panel${capitalize(tab)}`).classList.add("active");

      // 탭 전환 시 데이터 갱신
      if (tab === "review") renderReview();
      if (tab === "table") renderTable();
      if (tab === "export") renderExportPreview();
    });
  });
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// === 월 선택기 초기화 ===
async function initMonthSelector() {
  const selectEl = document.getElementById("monthSelect");
  if (!selectEl) return;

  try {
    const res = await fetch("/api/months");
    state.months = await res.json();
    
    selectEl.innerHTML = "";
    if (state.months.length === 0) {
      selectEl.innerHTML = '<option value="">진행 중인 월 없음</option>';
      state.currentMonth = "";
      return;
    }

    state.months.forEach((m) => {
      selectEl.innerHTML += `<option value="${m}">${m}</option>`;
    });

    // 기본값으로 최신 월 설정
    state.currentMonth = state.months[0];
    selectEl.value = state.currentMonth;

    selectEl.addEventListener("change", async (e) => {
      state.currentMonth = e.target.value;
      state.currentIndex = 0;
      await loadReceipts();
      // 현재 탭 렌더링 갱신
      const activeTab = document.querySelector(".tab-btn.active").dataset.tab;
      if (activeTab === "review") renderReview();
      if (activeTab === "table") renderTable();
      if (activeTab === "export") renderExportPreview();
    });

    // 첫 월 데이터 로딩
    await loadReceipts();
  } catch (e) {
    console.error("월 목록 로드 실패:", e);
    showToast("월 목록을 불러오는 중 오류가 발생했습니다.", "error");
  }
}

// === 마스터 데이터 로드 ===
async function loadMasterData() {
  try {
    const [accRes, memRes] = await Promise.all([
      fetch("/api/accounts"),
      fetch("/api/members"),
    ]);
    state.accounts = await accRes.json();
    state.members = await memRes.json();
    populateDropdowns();
  } catch (e) {
    console.error("마스터 데이터 로드 실패:", e);
  }
}

function populateDropdowns() {
  // 담당자 드롭다운
  const personSelect = document.getElementById("editPerson");
  personSelect.innerHTML = '<option value="">— 선택 —</option>';
  state.members.forEach((m) => {
    personSelect.innerHTML += `<option value="${m}">${m}</option>`;
  });

  // 대계정 드롭다운
  const majorSelect = document.getElementById("editMajor");
  majorSelect.innerHTML = '<option value="">— 선택 —</option>';
  const majors = [...new Set(state.accounts.map((a) => a.major))];
  majors.forEach((m) => {
    majorSelect.innerHTML += `<option value="${m}">${m}</option>`;
  });

  // 대계정 변경 시 소계정 연동
  majorSelect.addEventListener("change", () => {
    const selectedMajor = majorSelect.value;
    updateMinorDropdown(selectedMajor);
  });
}

function updateMinorDropdown(majorVal, selectedMinor = "") {
  const minorSelect = document.getElementById("editMinor");
  minorSelect.innerHTML = '<option value="">— 선택 —</option>';
  
  if (!majorVal) return;

  const minors = state.accounts
    .filter((a) => a.major === majorVal && a.minor)
    .map((a) => a.minor);
    
  [...new Set(minors)].forEach((m) => {
    minorSelect.innerHTML += `<option value="${m}">${m}</option>`;
  });

  if (selectedMinor) {
    minorSelect.value = selectedMinor;
  }
}

// === 이미지 URL 헬퍼 ===
function getReceiptImgUrl(r) {
  if (!r || !r.file_path) return "";
  const parts = r.file_path.split("/");
  const filename = parts[parts.length - 1];
  const person = r.person || "Unknown";
  return `/api/months/${state.currentMonth}/images/${person}/${filename}`;
}

// === 영수증 데이터 로드 ===
async function loadReceipts() {
  if (!state.currentMonth) return;

  try {
    const res = await fetch(`/api/months/${state.currentMonth}/receipts`);
    state.receipts = await res.json();
    
    // Sort receipts by evidence_no
    state.receipts.sort((a, b) => (a.evidence_no || 999) - (b.evidence_no || 999));
    
    updateStats();
    renderThumbnails();
    renderTable();
  } catch (e) {
    console.error("영수증 로드 실패:", e);
    showToast("영수증 목록을 불러오는 중 오류가 발생했습니다.", "error");
  }
}

function updateStats() {
  const total = state.receipts.length;
  const processed = state.receipts.filter((r) => r.amount != null && r.is_mapped !== false).length;
  const totalAmt = state.receipts.reduce((s, r) => s + (r.amount || 0), 0);

  document.getElementById("statTotal").textContent = `📄 총 ${total}건`;
  document.getElementById("statProcessed").textContent = `✅ 처리 ${processed}건`;
  document.getElementById("statAmount").textContent = `💰 ¥${totalAmt.toLocaleString("ko-KR", { minimumFractionDigits: 2 })}`;
}

// === 썸네일 그리드 ===
function renderThumbnails() {
  const grid = document.getElementById("thumbGrid");
  const countEl = document.getElementById("thumbCount");
  const section = document.getElementById("thumbSection");

  if (!grid || !countEl || !section) return;

  if (state.receipts.length === 0) {
    section.style.display = "none";
    return;
  }
  section.style.display = "block";
  countEl.textContent = state.receipts.length;

  grid.innerHTML = state.receipts
    .map((r, i) => {
      const imgUrl = getReceiptImgUrl(r);
      const isSelected = i === state.currentIndex;
      const isUnmapped = r.is_mapped === false;
      const warningClass = isUnmapped ? "unmapped-thumb" : "";
      
      return `
        <div class="thumb-card ${isSelected ? "selected" : ""} ${warningClass}" data-index="${i}" onclick="selectReceipt(${i})">
          <img src="${imgUrl}" alt="영수증 ${r.evidence_no}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 80%22><rect fill=%22%23f1f5f9%22 width=%22100%22 height=%2280%22/><text x=%2250%22 y=%2245%22 text-anchor=%22middle%22 fill=%22%2394a3b8%22 font-size=%2210%22>No Preview</text></svg>'">
          <span class="thumb-badge">${r.type || "기타"}</span>
          ${isUnmapped ? '<span class="warning-badge">⚠️ 계정 확인 필요</span>' : ''}
          <div class="thumb-info">
            <div class="name">증빙 #${r.evidence_no} (${r.person || '미지정'})</div>
            <div class="amount">${r.amount != null ? `¥${r.amount.toLocaleString("ko-KR", { minimumFractionDigits: 2 })}` : "—"}</div>
          </div>
        </div>
      `;
    })
    .join("");
}

function selectReceipt(index) {
  state.currentIndex = index;
  // 검토 탭으로 전환
  document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  document.getElementById("tabReview").classList.add("active");
  document.getElementById("panelReview").classList.add("active");
  renderReview();
  renderThumbnails();
}

// === 데이터 검토 (2컬럼) ===
function renderReview() {
  if (state.receipts.length === 0) {
    document.getElementById("navCounter").textContent = "0 / 0";
    document.getElementById("reviewImage").src = "";
    document.getElementById("editForm").reset();
    return;
  }

  const r = state.receipts[state.currentIndex];
  document.getElementById("navCounter").textContent = `${state.currentIndex + 1} / ${state.receipts.length}`;

  // 이미지 뷰어 갱신
  const imgUrl = getReceiptImgUrl(r);
  document.getElementById("reviewImage").src = imgUrl;
  state.imageZoom = 1;
  state.imageRotation = 0;
  applyImageTransform();

  // 폼 필드 채우기
  document.getElementById("editType").value = r.type || "기타";
  document.getElementById("editDate").value = r.date || "";
  document.getElementById("editAmount").value = r.amount != null ? r.amount : "";
  document.getElementById("editDescription").value = r.description || "";
  document.getElementById("editSeller").value = r.seller || "";
  document.getElementById("editPerson").value = r.person || "";
  document.getElementById("editRawText").value = r.raw_text || "";

  // 계정 매핑 경고 처리 (클래스 추가/제거)
  const majorSelect = document.getElementById("editMajor");
  const minorSelect = document.getElementById("editMinor");
  
  if (r.is_mapped === false) {
    majorSelect.classList.add("warning-border");
    minorSelect.classList.add("warning-border");
  } else {
    majorSelect.classList.remove("warning-border");
    minorSelect.classList.remove("warning-border");
  }

  // 대계정 및 소계정 세팅
  majorSelect.value = r.account_major || "";
  updateMinorDropdown(r.account_major || "", r.account_minor || "");
}

// === 이미지 뷰어 컨트롤 ===
function initViewerControls() {
  document.getElementById("btnZoomIn").addEventListener("click", () => {
    state.imageZoom = Math.min(state.imageZoom + 0.25, 3);
    applyImageTransform();
  });
  document.getElementById("btnZoomOut").addEventListener("click", () => {
    state.imageZoom = Math.max(state.imageZoom - 0.25, 0.5);
    applyImageTransform();
  });
  document.getElementById("btnRotate").addEventListener("click", () => {
    state.imageRotation = (state.imageRotation + 90) % 360;
    applyImageTransform();
  });
  document.getElementById("btnReset").addEventListener("click", () => {
    state.imageZoom = 1;
    state.imageRotation = 0;
    applyImageTransform();
  });
}

function applyImageTransform() {
  const img = document.getElementById("reviewImage");
  if (img) {
    img.style.transform = `scale(${state.imageZoom}) rotate(${state.imageRotation}deg)`;
  }
}

// === 폼 저장/삭제/이전/다음 ===
function initFormActions() {
  document.getElementById("btnSaveReceipt").addEventListener("click", saveCurrentReceipt);
  document.getElementById("btnDeleteReceipt").addEventListener("click", deleteCurrentReceipt);
  document.getElementById("btnPrev").addEventListener("click", () => navigateReceipt(-1));
  document.getElementById("btnNext").addEventListener("click", () => navigateReceipt(1));
  document.getElementById("btnExport").addEventListener("click", exportExcel);
}

async function saveCurrentReceipt() {
  if (state.receipts.length === 0) return;
  const r = state.receipts[state.currentIndex];

  const update = {
    type: document.getElementById("editType").value,
    date: document.getElementById("editDate").value || null,
    amount: parseFloat(document.getElementById("editAmount").value) || null,
    description: document.getElementById("editDescription").value || null,
    seller: document.getElementById("editSeller").value || null,
    person: document.getElementById("editPerson").value || null,
    account_major: document.getElementById("editMajor").value || null,
    account_minor: document.getElementById("editMinor").value || null,
  };

  // 대계정 코드 매핑 자동 연동
  if (update.account_major) {
    const match = state.accounts.find((a) => a.major === update.account_major && (!update.account_minor || a.minor === update.account_minor));
    if (match) {
      update.account_code = match.code;
    }
  }

  try {
    const res = await fetch(`/api/months/${state.currentMonth}/receipts/${r.evidence_no}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
    });
    if (!res.ok) throw new Error("저장 실패");

    showToast("영수증 정보 저장 완료 및 엑셀 정산서 동기화 완료!", "success");
    await loadReceipts();
    renderReview();
  } catch (e) {
    showToast("저장 중 오류가 발생했습니다.", "error");
  }
}

async function deleteCurrentReceipt() {
  if (state.receipts.length === 0) return;
  const r = state.receipts[state.currentIndex];

  if (!confirm(`증빙번호 [${r.evidence_no}번] 영수증을 삭제하시겠습니까?\n삭제 시 이후 영수증들이 자동으로 당겨져 리네이밍(재정렬)됩니다.`)) return;

  try {
    const res = await fetch(`/api/months/${state.currentMonth}/receipts/${r.evidence_no}`, { method: "DELETE" });
    if (!res.ok) throw new Error("삭제 실패");

    showToast("영수증 삭제 및 일련번호 리네이밍 완료!", "info");
    await loadReceipts();
    if (state.currentIndex >= state.receipts.length) {
      state.currentIndex = Math.max(0, state.receipts.length - 1);
    }
    renderReview();
  } catch (e) {
    showToast("삭제 중 오류가 발생했습니다.", "error");
  }
}

function navigateReceipt(direction) {
  const newIndex = state.currentIndex + direction;
  if (newIndex >= 0 && newIndex < state.receipts.length) {
    state.currentIndex = newIndex;
    renderReview();
    renderThumbnails();
  }
}

// === 정산 내역 테이블 ===
function renderTable() {
  const tbody = document.getElementById("tableBody");
  const empty = document.getElementById("tableEmpty");
  const totalEl = document.getElementById("totalAmount");

  if (!tbody || !empty || !totalEl) return;

  if (state.receipts.length === 0) {
    tbody.innerHTML = "";
    empty.style.display = "block";
    totalEl.textContent = "¥0.00";
    return;
  }
  empty.style.display = "none";

  let total = 0;
  tbody.innerHTML = state.receipts
    .map((r, i) => {
      total += r.amount || 0;
      const isUnmapped = r.is_mapped === false;
      const rowClass = isUnmapped ? "unmapped-row" : "";
      
      return `
        <tr class="${rowClass}">
          <td>${r.evidence_no}</td>
          <td>${r.date || "—"}</td>
          <td>${r.description || "—"}</td>
          <td>${r.person || "—"}</td>
          <td>${r.account_major || (isUnmapped ? '<span class="warning-text">⚠️ 확인 필요</span>' : "—")}</td>
          <td>${r.account_minor || "—"}</td>
          <td class="amount-cell">${r.amount != null ? `¥${r.amount.toLocaleString("ko-KR", { minimumFractionDigits: 2 })}` : "—"}</td>
          <td><span class="thumb-badge" style="position:static;">${r.type || "기타"}</span></td>
          <td><button class="btn btn-secondary btn-sm" onclick="selectReceipt(${i})">편집</button></td>
        </tr>
      `;
    })
    .join("");

  totalEl.textContent = `¥${total.toLocaleString("ko-KR", { minimumFractionDigits: 2 })}`;
}

// === 내보내기 미리보기 ===
function renderExportPreview() {
  const total = state.receipts.length;
  const totalAmt = state.receipts.reduce((s, r) => s + (r.amount || 0), 0);
  const persons = new Set(state.receipts.map((r) => r.person).filter(Boolean));

  document.getElementById("exportTotal").textContent = `${total}건`;
  document.getElementById("exportAmount").textContent = `¥${totalAmt.toLocaleString("ko-KR", { minimumFractionDigits: 2 })}`;
  document.getElementById("exportPersons").textContent = `${persons.size}명`;
}

// === 엑셀 내보내기 (다운로드) ===
async function exportExcel() {
  if (!state.currentMonth || state.receipts.length === 0) {
    showToast("내보낼 영수증이 없습니다.", "warning");
    return;
  }

  const btn = document.getElementById("btnExport");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 엑셀 준비 중...';

  try {
    const url = `/api/months/${state.currentMonth}/export`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("엑셀 정산서 조회 실패");

    const blob = await res.blob();
    const downloadUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.download = `정산내역_${state.currentMonth}.xlsx`;
    a.href = downloadUrl;
    a.click();
    URL.revokeObjectURL(downloadUrl);

    showToast("최신 엑셀 정산서가 정상 다운로드되었습니다!", "success");
  } catch (e) {
    showToast(`다운로드 오류: ${e.message}`, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "📥 관리 양식 엑셀 다운로드";
  }
}

// === 토스트 알림 ===
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const icons = { success: "✅", error: "❌", info: "ℹ️", warning: "⚠️" };
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `${icons[type] || ""} ${message}`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}
