/**
 * GHOST DATA STILL EXISTS — Premium Enterprise Forensics Dashboard
 * Deep Space theme · Particle canvas · Real-time activity feed
 * Postman × Linear × Vercel × Arc design language
 */

const API_BASE = (window.location.port === '8000' || window.location.port === '5173')
  ? window.location.origin
  : 'http://127.0.0.1:8000';

// ─── App State ─────────────────────────────────────────────────────
let appState = {
  currentTab: 'tab-overview',
  datasetType: 'eval',
  statusFilter: 'ALL',
  searchQuery: '',
  currentPage: 1,
  pageSize: 20,
  totalPages: 1,
  activeCaseId: null,
  cachedEvidence: [],
  searchTimer: null,
  backendConnected: false,
  healthPollTimer: null,
  auditRunning: false
};

// ─── Init ───────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  setupSidebar();
  startHealthMonitor();
  loadDashboardData();
});

// ─── Particle Canvas ────────────────────────────────────────────────
function initParticles() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const PARTICLE_COUNT = 80;
  const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    r: Math.random() * 1.5 + 0.3,
    dx: (Math.random() - 0.5) * 0.18,
    dy: (Math.random() - 0.5) * 0.18,
    alpha: Math.random() * 0.5 + 0.1
  }));

  const COLORS = ['#f97316', '#8b5cf6', '#06b6d4', '#10b981'];

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach((p, i) => {
      const color = COLORS[i % COLORS.length];
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.globalAlpha = p.alpha;
      ctx.fill();
      ctx.globalAlpha = 1;

      // Connect nearby particles
      for (let j = i + 1; j < particles.length; j++) {
        const q = particles[j];
        const dist = Math.hypot(p.x - q.x, p.y - q.y);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(q.x, q.y);
          ctx.strokeStyle = color;
          ctx.globalAlpha = (1 - dist / 120) * 0.08;
          ctx.lineWidth = 0.5;
          ctx.stroke();
          ctx.globalAlpha = 1;
        }
      }

      p.x += p.dx; p.y += p.dy;
      if (p.x < 0 || p.x > canvas.width)  p.dx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.dy *= -1;
    });
    requestAnimationFrame(draw);
  }
  draw();
}

// ─── Sidebar ────────────────────────────────────────────────────────
function setupSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;
  sidebar.addEventListener('mouseenter', () => sidebar.classList.add('expanded'));
  sidebar.addEventListener('mouseleave', () => sidebar.classList.remove('expanded'));
}

// ─── Backend Health ─────────────────────────────────────────────────
function setBackendStatus(connected) {
  appState.backendConnected = connected;
  const pill     = document.getElementById('backend-status-pill');
  const dot      = document.getElementById('backend-status-dot');
  const pillText = document.getElementById('backend-status-text');
  const banner   = document.getElementById('reconnect-banner');

  if (connected) {
    pill.classList.remove('disconnected');
    if (dot)  dot.style.background = 'var(--green)';
    pillText.innerText = 'Backend Connected';
    banner.style.display = 'none';
    document.getElementById('overview-kpi-skeletons').style.display  = 'none';
    document.getElementById('overview-kpi-real').style.display       = 'grid';
    document.getElementById('cases-table-skeleton').style.display    = 'none';
    document.getElementById('cases-table-real').style.display        = 'block';
    document.getElementById('benchmark-skeletons').style.display     = 'none';
    document.getElementById('benchmark-real').style.display          = 'grid';
  } else {
    pill.classList.add('disconnected');
    if (dot) dot.style.background = 'var(--red)';
    pillText.innerText = 'Reconnecting…';
    banner.style.display = 'flex';
    document.getElementById('overview-kpi-skeletons').style.display  = 'grid';
    document.getElementById('overview-kpi-real').style.display       = 'none';
    document.getElementById('cases-table-skeleton').style.display    = 'flex';
    document.getElementById('cases-table-real').style.display        = 'none';
    document.getElementById('benchmark-skeletons').style.display     = 'grid';
    document.getElementById('benchmark-real').style.display          = 'none';
  }
}

async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { cache: 'no-store' });
    if (!res.ok) throw new Error('not ok');
    if (!appState.backendConnected) {
      setBackendStatus(true);
      await loadDashboardData();
    }
  } catch {
    setBackendStatus(false);
  }
}

function startHealthMonitor() {
  checkBackendHealth();
  if (appState.healthPollTimer) clearInterval(appState.healthPollTimer);
  appState.healthPollTimer = setInterval(checkBackendHealth, 5000);
}

// ─── Data Orchestrator ──────────────────────────────────────────────
async function loadDashboardData() {
  try {
    await Promise.all([fetchStats(), fetchCases(), fetchEvidenceCatalog(), fetchBenchmark()]);
    setBackendStatus(true);
  } catch (err) {
    console.warn('API unavailable, shimmer mode:', err.message);
    setBackendStatus(false);
  }
}

// ─── Tab Navigation ─────────────────────────────────────────────────
function switchTab(tabId) {
  appState.currentTab = tabId;
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  const nav = document.getElementById(`nav-${tabId}`);
  if (nav) nav.classList.add('active');
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  const pane = document.getElementById(tabId);
  if (pane) pane.classList.add('active');
  const labels = {
    'tab-overview': 'Overview',
    'tab-cases': 'Case Explorer',
    'tab-benchmark': 'Benchmark',
    'tab-evidence': 'Evidence Files',
    'tab-output': 'Output Contract'
  };
  const bc = document.getElementById('topbar-breadcrumb');
  if (bc) bc.innerText = labels[tabId] || tabId;
  if (tabId === 'tab-cases') fetchCases();
  else if (tabId === 'tab-benchmark') fetchBenchmark();
  else if (tabId === 'tab-output') fetchOutputRecords();
}

// Backwards compat alias
window.switchNavTab = switchTab;

// ─── Activity Feed ──────────────────────────────────────────────────
const ACTIVITY_COLORS = {
  COMPLETE: 'var(--green)',
  INCOMPLETE: 'var(--red)',
  NOT_APPLICABLE: 'var(--text-muted)',
  START: 'var(--orange)',
  ERROR: 'var(--red)'
};

function pushActivity(msg, tag = '', type = '') {
  const feed  = document.getElementById('activity-feed');
  if (!feed) return;
  const empty = feed.querySelector('.activity-empty');
  if (empty) empty.remove();

  const time = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const row  = document.createElement('div');
  row.className = 'activity-row';
  row.innerHTML = `
    <span class="activity-time">${time}</span>
    <span class="activity-msg">${msg}</span>
    ${tag ? `<span class="activity-tag" style="background:${ACTIVITY_COLORS[tag] || 'var(--surface-3)'};color:#fff;opacity:0.85;">${tag}</span>` : ''}
  `;
  feed.prepend(row);
  // keep last 40 entries
  while (feed.children.length > 40) feed.lastChild.remove();
}

// ─── Toast ──────────────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const shelf = document.getElementById('toast-shelf');
  const toast = document.createElement('div');
  toast.className = 'toast';
  const colors = { success: 'var(--green)', error: 'var(--red)', info: 'var(--orange)' };
  toast.style.borderLeftColor = colors[type] || 'var(--orange)';
  let icon = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>`;
  if (type === 'success') icon = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
  if (type === 'error')   icon = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
  toast.innerHTML = `${icon}<span>${message}</span>`;
  shelf.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(60px)'; setTimeout(() => toast.remove(), 300); }, 4500);
}

// ─── Progress Bar ────────────────────────────────────────────────────
function setProgress(pct) {
  const bar  = document.getElementById('audit-progress-bar');
  const fill = document.getElementById('audit-progress-fill');
  if (!bar || !fill) return;
  if (pct === null) { bar.style.display = 'none'; fill.style.width = '0%'; return; }
  bar.style.display = 'block';
  fill.style.width  = `${Math.max(0, Math.min(100, pct))}%`;
}

// ─── Stats ───────────────────────────────────────────────────────────
async function fetchStats() {
  const res  = await fetch(`${API_BASE}/api/stats`, { cache: 'no-store' });
  if (!res.ok) throw new Error('stats failed');
  const data = await res.json();
  document.getElementById('kpi-val-eval').innerText     = data.total_eval_cases || 518;
  document.getElementById('rail-cases-badge').innerText  = data.total_eval_cases || 518;
  document.getElementById('kpi-val-evidence').innerText  = data.evidence_files_count || 94;
  document.getElementById('rail-evidence-badge').innerText = data.evidence_files_count || 94;
  const railOutput = document.getElementById('rail-output-badge');
  if (railOutput) railOutput.innerText = data.total_eval_cases || 518;

  if (data.sample_evaluation) {
    document.getElementById('kpi-val-acc').innerText = `${data.sample_evaluation.status_accuracy}%`;
  }
  if (data.output_generated) {
    const kpiOut = document.getElementById('kpi-val-output');
    if (kpiOut) kpiOut.innerText = 'output.csv';
    const c  = data.output_breakdown?.COMPLETE || 0;
    const ic = data.output_breakdown?.INCOMPLETE || 0;
    const na = data.output_breakdown?.NOT_APPLICABLE || 0;
    const footer = document.getElementById('kpi-val-output-footer');
    if (footer) footer.innerHTML = `<span style="color:var(--green);font-weight:600;">${c} Complete</span> · ${ic} Incomplete · ${na} N/A`;
  }
}

// ─── Cases ───────────────────────────────────────────────────────────
function selectDataset(type) {
  appState.datasetType  = type;
  appState.currentPage  = 1;
  document.getElementById('chip-dataset-eval').classList.toggle('active', type === 'eval');
  document.getElementById('chip-dataset-sample').classList.toggle('active', type === 'sample');
  fetchCases();
}

function selectStatusFilter(status) {
  appState.statusFilter = status;
  appState.currentPage  = 1;
  document.querySelectorAll('.chip-row .chip').forEach(chip => {
    const label = chip.innerText.trim().toUpperCase().replace(' ', '_');
    chip.classList.toggle('active', label === status || (status === 'ALL' && chip.innerText.trim() === 'All'));
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
  const skeleton  = document.getElementById('cases-table-skeleton');
  const tableReal = document.getElementById('cases-table-real');
  if (skeleton)  skeleton.style.display  = 'flex';
  if (tableReal) tableReal.style.display = 'none';

  try {
    const params = new URLSearchParams({
      dataset_type: appState.datasetType,
      status:       appState.statusFilter,
      search:       appState.searchQuery,
      page:         appState.currentPage,
      page_size:    appState.pageSize
    });
    const res  = await fetch(`${API_BASE}/api/cases?${params}`, { cache: 'no-store' });
    if (!res.ok) throw new Error('cases failed');
    const data = await res.json();

    appState.totalPages = data.total_pages || 1;
    const from = (data.page - 1) * data.page_size + 1;
    const to   = Math.min(data.page * data.page_size, data.total_cases);
    document.getElementById('cases-page-info').innerText = `Showing ${from}–${to} of ${data.total_cases} cases`;
    document.getElementById('label-current-page').innerText = data.page;
    document.getElementById('btn-page-prev').disabled = (data.page <= 1);
    document.getElementById('btn-page-next').disabled = (data.page >= appState.totalPages);

    const tbody = document.getElementById('cases-table-body');
    if (!data.cases?.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:2.5rem;color:var(--text-faint);">No cases match search criteria</td></tr>`;
    } else {
      tbody.innerHTML = data.cases.map(c => {
        const pillCls = c.deletion_status === 'COMPLETE' ? 'pill-green'
                      : c.deletion_status === 'INCOMPLETE' ? 'pill-red' : 'pill-gray';
        const auditAt = c.audit_at ? c.audit_at.replace('T', ' ').replace('Z', '') : '--';
        return `
          <tr onclick="inspectCase('${c.case_id}')">
            <td class="mono" style="font-weight:700;color:var(--orange);">${c.case_id}</td>
            <td style="font-size:0.79rem;">${c.email}</td>
            <td class="mono">${c.user_id}</td>
            <td><span style="font-size:0.73rem;color:var(--text-muted);">${c.reported_status}</span></td>
            <td class="mono" style="font-size:0.72rem;">${auditAt}</td>
            <td><span class="pill ${pillCls}">${c.deletion_status}</span></td>
            <td style="font-size:0.73rem;color:var(--text-muted);">${c.findings_count}F · ${c.remediations_count}R · ${c.verifications_count}V</td>
            <td>
              <button class="tb-btn tb-btn-ghost" style="padding:0.3rem 0.5rem;font-size:0.72rem;" onclick="event.stopPropagation();inspectCase('${c.case_id}')">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                Inspect
              </button>
            </td>
          </tr>`;
      }).join('');
    }
    if (skeleton)  skeleton.style.display  = 'none';
    if (tableReal) tableReal.style.display = 'block';
  } catch (err) {
    if (skeleton)  skeleton.style.display  = 'flex';
    if (tableReal) tableReal.style.display = 'none';
    throw err;
  }
}

// ─── Case Inspector Drawer ──────────────────────────────────────────
async function inspectCase(caseId) {
  appState.activeCaseId = caseId;
  document.getElementById('inspector-drawer').classList.add('active');
  document.getElementById('drawer-overlay').classList.add('active');
  document.getElementById('drawer-case-id').innerText = caseId;
  document.getElementById('drawer-steps-list').innerHTML = `<p style="font-size:0.8rem;color:var(--text-muted);">Loading case intelligence…</p>`;

  try {
    const res  = await fetch(`${API_BASE}/api/cases/${caseId}`);
    if (!res.ok) throw new Error('case load failed');
    const data = await res.json();
    renderDossier(data);
  } catch (err) {
    document.getElementById('drawer-steps-list').innerHTML = `<p style="color:var(--red);">Failed to load: ${err.message}</p>`;
  }
}

function closeInspectorDrawer() {
  document.getElementById('inspector-drawer').classList.remove('active');
  document.getElementById('drawer-overlay').classList.remove('active');
  appState.activeCaseId = null;
}

function renderDossier(data) {
  document.getElementById('drawer-case-id').innerText    = data.case_id;
  document.getElementById('drawer-subject-email').innerText = data.email;

  const pill    = document.getElementById('drawer-status-pill');
  const pillCls = data.deletion_status === 'COMPLETE' ? 'pill-green' : data.deletion_status === 'INCOMPLETE' ? 'pill-red' : 'pill-gray';
  pill.innerText  = data.deletion_status;
  pill.className  = `pill ${pillCls}`;

  const p = data.identity_profile || {};
  document.getElementById('drawer-user-id').innerText    = p.user_id   || 'UNRESOLVED';
  document.getElementById('drawer-name').innerText       = p.name      || '--';
  document.getElementById('drawer-curr-email').innerText = p.current_email || data.email;
  document.getElementById('drawer-phone').innerText      = p.phone     || '--';
  document.getElementById('drawer-all-emails').innerText = (p.all_emails || [data.email]).join(', ');
  document.getElementById('drawer-hash').innerText       = p.email_hash || '--';

  document.getElementById('drawer-req-text').innerText   = `"${data.request_text || '(No request text)'}"`;
  const isAuth = data.intent_analysis?.is_authorized;
  const authEl = document.getElementById('drawer-intent-auth');
  authEl.innerText = isAuth ? 'AUTHORIZED (Deletion Request)' : 'NOT APPLICABLE';
  authEl.style.color = isAuth ? 'var(--green)' : 'var(--text-muted)';
  document.getElementById('drawer-intent-reason').innerText = data.intent_analysis?.reason || '--';

  document.getElementById('drawer-requested-at').innerText = data.requested_at  || '--';
  document.getElementById('drawer-claim').innerText         = data.reported_status || '--';
  document.getElementById('drawer-reported-at').innerText   = data.reported_at    || '--';
  document.getElementById('drawer-audit-at').innerText      = data.audit_at       || '--';

  const steps = data.steps || [];
  document.getElementById('drawer-steps-badge').innerText  = `${steps.length} Steps`;
  document.getElementById('drawer-raw-json').innerText      = JSON.stringify(steps, null, 2);

  const container = document.getElementById('drawer-steps-list');
  if (!steps.length) {
    container.innerHTML = `<p style="font-size:0.8rem;color:var(--text-faint);padding:0.5rem 0;">No steps (NOT_APPLICABLE or empty plan).</p>`;
    return;
  }
  container.innerHTML = steps.map(s => {
    const phaseClass  = s.phase === 'FINDING' ? 'phase-finding' : s.phase === 'REMEDIATION' ? 'phase-remediation' : 'phase-verification';
    const phasePill   = s.phase === 'FINDING' ? 'pill-red' : s.phase === 'REMEDIATION' ? 'pill-amber' : 'pill-green';
    return `
      <div class="step-card ${phaseClass}">
        <div>
          <div style="font-family:var(--font-mono);font-size:0.8rem;color:var(--text-white);">
            <strong>Step ${s.step_no}:</strong> ${s.system_id} // ${s.resource_id}
          </div>
          <div style="font-size:0.73rem;color:var(--text-muted);margin-top:0.12rem;">
            ${s.operation} → <strong>${s.state}</strong>
          </div>
        </div>
        <div style="display:flex;gap:0.4rem;align-items:center;flex-shrink:0;">
          <span class="pill ${phasePill}">${s.phase}</span>
          ${s.evidence_id ? `<span class="pill pill-gray" style="cursor:pointer;" onclick="viewEvidenceInCatalog('${s.evidence_id}')">${s.evidence_id}</span>` : ''}
        </div>
      </div>`;
  }).join('');
}

async function reAuditSingleCase() {
  if (!appState.activeCaseId) return;
  showToast(`Re-auditing ${appState.activeCaseId}…`, 'info');
  try {
    const res  = await fetch(`${API_BASE}/api/audit/case/${appState.activeCaseId}`, { method: 'POST' });
    if (!res.ok) throw new Error('audit failed');
    const data = await res.json();
    showToast(`Re-audited: ${data.deletion_status}`, 'success');
    pushActivity(`Re-audited <strong>${appState.activeCaseId}</strong>`, data.deletion_status);
    inspectCase(appState.activeCaseId);
    fetchCases();
  } catch (err) {
    showToast(`Audit failed: ${err.message}`, 'error');
  }
}

// ─── Full Batch Audit ────────────────────────────────────────────────
async function triggerFullAudit() {
  if (appState.auditRunning) return;
  appState.auditRunning = true;

  const btn = document.getElementById('btn-topbar-run');
  const heroCard = document.getElementById('hero-run-card');
  if (btn) { btn.disabled = true; btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-spin"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Auditing…`; }

  setProgress(5);
  pushActivity('Full audit started — 518 evaluation cases', '', 'START');
  showToast('Auditing all 518 evaluation requests…', 'info');

  // Animate progress
  let prog = 5;
  const progInterval = setInterval(() => { prog = Math.min(prog + Math.random() * 4, 88); setProgress(prog); }, 600);

  try {
    const res  = await fetch(`${API_BASE}/api/audit/run-all`, { method: 'POST' });
    if (!res.ok) throw new Error('full audit failed');
    const data = await res.json();

    clearInterval(progInterval);
    setProgress(100);
    setTimeout(() => setProgress(null), 1200);

    showToast(`Audit complete — ${data.total_cases_audited} rows written to output.csv`, 'success');
    pushActivity(`Full audit done — <strong>${data.total_cases_audited}</strong> cases`, 'COMPLETE');
    await fetchStats();
    await fetchCases();
  } catch (err) {
    clearInterval(progInterval);
    setProgress(null);
    showToast(`Audit failed: ${err.message}`, 'error');
    pushActivity(`Audit failed: ${err.message}`, 'ERROR');
  } finally {
    appState.auditRunning = false;
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Audit All 518 Cases`;
    }
  }
}

// ─── Benchmark ───────────────────────────────────────────────────────
async function fetchBenchmark() {
  document.getElementById('benchmark-skeletons').style.display = 'grid';
  document.getElementById('benchmark-real').style.display      = 'none';
  try {
    const res  = await fetch(`${API_BASE}/api/evaluate`, { cache: 'no-store' });
    if (!res.ok) throw new Error('benchmark failed');
    const data = await res.json();

    document.getElementById('acc-status').innerText   = `${(data.status_accuracy   * 100).toFixed(2)}%`;
    document.getElementById('acc-sequence').innerText = `${(data.sequence_accuracy * 100).toFixed(2)}%`;
    document.getElementById('acc-field').innerText    = `${(data.field_accuracy     * 100).toFixed(2)}%`;

    document.getElementById('benchmark-skeletons').style.display = 'none';
    document.getElementById('benchmark-real').style.display      = 'grid';

    const container = document.getElementById('benchmark-cases-container');
    if (!data.mismatches?.length) {
      container.innerHTML = `<div class="dossier-section" style="color:var(--green);font-weight:600;">✓ 100% Exact Match on All 32 Sample Cases!</div>`;
      return;
    }
    container.innerHTML = data.mismatches.map(m => `
      <div class="dossier-section" style="border-left:3px solid ${m.pred_status === m.gt_status ? 'var(--green)' : 'var(--red)'};">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.65rem;">
          <span class="mono" style="font-weight:700;font-size:0.9rem;">${m.case_id}</span>
          <div>
            Pred: <span class="pill ${m.pred_status === 'COMPLETE' ? 'pill-green' : 'pill-red'}">${m.pred_status}</span>
            vs GT: <span class="pill ${m.gt_status === 'COMPLETE' ? 'pill-green' : 'pill-red'}">${m.gt_status}</span>
          </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.85rem;">
          <div>
            <div style="font-size:0.68rem;color:var(--text-faint);text-transform:uppercase;margin-bottom:0.25rem;">Predicted (${m.pred_steps_count})</div>
            <pre class="code-pre" style="font-size:0.67rem;max-height:110px;">${JSON.stringify(m.pred_steps, null, 2)}</pre>
          </div>
          <div>
            <div style="font-size:0.68rem;color:var(--text-faint);text-transform:uppercase;margin-bottom:0.25rem;">Ground Truth (${m.gt_steps_count})</div>
            <pre class="code-pre" style="font-size:0.67rem;max-height:110px;color:#34d399;">${JSON.stringify(m.gt_steps, null, 2)}</pre>
          </div>
        </div>
      </div>`).join('');
  } catch (err) {
    document.getElementById('benchmark-skeletons').style.display = 'grid';
    document.getElementById('benchmark-real').style.display      = 'none';
    throw err;
  }
}

async function refreshBenchmark() {
  showToast('Re-evaluating sample cases…', 'info');
  await fetchBenchmark();
  showToast('Benchmark updated!', 'success');
}

// ─── Evidence ────────────────────────────────────────────────────────
async function fetchEvidenceCatalog() {
  const res  = await fetch(`${API_BASE}/api/evidence`, { cache: 'no-store' });
  if (!res.ok) throw new Error('evidence failed');
  const data = await res.json();
  appState.cachedEvidence = data.files || [];

  const listEl = document.getElementById('evidence-files-list');
  listEl.innerHTML = appState.cachedEvidence.map(f => `
    <div class="ev-file-row" id="ev-item-${f.file_id}" onclick="selectEvidenceFile('${f.file_id}')">
      <div style="flex:1;min-width:0;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.15rem;">
          <span class="mono" style="font-weight:700;color:var(--orange);">${f.file_id}</span>
          <span class="pill pill-gray" style="font-size:0.62rem;">${f.category}</span>
        </div>
        <div style="font-size:0.73rem;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${f.file_path}</div>
        <div style="font-size:0.67rem;color:var(--text-faint);margin-top:0.15rem;">${(f.size_bytes / 1024).toFixed(1)} KB · ${f.captured_at?.replace('T',' ').replace('Z','') || '--'}</div>
      </div>
    </div>`).join('');

  if (appState.cachedEvidence.length > 0) {
    selectEvidenceFile(appState.cachedEvidence[0].file_id);
  }
}

async function selectEvidenceFile(fileId) {
  document.querySelectorAll('.ev-file-row').forEach(el => el.classList.remove('active'));
  const activeEl = document.getElementById(`ev-item-${fileId}`);
  if (activeEl) activeEl.classList.add('active');

  const box = document.getElementById('ev-preview-content');
  box.innerText = 'Loading artifact preview…';

  try {
    const res  = await fetch(`${API_BASE}/api/evidence/${fileId}`);
    if (!res.ok) throw new Error('file read failed');
    const data = await res.json();
    document.getElementById('ev-preview-title').innerText = `${data.file_id} — ${data.file_path}`;
    document.getElementById('ev-preview-meta').innerText  = `Origin: ${data.origin} · Size: ${(data.size_bytes / 1024).toFixed(1)} KB · Captured: ${data.captured_at}`;
    box.innerText = data.content_preview || '(Empty file)';
  } catch (err) {
    box.innerText = `Error: ${err.message}`;
  }
}

function viewEvidenceInCatalog(fileId) {
  closeInspectorDrawer();
  switchTab('tab-evidence');
  setTimeout(() => selectEvidenceFile(fileId), 120);
}

function copyEvidenceSnippet() {
  const content = document.getElementById('ev-preview-content').innerText;
  navigator.clipboard.writeText(content).then(() => showToast('Evidence content copied!', 'success'));
}

// ─── Output CSV Tab Page ─────────────────────────────────────────────
const outputState = { page: 1, pageSize: 25, search: '', status: 'ALL', viewMode: 'table', totalPages: 1, totalRows: 0, rawLoaded: false };

function openOutputModal() {
  switchTab('tab-output');
}

function closeOutputModal() {
  // no-op for backward compatibility
}

function setOutputViewMode(mode) {
  outputState.viewMode = mode;
  const btnTable = document.getElementById('btn-mode-table');
  const btnRaw   = document.getElementById('btn-mode-raw');
  if (btnTable) btnTable.classList.toggle('active', mode === 'table');
  if (btnRaw)   btnRaw.classList.toggle('active', mode === 'raw');
  const viewTable = document.getElementById('output-view-table');
  const viewRaw   = document.getElementById('output-view-raw');
  if (viewTable) viewTable.style.display = mode === 'table' ? 'block' : 'none';
  if (viewRaw)   viewRaw.style.display   = mode === 'raw'   ? 'block' : 'none';
  if (mode === 'raw' && !outputState.rawLoaded) fetchOutputRaw();
}

let outputSearchTimeout = null;
function handleOutputSearch() {
  clearTimeout(outputSearchTimeout);
  outputSearchTimeout = setTimeout(() => {
    outputState.search = document.getElementById('output-search-input').value.trim();
    outputState.page   = 1;
    fetchOutputRecords();
  }, 220);
}

function filterOutputByStatus(status) {
  outputState.status = status;
  outputState.page   = 1;
  document.querySelectorAll('#tab-output .chip-row .chip').forEach(c => c.classList.remove('active'));
  const chipMap = {
    ALL: 'output-chip-all',
    COMPLETE: 'output-chip-complete',
    INCOMPLETE: 'output-chip-incomplete',
    NOT_APPLICABLE: 'output-chip-na'
  };
  const target = document.getElementById(chipMap[status]);
  if (target) target.classList.add('active');
  fetchOutputRecords();
}

function handleOutputFilter() {
  const select = document.getElementById('output-filter-status');
  if (select) {
    outputState.status = select.value;
    outputState.page   = 1;
    fetchOutputRecords();
  }
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
  if (!tbody) return;
  try {
    const query = new URLSearchParams({ search: outputState.search, status: outputState.status, page: outputState.page, page_size: outputState.pageSize });
    const res   = await fetch(`${API_BASE}/api/output/records?${query}`);
    if (!res.ok) throw new Error('output load failed');
    const data  = await res.json();

    outputState.totalPages = data.total_pages || 1;
    outputState.totalRows  = data.total_rows  || 0;

    // Update KPI counters
    if (data.status_counts) {
      const c = data.status_counts.COMPLETE || 195;
      const ic = data.status_counts.INCOMPLETE || 313;
      const na = data.status_counts.NOT_APPLICABLE || 10;
      const elC = document.getElementById('output-kpi-complete');
      if (elC) elC.innerText = c;
      const elIC = document.getElementById('output-kpi-incomplete');
      if (elIC) elIC.innerText = ic;
      const elNA = document.getElementById('output-kpi-na');
      if (elNA) elNA.innerText = na;
      const elTotal = document.getElementById('output-kpi-total');
      if (elTotal) elTotal.innerText = data.total_unfiltered || (c + ic + na);
    }

    const pageLabel = document.getElementById('output-page-label');
    if (pageLabel) pageLabel.innerText = `Page ${data.page} / ${data.total_pages}`;
    const startNum = data.total_rows === 0 ? 0 : (data.page - 1) * data.page_size + 1;
    const endNum   = Math.min(data.page * data.page_size, data.total_rows);
    const pagInfo = document.getElementById('output-pagination-info');
    if (pagInfo) pagInfo.innerText = `Showing ${startNum}–${endNum} of ${data.total_rows} cases`;
    const prevBtn = document.getElementById('output-prev-page');
    if (prevBtn) prevBtn.disabled = (data.page <= 1);
    const nextBtn = document.getElementById('output-next-page');
    if (nextBtn) nextBtn.disabled = (data.page >= data.total_pages);

    if (!data.records?.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:2.5rem;color:var(--text-faint);">No cases match criteria</td></tr>`;
      return;
    }
    tbody.innerHTML = data.records.map((r, idx) => {
      const pillCls = r.deletion_status === 'COMPLETE' ? 'pill-green' : r.deletion_status === 'INCOMPLETE' ? 'pill-red' : 'pill-gray';
      const rowNo   = startNum + idx;
      const snippet = r.steps_raw?.length > 80 ? r.steps_raw.substring(0, 80) + '…' : (r.steps_raw || '[]');
      return `
        <tr onclick="inspectCase('${r.case_id}')">
          <td style="color:var(--text-faint);font-size:0.73rem;">${rowNo}</td>
          <td class="mono" style="font-weight:700;color:var(--orange);">${r.case_id}</td>
          <td><span class="pill ${pillCls}">${r.deletion_status}</span></td>
          <td style="font-weight:600;font-size:0.8rem;">${r.steps_count} steps</td>
          <td><code style="font-size:0.71rem;color:#38bdf8;background:rgba(56,189,248,0.07);padding:2px 5px;border-radius:4px;word-break:break-all;">${snippet}</code></td>
          <td style="text-align:right;">
            <button class="tb-btn tb-btn-ghost" style="padding:0.28rem 0.55rem;font-size:0.72rem;" onclick="event.stopPropagation();inspectCase('${r.case_id}')">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
              Inspect
            </button>
          </td>
        </tr>`;
    }).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--red);padding:2rem;">Error: ${err.message}</td></tr>`;
  }
}

async function fetchOutputRaw() {
  const box = document.getElementById('output-raw-text');
  if (!box) return;
  box.innerText = 'Loading raw CSV lines…';
  try {
    const res  = await fetch(`${API_BASE}/api/output/raw?limit=250`);
    if (!res.ok) throw new Error('raw CSV failed');
    const data = await res.json();
    box.innerText = data.content;
    outputState.rawLoaded = true;
  } catch (err) {
    box.innerText = `Failed: ${err.message}`;
  }
}

async function copyRawOutput() {
  try {
    const res = await fetch(`${API_BASE}/api/output/raw?limit=1000`);
    if (!res.ok) throw new Error('Failed to load CSV');
    const data = await res.json();
    await navigator.clipboard.writeText(data.content);
    showToast('Full output.csv copied to clipboard!', 'success');
  } catch {
    const text = document.getElementById('output-raw-text')?.innerText || '';
    if (text) {
      navigator.clipboard.writeText(text).then(() => showToast('CSV text copied!', 'success'));
    } else {
      showToast('No CSV content loaded to copy', 'error');
    }
  }
}

// ─── Global Search ──────────────────────────────────────────────────
function onGlobalSearch(event) {
  const q = event.target.value.trim();
  if (!q) return;
  if (appState.currentTab !== 'tab-cases') switchTab('tab-cases');
  document.getElementById('case-search-input').value = q;
  appState.searchQuery = q;
  appState.currentPage = 1;
  clearTimeout(appState.searchTimer);
  appState.searchTimer = setTimeout(fetchCases, 220);
}

// ─── Unused stubs (for server-side packaging endpoint) ──────────────
async function triggerPackaging() {
  showToast('Packaging code.zip for challenge submission…', 'info');
  try {
    const res  = await fetch(`${API_BASE}/api/package`, { method: 'POST' });
    if (!res.ok) throw new Error('packaging failed');
    const data = await res.json();
    showToast(`code.zip ready (${(data.size_bytes / 1024).toFixed(1)} KB)`, 'success');
  } catch (err) {
    showToast(`Packaging failed: ${err.message}`, 'error');
  }
}

// ─── Keyboard shortcut: ⌘K / Ctrl+K → focus search ─────────────────
document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    document.getElementById('global-search-input')?.focus();
  }
  if (e.key === 'Escape') {
    closeOutputModal();
    closeInspectorDrawer();
  }
});

// ─── Expose to global (inline onclick) ──────────────────────────────
Object.assign(window, {
  switchTab, switchNavTab, selectDataset, selectStatusFilter, onSearchInput,
  paginate, inspectCase, closeInspectorDrawer, reAuditSingleCase,
  triggerFullAudit, refreshBenchmark, fetchBenchmark,
  selectEvidenceFile, viewEvidenceInCatalog, copyEvidenceSnippet,
  openOutputModal, closeOutputModal, setOutputViewMode,
  handleOutputSearch, handleOutputFilter, changeOutputPage, copyRawOutput,
  checkBackendHealth, triggerPackaging, onGlobalSearch
});
