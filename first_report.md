# Academic Progress Report: Pre-Trade Risk Management System (Phase I)

**Project Title:** Aegis Pre-Trade Risk Management System  
**Course / Track:** Software Verification & Testing / Financial Computing  
**Document ID:** `first_report.md`  
**Date:** October 23, 2026  
**Status:** Phase I Completed & Production-Ready  
**Repository Working Directory:** `/Users/ayankhan/Desktop/pre-trade-risk-S`

---

## Executive Summary

This progress report documents the transition of the **Pre-Trade Risk Management Simulator** from an initial proof-of-concept prototype with hardcoded values and command-line interfaces into a fully operational, production-ready pre-trade risk engine equipped with an institutional-grade financial dashboard.

Based directly on faculty review and domain-specific trading feedback, the system was re-architected to solve five critical deficiencies:
1. **Absence of User Interface:** Replaced raw HTTP/Swagger calls with a unified single-page application (React 18, TypeScript, Tailwind CSS) served directly via FastAPI.
2. **Opaque Rule Execution:** Built a deterministic, non-short-circuiting pipeline with real-time pre-validation and interactive audit dossiers for complete operational transparency.
3. **Penny Stock Anomaly ($0.01 Input):** Implemented **RISK-05 (Penny Stock Floor)** to intercept sub-dollar microcaps and prevent illiquid/erroneous executions.
4. **Hardcoded Configuration:** Transitioned all risk thresholds (position sizing, compliance blacklists, daily limits) to dynamic, runtime-configurable parameters via REST endpoints and UI controls.
5. **System Usability & Practical Relevance:** Introduced fat-finger price protection (RISK-07), daily portfolio limits (RISK-08 & 09), 1-click demonstration test buttons, and telemetry charts.

The test suite was expanded from **88 to 124 passing automated tests**, achieving 100% test pass rate across unit, integration, and frontend static asset delivery layers.

---

## 1. Faculty Feedback & Corrective Action Matrix

| Faculty Observation / Critique | Underlying Vulnerability | Engineering Remedy Implemented | Verification Method |
|---|---|---|---|
| *"There is no UI; why must orders be entered via curl/Swagger?"* | Prototype lacked presentation layer; inaccessible to non-technical traders. | Engineered a responsive financial terminal SPA (React 18 + Tailwind CSS) compiled into FastAPI's static asset bundle (`app/static/`). | End-to-end browser testing + automated SPA routing test (`test_frontend.py`). |
| *"When $0.01 was entered, it passed. This is less than a penny stock and should be an invalid price."* | Absence of price-floor boundaries; system only validated that price was $> 0$. | Introduced **RISK-05 (Penny Stock Protection)** with a configurable floor (default: \$1.00). Submissions below this threshold are immediately rejected with diagnostic reasoning. | Dedicated unit tests (`test_penny_stock_001_rejected`) + API integration tests. |
| *"I didn't understand how the risk rules are being applied or the logic behind them."* | Black-box decision outcome (`APPROVED`/`REJECTED`) gave no visibility into individual gate evaluations. | Shifted engine to an exhaustive non-short-circuiting model. Added live pre-validation feedback on keystroke, an interactive 9-gate audit matrix, and a visual architectural workflow. | UI verification + structured response schema (`risk_checks` array). |
| *"The values are hardcoded in the demonstration phase."* | Risk parameters were static constants, requiring code changes to alter limits. | Designed `RiskConfig` data model with runtime mutation via `PUT /api/risk-config`, persisted across sessions, with inline editing in the UI. | `test_update_risk_config` integration test + live configuration UI. |
| *"Make it polished and usable for someone who actually trades stocks."* | System lacked institutional features like fat-finger guards, cumulative daily limits, and history search. | Added fat-finger price ceilings (RISK-07), daily order throttles (RISK-08), cumulative notional caps (RISK-09), and an audit ledger with search and status filters. | 26 new unit tests + automated API tests. |

---

## 2. System Architecture & Technical Specifications

```
+-----------------------------------------------------------------------------------+
|                        React 18 + TypeScript Web Dashboard                        |
|   [Order Terminal]    [Audit Ledger]    [Risk Rules Manager]    [Risk Analytics]   |
+------------------------------------------+----------------------------------------+
                                           | HTTP REST / JSON
                                           v
+-----------------------------------------------------------------------------------+
|                             FastAPI Backend Gateway                               |
|   /api/orders         /api/risk-config         /api/risk-rules       /api/health   |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                            Domain & Risk Evaluation Layer                         |
|   Order Service  -->  Risk Engine (9 Non-Short-Circuit Gates)  -->  Config State  |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                       Persistence Layer (aiosqlite / SQLite)                      |
|                 Orders Table (id, symbol, side, notional, status,                 |
|                      rejection_reasons, risk_checks, created_at)                  |
+-----------------------------------------------------------------------------------+
```

### 2.1 Backend Layer (FastAPI & Python 3.14)
- **Modular Hexagonal Architecture:** Clean decoupling between API routing (`app/api/`), service orchestration (`app/services/`), domain models (`app/models/`), repository persistence (`app/repositories/`), and data schemas (`app/schemas/`).
- **Precision Monetary Arithmetic:** All price and notional calculations use Python's `Decimal` type to prevent IEEE-754 floating-point inaccuracies.
- **Finite State Machine Invariants:** Lifecycle enforces valid state transitions:
  $$\text{CREATED} \longrightarrow \text{VALIDATING} \longrightarrow \begin{cases} \text{APPROVED} \longrightarrow \text{EXECUTED} \\ \text{REJECTED} \end{cases}$$
  Illegal transitions (e.g., executing a rejected trade or re-approving an executed trade) throw `InvalidStateTransitionError`.

### 2.2 Frontend Layer (React 18, TypeScript & Tailwind CSS)
- **Build & Asset Pipeline:** Built with Vite 5, outputting optimized static bundles into `app/static/`, enabling zero-overhead single-command deployment (`uvicorn app.main:app`).
- **Real-Time Client Pre-Validation:** Re-evaluates order parameters locally against cached risk configuration before dispatch, providing instantaneous visual feedback.
- **Visual Terminal Aesthetic:** Slate-950 dark theme matching professional financial terminals (Bloomberg, Refinitiv, TradingView), styled with Tailwind CSS and Lucide icons.

---

## 3. The 9 Deterministic Pre-Trade Risk Gates

The risk engine runs an exhaustive, non-short-circuiting evaluation across 9 distinct compliance and risk gates:

| Rule ID | Rule Name | Category | Enforcement Condition | Default Parameter |
|---|---|---|---|---|
| **RISK-01** | Maximum Order Value | Position Limits | $\text{Quantity} \times \text{Price} \le \text{Max Value}$ | $\$10,000.00$ |
| **RISK-02** | Compliance Blacklist | Regulatory | $\text{Symbol} \notin \text{Restricted List}$ | `TSLA`, `GME`, `AMC` |
| **RISK-03** | Quantity Validity | Input Validation | $\text{Quantity} \in \mathbb{Z}^+$ and $\text{Quantity} > 0$ | Positive integer |
| **RISK-04** | Price Validity | Input Validation | $\text{Price} \in \mathbb{R}^+$ and $\text{Price} > 0$ | Positive decimal |
| **RISK-05** | Penny Stock Floor | Price Controls | $\text{Price} \ge \text{Min Price Threshold}$ | $\$1.00$ (Rejects $\$0.01$) |
| **RISK-06** | Maximum Quantity Cap | Position Limits | $\text{Quantity} \le \text{Max Quantity Cap}$ | $10,000$ shares |
| **RISK-07** | Fat-Finger Ceiling | Price Controls | $\text{Price} \le \text{Max Price Threshold}$ | $\$50,000.00$ |
| **RISK-08** | Daily Order Limit | Activity Limits | $\text{Orders Placed Today} < \text{Max Daily Orders}$ | $50$ orders/day |
| **RISK-09** | Daily Notional Cap | Portfolio Limits | $\text{Cumulative Notional Today} + \text{Order Value} \le \text{Max Notional}$ | $\$500,000.00$/day |

### 3.1 Non-Short-Circuiting Rationale
In institutional execution systems, rejecting an order solely on the first failing rule forces the trader or execution algorithm to repeatedly resubmit to uncover downstream violations. By running all checks concurrently, the engine constructs a full diagnostic matrix in a single pass, enhancing transparency and operational auditability.

---

## 4. UI Module Overview

The frontend application provides four dedicated operational tabs:

1. **Order Execution Terminal (`/`)**
   - Interactive order entry form with auto-capitalizing ticker inputs, side toggle (BUY/SELL), and dynamic notional calculation.
   - **Demonstration Test Buttons:** 1-click test scenarios designed specifically for faculty evaluation:
     - `Valid Order`: `AAPL 10 @ $150.00` $\rightarrow$ Approved.
     - `Penny Stock ($0.01)`: `PENN 100 @ $0.01` $\rightarrow$ Rejected by RISK-05.
     - `Restricted Symbol`: `TSLA 5 @ $100.00` $\rightarrow$ Rejected by RISK-02.
     - `Fat-Finger Price`: `AAPL 1 @ $60,000.00` $\rightarrow$ Rejected by RISK-07.
     - `Exceeds Max Value`: `MSFT 100 @ $250.00 ($25,000)` $\rightarrow$ Rejected by RISK-01.
     - `Valid Sell`: `NVDA 10 @ $120.00` $\rightarrow$ Approved sell-side execution.
   - **Live Pre-Check Card:** Dynamic indicator updating per keystroke to preview which rules pass or fail prior to submission.
   - **Decision Banner:** Color-coded status card (`APPROVED` in emerald / `REJECTED` in rose) featuring an expandable **Audit Matrix** detailing pass/fail status across all 9 gates.

2. **Order Audit History Ledger (`/orders`)**
   - Real-time ledger displaying timestamp, ticker, side badge, share count, limit price, total notional, and final decision status.
   - Live filtering by ticker symbol, order status (`APPROVED` / `REJECTED`), and order side (`BUY` / `SELL`).
   - "Inspect" modal presenting the complete **Risk Audit Dossier** for any historical order.

3. **Risk Rules Engine Manager (`/rules`)**
   - Interactive rule cards displaying rule ID, category badges, descriptions, and current threshold values.
   - Inline configuration editors allowing immediate threshold modification via `PUT /api/risk-config`.
   - Visual architectural pipeline flowchart detailing the six-stage order verification lifecycle.

4. **Risk Analytics Dashboard (`/analytics`)**
   - KPI telemetry cards: Orders Today, Approval Rate (%), Session Notional Exposure ($), and All-Time Cumulative Volume.
   - Recharts Visualizations: Session vs. All-Time Approval/Rejection comparison bar chart, and Decision Ratio distribution donut chart.
   - Most active tickers summary table.

---

## 5. Verification & Testing

The project's quality assurance framework combines unit testing, boundary-value analysis, API integration testing, and database migration verification.

### 5.1 Test Suite Breakdown (124 Automated Tests)

```bash
$ .venv/bin/python -m pytest tests/ -v
============================= 124 passed in 0.41s ==============================
```

- **Order Model & Enums (`tests/unit/test_order_model.py`):** 11 tests verifying enum parsing, defaults, and decimal value integrity.
- **State Machine Transitions (`tests/unit/test_state_transitions.py`):** 28 tests verifying valid lifecycle progressions and strict rejection of illegal state changes.
- **Baseline Risk Engine (`tests/unit/test_risk_engine.py`):** 44 tests covering boundary-value analysis on maximum order values (\$9,999.99, \$10,000.00, \$10,000.01), case-insensitive symbol restrictions, and input validation.
- **New Risk Rules (`tests/unit/test_new_risk_rules.py`):** 26 tests validating RISK-05 through RISK-09 (including \$0.01 penny stock interception, fat-finger thresholds, share quantity limits, and daily caps).
- **API Integration (`tests/integration/test_submit_order.py`):** 12 integration tests validating complete HTTP request/response lifecycles, configuration updates (`PUT /api/risk-config`), order listing, and telemetry endpoints.
- **Frontend SPA Routing (`tests/integration/test_frontend.py`):** 3 tests ensuring static HTML/JS assets are served and client-side routes (`/orders`, `/rules`, `/analytics`) resolve correctly without shadowing `/api/*`.

### 5.2 Database Migration Verification
Resolved a legacy database schema issue where existing `orders.db` instances lacked the `risk_checks` column. Implemented an automatic `PRAGMA table_info` migration inside `init_db()` alongside defensive row parsing in `order_repository.py`.

---

## 6. How to Run the Application

### 6.1 Starting the Unified Server
From the project root:

```bash
cd /Users/ayankhan/Desktop/pre-trade-risk-S
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6.2 Accessing Application Interfaces
- **Trading Dashboard:** [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 7. Next Steps & Future Roadmap (Phase II)

1. **Market Data Feed Simulator:** Integrate WebSocket or simulated Level-1 quotes to allow dynamic bid/ask spread checks and slippage estimation.
2. **Account Capital & Margin Ledger:** Track mock buying power and maintenance margin requirements on a simulated portfolio balance.
3. **Order Type Expansion:** Extend beyond limit/market orders to include Stop-Loss, Take-Profit, and Trailing Stops.
4. **Historical Backtesting Sandbox:** Allow users to replay historical market scenarios against configured risk rules to measure rejection frequency and false-positive rates.

---

**Report Prepared By:** Project Team  
**Reviewed For:** Faculty Evaluation & Phase I Milestone Defense
