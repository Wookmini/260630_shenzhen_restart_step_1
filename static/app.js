/**
 * 심천지사 전도금 정산 자동화 시스템 — V2 JavaScript
 * 업로드/내보내기 제거, 담당자 자동완성 수정, remark 연동, 엑셀 저장 통합
 */

// === 상태 관리 ===
const state = {
  months: [],
  currentMonth: "",
  receipts: [],         // 전체 원본 목록
  filtered: [],         // 검색 필터 적용 후 목록
  currentIndex: 0,      // 검토 탭 현재 증빙 인덱스 (receipts 기준)
  accounts: [],
  members: [],
  imageZoom: 1,
  imageRotation: 0,
  panX: 0,
  panY: 0,
  sortCol: null,
  sortDir: 1,           // 1=오름차순, -1=내림차순
};

// === 초기화 ===
document.addEventListener("DOMContentLoaded", async () => {
  if (checkLogin()) {
    initApp();
  }
});

function checkLogin() {
  const isLoggedIn = sessionStorage.getItem("isLoggedIn");
  const loginOverlay = document.getElementById("loginOverlay");
  const loginForm = document.getElementById("loginForm");
  const loginErrorMsg = document.getElementById("loginErrorMsg");

  if (isLoggedIn === "true") {
    loginOverlay.style.display = "none";
    startHeartbeat();
    return true;
  }

  loginOverlay.style.display = "flex";
  
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const empId = document.getElementById("empIdInput").value.trim();
    const empName = document.getElementById("empNameInput").value.trim();
    
    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ emp_id: empId, name: empName })
      });
      const data = await res.json();
      if (data.success) {
        sessionStorage.setItem("isLoggedIn", "true");
        sessionStorage.setItem("empId", empId);
        sessionStorage.setItem("empName", empName);
        loginOverlay.style.display = "none";
        startHeartbeat();
        initApp();
      } else {
        loginErrorMsg.innerHTML = data.message;
        loginErrorMsg.style.display = "block";
      }
    } catch (err) {
      console.error(err);
      loginErrorMsg.innerHTML = "서버 통신 오류가 발생했습니다.";
      loginErrorMsg.style.display = "block";
    }
  });
  
  return false;
}

// === 세션(Lock) 관리 ===
let heartbeatInterval = null;

function startHeartbeat() {
  if (heartbeatInterval) clearInterval(heartbeatInterval);
  
  // 30초마다 하트비트 전송
  heartbeatInterval = setInterval(async () => {
    const empId = sessionStorage.getItem("empId");
    const empName = sessionStorage.getItem("empName");
    if (!empId) return;
    
    try {
      await fetch("/api/heartbeat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ emp_id: empId, name: empName })
      });
    } catch (e) {
      console.error("Heartbeat error", e);
    }
  }, 30000);
}

window.addEventListener("beforeunload", () => {
  const empId = sessionStorage.getItem("empId");
  const empName = sessionStorage.getItem("empName");
  if (empId) {
    const data = JSON.stringify({ emp_id: empId, name: empName });
    navigator.sendBeacon("/api/logout", data);
  }
});

async function initApp() {
  initTabs();
  initViewerControls();
  initFormActions();
  initTableSort();
  initSearch();
  await loadMasterData();
  await initMonthSelector();
  initCloseMonth();
}

// === 탭 전환 ===
function initTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`panel${capitalize(tab)}`).classList.add("active");
      if (tab === "review") renderReview();
      if (tab === "table") renderTable();
    });
  });

  // 기본 진입: 정산 내역 탭
  document.getElementById("tabTable").classList.add("active");
  document.getElementById("panelTable").classList.add("active");
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// === 월 선택기 ===
async function initMonthSelector() {
  const selectEl = document.getElementById("monthSelect");
  if (!selectEl) return;
  try {
    const res = await fetch("/api/months");
    state.months = await res.json();
    selectEl.innerHTML = "";
    if (state.months.length === 0) {
      selectEl.innerHTML = '<option value="">진행 중인 월 없음</option>';
      return;
    }
    state.months.forEach((m) => {
      selectEl.innerHTML += `<option value="${m}">${m}</option>`;
    });
    state.currentMonth = state.months[0];
    selectEl.value = state.currentMonth;
    selectEl.addEventListener("change", async (e) => {
      state.currentMonth = e.target.value;
      state.currentIndex = 0;
      await loadReceipts();
      const activeTab = document.querySelector(".tab-btn.active")?.dataset.tab;
      if (activeTab === "review") renderReview();
      if (activeTab === "table") renderTable();
    });
    await loadReceipts();
  } catch (e) {
    console.error("월 목록 로드 실패:", e);
    showToast("월 목록을 불러오는 중 오류가 발생했습니다.", "error");
  }
}

// === 마스터 데이터 ===
async function loadMasterData() {
  try {
    const [accRes, memRes] = await Promise.all([
      fetch("/api/accounts"),
      fetch("/api/members"),
    ]);
    state.accounts = await accRes.json();
    state.members = await memRes.json();
  } catch (e) {
    console.error("마스터 데이터 로드 실패:", e);
  }
}

// 담당자 드롭다운 — 마스터 목록 + 현재 receipts에 등장하는 person 모두 포함
function buildPersonDropdown(currentPerson = "") {
  const personSelect = document.getElementById("editPerson");
  const allPersons = new Set([...state.members]);
  // receipts에 등장하는 person 값도 동적으로 추가
  state.receipts.forEach((r) => {
    if (r.person) allPersons.add(r.person);
  });

  personSelect.innerHTML = '<option value="">— 선택 —</option>';
  [...allPersons].sort().forEach((m) => {
    const sel = m === currentPerson ? "selected" : "";
    personSelect.innerHTML += `<option value="${m}" ${sel}>${m}</option>`;
  });
}

// 소계정 드롭다운
function updateMinorDropdown(majorVal, selectedMinor = "") {
  const minorSelect = document.getElementById("editMinor");
  minorSelect.innerHTML = '<option value="">— 선택 —</option>';
  if (!majorVal) return;
  const minors = state.accounts
    .filter((a) => a.major === majorVal && a.minor)
    .map((a) => a.minor);
  [...new Set(minors)].forEach((m) => {
    const sel = m === selectedMinor ? "selected" : "";
    minorSelect.innerHTML += `<option value="${m}" ${sel}>${m}</option>`;
  });
}

// 대계정 변경 이벤트
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("editMajor")?.addEventListener("change", () => {
    updateMinorDropdown(document.getElementById("editMajor").value);
  });
});

// === 이미지 URL ===
function getReceiptImgUrl(r) {
  if (!r || !r.file_path) return "";
  return `/api/images/${encodeURIComponent(r.file_path)}`;
}

// === 영수증 데이터 로드 ===
async function loadReceipts() {
  if (!state.currentMonth) return;
  try {
    const res = await fetch(`/api/months/${state.currentMonth}/receipts`);
    state.receipts = await res.json();
    state.receipts.sort((a, b) => (a.evidence_no || 999) - (b.evidence_no || 999));
    state.filtered = [...state.receipts];
    updateTablePersonFilter();
    updateTableMajorFilter();
    updateStats();
    renderTable();
    renderSidebar();
  } catch (e) {
    console.error("영수증 로드 실패:", e);
    showToast("영수증 목록을 불러오는 중 오류가 발생했습니다.", "error");
  }
}

// === 시스템 판독 결과 헬퍼 ===
function getValidationWarnings(r) {
  const warnings = [];
  if (r.validation_warning && r.validation_warning !== "✅ 금액 일치") {
    let warnStr = r.validation_warning.replace(/~~/g, "").replace(/➡️ /g, "");
    if (!warnStr.includes("⚠️") && warnStr.includes("금액 불일치")) {
      warnStr = "⚠️ " + warnStr;
    }
    warnings.push(warnStr);
  }
  if (r.type === '增值税发票') {
    if (!r.tax_code_valid) {
      if (r.description === '통신비') {
        warnings.push('✅ 통신비 - 파표 회사코드 X (개인)');
      } else {
        warnings.push('⚠️ 파표 회사코드 불일치/누락');
      }
    }
  }
  return warnings;
}

// === 통계 뱃지 업데이트 ===
function updateStats() {
  const total     = state.receipts.length;
  const warning   = state.receipts.filter((r) => r.is_mapped === false || getValidationWarnings(r).filter(w => !w.includes('✅')).length > 0).length;
  const processed = total - warning; // 완벽하게 처리되어 사람의 확인이 필요 없는 건수
  const totalAmt  = state.receipts.reduce((s, r) => s + (r.amount || 0), 0);

  document.getElementById("valTotal").textContent     = total;
  document.getElementById("valProcessed").textContent = processed;
  document.getElementById("valWarning").textContent   = warning;
  document.getElementById("valAmount").textContent    =
    "¥" + totalAmt.toLocaleString("ko-KR", { minimumFractionDigits: 0, maximumFractionDigits: 2 });

  // 확인필요 뱃지 강조
  const warnPill = document.getElementById("statWarning");
  if (warning > 0) {
    warnPill.style.background = "rgba(251,191,36,0.18)";
  } else {
    warnPill.style.background = "";
  }
}

// === 테이블 검색 및 필터 ===
function applyTableFilters() {
  const searchEl = document.getElementById("tableSearch");
  const personEl = document.getElementById("tablePersonFilter");
  const majorEl = document.getElementById("tableMajorFilter");
  const q = searchEl ? searchEl.value.trim().toLowerCase() : "";
  const personFilter = personEl ? personEl.value : "";
  const majorFilter = majorEl ? majorEl.value : "";

  state.filtered = state.receipts.filter((r) => {
    const matchPerson = !personFilter || (r.person === personFilter);
    if (!matchPerson) return false;
    
    const matchMajor = !majorFilter || (r.account_major === majorFilter);
    if (!matchMajor) return false;

    if (!q) return true;
    return (
      (r.description || "").toLowerCase().includes(q) ||
      (r.person || "").toLowerCase().includes(q) ||
      (r.account_major || "").toLowerCase().includes(q) ||
      (r.account_minor || "").toLowerCase().includes(q) ||
      String(r.evidence_no).includes(q)
    );
  });
  renderTable();
}

function initSearch() {
  const searchEl = document.getElementById("tableSearch");
  const personEl = document.getElementById("tablePersonFilter");
  const majorEl = document.getElementById("tableMajorFilter");
  
  if (searchEl) {
    searchEl.addEventListener("input", applyTableFilters);
  }
  if (personEl) {
    personEl.addEventListener("change", applyTableFilters);
  }
  if (majorEl) {
    majorEl.addEventListener("change", applyTableFilters);
  }
}

function updateTablePersonFilter() {
  const personEl = document.getElementById("tablePersonFilter");
  if (!personEl) return;
  
  const currentVal = personEl.value;
  const allPersons = new Set();
  state.receipts.forEach((r) => {
    if (r.person) allPersons.add(r.person);
  });
  
  personEl.innerHTML = '<option value="">👤 담당자 전체</option>';
  [...allPersons].sort().forEach((m) => {
    const sel = m === currentVal ? "selected" : "";
    personEl.innerHTML += `<option value="${m}" ${sel}>${m}</option>`;
  });
}

function updateTableMajorFilter() {
  const majorEl = document.getElementById("tableMajorFilter");
  if (!majorEl) return;
  
  const currentVal = majorEl.value;
  const allMajors = new Set();
  state.receipts.forEach((r) => {
    if (r.account_major) allMajors.add(r.account_major);
  });
  
  majorEl.innerHTML = '<option value="">📁 대계정 전체</option>';
  [...allMajors].sort().forEach((m) => {
    const sel = m === currentVal ? "selected" : "";
    majorEl.innerHTML += `<option value="${m}" ${sel}>${m}</option>`;
  });
}

// === 테이블 정렬 ===
function initTableSort() {
  document.querySelectorAll(".data-table thead th.sortable").forEach((th) => {
    th.addEventListener("click", () => {
      const col = th.dataset.col;
      if (state.sortCol === col) {
        state.sortDir *= -1;
      } else {
        state.sortCol = col;
        state.sortDir = 1;
      }
      state.filtered.sort((a, b) => {
        const va = a[col] ?? "";
        const vb = b[col] ?? "";
        return va < vb ? -state.sortDir : va > vb ? state.sortDir : 0;
      });
      document.querySelectorAll(".sort-icon").forEach((el) => (el.textContent = "↕"));
      th.querySelector(".sort-icon").textContent = state.sortDir === 1 ? "↑" : "↓";
      renderTable();
    });
  });
}

// === 정산 내역 테이블 렌더링 ===
function renderTable() {
  const tbody  = document.getElementById("tableBody");
  const empty  = document.getElementById("tableEmpty");
  const totalEl = document.getElementById("totalAmount");
  const countEl = document.getElementById("recordCount");
  if (!tbody) return;

  if (state.filtered.length === 0) {
    tbody.innerHTML = "";
    empty.style.display = "block";
    totalEl.textContent = "¥0.00";
    countEl.textContent = "0건";
    return;
  }
  empty.style.display = "none";
  countEl.textContent = `${state.filtered.length}건`;

  let total = 0;
  tbody.innerHTML = state.filtered.map((r) => {
    total += r.amount || 0;
    const warnings = getValidationWarnings(r);
    const realWarnings = warnings.filter(w => !w.includes("✅"));
    const hasIssue = realWarnings.length > 0;
    
    // 이슈가 있거나 매핑이 안 된 경우 unmapped-row 적용
    const isUnmapped = r.is_mapped === false || hasIssue;
    const rowCls = isUnmapped ? "unmapped-row" : "";
    const origIdx = state.receipts.indexOf(r);

    const majorCell = (r.is_mapped === false)
      ? `<span class="warning-text">⚠️ 확인 필요</span>`
      : (r.account_major || "—");

    let remarkHtml = "—";
    if (hasIssue) {
      const wText = warnings.join(' / ').replace(/\n/g, '<br>');
      const plainText = warnings.join(' / ').replace(/\n/g, ' ');
      remarkHtml = `<span class="warning-text" title="${plainText}">${wText}</span>`;
    } else if (warnings.length > 0 || (r.validation_warning && r.validation_warning.includes("✅ 금액 일치"))) {
      let formatted = "";
      if (warnings.length > 0) {
        formatted = warnings.join(" / ").replace(/\n/g, "<br>");
      } else {
        formatted = r.validation_warning.replace(/\n/g, "<br>");
      }
      remarkHtml = `<span style="color: #059669; font-weight: 500; font-size: 0.85em; line-height: 1.4;">${formatted}</span>`;
    }

    return `
      <tr class="${rowCls}">
        <td class="col-no">${r.evidence_no}</td>
        <td class="col-date">${r.withdrawal_date || "—"}</td>
        <td class="col-date">${r.date || "—"}</td>
        <td class="col-receipt-no">${r.receipt_number || "—"}</td>
        <td class="col-desc">${r.description || "—"}</td>
        <td class="col-person">${r.person || "—"}</td>
        <td class="col-major">${majorCell}</td>
        <td class="col-minor">${r.account_minor || "—"}</td>
        <td class="col-amount amount-cell" title="${r.amount != null ? "¥" + r.amount.toLocaleString("ko-KR") : ""}">
          ${(r.amount != null && r.type !== '입금영수증' && r.type !== '입금수수료') ? "¥" + r.amount.toLocaleString("ko-KR", { minimumFractionDigits: 2 }) : "—"}
        </td>
        <td class="col-type"><span class="type-badge">${r.type || "기타"}</span></td>
        <td class="col-remark">${remarkHtml}</td>
        <td class="col-action">
          <button class="btn-edit-sm" onclick="openReviewAt(${origIdx})">편집</button>
        </td>
      </tr>
    `;
  }).join("");

  totalEl.textContent = "¥" + total.toLocaleString("ko-KR", { minimumFractionDigits: 2 });
}

// 테이블 편집 버튼 → 검토 탭으로 이동
function openReviewAt(index) {
  state.currentIndex = index;
  document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  document.getElementById("tabReview").classList.add("active");
  document.getElementById("panelReview").classList.add("active");
  renderReview();
  renderSidebar();
}

// === 사이드바 썸네일 목록 렌더링 ===
function renderSidebar() {
  const list    = document.getElementById("sidebarList");
  const countEl = document.getElementById("sidebarCount");
  if (!list) return;

  countEl.textContent = `${state.receipts.length}건`;
  list.innerHTML = state.receipts.map((r, i) => {
    const imgUrl     = getReceiptImgUrl(r);
    const isActive   = i === state.currentIndex;
    const warnings   = getValidationWarnings(r);
    const realWarnings = warnings.filter(w => !w.includes("✅"));
    const hasIssue   = realWarnings.length > 0;
    const isUnmapped = r.is_mapped === false || hasIssue;
    return `
      <div class="sidebar-item${isActive ? " active" : ""}${isUnmapped ? " unmapped" : ""}"
           data-index="${i}" onclick="selectFromSidebar(${i})">
        <img class="sidebar-thumb" src="${imgUrl}"
             onerror="this.style.opacity=0.3" alt="">
        <div class="sidebar-info">
          <div class="sidebar-no">#${r.evidence_no}</div>
          <div class="sidebar-desc">${r.description || r.type || "—"}</div>
        </div>
        ${isUnmapped ? '<span class="sidebar-warn">⚠</span>' : ""}
      </div>
    `;
  }).join("");

  // 선택 항목 자동 스크롤
  const activeItem = list.querySelector(".sidebar-item.active");
  if (activeItem) {
    activeItem.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
}

function selectFromSidebar(index) {
  state.currentIndex = index;
  // 검토 탭으로 전환
  document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  document.getElementById("tabReview").classList.add("active");
  document.getElementById("panelReview").classList.add("active");
  renderReview();
  renderSidebar();
}

// === 데이터 검토 렌더링 ===
function renderReview() {
  if (state.receipts.length === 0) {
    document.getElementById("navCounter").textContent = "0 / 0";
    document.getElementById("reviewImage").src = "";
    document.getElementById("editForm").reset();
    return;
  }

  const r = state.receipts[state.currentIndex];
  document.getElementById("navCounter").textContent =
    `${state.currentIndex + 1} / ${state.receipts.length}`;

  // 이미지 갱신
  const imgUrl = getReceiptImgUrl(r);
  const img = document.getElementById("reviewImage");
  img.src = imgUrl;
  state.imageZoom = 1;
  state.imageRotation = 0;
  state.panX = 0;
  state.panY = 0;
  applyImageTransform();

  // 배지 행
  document.getElementById("badgeType").textContent   = r.type || "기타";
  document.getElementById("badgeNo").textContent     = `증빙 #${r.evidence_no}`;
  document.getElementById("badgeAmount").textContent =
    (r.amount != null && r.type !== '입금영수증' && r.type !== '입금수수료')
      ? "¥" + r.amount.toLocaleString("ko-KR", { minimumFractionDigits: 2 })
      : "—";

  // 매핑 상태 뱃지
  const badge = document.getElementById("mappedBadge");
  if (r.is_mapped === false) {
    badge.textContent = "⚠️ 계정 확인 필요";
    badge.className   = "mapped-badge warn";
  } else {
    badge.textContent = "✅ 정상";
    badge.className   = "mapped-badge ok";
  }

  document.getElementById("editType").value        = r.type || "기타";
  document.getElementById("editWithdrawalDate").value = r.withdrawal_date || "";
  document.getElementById("editDate").value        = r.date || "";
  document.getElementById("editReceiptNumber").value = r.receipt_number || "";
  document.getElementById("editAmount").value      = r.amount != null ? r.amount : "";
  document.getElementById("editDescription").value = r.description || "";
  document.getElementById("editRemark").value      = r.remark || "";

  // S열 로직(자동화 시스템 판독 결과)
  const warnings = getValidationWarnings(r);
  const realWarnings = warnings.filter(w => !w.includes("✅"));
  const sysResultEl = document.getElementById("systemValidationResult");
  
  if (realWarnings.length > 0) {
    const wText = warnings.join(" / ").replace(/\n/g, "<br>");
    sysResultEl.innerHTML = wText;
    sysResultEl.style.backgroundColor = "#fee2e2";
    sysResultEl.style.color = "#b91c1c";
    sysResultEl.style.borderColor = "#fca5a5";
    sysResultEl.parentElement.style.display = "block";
  } else if (warnings.length > 0) {
    // Only '✅' warnings present
    const wText = warnings.join(" / ").replace(/\n/g, "<br>");
    sysResultEl.innerHTML = wText;
    sysResultEl.style.backgroundColor = "#d1fae5";
    sysResultEl.style.color = "#059669";
    sysResultEl.style.borderColor = "#a7f3d0";
    sysResultEl.parentElement.style.display = "block";
  } else if (r.validation_warning && r.validation_warning === "✅ 금액 일치") {
    let formatted = r.validation_warning.replace(/\n/g, "<br>");
    sysResultEl.innerHTML = formatted;
    sysResultEl.style.backgroundColor = "#d1fae5";
    sysResultEl.style.color = "#059669";
    sysResultEl.style.borderColor = "#a7f3d0";
    sysResultEl.parentElement.style.display = "block";
  } else {
    sysResultEl.textContent = "";
    sysResultEl.parentElement.style.display = "none";
  }

  // 담당자 드롭다운 (동적 생성)
  buildPersonDropdown(r.person || "");

  // 대계정 / 소계정
  const majorSelect = document.getElementById("editMajor");
  const minorSelect = document.getElementById("editMinor");
  majorSelect.value = r.account_major || "";
  updateMinorDropdown(r.account_major || "", r.account_minor || "");

  if (r.is_mapped === false) {
    majorSelect.classList.add("warning-border");
    minorSelect.classList.add("warning-border");
  } else {
    majorSelect.classList.remove("warning-border");
    minorSelect.classList.remove("warning-border");
  }
}

// === 이미지 뷰어 컨트롤 ===
function initViewerControls() {
  document.getElementById("btnZoomIn")?.addEventListener("click", () => {
    state.imageZoom = Math.min(state.imageZoom + 0.25, 4);
    applyImageTransform();
  });
  document.getElementById("btnZoomOut")?.addEventListener("click", () => {
    state.imageZoom = Math.max(state.imageZoom - 0.25, 0.5);
    applyImageTransform();
  });
  document.getElementById("btnRotate")?.addEventListener("click", () => {
    state.imageRotation = (state.imageRotation + 90) % 360;
    applyImageTransform();
  });
  document.getElementById("btnReset")?.addEventListener("click", () => {
    state.imageZoom = 1;
    state.imageRotation = 0;
    state.panX = 0;
    state.panY = 0;
    applyImageTransform();
  });

  const img = document.getElementById("reviewImage");
  if (img) {
    let isDragging = false;
    let startX, startY;

    img.addEventListener("mousedown", (e) => {
      isDragging = true;
      startX = e.clientX - state.panX;
      startY = e.clientY - state.panY;
      img.style.cursor = "grabbing";
      e.preventDefault(); // prevent default browser image dragging
    });

    window.addEventListener("mousemove", (e) => {
      if (!isDragging) return;
      state.panX = e.clientX - startX;
      state.panY = e.clientY - startY;
      applyImageTransform();
    });

    window.addEventListener("mouseup", () => {
      if (isDragging) {
        isDragging = false;
        img.style.cursor = "grab";
      }
    });

    img.parentElement.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomStep = 0.15;
      if (e.deltaY < 0) {
        state.imageZoom = Math.min(state.imageZoom + zoomStep, 4);
      } else {
        state.imageZoom = Math.max(state.imageZoom - zoomStep, 0.5);
      }
      applyImageTransform();
    }, { passive: false });
  }
}

function applyImageTransform() {
  const img = document.getElementById("reviewImage");
  if (img) {
    img.style.transform = `translate(${state.panX}px, ${state.panY}px) scale(${state.imageZoom}) rotate(${state.imageRotation}deg)`;
  }
}

// === 폼 저장 / 삭제 / 이전 / 다음 ===
function initFormActions() {
  document.getElementById("btnSaveReceipt")?.addEventListener("click", saveCurrentReceipt);
  document.getElementById("btnDeleteReceipt")?.addEventListener("click", deleteCurrentReceipt);
  document.getElementById("btnPrev")?.addEventListener("click", () => navigateReceipt(-1));
  document.getElementById("btnNext")?.addEventListener("click", () => navigateReceipt(1));
  document.getElementById("btnSaveExcel")?.addEventListener("click", saveExcel);
}

async function saveCurrentReceipt() {
  if (state.receipts.length === 0) return;
  const r = state.receipts[state.currentIndex];

  const update = {
    type:          document.getElementById("editType").value,
    withdrawal_date: document.getElementById("editWithdrawalDate").value || null,
    date:          document.getElementById("editDate").value || null,
    receipt_number: document.getElementById("editReceiptNumber").value || null,
    amount:        parseFloat(document.getElementById("editAmount").value) || null,
    description:   document.getElementById("editDescription").value || null,
    person:        document.getElementById("editPerson").value || null,
    account_major: document.getElementById("editMajor").value || null,
    account_minor: document.getElementById("editMinor").value || null,
    remark:        document.getElementById("editRemark").value || null,
  };

  // 계정 코드 자동 연동
  if (update.account_major) {
    const match = state.accounts.find(
      (a) => a.major === update.account_major &&
             (!update.account_minor || a.minor === update.account_minor)
    );
    if (match) update.account_code = match.code;
  }

  try {
    const res = await fetch(
      `/api/months/${state.currentMonth}/receipts/${r.evidence_no}`,
      { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(update) }
    );
    if (!res.ok) throw new Error("저장 실패");
    showToast(`<strong style="color: #fff8a3; letter-spacing: 0.5px;">#${r.evidence_no} 영수증</strong> 임시저장 완료!<br>상단 엑셀 최종 저장버튼을 눌러야 엑셀에 반영됩니다.`, "success");
    await loadReceipts();
    renderReview();
  } catch (e) {
    showToast("저장 중 오류가 발생했습니다.", "error");
  }
}

async function deleteCurrentReceipt() {
  if (state.receipts.length === 0) return;
  const r = state.receipts[state.currentIndex];
  if (!confirm(`증빙번호 [${r.evidence_no}번] 영수증을 삭제하시겠습니까?\n삭제 시 이후 영수증들이 자동으로 당겨져 재정렬됩니다.`)) return;

  try {
    const res = await fetch(
      `/api/months/${state.currentMonth}/receipts/${r.evidence_no}`,
      { method: "DELETE" }
    );
    if (!res.ok) throw new Error("삭제 실패");
    showToast("삭제 완료! 증빙번호가 자동 재정렬되었습니다.", "info");
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
  const newIdx = state.currentIndex + direction;
  if (newIdx >= 0 && newIdx < state.receipts.length) {
    state.currentIndex = newIdx;
    renderReview();
    renderSidebar();
  }
}

// === 엑셀 최종 저장 (덮어쓰기) ===
async function saveExcel() {
  if (!state.currentMonth || state.receipts.length === 0) {
    showToast("저장할 데이터가 없습니다.", "warning");
    return;
  }

  if (!confirm(`현재 작업하신 내용으로 [정산내역_${state.currentMonth}.xlsx] 파일을 덮어쓰시겠습니까?`)) {
    return;
  }

  const btn = document.getElementById("btnSaveExcel");
  btn.disabled = true;
  btn.innerHTML = `<span>⏳</span> 저장 중...`;

  try {
    const res = await fetch(`/api/months/${state.currentMonth}/save`, { method: "POST" });
    if (!res.ok) throw new Error("저장 실패");
    const data = await res.json();
    showToast(`✅ ${data.message}`, "success");
  } catch (e) {
    showToast(`저장 오류: ${e.message}`, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
        <polyline points="17 21 17 13 7 13 7 21"/>
        <polyline points="7 3 7 8 15 8"/>
      </svg>
      엑셀 최종 저장`;
  }
}

// === 토스트 알림 ===
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(30px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 8000);
}

// === 시스템 재가동 로직 ===
async function reprocessBatch() {
  if (!state.currentMonth) return;
  if (!confirm("최종 저장된 엑셀 데이터를 바탕으로 파이썬 시스템 검증을 다시 가동하시겠습니까?\n\n수정된 금액 등의 정보가 반영되어 ⚠️ 경고 마크가 최신화됩니다. (약 3~10초 소요)")) return;
  
  showToast("시스템을 재가동합니다. 잠시만 기다려주세요...", "info");
  
  const btn = document.getElementById("btnReprocess");
  if(btn) {
      btn.disabled = true;
      btn.innerHTML = `<span>⏳</span> 재가동 중...`;
  }
  
  try {
    const res = await fetch(`/api/months/${state.currentMonth}/reprocess`, {
      method: "POST"
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "시스템 재가동 실패");
    }
    
    showToast("시스템 판독이 성공적으로 재가동되었습니다! 화면을 새로고침합니다.", "success");
    
    // 1초 뒤 데이터 새로고침
    setTimeout(() => {
      location.reload();
    }, 1000);
    
  } catch (err) {
    showToast("오류 발생: " + err.message, "error");
    if(btn) {
        btn.disabled = false;
        btn.innerHTML = `시스템 판독 재검증`;
    }
  }
}

// === 재무관리팀 마감 로직 ===
function initCloseMonth() {
  const btnCloseMonth = document.getElementById("btnCloseMonth");
  if (!btnCloseMonth) return;

  const empName = sessionStorage.getItem("empName") || "";
  if (empName === "정영욱" || empName === "김수민") {
    btnCloseMonth.style.display = "inline-flex";
  }

  btnCloseMonth.addEventListener("click", () => {
    if (!state.currentMonth) return;
    document.getElementById("closeMonthText").textContent = state.currentMonth;
    document.getElementById("closeMonthOverlay").style.display = "flex";
  });

  const btnConfirmClose = document.getElementById("btnConfirmClose");
  const btnCancelClose = document.getElementById("btnCancelClose");

  if (btnCancelClose) {
    btnCancelClose.addEventListener("click", () => {
      document.getElementById("closeMonthOverlay").style.display = "none";
    });
  }

  if (btnConfirmClose) {
    btnConfirmClose.addEventListener("click", async () => {
      document.getElementById("closeMonthOverlay").style.display = "none";
      if (!state.currentMonth) return;
      
      try {
        const res = await fetch(`/api/months/${state.currentMonth}/close`, { method: "POST" });
        if (!res.ok) {
          const errData = await res.json();
          if (res.status === 409) {
            document.getElementById("closeErrorMsg").innerHTML = errData.detail.replace(/\n/g, "<br>");
            document.getElementById("closeErrorOverlay").style.display = "flex";
            return;
          }
          throw new Error(errData.detail || "마감 처리 실패");
        }
        showToast(`${state.currentMonth}월 데이터 마감이 완료되었습니다!`, "success");
      } catch (err) {
        showToast("오류 발생: " + err.message, "error");
      }
    });
  }

  const btnCloseErrorOk = document.getElementById("btnCloseErrorOk");
  if (btnCloseErrorOk) {
    btnCloseErrorOk.addEventListener("click", () => {
      document.getElementById("closeErrorOverlay").style.display = "none";
    });
  }
}
