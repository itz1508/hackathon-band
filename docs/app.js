/** ProofGate for Band — direct submission and live workflow processing. */

/* ============================================================
   STAGE DEFINITIONS — one row per logical stage
   ============================================================ */
const WORKFLOW_STAGES = [
  { key: 'human-request', label: 'Human Request', summary: 'Request submitted' },
  { key: 'intake', label: 'Intake', summary: 'Structured request created' },
  { key: 'planner', label: 'Plan', summary: 'Success criteria defined' },
  { key: 'resolution', label: 'Resolution', summary: 'Checking the proposed result against requirements' },
  { key: 'issue-isolator', label: 'Issue Isolation', summary: 'Locating the exact failure', optional: true },
  { key: 'resolution-retry', label: 'Resolution Retry', summary: 'Applying the focused correction', optional: true },
  { key: 'finalizing', label: 'Finalizing', summary: 'Final result delivered' },
];

/* Stage state machine: waiting → thinking → processing → completed|failed */
const STAGE_LABELS = {
  waiting: 'WAITING',
  thinking: 'THINKING',
  processing: 'PROCESSING',
  completed: 'COMPLETED',
  failed: 'FAILED',
  not_used: 'NOT USED',
};

const STAGE_SUMMARIES = {
  'human-request': { waiting: 'Waiting', thinking: 'Preparing request', processing: 'Submitting', completed: 'Request submitted', failed: 'Submission failed' },
  'intake': { waiting: 'Waiting for request', thinking: 'Preparing structured output', processing: 'Building intake record', completed: 'Structured request created', failed: 'Intake failed' },
  'planner': { waiting: 'Waiting for Intake handoff', thinking: 'Preparing success requirements', processing: 'Validating scope and building the Resolution handoff', completed: 'Success criteria defined and sent to Resolution', failed: 'Planning failed' },
  'resolution': { waiting: 'Waiting for Plan handoff', thinking: 'Checking requirements', processing: 'Checking the proposed result against requirements', completed: 'Requirements met', failed: 'One or more requirements were not met' },
  'issue-isolator': { waiting: 'Waiting for failure data', thinking: 'Locating the exact failure', processing: 'Building a focused recovery handoff', completed: 'Failure isolated and retry handoff created', failed: 'Isolation failed', not_used: 'Not required' },
  'resolution-retry': { waiting: 'Waiting for isolation handoff', thinking: 'Preparing focused correction', processing: 'Applying the focused correction', completed: 'Focused correction passed validation', failed: 'Focused correction did not satisfy requirements', not_used: 'Not required' },
  'finalizing': { waiting: 'Waiting for Resolution', thinking: 'Preparing final delivery', processing: 'Delivering terminal result', completed: 'Final result delivered', failed: 'Delivery failed' },
};

/* Event reason → which stage it affects and what state */
const EVENT_TO_STAGE = {
  'new_request': { stage: 'human-request', state: 'completed' },
  'intake_complete': { stage: 'intake', state: 'completed' },
  'plan_complete': { stage: 'planner', state: 'completed' },
  'requirements_met': { stage: 'resolution', state: 'completed' },
  'requirements_not_met': { stage: 'resolution', state: 'failed' },
  'focused_retry': { stage: 'issue-isolator', state: 'completed' },
  'retry_exhausted': { stage: 'resolution-retry', state: 'failed' },
  'terminal_result': { stage: 'finalizing', state: 'completed' },
};

/* Map to_role in events to which stage is now receiving work */
const ROLE_TO_STAGE = {
  'intake': 'intake',
  'planner': 'planner',
  'resolution': 'resolution',
  'issue-isolator': 'issue-isolator',
  'finalizing': 'finalizing',
  'human': 'finalizing',
};

const COMMANDS = [
  { id: 'fix', label: 'Fix', template: 'Fix the following issue: [describe the problem and target file].' },
  { id: 'review', label: 'Review', template: 'Review the following target: [target file or path]. Focus on: [what to look for].' },
];

let selectedRun = null;
let pollTimer = null;
let runtimeOn = false;
let readiness = { send_enabled: false };
let submissionPending = false;
let activeObjective = '';
let activeRunId = '';
let lastSequence = 0;
let selectedConstraints = [];

/* Stage state tracking — deduplicated */
let stageStates = {};

document.addEventListener('DOMContentLoaded', async () => {
  renderCommands();
  initTextarea();
  initActions();
  initRuntime();
  resetStageStates();
  renderWorkflow();
  await Promise.all([loadTestInputs(), checkStatus()]);
});

function resetStageStates() {
  stageStates = {};
  WORKFLOW_STAGES.forEach(s => {
    stageStates[s.key] = { status: 'waiting', updated_at: null };
  });
}

/* ============================================================
   STAGE STATE COMPUTATION FROM EVENTS (deduplication)
   ============================================================ */
function computeStageStates() {
  resetStageStates();
  if (!selectedRun) {
    if (submissionPending) {
      stageStates['human-request'].status = 'processing';
    }
    return;
  }

  const events = selectedRun.conversation_events || [];
  const results = selectedRun.stage_results || {};
  const path = selectedRun.workflow_path || [];
  const outcome = selectedRun.outcome || '';

  // Human request is always completed once we have a run
  stageStates['human-request'].status = 'completed';

  // Walk events to determine transitions (deduplicated by stage)
  const seenReasons = new Set();
  for (const ev of events) {
    const reason = ev.event || '';
    if (seenReasons.has(reason)) continue; // deduplicate
    seenReasons.add(reason);

    const mapping = EVENT_TO_STAGE[reason];
    if (mapping) {
      stageStates[mapping.stage].status = mapping.state;
      stageStates[mapping.stage].updated_at = ev.timestamp;
    }
  }

  // Use stage_results from the run data to fill in
  for (const [key, result] of Object.entries(results)) {
    const stageKey = key === 'issue_isolation' ? 'issue-isolator' : key;
    if (stageStates[stageKey]) {
      if (result.role_success) {
        stageStates[stageKey].status = 'completed';
      } else if (result.role_success === false) {
        stageStates[stageKey].status = 'failed';
      }
    }
  }

  // Determine current processing stage from workflow_path
  if (!outcome && path.length > 0) {
    const current = path[path.length - 1];
    const currentKey = current === 'issue_isolation' ? 'issue-isolator' : current;
    if (stageStates[currentKey] && stageStates[currentKey].status === 'waiting') {
      stageStates[currentKey].status = 'processing';
    }
  }

  // If terminal, mark finalizing as completed
  if (outcome) {
    stageStates['finalizing'].status = 'completed';
  }

  // Mark optional stages as not_used if terminal and they never activated
  if (outcome) {
    if (stageStates['issue-isolator'].status === 'waiting') {
      stageStates['issue-isolator'].status = 'not_used';
    }
    if (stageStates['resolution-retry'].status === 'waiting') {
      stageStates['resolution-retry'].status = 'not_used';
    }
  }

  // If resolution failed and issue-isolator hasn't been marked, set it processing
  if (stageStates['resolution'].status === 'failed') {
    if (stageStates['issue-isolator'].status === 'waiting') {
      stageStates['issue-isolator'].status = 'processing';
    }
    // If isolation completed, resolution-retry should be processing
    if (stageStates['issue-isolator'].status === 'completed' && stageStates['resolution-retry'].status === 'waiting') {
      stageStates['resolution-retry'].status = 'processing';
    }
  }

  // Advance waiting stages that should be thinking/processing based on predecessor completion
  const order = WORKFLOW_STAGES.map(s => s.key);
  for (let i = 1; i < order.length; i++) {
    const prev = order[i - 1];
    const curr = order[i];
    // Skip optional stages in the chain for advancement
    if (stageStates[prev].status === 'completed' && stageStates[curr].status === 'waiting') {
      // Only auto-advance if this stage is in the path or is next logically
      if (path.includes(curr) || path.includes(curr.replace('-', '_'))) {
        stageStates[curr].status = 'processing';
      }
    }
  }
}

function getStageSummary(stageKey, status) {
  const summaries = STAGE_SUMMARIES[stageKey];
  if (!summaries) return '';
  return summaries[status] || summaries['waiting'] || '';
}

/* ============================================================
   COMMANDS
   ============================================================ */
function renderCommands() {
  const grid = document.getElementById('command-grid');
  grid.innerHTML = COMMANDS.map(command =>
    `<button class="cmd-btn" data-cmd="${command.id}">${command.label}</button>`
  ).join('');
  grid.addEventListener('click', event => {
    const button = event.target.closest('.cmd-btn');
    if (!button) return;
    const command = COMMANDS.find(item => item.id === button.dataset.cmd);
    if (!command) return;
    selectedConstraints = [];
    const input = document.getElementById('chat-input');
    input.value = command.template;
    input.focus();
    updatePreview();
    updateSendState();
  });
}

async function loadTestInputs() {
  const container = document.getElementById('test-input-list');
  try {
    const response = await fetch('/internal/test-inputs');
    const data = response.ok ? await response.json() : { items: [] };
    if (!data.items?.length) {
      container.innerHTML = '<span class="op-empty">No test inputs</span>';
      return;
    }
    container.innerHTML = data.items.map(item =>
      `<button class="test-input-item" data-request="${esc(item.request_text)}" data-constraints="${esc(JSON.stringify(item.constraints || []))}" data-path="${esc(item.path || '')}">
        <span class="ti-label">${esc(item.label)}</span>
        <span class="ti-meta">${esc(item.expected_outcome)}</span>
      </button>`
    ).join('');
    container.querySelectorAll('.test-input-item').forEach(item => {
      item.addEventListener('click', async () => {
        const input = document.getElementById('chat-input');
        input.value = item.dataset.request;
        selectedConstraints = JSON.parse(item.dataset.constraints || '[]');
        input.focus();
        updatePreview();
        updateSendState();
        // Load demo run if available
        const path = item.dataset.path;
        if (path) {
          try {
            const resp = await fetch(`/${path}`);
            if (resp.ok) {
              const data = await resp.json();
              if (data.demo_run) {
                selectedRun = data.demo_run;
                activeRunId = data.demo_run.run_id || '';
                renderRun();
              }
            }
          } catch (_e) { /* ignore */ }
        }
      });
    });
  } catch (_error) {
    container.innerHTML = '<span class="op-empty">Test inputs unavailable</span>';
  }
}

function initTextarea() {
  document.getElementById('chat-input').addEventListener('input', () => {
    selectedConstraints = [];
    updatePreview();
    updateSendState();
  });
}

function updatePreview() {
  const text = document.getElementById('chat-input').value.trim();
  document.getElementById('routing-preview').innerHTML = text
    ? `<span class="preview-label">Direct route:</span> <code class="preview-content">UI → Band → @itz1508/intake</code>`
    : '';
}

function updateSendState() {
  const button = document.getElementById('chat-send');
  const hasText = Boolean(document.getElementById('chat-input').value.trim());
  button.disabled = !hasText || !readiness.send_enabled || submissionPending;
}

function initActions() {
  document.getElementById('chat-send').addEventListener('click', sendToBand);
  document.getElementById('chat-open-room').addEventListener('click', openRoom);
}

async function sendToBand() {
  if (submissionPending) return;
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;

  submissionPending = true;
  activeObjective = text;
  activeRunId = '';
  lastSequence = 0;
  selectedRun = null;
  setSubmissionStatus('sending', 'Sending directly to Intake through Band…');
  resetProcessingView();
  updateSendState();

  const requestId = globalThis.crypto?.randomUUID?.() || `request-${Date.now()}`;
  try {
    const response = await fetch('/internal/chat/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, constraints: selectedConstraints, client_request_id: requestId }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail?.message || 'Band rejected the request.');
    }
    setSubmissionStatus('sent', `Submitted → ${data.routed_to}. Waiting for Intake…`);
    document.getElementById('chat-input').disabled = true;
    startMirrorPolling();
  } catch (error) {
    submissionPending = false;
    setSubmissionStatus('error', error.message || 'Unable to send to Band.');
    updateSendState();
  }
}

function setSubmissionStatus(state, message) {
  const element = document.getElementById('submission-status');
  element.className = `submission-status status-${state}`;
  element.textContent = message;
}

function openRoom() {
  const button = document.getElementById('chat-open-room');
  window.open(button.dataset.url || 'https://app.band.ai', '_blank', 'noopener');
}

function initRuntime() {
  document.getElementById('runtime-btn').addEventListener('click', toggleRuntime);
}

async function toggleRuntime() {
  const button = document.getElementById('runtime-btn');
  button.disabled = true;
  button.textContent = '…';
  try {
    const action = runtimeOn ? 'stop' : 'start';
    const response = await fetch(`/internal/runtime/${action}`, { method: 'POST' });
    if (!response.ok) throw new Error('Runtime action failed');
    await checkStatus();
  } catch (_error) {
    setSubmissionStatus('error', 'Agent runtime could not be changed.');
  } finally {
    button.disabled = false;
  }
}

async function checkStatus() {
  try {
    const [statusResponse, runtimeResponse] = await Promise.all([
      fetch('/internal/chat/status'),
      fetch('/internal/runtime/status'),
    ]);
    if (!statusResponse.ok || !runtimeResponse.ok) throw new Error('Status unavailable');
    readiness = await statusResponse.json();
    const runtime = await runtimeResponse.json();
    runtimeOn = Boolean(runtime.all_running);

    document.getElementById('st-entry-mode').textContent = 'Direct Band';
    document.getElementById('st-runtime').textContent = runtimeOn ? 'On (5/5)' : `${readiness.agents_running || 0}/5 running`;
    document.getElementById('st-room').textContent = readiness.room_selected ? 'Ready' : 'Unavailable';
    document.getElementById('st-intake').textContent = readiness.intake_handle || '@itz1508/intake';
    document.getElementById('st-run').textContent = readiness.active_run_id || activeRunId || 'None';
    if (readiness.room_url) document.getElementById('chat-open-room').dataset.url = readiness.room_url;

    const runtimeButton = document.getElementById('runtime-btn');
    runtimeButton.textContent = runtimeOn ? 'ON' : 'OFF';
    runtimeButton.classList.toggle('on', runtimeOn);
    document.getElementById('runtime-roles').innerHTML = (runtime.agents || []).map(agent =>
      `<div class="runtime-role-row"><span class="role-name">${esc(agent.role)}</span><span class="${agent.running ? 'status-running' : 'status-stopped'}">${agent.running ? 'Running' : 'Stopped'}</span></div>`
    ).join('');

    if (!submissionPending) {
      setSubmissionStatus(readiness.send_enabled ? 'ready' : 'idle', readiness.send_enabled ? 'Ready for direct Band submission.' : (readiness.error || 'Workflow is not ready.'));
    }
  } catch (_error) {
    readiness = { send_enabled: false };
    setSubmissionStatus('error', 'Backend status is unavailable.');
  }
  updateSendState();
}

function startMirrorPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollWorkflow();
  pollTimer = setInterval(pollWorkflow, 1200);
}

async function pollWorkflow() {
  try {
    const query = activeRunId
      ? `run_id=${encodeURIComponent(activeRunId)}&after_sequence=${lastSequence}`
      : `after_sequence=0`;
    const response = await fetch(`/internal/chat/events?${query}`);
    if (!response.ok) return;
    const eventData = await response.json();
    if (!eventData.run_id) return;

    const runResponse = await fetch(`/internal/chat/runs/${encodeURIComponent(eventData.run_id)}`);
    if (!runResponse.ok) return;
    const run = await runResponse.json();
    if (!activeRunId && !objectiveMatches(run.objective, activeObjective)) return;

    activeRunId = eventData.run_id;
    selectedRun = run;
    lastSequence = eventData.next_sequence || lastSequence;
    document.getElementById('st-run').textContent = activeRunId;
    renderRun();

    if (run.terminal) {
      clearInterval(pollTimer);
      pollTimer = null;
      submissionPending = false;
      setSubmissionStatus('complete', `Finalizing delivered: ${run.outcome}`);
      document.getElementById('chat-input').disabled = false;
      updateSendState();
    } else {
      setSubmissionStatus('processing', `Processing → ${currentStageLabel(run)}`);
    }
  } catch (_error) {
    setSubmissionStatus('error', 'Workflow polling was interrupted; retrying…');
  }
}

function objectiveMatches(actual, expected) {
  const normalizedActual = String(actual || '').replace(/^@?itz1508\/intake\s*/i, '').trim();
  return normalizedActual === expected.trim() || normalizedActual.includes(expected.trim());
}

function currentStageLabel(run) {
  const path = run.workflow_path || [];
  const key = path[path.length - 1] || 'intake';
  return WORKFLOW_STAGES.find(stage => stage.key === key)?.label || key;
}

function resetProcessingView() {
  document.getElementById('result-card').innerHTML = '<p class="result-pending">Waiting for Finalizing to deliver the terminal result.</p>';
  document.getElementById('terminal-body').innerHTML = '<p class="terminal-pending">Request submitted. Waiting for Intake delivery…</p>';
  document.getElementById('artifact-tabs').innerHTML = '';
  document.getElementById('artifact-content').innerHTML = '<p class="artifact-pending">Stage outputs appear as participants complete.</p>';
  resetStageStates();
  stageStates['human-request'].status = 'processing';
  renderWorkflow();
}

function renderRun() {
  computeStageStates();
  renderWorkflow();
  renderResult();
  renderConversation();
  renderArtifacts();
}

/* ============================================================
   WORKFLOW DISPLAY — one card per logical stage with state
   ============================================================ */
function renderWorkflow() {
  const container = document.getElementById('workflow-steps-container');
  container.innerHTML = `<div class="workflow-grid">${WORKFLOW_STAGES.map((stage, index) => {
    const state = stageStates[stage.key]?.status || 'waiting';
    const cssState = state === 'completed' ? 'delivered' : state === 'not_used' ? 'skipped' : state;
    const summary = getStageSummary(stage.key, state);
    return `<article class="workflow-card stage-${cssState}">
      <div class="workflow-card-head"><span class="stage-index">${String(index + 1).padStart(2, '0')}</span><h3>${stage.label}</h3><span class="stage-state">${STAGE_LABELS[state] || state}</span></div>
      <p>${esc(summary)}</p>
    </article>`;
  }).join('')}</div>`;

  const note = document.getElementById('workflow-note');
  note.textContent = selectedRun?.terminal
    ? `Terminal delivery completed with outcome: ${selectedRun.outcome}`
    : 'Band advances each structured packet automatically. One isolation-guided retry is available.';
}

/* ============================================================
   BAND DELIVERY TRACE — deduplicated stage status view
   ============================================================ */
function renderConversation() {
  document.getElementById('terminal-title').textContent = `proofgate.band.v1 — ${selectedRun?.outcome || 'processing'}`;

  // Build deduplicated stage status lines instead of raw events
  const lines = [];
  for (const stage of WORKFLOW_STAGES) {
    const state = stageStates[stage.key]?.status || 'waiting';
    if (state === 'waiting') continue; // Don't show stages that haven't started
    if (state === 'not_used') continue; // Don't clutter the trace with unused stages

    const summary = getStageSummary(stage.key, state);
    const stateClass = state === 'completed' ? 'term-success' :
                       state === 'failed' ? 'term-fail' :
                       state === 'processing' || state === 'thinking' ? '' :
                       '';
    lines.push(`<div class="term-line ${stateClass}"><span class="term-sender">${esc(stage.label)}</span><span class="term-arrow">→</span><span class="term-receiver">${esc(STAGE_LABELS[state])}</span><span class="term-info">${esc(summary)}</span></div>`);
  }

  document.getElementById('terminal-body').innerHTML = lines.length
    ? lines.join('')
    : '<p class="terminal-pending">Waiting for the first mirrored Band event…</p>';
}

/* ============================================================
   DELIVERED RESULT
   ============================================================ */
function renderResult() {
  const element = document.getElementById('result-card');
  const final = selectedRun?.final_result || {};
  if (!selectedRun?.outcome) {
    element.innerHTML = `<p class="result-pending">Workflow processing. Current stage: ${esc(currentStageLabel(selectedRun || {}))}</p>`;
    return;
  }
  const unresolved = final.unresolved_items || [];
  const uncertainty = final.remaining_uncertainty || [];
  const contributions = final.role_successes || {};
  element.innerHTML = `
    <div class="result-outcome"><span class="outcome-badge outcome-${esc(selectedRun.outcome)}">${esc(selectedRun.outcome)}</span></div>
    <p class="result-summary">${esc(final.final_summary || 'Finalizing delivered the terminal result.')}</p>
    <dl class="field-list">
      <dt>Resolution</dt><dd>${esc(valueSummary(final.resolution) || '—')}</dd>
      <dt>Requirements met</dt><dd>${final.requirements_met === true ? 'Yes' : 'No'}</dd>
      <dt>Retry count</dt><dd>${esc(selectedRun.retry_count)}</dd>
      <dt>Unresolved</dt><dd>${esc(unresolved.join(', ') || 'None')}</dd>
      <dt>Uncertainty</dt><dd>${esc(Array.isArray(uncertainty) ? uncertainty.join(', ') || 'None' : uncertainty || 'None')}</dd>
    </dl>
    <div class="contribution-grid">${Object.entries(contributions).map(([role, value]) => `<div><strong>${esc(role)}</strong><span>${esc(value)}</span></div>`).join('')}</div>
    <details class="result-detail"><summary>Structured final result</summary><pre class="json-block">${esc(JSON.stringify(final, null, 2))}</pre></details>`;
}

function valueSummary(value) {
  if (typeof value === 'string') return value;
  if (!value || typeof value !== 'object') return '';
  return value.solution || value.summary || value.final_summary || JSON.stringify(value);
}

/* ============================================================
   STAGE RESULTS
   ============================================================ */
function renderArtifacts() {
  const results = selectedRun?.stage_results || {};
  const keys = Object.keys(results);
  const tabs = document.getElementById('artifact-tabs');
  const content = document.getElementById('artifact-content');
  if (!keys.length) return;
  tabs.innerHTML = keys.map((key, index) => `<button class="artifact-tab${index === 0 ? ' active' : ''}" data-tab="artifact-${key}">${esc(WORKFLOW_STAGES.find(stage => stage.key === key)?.label || key)}</button>`).join('');
  content.innerHTML = keys.map((key, index) => `<pre id="artifact-${key}" class="artifact-block${index === 0 ? ' active' : ''}">${esc(JSON.stringify(results[key], null, 2))}</pre>`).join('');
  tabs.querySelectorAll('.artifact-tab').forEach(tab => tab.addEventListener('click', () => {
    tabs.querySelectorAll('.artifact-tab').forEach(item => item.classList.remove('active'));
    content.querySelectorAll('.artifact-block').forEach(item => item.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab)?.classList.add('active');
  }));
}

function esc(value) {
  const element = document.createElement('span');
  element.textContent = value == null ? '' : String(value);
  return element.innerHTML;
}
