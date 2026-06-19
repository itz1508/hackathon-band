/** ProofGate for Band — direct submission and live workflow processing. */

const WORKFLOW_STAGES = [
  { key: 'intake', label: 'Intake', responsibility: 'Bound the request and preserve its constraints.' },
  { key: 'planner', label: 'Plan', responsibility: 'Define measurable requirements, scope, and risks.' },
  { key: 'resolution', label: 'Resolution', responsibility: 'Produce and assess the proposed solution.' },
  { key: 'issue-isolator', label: 'Issue Isolation', responsibility: 'Explain a failed attempt and focus recovery.', optional: true },
  { key: 'resolution-retry', label: 'Resolution Retry', responsibility: 'Retry once using the isolation evidence.', optional: true },
  { key: 'finalizing', label: 'Finalizing', responsibility: 'Deliver one terminal result with evidence.' },
];

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

document.addEventListener('DOMContentLoaded', async () => {
  renderCommands();
  initTextarea();
  initActions();
  initRuntime();
  renderWorkflow();
  await Promise.all([loadTestInputs(), checkStatus()]);
});

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
      `<button class="test-input-item" data-request="${esc(item.request_text)}">
        <span class="ti-label">${esc(item.label)}</span>
        <span class="ti-meta">${esc(item.expected_outcome)}</span>
      </button>`
    ).join('');
    container.querySelectorAll('.test-input-item').forEach(item => {
      item.addEventListener('click', () => {
        const input = document.getElementById('chat-input');
        input.value = item.dataset.request;
        input.focus();
        updatePreview();
        updateSendState();
      });
    });
  } catch (_error) {
    container.innerHTML = '<span class="op-empty">Test inputs unavailable</span>';
  }
}

function initTextarea() {
  document.getElementById('chat-input').addEventListener('input', () => {
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
      body: JSON.stringify({ text, client_request_id: requestId }),
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
  renderWorkflow();
}

function renderRun() {
  renderWorkflow();
  renderResult();
  renderConversation();
  renderArtifacts();
}

function stageState(stage) {
  if (!selectedRun) return stage.key === 'intake' && submissionPending ? 'processing' : 'waiting';
  const results = selectedRun.stage_results || {};
  if (results[stage.key]) return results[stage.key].role_success ? 'delivered' : 'failed';
  const path = selectedRun.workflow_path || [];
  if (stage.optional && selectedRun.terminal) return 'skipped';
  const current = path[path.length - 1];
  if (current === stage.key) return 'processing';
  if (stage.key === 'finalizing' && selectedRun.outcome) return 'delivered';
  return 'waiting';
}

function renderWorkflow() {
  const container = document.getElementById('workflow-steps-container');
  const results = selectedRun?.stage_results || {};
  container.innerHTML = `<div class="workflow-grid">${WORKFLOW_STAGES.map((stage, index) => {
    const state = stageState(stage);
    const result = results[stage.key] || {};
    const unmet = result.unmet_requirements || [];
    const evidence = result.evidence || [];
    const output = result.output || {};
    const summary = result.role_success || output.summary || output.solution || output.final_summary || stage.responsibility;
    return `<article class="workflow-card stage-${state}">
      <div class="workflow-card-head"><span class="stage-index">${String(index + 1).padStart(2, '0')}</span><h3>${stage.label}</h3><span class="stage-state">${state}</span></div>
      <p>${esc(summary)}</p>
      ${evidence.length ? `<div class="stage-meta">Evidence: ${esc(evidence.length)} item${evidence.length === 1 ? '' : 's'}</div>` : ''}
      ${unmet.length ? `<div class="stage-unmet">Unmet: ${esc(unmet.join(', '))}</div>` : ''}
    </article>`;
  }).join('')}</div>`;
  const note = document.getElementById('workflow-note');
  note.textContent = selectedRun?.terminal
    ? `Terminal delivery completed with outcome: ${selectedRun.outcome}`
    : 'Band advances each structured packet automatically. One isolation-guided retry is available.';
}

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

function renderConversation() {
  const events = selectedRun?.conversation_events || [];
  document.getElementById('terminal-title').textContent = `proofgate.band.v1 — ${selectedRun?.outcome || 'processing'}`;
  document.getElementById('terminal-body').innerHTML = events.length
    ? events.map(event => `<div class="term-line"><span class="term-sender">${esc(event.sender_role || 'human')}</span><span class="term-arrow">→</span><span class="term-receiver">${esc(event.recipient_role)}</span><span class="term-info">${esc(event.summary || event.event)}</span></div>`).join('')
    : '<p class="terminal-pending">Waiting for the first mirrored Band event…</p>';
}

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
