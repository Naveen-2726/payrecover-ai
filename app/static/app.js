// PayRecover AI Client App Logic (v3 Razorpay Domain Edition)

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  loadAnalytics();
  loadTransactions();
  loadAuditLogs();
  loadGuardrailConfig();
  loadInsights();
  loadHumanQueue();
  loadControlTower();
  loadOpportunities();
  loadSubscriptions();
  loadJudgeEvidence();
  loadAgentGovernance();
  loadRemainingOperations();

  setInterval(() => {
    loadAnalytics();
    loadTransactions();
    loadHumanQueue();
    loadControlTower();
  }, 8000);
});

function setupTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      
      btn.classList.add("active");
      const target = btn.getAttribute("data-tab");
      document.getElementById(target).classList.add("active");

      if (target === "tab-benchmark") loadBenchmark();
      if (target === "tab-human") loadHumanQueue();
      if (target === "tab-attribution") loadAttribution();
      if (target === "tab-control-tower") loadControlTower();
      if (target === "tab-intelligence") loadOpportunities();
      if (target === "tab-subscriptions") loadSubscriptions();
    });
  });
}

function toggleJudgeMode() {
  document.getElementById("judge-modal").classList.toggle("hidden");
}

async function runScenario(scenarioId) {
  try {
    const res = await fetch(`/api/demo/scenario/${scenarioId}`, { method: "POST" });
    const data = await res.json();
    
    document.getElementById("scenario-output-box").innerText = JSON.stringify(data, null, 2);
    alert(`Executed ${scenarioId}! Result: ${data.transaction?.status || 'PROCESSED'}`);
    
    loadAnalytics();
    loadTransactions();
    loadAuditLogs();
    loadHumanQueue();
    loadControlTower();
  } catch (err) {
    alert(`Scenario Execution Failed: ${err.message}`);
  }
}

async function loadAttribution() {
  try {
    const res = await fetch("/api/analytics/attribution");
    if (!res.ok) return;
    const data = await res.json();

    const container = document.getElementById("attribution-cards-grid");
    container.innerHTML = Object.entries(data).map(([action, amount]) => `
      <div class="card">
        <span class="metric-title">${action}</span>
        <div class="metric-value text-emerald">₹${amount.toLocaleString('en-IN')}</div>
        <div class="metric-sub text-muted">Recovered Net Revenue</div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load attribution:", err);
  }
}

async function loadAnalytics() {
  try {
    const res = await fetch("/api/analytics");
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("kpi-failed-volume").innerText = `₹${data.total_failed_volume_inr.toLocaleString('en-IN')}`;
    document.getElementById("kpi-recovered-arr").innerText = `₹${data.total_recovered_revenue_inr.toLocaleString('en-IN')}`;
    document.getElementById("kpi-unrecoverable").innerText = `₹${data.unrecoverable_revenue_inr.toLocaleString('en-IN')}`;
    document.getElementById("kpi-recovery-rate").innerText = `${data.recovery_rate_pct}% Recovery Rate (${data.recovery_uplift_pct} Uplift)`;
    document.getElementById("kpi-roi").innerText = data.roi_multiplier;
  } catch (err) {
    console.error("Failed to load analytics:", err);
  }
}

async function loadControlTower() {
  try {
    const res = await fetch("/api/analytics/control-tower");
    if (!res.ok) return;
    const data = await res.json();
    const m = data.metrics;
    const money = value => `₹${Number(value || 0).toLocaleString('en-IN')}`;
    document.getElementById("kpi-failed-volume").innerText = money(m.revenue_currently_at_risk_inr);
    document.getElementById("kpi-recovered-arr").innerText = money(m.net_recovered_revenue_inr);
    document.getElementById("kpi-recovery-rate").innerText = `${m.recovery_rate_pct}% Recovery Rate`;
    document.getElementById("kpi-roi").innerText = m.recovery_cost_inr ? `${(m.net_recovered_revenue_inr / m.recovery_cost_inr).toFixed(1)}x` : "N/A";
    const cards = [
      ["Revenue at risk", money(m.revenue_currently_at_risk_inr)],
      ["Predicted recoverable", money(m.predicted_recoverable_revenue_inr)],
      ["Recovered revenue", money(m.revenue_recovered_inr)],
      ["Incremental vs baseline", money(m.incremental_recovered_revenue_inr)],
      ["Payment cohort incremental", money(m.payment_cohort_incremental_recovered_revenue_inr)],
      ["Recovery cost", money(m.recovery_cost_inr)],
      ["Avoided retries", m.avoided_unnecessary_retry_attempts],
      ["Late-auth exposure", money(m.late_authorisation_exposure_inr)],
      ["Subscription risk", money(m.subscription_revenue_at_risk_inr)]
    ];
    document.getElementById("control-tower-metrics").innerHTML = cards.map(([label, value]) => `<div class="card"><span class="metric-title">${label}</span><div class="metric-value text-emerald">${value}</div></div>`).join("");
    document.getElementById("judge-recovery-rate").innerText = `${m.recovery_rate_pct}%`;
    document.getElementById("judge-incremental").innerText = money(m.incremental_recovered_revenue_inr);
  } catch (err) { console.error("Failed to load control tower:", err); }
}

async function loadSubscriptions() {
  try {
    const res = await fetch("/api/subscriptions/metrics");
    if (!res.ok) return;
    const data = await res.json();
    const money = value => `₹${Number(value || 0).toLocaleString('en-IN')}`;
    document.getElementById("subscription-metrics").innerHTML = [
      ["At-risk revenue", money(data.at_risk_revenue_inr)],
      ["Predicted recoverable", money(data.predicted_recoverable_revenue_inr)],
      ["Recovered revenue", money(data.recovered_revenue_inr)],
      ["Recovery rate", `${data.recovery_rate_pct}%`]
    ].map(([label, value]) => `<div class="card"><span class="metric-title">${label}</span><div class="metric-value text-emerald">${value}</div></div>`).join("");
    document.getElementById("subscription-records").innerHTML = data.transaction_records.map(tx => `<tr><td>${tx.subscription_id}</td><td>${money(tx.amount)}</td><td>${tx.orchestration.recommended_action}</td><td>${tx.status}</td><td>Synthetic event ledger</td></tr>`).join("");
  } catch (err) { console.error("Failed to load subscriptions:", err); }
}

async function loadOpportunities() {
  try {
    const res = await fetch("/api/analytics/opportunities");
    if (!res.ok) return;
    const data = await res.json();
    const tbody = document.getElementById("opportunities-tbody");
    tbody.innerHTML = data.opportunities.map(item => `
      <tr>
        <td class="font-mono">${item.payment_id}</td>
        <td><span class="badge badge-${item.priority === 'HIGH' ? 'crimson' : 'amber'}">${item.priority}</span></td>
        <td><strong>₹${item.opportunity_value_inr.toLocaleString('en-IN')}</strong></td>
        <td>${item.recovery_probability_pct}%</td>
        <td>${item.recommended_action}</td>
        <td><button class="btn btn-sm btn-outline" onclick="replayTransaction('${item.payment_id}')">↻ Replay</button></td>
      </tr>`).join("");
  } catch (err) { console.error("Failed to load opportunities:", err); }
}

async function replayTransaction(txId) {
  try {
    const res = await fetch(`/api/transactions/${txId}/replay`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    const data = await res.json();
    document.getElementById("scenario-output-box").innerText = JSON.stringify(data, null, 2);
    alert(`Replay complete for ${txId}. Alternative comparison is estimate-only.`);
    loadAuditLogs();
  } catch (err) { console.error("Failed to replay transaction:", err); }
}

async function loadJudgeEvidence() {
  try {
    const [mlRes, benchmarkRes, reliabilityRes] = await Promise.all([
      fetch("/api/ml/metrics"), fetch("/api/analytics/benchmark"), fetch("/api/lab/judge-evidence")
    ]);
    const ml = await mlRes.json();
    const benchmark = await benchmarkRes.json();
    const reliability = await reliabilityRes.json();
    document.getElementById("judge-accuracy").innerText = `${(ml.accuracy * 100).toFixed(1)}%`;
    document.getElementById("judge-precision").innerText = `${(ml.precision * 100).toFixed(2)}%`;
    document.getElementById("judge-recall").innerText = `${(ml.recall * 100).toFixed(2)}%`;
    document.getElementById("judge-f1").innerText = `${(ml.f1_score * 100).toFixed(2)}%`;
    document.getElementById("judge-uplift").innerText = `₹${benchmark.uplift.net_revenue_saved_inr.toLocaleString('en-IN')}`;
    document.getElementById("bench-confidence-box").innerText = benchmark.confidence_intervals.message;
    document.getElementById("judge-reliability-evidence").innerText = reliability.results.map(item => `${item.status} ${item.attack_type}: ${item.input_event} -> ${item.final_state} -> ${item.audit_event}`).join("\n");
  } catch (err) { console.error("Failed to load Judge Mode evidence:", err); }
}

async function loadAgentGovernance() {
  try {
    const cert = await (await fetch("/api/agent/certification")).json();
    const sandbox = await (await fetch("/api/agent/sandbox")).json();
    const health = await (await fetch("/api/agent/health")).json();
    document.getElementById("agent-certification-status").innerText = cert.status;
    document.getElementById("agent-safety-score").innerText = `${sandbox.safety_score_pct}%`;
    document.getElementById("agent-sandbox-summary").innerText = `${sandbox.transactions_evaluated} evaluated, ${sandbox.correct_decisions} correct, ${sandbox.unsafe_actions} unsafe, ${sandbox.abstentions} abstentions`;
    document.getElementById("agent-health-state").innerText = health.state;
    document.getElementById("agent-health-reason").innerText = health.reason;
    const button = document.getElementById("agent-kill-switch-btn");
    button.innerText = health.state === "PAUSED" ? "▶ Resume Agent" : "⏸ Pause Agent";
  } catch (err) { console.error("Failed to load agent governance:", err); }
}

async function loadRemainingOperations() {
  try {
    const [budget, observability, forecast] = await Promise.all([
      fetch("/api/agent/budget").then(res => res.json()),
      fetch("/api/agent/observability").then(res => res.json()),
      fetch("/api/analytics/reliability-forecast").then(res => res.json())
    ]);
    document.getElementById("agent-budget-status").innerText = `₹${budget.used_inr.toLocaleString('en-IN')} used / ₹${budget.remaining_inr.toLocaleString('en-IN')} remaining`;
    document.getElementById("agent-observability-status").innerText = `${observability.decisions} decisions, ${observability.actions} actions, ${observability.abstentions} abstentions, ${observability.guardrail_blocks} guardrail blocks`;
    const highRisk = forecast.forecasts.filter(item => item.risk === "HIGH").length;
    document.getElementById("agent-forecast-status").innerText = `${highRisk} high-risk routes in the next ${forecast.window_minutes} minutes`;
  } catch (err) { console.error("Failed to load agent operations:", err); }
}

async function toggleAgentPause() {
  try {
    const health = await (await fetch("/api/agent/health")).json();
    const action = health.state === "PAUSED" ? "RESUME" : "PAUSE";
    await fetch("/api/agent/kill-switch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: action, reason: `Judge Mode ${action.toLowerCase()} action` })
    });
    loadAgentGovernance();
  } catch (err) { console.error("Failed to update agent kill switch:", err); }
}

async function loadInsights() {
  try {
    const res = await fetch("/api/insights");
    if (!res.ok) return;
    const insights = await res.json();

    const container = document.getElementById("merchant-insights-list");
    container.innerHTML = insights.map(i => `
      <div class="insight-item mb-2 p-2" style="background: rgba(99,102,241,0.05); border-left: 3px solid var(--color-${i.type === 'SUCCESS' ? 'emerald' : (i.type === 'GUARDRAIL' ? 'amber' : 'indigo')}); border-radius: 4px;">
        <strong style="font-size: 0.85rem; color: var(--text-primary);">${i.title}</strong>
        <p style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 2px;">${i.description}</p>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load insights:", err);
  }
}

async function loadTransactions() {
  try {
    const res = await fetch("/api/transactions");
    if (!res.ok) return;
    const transactions = await res.json();

    const tbody = document.getElementById("transactions-tbody");
    if (transactions.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No transactions logged yet. Inject a webhook to test!</td></tr>`;
      return;
    }

    tbody.innerHTML = transactions.map(tx => {
      const orch = tx.orchestration || tx.ai_plan || {};
      const statusBadge = getStatusBadge(tx.status);
      const category = orch.failure_category || 'TEMPORARY';
      const evScore = orch.expected_recovery_value !== undefined ? `₹${orch.expected_recovery_value}` : 'N/A';
      const actionLabel = orch.recommended_action || 'EVALUATING';

      return `
        <tr>
          <td class="font-mono">${tx.id}</td>
          <td><strong>₹${tx.amount.toLocaleString('en-IN')}</strong></td>
          <td><span class="badge badge-indigo">${tx.bank}</span> / ${tx.payment_method}</td>
          <td><code class="text-amber">${category}</code></td>
          <td class="text-muted">${tx.customer_email}</td>
          <td><span class="badge badge-indigo">${actionLabel}</span></td>
          <td><strong class="text-emerald">${evScore}</strong></td>
          <td>${statusBadge}</td>
          <td>
            <button class="btn btn-sm btn-outline" onclick="inspectTransaction('${tx.id}')">🔍 Inspect</button>
            ${tx.status !== 'RECOVERED' && tx.status !== 'RECOVERED_OR_LATE_AUTHORIZED' && tx.status !== 'ESCALATED' ? `<button class="btn btn-sm btn-emerald ml-1" onclick="triggerRecovery('${tx.id}')">⚡ Recover</button>` : ''}
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Failed to load transactions:", err);
  }
}

function getStatusBadge(status) {
  switch (status) {
    case 'RECOVERED':
    case 'RECOVERED_OR_LATE_AUTHORIZED':
      return `<span class="badge badge-success">✓ ${status}</span>`;
    case 'POTENTIALLY_LATE_AUTHORIZABLE':
      return `<span class="badge badge-amber">⏳ LATE AUTH MONITORING</span>`;
    case 'RECOVERY_PENDING':
      return `<span class="badge badge-amber">⏳ RECOVERY PENDING</span>`;
    case 'ESCALATED':
      return `<span class="badge badge-crimson">⚠️ ESCALATED</span>`;
    case 'BLOCKED_GUARDRAIL':
      return `<span class="badge badge-crimson">🛡️ GUARDRAIL BLOCKED</span>`;
    default:
      return `<span class="badge badge-crimson">${status}</span>`;
  }
}

async function loadBenchmark() {
  try {
    const res = await fetch("/api/analytics/benchmark");
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("bench-base-rate").innerText = `${data.baseline.recovery_rate_pct}%`;
    document.getElementById("bench-base-rev").innerText = `Net Revenue: ₹${data.baseline.net_recovered_revenue_inr.toLocaleString('en-IN')}`;
    document.getElementById("bench-base-att").innerText = `Attempts: ${data.baseline.attempts_count}`;

    document.getElementById("bench-ai-rate").innerText = `${data.payrecover_ai.recovery_rate_pct}%`;
    document.getElementById("bench-ai-rev").innerText = `Net Revenue: ₹${data.payrecover_ai.net_recovered_revenue_inr.toLocaleString('en-IN')}`;
    document.getElementById("bench-ai-att").innerText = `Attempts: ${data.payrecover_ai.attempts_count} (Cost Capped)`;

    document.getElementById("bench-uplift-val").innerText = `+₹${data.uplift.net_revenue_saved_inr.toLocaleString('en-IN')}`;
    document.getElementById("bench-uplift-pct").innerText = `${data.uplift.net_value_uplift_percentage} Net Revenue Uplift`;
    document.getElementById("bench-confidence-box").innerText = data.confidence_intervals.message;

    document.getElementById("bench-json-box").innerText = JSON.stringify(data, null, 2);
  } catch (err) {
    console.error("Failed to load benchmark:", err);
  }
}

async function handleRunSimulator(e) {
  e.preventDefault();
  const retries = parseInt(document.getElementById("sim-cfg-retries").value);
  const discount = parseFloat(document.getElementById("sim-cfg-discount").value);
  const human = parseFloat(document.getElementById("sim-cfg-human").value);

  try {
    const res = await fetch("/api/analytics/simulator", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        max_retries: retries,
        max_discount_pct: discount,
        human_approval_threshold: human
      })
    });
    const data = await res.json();
    document.getElementById("sim-results-container").innerText = JSON.stringify(data, null, 2);
  } catch (err) {
    console.error("Failed to run simulator:", err);
  }
}

async function loadHumanQueue() {
  try {
    const res = await fetch("/api/human-queue");
    if (!res.ok) return;
    const queue = await res.json();

    document.getElementById("human-queue-count").innerText = queue.length;
    const tbody = document.getElementById("human-queue-tbody");

    if (queue.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No transactions requiring human approval. All operating safely within automated guardrails.</td></tr>`;
      return;
    }

    tbody.innerHTML = queue.map(tx => `
      <tr>
        <td class="font-mono">${tx.id}</td>
        <td><strong>₹${tx.amount.toLocaleString('en-IN')}</strong></td>
        <td><span class="badge badge-indigo">${tx.bank}</span> / <code class="text-amber">${tx.error_code}</code></td>
        <td class="text-crimson">${tx.orchestration?.guardrail_result?.reason || 'Circuit Breaker / Risk Cap'}</td>
        <td><span class="badge badge-indigo">${tx.orchestration?.recommended_action || 'MANUAL_REVIEW'}</span></td>
        <td>
          <button class="btn btn-sm btn-emerald" onclick="handleHumanDecision('${tx.id}', 'APPROVE')">✓ Approve</button>
          <button class="btn btn-sm btn-outline ml-1" onclick="handleHumanDecision('${tx.id}', 'REJECT')" style="color: var(--color-crimson);">✗ Reject</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Failed to load human queue:", err);
  }
}

async function handleHumanDecision(txId, decision) {
  try {
    const res = await fetch("/api/human-queue/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transaction_id: txId, decision: decision, notes: `Manual merchant ${decision} action` })
    });
    if (res.ok) {
      alert(`Decision '${decision}' recorded into SHA-256 Audit Ledger!`);
      loadAnalytics();
      loadTransactions();
      loadHumanQueue();
      loadAuditLogs();
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

async function handleSimulateWebhook(e) {
  if (e && e.preventDefault) e.preventDefault();
  const amount = parseFloat(document.getElementById("sim-amount").value);
  const bank = document.getElementById("sim-bank").value;
  const errorCode = document.getElementById("sim-error-code").value;

  try {
    const res = await fetch("/api/simulate/failed-payment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_type: "payment.failed",
        amount: amount,
        bank: bank,
        error_code: errorCode,
        customer_email: "demo_user@example.com",
        customer_phone: "+919876543210"
      })
    });
    const data = await res.json();
    
    loadAnalytics();
    loadTransactions();
    loadAuditLogs();
    loadInsights();
    alert(`Webhook Injected! Payment Status: ${data.transaction?.status || 'PROCESSED'}`);
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

async function inspectTransaction(txId) {
  try {
    const res = await fetch("/api/transactions");
    const transactions = await res.json();
    const tx = transactions.find(t => t.id === txId);
    if (!tx) return;

    const intelligence = await (await fetch(`/api/transactions/${txId}/intelligence`)).json();

    const orch = tx.orchestration || tx.ai_plan || {};
    const exp = orch.explanation || {};
    const graph = orch.decision_graph || [];
    const health = orch.network_health || {};

    const graphHtml = graph.map(g => `
      <span class="badge badge-${g.status === 'COMPLETED' ? 'indigo' : (g.status === 'APPROVED' ? 'success' : 'amber')}">${g.step}: ${g.detail}</span>
    `).join(" ➔ ");

    const html = `
      <div class="modal-detail">
        <p><strong>Transaction ID:</strong> <code class="text-indigo">${tx.id}</code> | <strong>State:</strong> <span class="badge badge-success">${tx.status}</span></p>
        <p><strong>Amount:</strong> ₹${tx.amount} | <strong>Bank Channel:</strong> ${tx.bank} (${health.status || 'HEALTHY'} ${health.success_rate_pct || 90}%)</p>
        <p><strong>Error Category:</strong> <span class="badge badge-amber">${orch.failure_category || 'TEMPORARY'}</span></p>

        <h4 class="text-emerald mt-3">🧠 Payment Intelligence Diagnosis</h4>
        <p><strong>Why:</strong> ${intelligence.diagnosis.why}</p>
        <p><strong>Likely outcome:</strong> ${intelligence.diagnosis.likely_outcome} (${intelligence.diagnosis.recovery_probability_pct}) | <strong>Best window:</strong> ${intelligence.diagnosis.best_window}</p>
        <p><strong>Best action:</strong> ${intelligence.diagnosis.best_action} | <strong>Confidence:</strong> ${intelligence.diagnosis.confidence}</p>
        <button class="btn btn-sm btn-outline" onclick="replayTransaction('${tx.id}')">↻ Replay Decision</button>
        
        <h4 class="text-indigo mt-3">🗺️ Recovery Decision Graph</h4>
        <div class="my-2 p-2" style="background: rgba(99,102,241,0.08); border-radius: 6px; font-size: 0.75rem; overflow-x: auto;">
          ${graphHtml}
        </div>

        <h4 class="text-emerald mt-3">💡 Structured AI 4-Why Explanations</h4>
        <div class="p-2 text-sm" style="background: rgba(16,185,129,0.05); border-left: 3px solid var(--color-emerald); border-radius: 4px;">
          <p><strong>Why This Payment?</strong> ${exp.why_this_payment || ''}</p>
          <p><strong>Why This Action?</strong> ${exp.why_this_action || ''}</p>
          <p><strong>Why Now?</strong> ${exp.why_now || ''}</p>
          <p><strong>Why Not Others?</strong> ${exp.why_not_others || ''}</p>
        </div>

        <h4 class="text-amber mt-3">🛡️ Safety & Guardrail Verification</h4>
        <p><strong>Late Auth Protection:</strong> ${orch.late_authorization_protected ? 'ACTIVE (Monitoring payment.captured)' : 'INACTIVE'}</p>
        <p><strong>Guardrail Check Status:</strong> <span class="badge badge-success">${orch.guardrail_result?.status}</span> (${orch.guardrail_result?.reason})</p>
      </div>
    `;

    document.getElementById("modal-body").innerHTML = html;
    document.getElementById("detail-modal").classList.remove("hidden");
  } catch (err) {
    console.error("Error inspecting transaction:", err);
  }
}

function closeModalDirect() {
  document.getElementById("detail-modal").classList.add("hidden");
}

function closeModal(e) {
  if (e.target.id === "detail-modal") {
    closeModalDirect();
  }
}

async function triggerRecovery(txId) {
  try {
    const res = await fetch("/api/recover/trigger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transaction_id: txId })
    });
    const data = await res.json();
    if (!res.ok) {
      alert(`Recovery Failed: ${data.detail}`);
      return;
    }
    alert(`Success! Recovered ₹${data.result.recovered_amount}`);
    loadAnalytics();
    loadTransactions();
    loadAuditLogs();
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

async function loadAuditLogs() {
  try {
    const res = await fetch("/api/audit-logs");
    if (!res.ok) return;
    const data = await res.json();

    const badge = document.getElementById("audit-status-badge");
    if (data.integrity_verified) {
      badge.className = "badge badge-indigo";
      badge.innerText = `🔒 SHA-256 LEDGER VERIFIED (${data.chain_length} BLOCKS)`;
    } else {
      badge.className = "badge badge-crimson";
      badge.innerText = `⚠️ AUDIT LEDGER TAMPERED!`;
    }

    const container = document.getElementById("audit-chain-container");
    container.innerHTML = data.blocks.map(b => `
      <div class="audit-block">
        <div class="audit-header">
          <span class="audit-title">BLOCK #${b.index} | ${b.event}</span>
          <span>${new Date(b.timestamp * 1000).toLocaleTimeString()}</span>
        </div>
        <div class="text-muted font-mono text-sm mb-1">Transaction ID: ${b.transaction_id || 'SYSTEM'}</div>
        <div class="hash-string">PREV HASH: ${b.previous_hash}</div>
        <div class="hash-string text-indigo">HASH: ${b.hash}</div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load audit logs:", err);
  }
}

async function loadGuardrailConfig() {
  try {
    const res = await fetch("/api/config/guardrails");
    if (!res.ok) return;
    const cfg = await res.json();

    document.getElementById("cfg-max-retries").value = cfg.max_retries_per_transaction;
    document.getElementById("cfg-cooloff").value = cfg.min_cooloff_seconds;
    document.getElementById("cfg-max-discount").value = cfg.max_discount_percent;
    document.getElementById("cfg-hmac-req").value = cfg.require_webhook_hmac ? "true" : "false";
  } catch (err) {
    console.error("Failed to load guardrails config:", err);
  }
}

async function handleSaveGuardrails(e) {
  e.preventDefault();
  const maxRetries = parseInt(document.getElementById("cfg-max-retries").value);
  const cooloff = parseInt(document.getElementById("cfg-cooloff").value);
  const maxDiscount = parseFloat(document.getElementById("cfg-max-discount").value);
  const hmacReq = document.getElementById("cfg-hmac-req").value === "true";

  try {
    const res = await fetch("/api/config/guardrails", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        max_retries_per_transaction: maxRetries,
        min_cooloff_seconds: cooloff,
        max_discount_percent: maxDiscount,
        require_webhook_hmac: hmacReq
      })
    });
    if (res.ok) {
      alert("Guardrail policies updated successfully!");
      loadAnalytics();
      loadAuditLogs();
    }
  } catch (err) {
    alert(`Failed to save config: ${err.message}`);
  }
}
