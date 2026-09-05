# ⚡ PayRecover AI — Governed Autonomous Revenue Recovery Engine

[![Python](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-green.svg)](https://fastapi.tiangolo.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.9.0-orange.svg)](https://scikit-learn.org/)
[![Security](https://img.shields.io/badge/SHA--256-Ledger%20Verified-indigo.svg)](#-cryptographic-audit-ledger)

**PayRecover AI** is a governed autonomous revenue-recovery engine designed for payment-failure scenarios.

It detects revenue at risk, analyzes payment failure context, predicts recovery probability, selects an economically optimal recovery intervention, validates AI decisions through deterministic governance controls, executes bounded recovery workflows, and measures recovered revenue.

> **Built for the Razorpay AI Buildathon — AI Revenue Recovery Track**

> ⚠️ **Important:** This project uses synthetic/demo transaction data, simulated payment events, and mock payment-gateway APIs. It does **not** claim live Razorpay production integration.

---

# 🎯 Problem

A failed payment does not always mean **"retry."**

Different failures require different interventions:

* Temporary gateway failures may require waiting.
* Bank/payment-route degradation may require an alternate route.
* Customer-action-required failures may require customer interaction.
* Payments affected by late authorization should not be blindly retried.
* High-value transactions may require human approval.
* Some recovery actions may cost more than the expected revenue recovered.

PayRecover treats recovery as a **decision and optimization problem**, rather than a simple retry workflow.

---

# 💡 Solution

PayRecover follows the principle:

> **AI recommends. Governance validates. Deterministic controls decide. Execution is bounded. Outcomes are measurable and auditable.**

The complete recovery pipeline is:

```text
Payment Event
      ↓
Webhook Security + Idempotency
      ↓
Payment & Error Intelligence
      ↓
Revenue Risk Detection
      ↓
ML Recovery Prediction
      ↓
AI Recovery Orchestrator
      ↓
Expected-Value Optimization
      ↓
Agent Governance
      ↓
Deterministic Guardrails
      ↓
Bounded Recovery Execution
      ↓
Payment State Machine
      ↓
Revenue Attribution
      ↓
Cryptographic Audit
      ↓
Agent Observability
```

---

# 🏗️ System Architecture

```text
                         PAYRECOVER AI
                              │
              ┌───────────────▼───────────────┐
              │ Payment Event Ingestion       │
              │ HMAC + Idempotency            │
              │ Duplicate/Replay Protection   │
              └───────────────┬───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │ Payment Intelligence          │
              │ • Error Semantics             │
              │ • Payment Health              │
              │ • Late Authorization          │
              │ • Reliability Forecast        │
              └───────────────┬───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │ Revenue Risk + ML Engine      │
              │ • Recovery Probability        │
              │ • Recovery Timing             │
              │ • Risk Scoring                │
              └───────────────┬───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │ AI Recovery Orchestrator      │
              │ • Failure Diagnosis           │
              │ • Strategy Recommendation     │
              │ • Decision Explanation        │
              └───────────────┬───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │ Expected-Value Optimizer      │
              │ • Recovery Probability        │
              │ • Recovery Cost               │
              │ • Communication Cost          │
              │ • Operational Cost             │
              └───────────────┬───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │ Agent Governance              │
              │ • Certification               │
              │ • Sandbox Evaluation           │
              │ • Policy Validation            │
              │ • Financial Budget             │
              │ • Consent Controls             │
              └───────────────┬───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │ Deterministic Guardrails      │
              │ • Action Limits                │
              │ • Retry Limits                 │
              │ • Contact Limits               │
              │ • Financial Limits             │
              │ • Kill Switch                  │
              └───────────────┬───────────────┘
                              │
             ┌────────────────┼─────────────────┐
             │                │                 │
             ▼                ▼                 ▼
        Smart Retry      Payment Link      Human Review
             │                │                 │
             └────────────────┼─────────────────┘
                              │
              ┌───────────────▼───────────────┐
              │ Payment State Machine         │
              │ Valid State Transitions       │
              │ Late-Authorization Handling   │
              └───────────────┬───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │ Measurement + Attribution     │
              │ Baseline Comparison           │
              │ Incremental Recovery          │
              └───────────────┬───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │ Audit + Agent Observability   │
              │ SHA-256 Ledger                │
              │ Health + Drift + Kill Switch  │
              └───────────────────────────────┘
```

---

# 🤖 AI & ML Recovery Intelligence

The ML layer estimates the probability that a failed payment can be recovered.

The prediction is **not allowed to directly execute payment actions**.

Instead:

```text
ML Prediction
      ↓
AI Recommendation
      ↓
Expected Value
      ↓
Governance
      ↓
Deterministic Guardrails
      ↓
Execution
```

## ML Evaluation

Evaluation was performed on **100 synthetic test transactions**.

| Metric              |          Result |
| ------------------- | --------------: |
| Test Transactions   |         **100** |
| Total Failed Volume | **₹168,736.86** |
| Recovered Revenue   | **₹121,210.06** |
| Recovery Rate       |      **71.83%** |
| Accuracy            |      **77.00%** |
| Precision           |      **83.56%** |
| Recall              |      **84.72%** |
| F1 Score            |      **84.14%** |
| False Positives     |          **12** |
| False Negatives     |          **11** |

These are **synthetic evaluation results** and are not production Razorpay metrics.

---

# 🧠 Payment Intelligence

PayRecover converts payment events into structured recovery context.

The intelligence layer considers:

* Error code
* Error source
* Error step
* Error reason
* Payment method
* Bank/payment route
* Payment health
* Customer action requirements
* Transaction value
* Recovery history
* Late-authorization signals

Example:

```text
Payment Failed
      ↓
Gateway Timeout
      ↓
Temporary Failure
      ↓
Payment Route Degraded
      ↓
Recovery Probability: HIGH
      ↓
Wait / Alternate Recovery
```

---

# 💰 Expected-Value Recovery Optimization

PayRecover does not optimize purely for the probability of success.

It evaluates the expected **net recovery value**.

```text
Expected Recovery Value
        -
Retry Cost
        -
Communication Cost
        -
Operational Cost
        =
Expected Net Recovery
```

Possible actions include:

* Smart retry
* Scheduled retry
* Alternate payment route
* Payment link
* UPI intent
* Human escalation
* No action

The system can **abstain** when acting is not economically or operationally justified.

---

# 🛡️ AI Agent Governance

PayRecover does not give an AI agent unrestricted authority over payment recovery.

## Agent Certification

Before activation, the agent can be evaluated against:

* Permission scope
* Data scope
* Action scope
* Financial limits
* Customer consent
* Dark-pattern checks
* Safety controls
* Audit coverage

Current result:

```text
Certification: CERTIFIED
Safety Score: 100%
Unsafe Actions: 0
Policy Violations: 0
```

---

# 🧪 Agent Sandbox

The recovery agent can be evaluated against a reproducible synthetic transaction cohort before activation.

```text
Evaluation Cohort: 100 transactions
Sandbox Result: PASS
Unsafe Actions: 0
```

The sandbox uses the existing recovery orchestration and evaluation pipeline rather than an isolated demonstration model.

---

# 🎛️ Agent Health Monitor

PayRecover continuously tracks operational indicators such as:

* Decisions
* Executed actions
* Abstentions
* Guardrail blocks
* Decision latency
* Performance indicators
* Drift indicators

Agent states:

```text
ACTIVE
   ↓
DEGRADED
   ↓
PAUSED
```

---

# 🛑 Kill Switch

The recovery agent can be paused through the governance layer.

When the agent is paused:

```text
Recovery Orchestrator
        ↓
Execution Blocked
        ↓
Audit Event
```

Resume requires a valid state transition.

Current verification:

```text
Pause: VERIFIED
Resume: VERIFIED
Unsafe actions while paused: 0
```

---

# 💵 Autonomous Recovery Budget

PayRecover supports bounded recovery spending.

Example demo configuration:

```text
Recovery Budget: ₹5,000
```

Execution-time checks prevent the system from exceeding the configured recovery budget.

When a financial boundary is reached:

```text
Recovery Action
      ↓
Budget Check
      ↓
LIMIT EXCEEDED
      ↓
ACTION BLOCKED
      ↓
HUMAN ESCALATION
      ↓
AUDIT EVENT
```

---

# 📡 Payment Reliability Forecast

PayRecover includes a synthetic **30-minute payment-reliability forecast** across **20 bank/payment routes**.

The forecast can inform recovery decisions by identifying potentially degraded payment paths.

```text
Payment Route
      ↓
Current Health
      ↓
Predicted Reliability
      ↓
Recovery Strategy
```

This is a **synthetic simulation**, not live gateway monitoring.

---

# 🔐 Webhook Security & Reliability

PayRecover includes safeguards for common webhook reliability problems.

### Security

* HMAC-SHA256 signature verification
* Constant-time comparison
* Idempotency
* Duplicate-event protection
* Replay protection

### Event Ordering

* Out-of-order event protection
* Valid payment state transitions
* Duplicate event handling
* Delayed event handling

Example:

```text
payment.failed
      ↓
Late Authorization
      ↓
payment.captured
```

The state machine prevents an already-successful payment from triggering an unnecessary recovery action.

---

# 🔄 Subscription Recovery

Subscription recovery is integrated into the same normalized transaction/event model used by the Revenue Control Tower.

Supported synthetic scenarios include:

* Temporary payment failure
* Customer-action-required failure
* Bank/payment-route failure
* Retry exhaustion
* Subscription recovery
* Human escalation

Subscription records contribute to the same recovery measurement and audit flow.

---

# 👤 Privacy-Safe Bounded Memory

PayRecover includes bounded customer recovery memory using **hashed customer keys**.

The memory can retain synthetic recovery context such as:

* Previous recovery outcome
* Preferred recovery method
* Recent recovery attempts
* Contact frequency

The implementation is designed for the synthetic/demo environment and does not claim production customer-data processing.

---

# 📱 Consent-Gated Customer Recovery

PayRecover supports a simulated customer recovery flow.

Example:

```text
Payment Failure
      ↓
Recovery Recommendation
      ↓
Customer Consent
      ↓
Mock Payment Link
      ↓
Customer Action
      ↓
Simulated Recovery
```

The consent gate prevents the recovery workflow from proceeding without the required customer authorization in the simulation.

---

# 🧾 Cryptographic Audit Ledger

Important recovery events are recorded in a tamper-evident audit ledger.

Audit information can include:

* Incoming payment events
* Recovery decisions
* Guardrail decisions
* Blocked actions
* State transitions
* Agent governance events
* Recovery outcomes
* Attribution information

The ledger uses **SHA-256 hash chaining** to provide tamper evidence.

---

# 📊 Revenue Recovery Results

Evaluation was performed using synthetic/demo cohorts.

## Baseline vs PayRecover

| Metric                |   Baseline |      PayRecover |
| --------------------- | ---------: | --------------: |
| Net Recovered Revenue | ₹44,063.86 |  **₹78,744.62** |
| Difference            |          — | **+₹34,680.76** |

## Incremental Recovered Revenue

```text
Payment Control-Tower Cohort:
₹14,347.90

Aggregate Including Subscription Scenarios:
₹30,947.38
```

These figures represent **synthetic evaluation results**.

They are not claims of real-world Razorpay revenue recovered.

---

# 🧪 Reliability & Governance Verification

Current final verification:

| Verification          |        Result |
| --------------------- | ------------: |
| Total Tests           |        **71** |
| Tests Passed          |        **71** |
| Tests Failed          |         **0** |
| Agent Certification   | **CERTIFIED** |
| Agent Sandbox         |      **PASS** |
| Safety Score          |      **100%** |
| Unsafe Actions        |         **0** |
| Policy Violations     |         **0** |
| Reliability Scenarios |  **6/6 PASS** |
| Forecast Routes       |        **20** |
| Kill Switch           |  **VERIFIED** |
| Customer Consent Gate |  **VERIFIED** |
| Diagnostics           |     **CLEAN** |

---

# 🎬 Judge Mode

Judge Mode provides deterministic scenarios demonstrating the complete recovery pipeline.

## Scenario 1 — Temporary Failure

```text
Payment Failure
→ Error Diagnosis
→ Recovery Prediction
→ Expected Value
→ Safe Retry
→ Recovery
→ Audit
```

## Scenario 2 — Customer Action Required

```text
Payment Failure
→ Customer Action Classification
→ Payment Link Strategy
→ Consent Gate
→ Recovery
→ Audit
```

## Scenario 3 — Payment Route Degradation

```text
Route Degradation
→ Reliability Forecast
→ Alternate Recovery Path
→ Guardrail Validation
→ Execution
→ Recovery
```

## Scenario 4 — Late Authorization

```text
Payment Failed
→ Late Authorization Signal
→ Retry Suppressed
→ Payment Later Captured
→ State Updated
→ Audit
```

## Scenario 5 — Subscription Failure

```text
Subscription Payment Failure
→ Recovery Prediction
→ Strategy Selection
→ Bounded Recovery
→ Subscription Recovery
→ Attribution
```

## Scenario 6 — High-Value Transaction

```text
High-Value Failure
→ Recovery Analysis
→ Financial Boundary Check
→ Human Review
→ Approved Action
→ Recovery
→ Audit
```

Each scenario follows:

```text
Failure
   ↓
Diagnosis
   ↓
Revenue at Risk
   ↓
ML Prediction
   ↓
AI Recommendation
   ↓
Expected Value
   ↓
Agent Governance
   ↓
Deterministic Guardrails
   ↓
Action
   ↓
Payment State
   ↓
Revenue Outcome
   ↓
Audit Event
```

---

# 🧩 Technology Stack

* **Python**
* **FastAPI**
* **scikit-learn**
* **React / frontend dashboard**
* **SQLite / synthetic transaction store**
* **Mock payment gateway**
* **Simulated payment webhooks**
* **SHA-256 audit ledger**
* **Deterministic policy and guardrail engine**

---

# 📁 Project Structure

```text
payrecover-ai/
│
├── app/
│   ├── API services
│   ├── recovery services
│   ├── governance
│   └── dashboard components
│
├── models/
│   └── ML / decision models
│
├── tests/
│   └── unit, integration, reliability,
│       and governance tests
│
├── eval_ml.py
├── eval_results.json
├── requirements.txt
├── run_app.py
└── README.md
```

---

# ⚡ Quickstart

## Prerequisites

Python 3.10+

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Run Complete Test Suite

```bash
py -m pytest -v
```

Expected final result:

```text
71 passed
```

## 3. Run ML Evaluation

```bash
py eval_ml.py
```

## 4. Launch Web Application

```bash
py run_app.py
```

Open:

```text
http://localhost:8000
```

---

# ⚠️ Limitations

This project intentionally uses synthetic/demo infrastructure.

* No live Razorpay production integration
* Payment gateway responses are simulated
* Evaluation data is synthetic
* Payment reliability forecasts are simulated
* Subscription scenarios use synthetic data
* Customer memory is synthetic and privacy-safe
* Browser runtime automation was not included because the development environment did not have Node.js available
* Confidence intervals are not reported because the current synthetic evaluation methodology does not support statistically reliable estimates

The project does **not** claim production payment-processing capability.

---

# 🔎 Design Principles

### 1. AI Does Not Have Unrestricted Authority

AI generates recommendations.

Deterministic controls decide whether those recommendations are allowed.

### 2. Every Recovery Action Is Bounded

Financial limits, action limits, customer-contact rules, policy rules, and kill-switch controls can prevent unsafe execution.

### 3. Recovery Must Be Economically Justified

A high probability of recovery does not automatically mean an action should be executed.

The system considers expected net recovery.

### 4. Payment State Is Authoritative

Late authorization, duplicate events, and out-of-order webhooks must not corrupt the payment state.

### 5. Outcomes Must Be Measurable

PayRecover measures recovery outcomes against a baseline using synthetic evaluation cohorts.

---

# 🏆 Key Results

```text
71/71 TESTS PASSING

ML F1
84.14%

AGENT SAFETY
100%

UNSAFE ACTIONS
0

POLICY VIOLATIONS
0

RELIABILITY SCENARIOS
6/6 PASS

SANDBOX
PASS

CERTIFICATION
CERTIFIED

PAYRECOVER NET RECOVERY
₹78,744.62

BASELINE NET RECOVERY
₹44,063.86

AGGREGATE INCREMENTAL RECOVERY
₹30,947.38
```

---

# 💬 Core Project Statement

> **PayRecover AI does not simply retry failed payments. It understands payment context, predicts recoverability, chooses an economically justified intervention, validates the action through deterministic governance, executes within strict boundaries, and measures the resulting recovery.**

---

# 👤 Author

**Naveen Kumar**

GitHub: **Naveen-2726**

---

# 📌 Buildathon

**Razorpay AI Buildathon — AI Revenue Recovery Track**

PayRecover AI is a synthetic/demo implementation created for the buildathon.

**No live Razorpay production integration is claimed.**
