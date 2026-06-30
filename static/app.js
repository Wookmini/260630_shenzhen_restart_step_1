/**
 * SROT — 심천지사 영수증 OCR 변환 웹앱
 * 프론트엔드 인터랙션 로직
 */

// === 상태 관리 ===
const state = {
  receipts: [],
  currentIndex: 0,
  accounts: [],
  members: [],
  imageZoom: 1,
  imageRotation: 0,
};

// === 초기화 ===
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initDropzone();
  initViewerControls();
  initFormActions();
  loadMasterData();
  loadReceipts();
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

// === 드래그 & 드롭 업로드 ===
function initDropzone() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");

  ["dragenter", "dragover"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) uploadFiles(files);
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) uploadFiles(e.target.files);
  });
}

async function uploadFiles(files) {
  const formData = new FormData();
  const total = Math.min(files.length, 50);

  for (let i = 0; i < total; i++) {
    formData.append("files", files[i]);
  }

  // 프로그레스 표시
  const progressBar = document.getElementById("uploadProgress");
  const progressFill = document.getElementById("uploadProgressFill");
  const statusEl = document.getElementById("uploadStatus");

  progressBar.style.display = "block";
  progressFill.style.width = "10%";
  statusEl.textContent = `⏳ ${total}건 업로드 및 OCR 처리 중...`;

  try {
    progressFill.style.width = "30%";

    const res = await fetch("/api/upload", { method: "POST", body: formData });
    progressFill.style.width = "80%";

    if (!res.ok) throw new Error("업로드 실패");

    const data = await res.json();
    progressFill.style.width = "100%";
    statusEl.textContent = `✅ ${data.uploaded}건 업로드 및 OCR 처리 완료!`;

    showToast(`${data.uploaded}건 영수증이 처리되었습니다.`, "success");

    // 데이터 갱신
    await loadReceipts();

    setTimeout(() => {
      progressBar.style.display = "none";
      progressFill.style.width = "0%";
    }, 2000);
  } catch (err) {
    statusEl.textContent = `❌ 오류: ${err.message}`;
    showToast("업로드 중 오류가 발생했습니다.", "error");
    progressBar.style.display = "none";
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
    const minorSelect = document.getElementById("editMinor");
    minorSelect.innerHTML = '<option value="">— 선택 —</option>';
    const minors = state.accounts
      .filter((a) => a.major === selectedMajor && a.minor)
      .map((a) => a.minor);
    [...new Set(minors)].forEach((m) => {
      minorSelect.innerHTML += `<option value="${m}">${m}</option>`;
    });
  });
}

// === 영수증 데이터 로드 ===
async function loadReceipts() {
  try {
    const res = await fetch("/api/receipts");
    state.receipts = await res.json();
    updateStats();
    renderThumbnails();
    renderTable();
  } catch (e) {
    console.error("영수증 로드 실패:", e);
  }
}

function updateStats() {
  const total = state.receipts.length;
  const processed = state.receipts.filter((r) => r.amount != null).length;
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

  if (state.receipts.length === 0) {
    section.style.display = "none";
    return;
  }
  section.style.display = "block";
  countEl.textContent = state.receipts.length;

  grid.innerHTML = state.receipts
    .map(
      (r, i) => `
    <div class="thumb-card ${i === state.currentIndex ? "selected" : ""}" data-index="${i}" onclick="selectReceipt(${i})">
      <img src="/api/preview/${r.id}" alt="${r.original_filename}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 80%22><rect fill=%22%23f1f5f9%22 width=%22100%22 height=%2280%22/><text x=%2250%22 y=%2245%22 text-anchor=%22middle%22 fill=%22%2394a3b8%22 font-size=%2212%22>No Preview</text></svg>'">
      <span class="thumb-badge">${r.type || "기타"}</span>
      <div class="thumb-info">
        <div class="name">${r.original_filename || "unnamed"}</div>
        <div class="amount">${r.amount != null ? `¥${r.amount.toLocaleString()}` : "—"}</div>
      </div>
    </div>
  `
    )
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
    return;
  }

  const r = state.receipts[state.currentIndex];
  document.getElementById("navCounter").textContent = `${state.currentIndex + 1} / ${state.receipts.length}`;

  // 이미지
  document.getElementById("reviewImage").src = `/api/preview/${r.id}`;
  state.imageZoom = 1;
  state.imageRotation = 0;
  applyImageTransform();

  // 폼 채우기
  document.getElementById("editType").value = r.type || "기타";
  document.getElementById("editDate").value = r.date || "";
  document.getElementById("editAmount").value = r.amount != null ? r.amount : "";
  document.getElementById("editDescription").value = r.description || "";
  document.getElementById("editSeller").value = r.seller || "";
  document.getElementById("editPerson").value = r.person || "";
  document.getElementById("editRawText").value = r.raw_text || "";

  // 계정 드롭다운
  if (r.account_major) {
    document.getElementById("editMajor").value = r.account_major;
    // 소계정 재구성
    const minorSelect = document.getElementById("editMinor");
    minorSelect.innerHTML = '<option value="">— 선택 —</option>';
    const minors = state.accounts
      .filter((a) => a.major === r.account_major && a.minor)
      .map((a) => a.minor);
    [...new Set(minors)].forEach((m) => {
      minorSelect.innerHTML += `<option value="${m}">${m}</option>`;
    });
    if (r.account_minor) minorSelect.value = r.account_minor;
  }
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
  img.style.transform = `scale(${state.imageZoom}) rotate(${state.imageRotation}deg)`;
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

  try {
    const res = await fetch(`/api/receipts/${r.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
    });
    if (!res.ok) throw new Error("저장 실패");

    showToast("저장 완료!", "success");
    await loadReceipts();
    renderReview();
  } catch (e) {
    showToast("저장 중 오류가 발생했습니다.", "error");
  }
}

async function deleteCurrentReceipt() {
  if (state.receipts.length === 0) return;
  const r = state.receipts[state.currentIndex];

  if (!confirm(`"${r.original_filename}" 영수증을 삭제하시겠습니까?`)) return;

  try {
    const res = await fetch(`/api/receipts/${r.id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("삭제 실패");

    showToast("삭제 완료!", "info");
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

  if (state.receipts.length === 0) {
    tbody.innerHTML = "";
    empty.style.display = "block";
    return;
  }
  empty.style.display = "none";

  let total = 0;
  tbody.innerHTML = state.receipts
    .map((r, i) => {
      total += r.amount || 0;
      return `
      <tr>
        <td>${i + 1}</td>
        <td>${r.date || "—"}</td>
        <td>${r.description || "—"}</td>
        <td>${r.person || "—"}</td>
        <td>${r.account_major || "—"}</td>
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

// === 엑셀 내보내기 ===
async function exportExcel() {
  if (state.receipts.length === 0) {
    showToast("내보낼 영수증이 없습니다.", "warning");
    return;
  }

  const btn = document.getElementById("btnExport");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 생성 중...';

  try {
    const res = await fetch("/api/export/excel", { method: "POST" });
    if (!res.ok) throw new Error("엑셀 생성 실패");

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const disposition = res.headers.get("Content-Disposition") || "";
    const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
    a.download = filenameMatch ? filenameMatch[1] : "정산_export.xlsx";
    a.href = url;
    a.click();
    URL.revokeObjectURL(url);

    showToast("엑셀 파일이 다운로드되었습니다!", "success");
  } catch (e) {
    showToast(`오류: ${e.message}`, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "📥 관리 양식 엑셀 다운로드";
  }
}

// === 토스트 알림 ===
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const icons = { success: "✅", error: "❌", info: "ℹ️", warning: "⚠️" };
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `${icons[type] || ""} ${message}`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
