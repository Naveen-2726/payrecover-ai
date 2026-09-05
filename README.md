# ⚡ PayRecover AI - Autonomous Payment Recovery & Dunning Engine

[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-green.svg)](https://fastapi.tiangolo.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.9.0-orange.svg)](https://scikit-learn.org/)
[![Build Status](https://img.shields.io/badge/tests-16%20passed-brightgreen.svg)](tests/)
[![Security](https://img.shields.io/badge/SHA--256-Ledger%20Verified-indigo.svg)](#cryptographic-audit-ledger)

**PayRecover AI** is an intelligent payment recovery and dunning engine built for the **Razorpay AI Buildathon**. It intercepts payment failure webhooks (`payment.failed`, `subscription.halted`, `invoice.payment_failed`), performs ML recovery propensity scoring, evaluates AI strategy recommendations, enforces deterministic safety guardrails, and automates multi-channel payment retries.

> **Note**: This repository features a **Razorpay-inspired test integration** with simulated payment webhooks, mock payment gateway APIs, and synthetic training datasets modeling Indian banking failure dynamics.

---

## 📐 System Architecture Diagram

```
                              ┌──────────────────────────────────┐
                              │  Simulated Webhook / Merchant    │
                              └─────────────────┬────────────────┘
                                                │ POST /api/webhooks/razorpay
                                                ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FastAPI Server                                      │
│                                                                                        │
│  1. HMAC SHA-256 Signature Check ──> 2. Idempotency Lock ──> 3. PII Masking Engine     │
└───────────────────┬─────────────────────────────────────────────────┬──────────────────┘
                    │                                                 │
                    ▼                                                 ▼
┌──────────────────────────────────────┐          ┌──────────────────────────────────────┐
│       ML Propensity Engine           │          │       AI Strategy Agent              │
│  • GradientBoosting Classifier       │          │  • Failure Context Analysis          │
│  • Recovery Probability P(recovery)  │          │  • Optimal Time Scheduling           │
│  • Optimal Retry Hour Regressor      │          │  • Dynamic Incentive Recommendation  │
└───────────────────┬──────────────────┘          └───────────────────┬──────────────────┘
                    │                                                 │
                    └───────────────────────┬─────────────────────────┘
                                            │
                                            ▼
                        ┌──────────────────────────────────────┐
                        │     Deterministic Safety Guardrails   │
                        │  • Max 3 Retries Cap                 │
                        │  • 2-Hour Minimum Cool-off           │
                        │  • 10% Maximum Discount Cap          │
                        │  • Schema & Bounds Validation        │
                        └───────────────────┬──────────────────┘
                                            │
                                            ├──────────── APPROVED ────────────┐
                                            │                                  │
                                            ▼                                  ▼
                        ┌───────────────────────────────┐   ┌──────────────────────────────┐
                        │   Mock Razorpay Retry API     │   │  Cryptographic Audit Ledger  │
                        │   (Scenario A / B Retry)      │   │  (SHA-256 Block Chaining)    │
                        └───────────────────────────────┘   └──────────────────────────────┘
```

---

## 📊 Evaluation & Machine Learning Metrics

Evaluated on **100 synthetic test transactions** modeling Indian banking payment dynamics (HDFC, ICICI, SBI, UPI Intent, e-NACH):

| Metric | Real Evaluated Score |
| :--- | :--- |
| **Total Test Transactions** | `100` |
| **Total Failed Volume** | `₹168,736.86` |
| **Recovered Revenue** | `₹121,210.06` |
| **Recovery Rate %** | `71.83%` |
| **ML Model Accuracy** | `77.00%` |
| **Precision** | `83.56%` |
| **Recall** | `84.72%` |
| **F1 Score** | `84.14%` |
| **False Positives Count** | `12` |
| **False Negatives Count** | `11` |

---

## 🛠️ Quickstart Guide

### Prerequisites
- Python 3.10+ installed

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Test Suite
```bash
py -m pytest -v
```
*(Runs all 16 unit & integration tests covering webhooks, HMAC, ML inference, guardrails, audit ledger, and API endpoints)*

### 3. Run ML Evaluation Script
```bash
py eval_ml.py
```

### 4. Launch Web Application
```bash
py run_app.py
```
Open your browser at **`http://localhost:8000`** to access the live PayRecover AI Dashboard & Razorpay Webhook Simulator.

---

## 🎯 Demo Scenarios

1. **Scenario A (Success Recovery)**:
   - Webhook: `payment.failed` (HDFC, `BAD_REQUEST_PAYMENT_TIMED_OUT`, ₹2,999)
   - Flow: HMAC verified -> ML propensity calculated (88%) -> Retried via gateway -> Status `RECOVERED` -> SHA-256 ledger block appended.
2. **Scenario B (Circuit Breaker Failure)**:
   - Webhook: `subscription.halted` (SBI, `FORCE_FAILURE_GATEWAY_TIMEOUT`, ₹14,999)
   - Flow: HMAC verified -> Gateway timed out 3 consecutive times -> Retry limit cap triggered -> Escalated to `HUMAN_ESCALATION_REQUIRED` -> Audit entry logged.

---

## 🛡️ Safety & Compliance Controls
- **HMAC Verification**: Standard Razorpay HMAC-SHA256 signature check using constant-time comparison.
- **PII Masking**: Customer emails (`r***@domain.com`) and phone numbers (`+9198******10`) obfuscated at ingestion.
- **Idempotency**: Duplicate event IDs return `SKIPPED`.
- **Tamper Evidence**: Cryptographic hash chain guarantees audit record immutability.
