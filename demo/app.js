/**
 * ProofGate for Band — Dashboard Frontend
 * 
 * Wire flow:
 *   1. On load: GET /api/health -> badge status
 *   2. "Run Live Demo" click: POST /api/run -> job_id
 *   3. Poll GET /api/jobs/<job_id> every 1.5s until completed/failed
 *   4. GET /api/results/<job_id> -> render all panels
 * 
 * No silent live-data fallback. Errors are always visible.
 */

const API_BASE = '';

// State
let jobId = null;
let polling = false;

// DOM refs
const $ = (id) => document.getElementById(id);
const healthBadge  = $('health-badge');
const runBtn       = $('run-btn');
const jobIdDisplay = $('job-id-display');

const progressSection = $('progress-section');
const progressFill    = $('progress-fill');
const progressStep    = $('progress-step');

const resultsSection = $('results-section');

const scenarioCard        = $('scenario-card');
const successPathCard     = $('success-path-card');
const failurePathCard     = $('failure-path-card');
const proofPacketCard     = $('proof-packet-card');
const failureProofCard    = $('failure-proof-card');
const transcriptCard      = $('transcript-card');
const testCasesCard       = $('test-cases-card');
const artifactCard        = $('artifact-card');

const errorDisplay = $('error-display');
const errorText    = $('error-text');

// Helpers
function show(el)  { el.classList.remove('hidden'); }
function hide(el)  { el.classList.add('hidden'); }

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

function showError(msg) {
  errorText.textContent = msg;
  show(errorDisplay);
}

function hideError() {
  hide(errorDisplay);
}

// Health Check
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data.status === 'ok') {
      healthBadge.className = 'badge badge-ok';
      healthBadge.textContent = 'Backend Connected';
      runBtn.disabled = false;
    } else {
      throw new Error('Unexpected response');
    }
  } catch (err) {
    healthBadge.className = 'badge badge-fail';
    healthBadge.textContent = 'Demo Fallback';
    // Button stays disabled, show fallback note
    showError(
      'Backend unreachable. Start the server with:\n' +
      '  python -m proofgate.server --host 127.0.0.1 --port 8787\n' +
      'Then refresh this page.'
    );
  }
}

// Run Live Demo
async function runLiveDemo() {
  hideError();
  runBtn.disabled = true;
  runBtn.innerHTML = '<span class="btn-icon">▶</span> Starting…';

  try {
    const res = await fetch(`${API_BASE}/api/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: 'Fix login validator',
        mode: 'success'
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
    const data = await res.json();
    jobId = data.job_id;

    jobIdDisplay.textContent = `Job ID: ${jobId}`;
    show(jobIdDisplay);
    show(progressSection);
    runBtn.textContent = '⏳ Running…';

    await pollJob(jobId);
  } catch (err) {
    showError(`Failed to start job: ${err.message}`);
    runBtn.disabled = false;
    runBtn.innerHTML = '<span class="btn-icon">▶</span> Run Live Demo';
  }
}

// Poll job status
async function pollJob(id) {
  polling = true;
  let done = false;

  while (polling && !done) {
    await sleep(1500); // 1.5s interval

    try {
      const res = await fetch(`${API_BASE}/api/jobs/${id}`);
      if (!res.ok) {
        if (res.status === 404) {
          showError('Job not found on server. It may have expired.');
          break;
        }
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();

      // Update progress
      progressFill.style.width = `${data.progress}%`;
      progressStep.textContent = data.current_step || data.status;

      if (data.status === 'completed') {
        done = true;
        runBtn.textContent = '✓ Complete';
        await fetchResults(id);
      } else if (data.status === 'failed') {
        done = true;
        showError(`Job failed: ${data.error || 'Unknown error'}`);
        runBtn.textContent = '✗ Failed';
        runBtn.disabled = false;
      }
    } catch (err) {
      showError(`Polling error: ${err.message}`);
      polling = false;
      runBtn.disabled = false;
      runBtn.innerHTML = '<span class="btn-icon">▶</span> Retry';
    }
  }
}

// Fetch & render results
async function fetchResults(id) {
  try {
    const res = await fetch(`${API_BASE}/api/results/${id}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
    const data = await res.json();

    renderResults(data);
    show(resultsSection);
    hide(progressSection);
  } catch (err) {
    showError(`Failed to fetch results: ${err.message}`);
  } finally {
    polling = false;
    runBtn.disabled = false;
  }
}

// Render all result panels
function renderResults(data) {
  // Scenario
  if (data.demo_scenario) {
    const s = data.demo_scenario;
    scenarioCard.innerHTML = `
      <h4 class="card-title">Scenario: ${escapeHtml(s.title)}</h4>
      <div class="proof-field">
        <div class="proof-field-label">Problem</div>
        <div class="proof-field-value">${escapeHtml(s.problem)}</div>
      </div>
      <div class="proof-field">
        <div class="proof-field-label">Fix</div>
        <div class="proof-field-value">${escapeHtml(s.fix)}</div>
      </div>
      <div class="proof-field">
        <div class="proof-field-label">Coverage</div>
        <div class="proof-field-value">${escapeHtml(s.coverage)}</div>
      </div>
    `;
    show(scenarioCard);
  }

  // Success path
  if (data.success_path && data.success_path.length) {
    successPathCard.querySelector('#success-agents').innerHTML =
      data.success_path.map(a => `
        <div class="agent-step">
          <div class="agent-step-header">
            <span class="icon-ok">✓</span>
            <span class="agent-step-name">${escapeHtml(a.name)}</span>
            <span class="agent-step-agent">${escapeHtml(a.agent)}</span>
          </div>
          <div class="agent-step-role">${escapeHtml(a.role)}</div>
          <div class="agent-step-desc">${escapeHtml(a.description)}</div>
        </div>
      `).join('');
    show(successPathCard);
  }

  // Failure path
  if (data.failure_path && data.failure_path.length) {
    failurePathCard.querySelector('#failure-agents').innerHTML =
      data.failure_path.map(a => `
        <div class="agent-step">
          <div class="agent-step-header">
            <span class="icon-fail">✗</span>
            <span class="agent-step-name">${escapeHtml(a.name)}</span>
            <span class="agent-step-agent">${escapeHtml(a.agent)}</span>
          </div>
          <div class="agent-step-role">${escapeHtml(a.role)}</div>
          <div class="agent-step-desc">${escapeHtml(a.description)}</div>
        </div>
      `).join('');
    show(failurePathCard);
  }

  // Proof packets
  if (data.proof_packet) {
    renderProofPacket('proof-packet-content', data.proof_packet);
    show(proofPacketCard);
  }
  if (data.failure_proof_packet) {
    renderProofPacket('failure-proof-content', data.failure_proof_packet);
    show(failureProofCard);
  }

  // Transcript
  if (data.transcript && data.transcript.length) {
    $('transcript-messages').innerHTML =
      data.transcript.map(m => `
        <div class="msg">
          <div class="msg-header">
            <span class="msg-agent">${escapeHtml(m.agent)}</span>
            <span class="msg-handle">${escapeHtml(m.handle)}</span>
            <span class="msg-time">${escapeHtml(m.timestamp)}</span>
          </div>
          <div class="msg-text">${escapeHtml(m.message)}</div>
        </div>
      `).join('');
    show(transcriptCard);
  }

  // Test cases
  if (data.test_cases && data.test_cases.length) {
    $('test-body').innerHTML =
      data.test_cases.map(t => `
        <tr>
          <td>${escapeHtml(t.name)}</td>
          <td>${escapeHtml(String(t.input))}</td>
          <td>${escapeHtml(String(t.expected))}</td>
          <td>${t.passed ? '✅ PASS' : '❌ FAIL'}</td>
        </tr>
      `).join('');
    show(testCasesCard);
  }

  // Artifact
  if (data.artifact) {
    $('artifact-diff').textContent = data.artifact.diff || '(no diff)';
    $('artifact-summary').textContent = data.artifact.summary || '';
    show(artifactCard);
  }
}

function renderProofPacket(containerId, packet) {
  const safeClass = packet.safe_to_apply ? 'proof-safe-true' : 'proof-safe-false';
  const container = $(containerId);
  container.innerHTML = `
    <div class="proof-field">
      <div class="proof-field-label">Title</div>
      <div class="proof-field-value">${escapeHtml(packet.title)}</div>
    </div>
    <div class="proof-field">
      <div class="proof-field-label">Status</div>
      <div class="proof-field-value">${escapeHtml(packet.status)}</div>
    </div>
    <div class="proof-field">
      <div class="proof-field-label">What's Wrong</div>
      <div class="proof-field-value">${escapeHtml(packet.what_wrong)}</div>
    </div>
    <div class="proof-field">
      <div class="proof-field-label">Why It Matters</div>
      <div class="proof-field-value">${escapeHtml(packet.why_it_matters)}</div>
    </div>
    <div class="proof-field">
      <div class="proof-field-label">How to Fix</div>
      <div class="proof-field-value">${escapeHtml(packet.how_to_fix)}</div>
    </div>
    <div class="proof-field">
      <div class="proof-field-label">Simulated Diff</div>
      <pre class="proof-diff">${escapeHtml(packet.simulated_diff)}</pre>
    </div>
    <div class="proof-field">
      <div class="proof-field-label">Validation Summary</div>
      <div class="proof-field-value">${escapeHtml(packet.validation_summary)}</div>
    </div>
    <div class="proof-field">
      <div class="proof-field-label">Safe to Apply</div>
      <div class="proof-field-value ${safeClass}">${String(packet.safe_to_apply)}</div>
    </div>
    <div class="proof-field">
      <div class="proof-field-label">Human Action</div>
      <div class="proof-field-value">${escapeHtml(packet.human_action)}</div>
    </div>
    <div class="proof-field">
      <div class="proof-field-label">Decision Reason</div>
      <div class="proof-field-value">${escapeHtml(packet.decision_reason)}</div>
    </div>
  `;
}

// Utility
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  runBtn.addEventListener('click', runLiveDemo);
});
