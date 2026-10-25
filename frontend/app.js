/**
 * GHOST DATA STILL EXISTS — ENTERPRISE ADMIN DASHBOARD CONTROLLER
 * Full integration with FastAPI Backend, continuous shimmer skeleton loaders,
 * Hotstar/JioCinema hover-overlay navigation, and Lucide SVG icons.
 */

const API_BASE = (window.location.port === '8000' || window.location.port === '5173') 
  ? window.location.origin 
  : 'http://127.0.0.1:8000';

// State Machine
let appState = {
  currentTab: 'tab-overview',
  datasetType: 'eval', // 'eval' or 'sample'
  statusFilter: 'ALL',
  searchQuery: '',
  currentPage: 1,
  pageSize: 20,
  totalPages: 1,
  activeCaseId: null,
  cachedEvidence: [],
  searchTimer: null,
  backendConnected: false,
  healthPollTimer: null
};

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
});

async function initDashboard() {
  setupSidebarInteractions();
  startHealthMonitor();
  await loadDashboardData();
}

function setupSidebarInteractions() {
  const sidebar = document.getElementById('hotstar-sidebar');
  if (!sidebar) return;
  sidebar.addEventListener('mouseenter', () => {
    sidebar.classList.add('expanded');
  });
  sidebar.addEventListener('mouseleave', () => {
    sidebar.classList.remove('expanded');
  });
}

// -------------------------------------------------------------
// Continuous Health Monitor & Shimmer Loading Management
// -------------------------------------------------------------
function setBackendStatus(connected) {
  appState.backendConnected = connected;
  const pill = document.getElementById('backend-status-pill');
  const pillText = document.getElementById('backend-status-text');
  const banner = document.getElementById('reconnect-banner');

  if (connected) {
    pill.classList.remove('disconnected');
    pillText.innerText = 'Backend Connected';
    banner.style.display = 'none';

    // Show real content, hide skeletons
    document.getElementById('overview-kpi-skeletons').style.display = 'none';
    document.getElementById('overview-kpi-real').style.display = 'grid';

    document.getElementById('cases-table-skeleton').style.display = 'none';
    document.getElementById('cases-table-real').style.display = 'block';

    document.getElementById('benchmark-skeletons').style.display = 'none';
    document.getElementById('benchmark-real').style.display = 'grid';
  } else {
    pill.classList.add('disconnected');
    pillText.innerText = 'Reconnecting...';
    banner.style.display = 'flex';

    // Show continuous shimmer skeletons, hide real content
    document.getElementById('overview-kpi-skeletons').style.display = 'grid';
    document.getElementById('overview-kpi-real').style.display = 'none';

    document.getElementById('cases-table-skeleton').style.display = 'flex';
    document.getElementById('cases-table-real').style.display = 'none';

    document.getElementById('benchmark-skeletons').style.display = 'grid';
    document.getElementById('benchmark-real').style.display = 'none';
  }
}

async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { cache: 'no-store' });
    if (!res.ok) throw new Error("Health check failed");
    const data = await res.json();
    if (!appState.backendConnected) {
      setBackendStatus(true);
      await loadDashboardData();
    }
  } catch (err) {
    setBackendStatus(false);
  }
}

function startHealthMonitor() {
  checkBackendHealth();
  if (appState.healthPollTimer) clearInterval(appState.healthPollTimer);
  appState.healthPollTimer = setInterval(checkBackendHealth, 4000);
}

// -------------------------------------------------------------
// Data Orchestrator
// -------------------------------------------------------------
async function loadDashboardData() {
  try {
    await Promise.all([
      fetchStats(),
      fetchCases(),
      fetchEvidenceCatalog(),
      fetchBenchmark()
    ]);
    setBackendStatus(true);
  } catch (err) {
    console.warn("API unavailable, displaying continuous shimmer skeleton:", err);
    setBackendStatus(false);
  }
}

// -------------------------------------------------------------
// Navigation & Tab Switching
// -------------------------------------------------------------
function switchNavTab(tabId) {
  appState.currentTab = tabId;

  // Update sidebar links
  document.querySelectorAll('.sidebar-menu .nav-link').forEach(link => {
    link.classList.remove('active');
  });
  const activeLink = document.getElementById(`nav-${tabId}`);
  if (activeLink) activeLink.classList.add('active');

  // Update active view
  document.querySelectorAll('.tab-content-area').forEach(pane => {
    pane.classList.remove('active');
  });
  const activePane = document.getElementById(tabId);
  if (activePane) activePane.classList.add('active');

  // Update breadcrumb
  const breadcrumb = document.getElementById('topbar-breadcrumb');
  if (tabId === 'tab-overview') breadcrumb.innerText = 'Overview';
  else if (tabId === 'tab-cases') breadcrumb.innerText = 'Case Explorer';
  else if (tabId === 'tab-benchmark') breadcrumb.innerText = 'Sample Benchmark';
  else if (tabId === 'tab-evidence') breadcrumb.innerText = 'Evidence Files';

  if (tabId === 'tab-cases') {
    fetchCases();
  } else if (tabId === 'tab-benchmark') {
    fetchBenchmark();
  }
}

// -------------------------------------------------------------
// Toast Notifications
// -------------------------------------------------------------
function showToast(message, type = 'info') {
  const shelf = document.getElementById('toast-shelf');
  const toast = document.createElement('div');
  toast.className = 'toast-msg';

  let iconSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y2="16"/></svg>`;
  if (type === 'success') {
    toast.style.borderLeftColor = 'var(--status-complete)';
    iconSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`;
  } else if (type === 'error') {
    toast.style.borderLeftColor = 'var(--status-incomplete)';
  }

  toast.innerHTML = `${iconSvg}<span>${message}</span>`;
  shelf.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 250);
  }, 4000);
}

// -------------------------------------------------------------
// Overview Statistics
// -------------------------------------------------------------
async function fetchStats() {
  const res = await fetch(`${API_BASE}/api/stats`, { cache: 'no-store' });
  if (!res.ok) throw new Error("Stats fetch failed");
  const data = await res.json();

  document.getElementById('kpi-val-eval').innerText = data.total_eval_cases || 518;
  document.getElementById('rail-cases-badge').innerText = data.total_eval_cases || 518;
  document.getElementById('kpi-val-evidence').innerText = data.evidence_files_count || 94;
  document.getElementById('rail-evidence-badge').innerText = data.evidence_files_count || 94;

  if (data.sample_evaluation) {
    document.getElementById('kpi-val-acc').innerText = `${data.sample_evaluation.status_accuracy}%`;
  }

  if (data.output_generated) {
    document.getElementById('kpi-val-output').innerText = 'Ready';
    const c = data.output_breakdown.COMPLETE || 0;
    const ic = data.output_breakdown.INCOMPLETE || 0;
    const na = data.output_breakdown.NOT_APPLICABLE || 0;
    document.getElementById('kpi-val-output-footer').innerHTML = 
      `<span class="highlight">${c} Complete</span>, ${ic} Incomplete, ${na} N/A`;
  }
}

// -------------------------------------------------------------
// Case Explorer & Filters
// -------------------------------------------------------------
function selectDataset(type) {
  appState.datasetType = type;
  appState.currentPage = 1;
  document.getElementById('chip-dataset-eval').classList.toggle('active', type === 'eval');
  document.getElementById('chip-dataset-sample').classList.toggle('active', type === 'sample');
  fetchCases();
}

function selectStatusFilter(status) {
  appState.statusFilter = status;
  appState.currentPage = 1;
  const chips = document.querySelectorAll('.chip-filters:last-child .filter-badge-chip');
  chips.forEach(chip => {
    chip.classList.toggle('active', chip.innerText.toUpperCase() === status || (status === 'ALL' && chip.innerText === 'All'));
  });
  fetchCases();
}

function onSearchInput() {
  clearTimeout(appState.searchTimer);
  appState.searchTimer = setTimeout(() => {
    appState.searchQuery = document.getElementById('case-search-input').value.trim();
    appState.currentPage = 1;
    fetchCases();
  }, 220);
}

function paginate(delta) {
  const target = appState.currentPage + delta;
  if (target >= 1 && target <= appState.totalPages) {
    appState.currentPage = target;
    fetchCases();
  }
}

async function fetchCases() {
  const skeleton = document.getElementById('cases-table-skeleton');
  const tableReal = document.getElementById('cases-table-real');

  skeleton.style.display = 'flex';
  tableReal.style.display = 'none';

  try {
    const params = new URLSearchParams({
      dataset_type: appState.datasetType,
      status: appState.statusFilter,
      search: appState.searchQuery,
      page: appState.currentPage,
      page_size: appState.pageSize
    });

    const res = await fetch(`${API_BASE}/api/cases?${params.toString()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error("Cases query failed");
    const data = await res.json();

    appState.totalPages = data.total_pages || 1;
    document.getElementById('cases-page-info').innerText = 
      `Showing ${(data.page - 1) * data.page_size + 1} to ${Math.min(data.page * data.page_size, data.total_cases)} of ${data.total_cases} cases`;
    document.getElementById('label-current-page').innerText = data.page;
    document.getElementById('btn-page-prev').disabled = (data.page <= 1);
    document.getElementById('btn-page-next').disabled = (data.page >= appState.totalPages);

    const tbody = document.getElementById('cases-table-body');
    if (!data.cases || data.cases.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 2.5rem; color: var(--text-tertiary);">No cases match search criteria</td></tr>`;
    } else {
      tbody.innerHTML = data.cases.map(c => {
        let pillClass = 'pill-na';
        if (c.deletion_status === 'COMPLETE') pillClass = 'pill-complete';
        else if (c.deletion_status === 'INCOMPLETE') pillClass = 'pill-incomplete';

        return `
          <tr onclick="inspectCase('${c.case_id}')">
            <td class="mono-tag" style="font-weight: 700;">${c.case_id}</td>
            <td>${c.email}</td>
            <td class="mono-tag">${c.user_id}</td>
            <td><span style="font-size: 0.75rem; color: var(--text-secondary);">${c.reported_status}</span></td>
            <td class="mono-tag" style="font-size: 0.72rem;">${c.audit_at ? c.audit_at.replace('T', ' ').replace('Z', '') : '--'}</td>
            <td><span class="badge-pill ${pillClass}">${c.deletion_status}</span></td>
            <td>
              <span style="font-size: 0.75rem; color: var(--text-secondary);">
                ${c.findings_count}F • ${c.remediations_count}R • ${c.verifications_count}V (${c.steps_count} total)
              </span>
            </td>
            <td>
              <button class="btn-action btn-outline btn-icon-only" title="Inspect Dossier" onclick="event.stopPropagation(); inspectCase('${c.case_id}')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
              </button>
            </td>
          </tr>
        `;
      }).join('');
    }

    // Switch from skeleton to real content
    skeleton.style.display = 'none';
    tableReal.style.display = 'block';
  } catch (err) {
    skeleton.style.display = 'flex';
    tableReal.style.display = 'none';
    throw err;
  }
}

// -------------------------------------------------------------
// Case Dossier Inspector Drawer
// -------------------------------------------------------------
async function inspectCase(caseId) {
  appState.activeCaseId = caseId;
  const drawer = document.getElementById('inspector-drawer');
  const overlay = document.getElementById('drawer-overlay');
  drawer.classList.add('active');
  overlay.classList.add('active');

  document.getElementById('drawer-case-id').innerText = caseId;
  document.getElementById('drawer-steps-list').innerHTML = `<p style="font-size: 0.8rem; color: var(--text-tertiary);">Loading case intelligence...</p>`;

  try {
    const res = await fetch(`${API_BASE}/api/cases/${caseId}`);
    if (!res.ok) throw new Error("Failed to load case");
    const data = await res.json();
    renderDossierDetail(data);
  } catch (err) {
    document.getElementById('drawer-steps-list').innerHTML = `<p style="color: var(--status-incomplete);">Failed to load: ${err.message}</p>`;
  }
}

function closeInspectorDrawer() {
  document.getElementById('inspector-drawer').classList.remove('active');
  document.getElementById('drawer-overlay').classList.remove('active');
  appState.activeCaseId = null;
}

function renderDossierDetail(data) {
  document.getElementById('drawer-case-id').innerText = data.case_id;
  document.getElementById('drawer-subject-email').innerText = data.email;

  const pill = document.getElementById('drawer-status-pill');
  pill.innerText = data.deletion_status;
  pill.className = `badge-pill ${data.deletion_status === 'COMPLETE' ? 'pill-complete' : data.deletion_status === 'INCOMPLETE' ? 'pill-incomplete' : 'pill-na'}`;

  // Subject Profile
  const profile = data.identity_profile || {};
  document.getElementById('drawer-user-id').innerText = profile.user_id || 'UNRESOLVED';
  document.getElementById('drawer-name').innerText = profile.name || '--';
  document.getElementById('drawer-curr-email').innerText = profile.current_email || data.email;
  document.getElementById('drawer-phone').innerText = profile.phone || '--';
  document.getElementById('drawer-all-emails').innerText = (profile.all_emails || [data.email]).join(', ');
  document.getElementById('drawer-hash').innerText = profile.email_hash || '--';

  // Request Intent
  document.getElementById('drawer-req-text').innerText = `"${data.request_text || '(No request text)'}"`;
  const intentAuth = document.getElementById('drawer-intent-auth');
  const isAuth = data.intent_analysis?.is_authorized;
  intentAuth.innerText = isAuth ? 'AUTHORIZED (Deletion Request)' : 'NOT APPLICABLE (Access/Export/Correction)';
  intentAuth.style.color = isAuth ? 'var(--status-complete)' : 'var(--status-na)';
  document.getElementById('drawer-intent-reason').innerText = data.intent_analysis?.reason || '--';

  // Timestamps
  document.getElementById('drawer-requested-at').innerText = data.requested_at || '--';
  document.getElementById('drawer-claim').innerText = data.reported_status || '--';
  document.getElementById('drawer-reported-at').innerText = data.reported_at || '--';
  document.getElementById('drawer-audit-at').innerText = data.audit_at || '--';

  // Steps
  const steps = data.steps || [];
  document.getElementById('drawer-steps-badge').innerText = `${steps.length} Steps`;
  document.getElementById('drawer-raw-json').innerText = JSON.stringify(steps, null, 2);

  const container = document.getElementById('drawer-steps-list');
  if (steps.length === 0) {
    container.innerHTML = `<p style="font-size: 0.8rem; color: var(--text-tertiary); padding: 0.5rem 0;">No steps (NOT_APPLICABLE or empty plan).</p>`;
    return;
  }

  container.innerHTML = steps.map(s => {
    let phaseClass = 'phase-verification';
    if (s.phase === 'FINDING') phaseClass = 'phase-finding';
    else if (s.phase === 'REMEDIATION') phaseClass = 'phase-remediation';

    return `
      <div class="step-item-card ${phaseClass}">
        <div>
          <div style="font-family: var(--font-mono); font-size: 0.82rem; color: #fff;">
            <strong>Step ${s.step_no}:</strong> ${s.system_id} // ${s.resource_id}
          </div>
          <div style="font-size: 0.74rem; color: var(--text-secondary); margin-top: 0.15rem;">
            ${s.operation} &rarr; Target: <strong>${s.state}</strong>
          </div>
        </div>
        <div style="display: flex; gap: 0.5rem; align-items: center;">
          <span class="badge-pill pill-na">${s.phase}</span>
          ${s.evidence_id ? `<span class="badge-pill pill-complete" style="cursor: pointer;" onclick="viewEvidenceInCatalog('${s.evidence_id}')">${s.evidence_id}</span>` : ''}
        </div>
      </div>
    `;
  }).join('');
}

async function reAuditSingleCase() {
  if (!appState.activeCaseId) return;
  showToast(`Re-auditing ${appState.activeCaseId}...`, 'info');
  try {
    const res = await fetch(`${API_BASE}/api/audit/case/${appState.activeCaseId}`, { method: 'POST' });
    if (!res.ok) throw new Error("Audit failed");
    const data = await res.json();
    showToast(`Case audited: ${data.deletion_status}`, 'success');
    inspectCase(appState.activeCaseId);
    fetchCases();
  } catch (err) {
    showToast(`Audit failed: ${err.message}`, 'error');
  }
}

// -------------------------------------------------------------
// Batch Audit Trigger
// -------------------------------------------------------------
async function triggerFullAudit() {
  const btn = document.getElementById('btn-topbar-run');
  btn.disabled = true;
  btn.innerText = 'Auditing 518 cases...';
  showToast("Auditing all 518 evaluation requests and writing output.csv...", "info");

  try {
    const res = await fetch(`${API_BASE}/api/audit/run-all`, { method: 'POST' });
    if (!res.ok) throw new Error("Full audit failed");
    const data = await res.json();

    showToast(`Full audit complete! Generated root output.csv (${data.total_cases_audited} rows)`, 'success');
    await fetchStats();
    await fetchCases();
  } catch (err) {
    showToast(`Audit failed: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Audit All 518 Cases`;
  }
}

// -------------------------------------------------------------
// Benchmark Evaluation
// -------------------------------------------------------------
async function fetchBenchmark() {
  const skeletons = document.getElementById('benchmark-skeletons');
  const real = document.getElementById('benchmark-real');
  skeletons.style.display = 'grid';
  real.style.display = 'none';

  try {
    const res = await fetch(`${API_BASE}/api/evaluate`, { cache: 'no-store' });
    if (!res.ok) throw new Error("Benchmark failed");
    const data = await res.json();

    document.getElementById('acc-status').innerText = `${(data.status_accuracy * 100).toFixed(2)}%`;
    document.getElementById('acc-sequence').innerText = `${(data.sequence_accuracy * 100).toFixed(2)}%`;
    document.getElementById('acc-field').innerText = `${(data.field_accuracy * 100).toFixed(2)}%`;

    skeletons.style.display = 'none';
    real.style.display = 'grid';

    const container = document.getElementById('benchmark-cases-container');
    if (!data.mismatches || data.mismatches.length === 0) {
      container.innerHTML = `<div class="dossier-section" style="color: var(--status-complete); font-weight: 600;">100% Exact Match on All 32 Sample Cases!</div>`;
      return;
    }

    container.innerHTML = data.mismatches.map(m => {
      return `
        <div class="dossier-section" style="border-left: 3.5px solid ${m.pred_status === m.gt_status ? 'var(--status-complete)' : 'var(--status-incomplete)'};">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.65rem;">
            <span class="mono-tag" style="font-weight: 700; font-size: 0.92rem;">${m.case_id}</span>
            <div>
              Pred: <span class="badge-pill ${m.pred_status === 'COMPLETE' ? 'pill-complete' : 'pill-incomplete'}">${m.pred_status}</span>
              vs GT: <span class="badge-pill ${m.gt_status === 'COMPLETE' ? 'pill-complete' : 'pill-incomplete'}">${m.gt_status}</span>
            </div>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem;">
            <div>
              <div style="font-size: 0.7rem; color: var(--text-tertiary); text-transform: uppercase;">Predicted (${m.pred_steps_count}):</div>
              <pre class="code-pre-box" style="font-size: 0.68rem; max-height: 120px;">${JSON.stringify(m.pred_steps, null, 2)}</pre>
            </div>
            <div>
              <div style="font-size: 0.7rem; color: var(--text-tertiary); text-transform: uppercase;">Ground Truth (${m.gt_steps_count}):</div>
              <pre class="code-pre-box" style="font-size: 0.68rem; max-height: 120px; color: #34d399;">${JSON.stringify(m.gt_steps, null, 2)}</pre>
            </div>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    skeletons.style.display = 'grid';
    real.style.display = 'none';
    throw err;
  }
}

async function refreshBenchmark() {
  showToast("Re-evaluating sample cases against ground truth...", "info");
  await fetchBenchmark();
  showToast("Benchmark updated!", "success");
}

// -------------------------------------------------------------
// Evidence Catalog & Previewer
// -------------------------------------------------------------
async function fetchEvidenceCatalog() {
  const res = await fetch(`${API_BASE}/api/evidence`, { cache: 'no-store' });
  if (!res.ok) throw new Error("Evidence query failed");
  const data = await res.json();
  appState.cachedEvidence = data.files || [];

  const listEl = document.getElementById('evidence-files-list');
  listEl.innerHTML = appState.cachedEvidence.map(f => {
    return `
      <div style="padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-subtle); cursor: pointer; transition: background 0.15s ease;"
           id="ev-item-${f.file_id}"
           onclick="selectEvidenceFile('${f.file_id}')">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem;">
          <span class="mono-tag" style="font-weight: 700;">${f.file_id}</span>
          <span class="badge-pill pill-na" style="font-size: 0.65rem;">${f.category}</span>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
          ${f.file_path}
        </div>
        <div style="font-size: 0.68rem; color: var(--text-tertiary); margin-top: 0.2rem;">
          ${(f.size_bytes / 1024).toFixed(1)} KB • ${f.captured_at ? f.captured_at.replace('T', ' ').replace('Z', '') : '--'}
        </div>
      </div>
    `;
  }).join('');

  if (appState.cachedEvidence.length > 0) {
    selectEvidenceFile(appState.cachedEvidence[0].file_id);
  }
}

async function selectEvidenceFile(fileId) {
  document.querySelectorAll('#evidence-files-list > div').forEach(el => el.style.background = 'transparent');
  const activeEl = document.getElementById(`ev-item-${fileId}`);
  if (activeEl) activeEl.style.background = 'var(--bg-surface-elevated)';

  const box = document.getElementById('ev-preview-content');
  box.innerText = 'Loading artifact preview...';

  try {
    const res = await fetch(`${API_BASE}/api/evidence/${fileId}`);
    if (!res.ok) throw new Error("Failed to read file");
    const data = await res.json();

    document.getElementById('ev-preview-title').innerText = `${data.file_id} — ${data.file_path}`;
    document.getElementById('ev-preview-meta').innerText = 
      `Origin: ${data.origin} • Size: ${(data.size_bytes / 1024).toFixed(1)} KB • Captured: ${data.captured_at}`;
    box.innerText = data.content_preview || '(Empty file)';
  } catch (err) {
    box.innerText = `Error: ${err.message}`;
  }
}

function viewEvidenceInCatalog(fileId) {
  closeInspectorDrawer();
  switchNavTab('tab-evidence');
  setTimeout(() => selectEvidenceFile(fileId), 100);
}

function copyEvidenceSnippet() {
  const content = document.getElementById('ev-preview-content').innerText;
  navigator.clipboard.writeText(content).then(() => {
    showToast("Evidence content copied to clipboard!", "success");
  });
}

// -------------------------------------------------------------
// Submission Packaging
// -------------------------------------------------------------
async function triggerPackaging() {
  showToast("Packaging code.zip for challenge submission...", "info");
  try {
    const res = await fetch(`${API_BASE}/api/package`, { method: 'POST' });
    if (!res.ok) throw new Error("Packaging failed");
    const data = await res.json();
    showToast(`code.zip ready (${(data.size_bytes / 1024).toFixed(1)} KB)`, "success");
    switchNavTab('tab-submission');
  } catch (err) {
    showToast(`Packaging failed: ${err.message}`, "error");
  }
}

// -------------------------------------------------------------
// output.csv Live Viewer Modal Logic
// -------------------------------------------------------------
const outputState = {
  page: 1,
  pageSize: 25,
  search: '',
  status: 'ALL',
  viewMode: 'table',
  totalPages: 1,
  totalRows: 0,
  rawLoaded: false
};

async function openOutputModal() {
  const modal = document.getElementById('output-modal-overlay');
  modal.classList.add('active');
  outputState.page = 1;
  await fetchOutputRecords();
}

function closeOutputModal() {
  const modal = document.getElementById('output-modal-overlay');
  modal.classList.remove('active');
}

function setOutputViewMode(mode) {
  outputState.viewMode = mode;
  const btnTable = document.getElementById('btn-mode-table');
  const btnRaw = document.getElementById('btn-mode-raw');
  const viewTable = document.getElementById('output-view-table');
  const viewRaw = document.getElementById('output-view-raw');

  if (mode === 'table') {
    btnTable.classList.add('active');
    btnRaw.classList.remove('active');
    viewTable.style.display = 'block';
    viewRaw.style.display = 'none';
  } else {
    btnRaw.classList.add('active');
    btnTable.classList.remove('active');
    viewTable.style.display = 'none';
    viewRaw.style.display = 'block';
    if (!outputState.rawLoaded) {
      fetchOutputRaw();
    }
  }
}

let outputSearchTimeout = null;
function handleOutputSearch() {
  clearTimeout(outputSearchTimeout);
  outputSearchTimeout = setTimeout(() => {
    outputState.search = document.getElementById('output-search-input').value.trim();
    outputState.page = 1;
    fetchOutputRecords();
  }, 250);
}

function handleOutputFilter() {
  outputState.status = document.getElementById('output-filter-status').value;
  outputState.page = 1;
  fetchOutputRecords();
}

async function changeOutputPage(delta) {
  const newPage = outputState.page + delta;
  if (newPage >= 1 && newPage <= outputState.totalPages) {
    outputState.page = newPage;
    await fetchOutputRecords();
  }
}

async function fetchOutputRecords() {
  const tbody = document.getElementById('output-table-body');
  try {
    const query = new URLSearchParams({
      search: outputState.search,
      status: outputState.status,
      page: outputState.page,
      page_size: outputState.pageSize
    });

    const res = await fetch(`${API_BASE}/api/output/records?${query.toString()}`);
    if (!res.ok) throw new Error("Could not load output.csv records");
    const data = await res.json();

    outputState.totalPages = data.total_pages || 1;
    outputState.totalRows = data.total_rows || 0;

    // Update status badge & pagination
    document.getElementById('output-modal-status-badge').innerText = `${data.total_unfiltered || data.total_rows} Cases Audited`;
    document.getElementById('output-page-label').innerText = `Page ${data.page} / ${data.total_pages}`;
    
    const startNum = data.total_rows === 0 ? 0 : (data.page - 1) * data.page_size + 1;
    const endNum = Math.min(data.page * data.page_size, data.total_rows);
    document.getElementById('output-pagination-info').innerText = `Showing ${startNum}-${endNum} of ${data.total_rows} cases`;

    document.getElementById('output-prev-page').disabled = (data.page <= 1);
    document.getElementById('output-next-page').disabled = (data.page >= data.total_pages);

    if (!data.records || data.records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2.5rem; color: var(--text-tertiary);">No cases match criteria</td></tr>`;
      return;
    }

    tbody.innerHTML = data.records.map((r, idx) => {
      let pillClass = 'pill-na';
      if (r.deletion_status === 'COMPLETE') pillClass = 'pill-complete';
      else if (r.deletion_status === 'INCOMPLETE') pillClass = 'pill-incomplete';

      const rowNo = startNum + idx;
      const snippet = r.steps_raw && r.steps_raw.length > 80 ? r.steps_raw.substring(0, 80) + '...' : (r.steps_raw || '[]');

      return `
        <tr>
          <td style="color: var(--text-tertiary); font-size: 0.75rem;">${rowNo}</td>
          <td class="mono-tag" style="font-weight: 700; color: var(--accent-orange);">${r.case_id}</td>
          <td><span class="badge-pill ${pillClass}">${r.deletion_status}</span></td>
          <td><span style="font-weight: 600; font-size: 0.8rem;">${r.steps_count} steps</span></td>
          <td><code style="font-size: 0.72rem; color: #38bdf8; background: rgba(56, 189, 248, 0.08); padding: 2px 6px; border-radius: 4px; word-break: break-all;">${snippet}</code></td>
          <td style="text-align: right;">
            <button class="btn-action btn-outline btn-icon-only" title="Inspect Full Dossier" onclick="closeOutputModal(); inspectCase('${r.case_id}')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--status-incomplete); padding: 2rem;">Error: ${err.message}</td></tr>`;
  }
}

async function fetchOutputRaw() {
  const box = document.getElementById('output-raw-text');
  box.innerText = "Loading raw CSV lines...";
  try {
    const res = await fetch(`${API_BASE}/api/output/raw?limit=200`);
    if (!res.ok) throw new Error("Failed to fetch raw CSV");
    const data = await res.json();
    box.innerText = data.content;
    outputState.rawLoaded = true;
  } catch (err) {
    box.innerText = `Failed to load raw CSV: ${err.message}`;
  }
}

function copyRawOutput() {
  const text = document.getElementById('output-raw-text').innerText;
  navigator.clipboard.writeText(text).then(() => {
    showToast("Raw CSV text copied to clipboard!", "success");
  });
}

// Attach handlers to window for inline onclick attributes
window.switchNavTab = switchNavTab;
window.selectDataset = selectDataset;
window.selectStatusFilter = selectStatusFilter;
window.onSearchInput = onSearchInput;
window.paginate = paginate;
window.inspectCase = inspectCase;
window.closeInspectorDrawer = closeInspectorDrawer;
window.reAuditSingleCase = reAuditSingleCase;
window.triggerFullAudit = triggerFullAudit;
window.refreshBenchmark = refreshBenchmark;
window.selectEvidenceFile = selectEvidenceFile;
window.viewEvidenceInCatalog = viewEvidenceInCatalog;
window.copyEvidenceSnippet = copyEvidenceSnippet;
window.triggerPackaging = triggerPackaging;
window.checkBackendHealth = checkBackendHealth;
window.openOutputModal = openOutputModal;
window.closeOutputModal = closeOutputModal;
window.setOutputViewMode = setOutputViewMode;
window.handleOutputSearch = handleOutputSearch;
window.handleOutputFilter = handleOutputFilter;
window.changeOutputPage = changeOutputPage;
window.copyRawOutput = copyRawOutput;


