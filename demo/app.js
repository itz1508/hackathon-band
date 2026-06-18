const fallbackTranscript = {
  room_id: "proofgate-demo-room",
  routing_model: "@mention",
  messages: [
    { sender: "@itz1508", mention: "@itz1508/planner", message_type: "text", content: "Fix a login validator so whitespace-only emails are rejected." },
    { sender: "@itz1508/planner", mention: "@itz1508/engineer", message_type: "task", content: "Scope approved. Produce the smallest patch candidate." },
    { sender: "@itz1508/engineer", mention: "@itz1508/tester", message_type: "tool_result", content: "Patch candidate ready. Validate behavior and scope." },
    { sender: "@itz1508/tester", mention: "@itz1508/reviewer", message_type: "tool_result", content: "Validation passed. Review proof packet readiness." },
    { sender: "@itz1508/reviewer", mention: "@itz1508", message_type: "task", content: "Proof packet ready for human apply decision." }
  ]
};

const fallbackProof = {
  what_wrong: "The login validator accepts whitespace-only values because it checks only for an at sign.",
  why_it_matters: "A weak validator lets invalid identity input pass into downstream login and account flows.",
  how_to_fix: "Trim the email value, reject empty strings, and keep the existing at-sign check.",
  simulated_diff: `--- demo_repo/auth.py.before
+++ demo_repo/auth.py.after
@@ -1,2 +1,3 @@
 def is_valid_email(value):
-    return "@" in value
+    value = value.strip()
+    return bool(value) and "@" in value`,
  validation_summary: {
    tests_run: [
      { name: "rejects_blank_email", status: "passed" },
      { name: "rejects_whitespace_email", status: "passed" },
      { name: "accepts_normal_email", status: "passed" },
      { name: "scope_limited_to_auth_py", status: "passed" }
    ]
  },
  safe_to_apply: true,
  decision_reason: "Patch stayed inside scope and validation passed."
};

async function loadJson(endpoint, fallback) {
  try {
    const response = await fetch(endpoint, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    return fallback;
  }
}

function renderTranscript(transcript) {
  const messages = document.querySelector("#messages");
  messages.replaceChildren();
  for (const message of transcript.messages) {
    const node = document.createElement("div");
    node.className = "message";
    node.innerHTML = `
      <header><strong></strong><span></span></header>
      <p></p>
    `;
    node.querySelector("strong").textContent = message.sender;
    node.querySelector("span").textContent = `${message.message_type} to ${message.mention}`;
    node.querySelector("p").textContent = message.content;
    messages.appendChild(node);
  }
}

function renderProof(proof) {
  document.querySelector("#decision").textContent = proof.safe_to_apply ? "Ready for human apply" : "Apply blocked";
  document.querySelector("#reason").textContent = proof.decision_reason;
  document.querySelector("#whatWrong").textContent = proof.what_wrong;
  document.querySelector("#whyMatters").textContent = proof.why_it_matters;
  document.querySelector("#howFix").textContent = proof.how_to_fix;
  document.querySelector("#diff").textContent = proof.simulated_diff;

  const tests = document.querySelector("#tests");
  tests.replaceChildren();
  for (const test of proof.validation_summary.tests_run) {
    const node = document.createElement("li");
    const name = document.createElement("strong");
    const status = document.createElement("span");
    name.textContent = test.name;
    status.textContent = test.status;
    node.append(name, status);
    tests.appendChild(node);
  }
}

async function main() {
  const [transcript, proof] = await Promise.all([
    loadJson("/api/transcript", fallbackTranscript),
    loadJson("/api/proof-packet", fallbackProof)
  ]);
  renderTranscript(transcript);
  renderProof(proof);
}

main();


