# Aegis Pre-Trade Risk Management System

A high-performance pre-trade risk management engine and financial trading dashboard that evaluates simulated equity buy and sell orders against multi-tier compliance, position, and price rules before approval.

> **Trading Simulator & Educational Platform.** Evaluates deterministic pre-trade risk controls without risking live market capital or requiring live broker credentials.

---

## Key Features

1. **Enterprise Financial Dashboard (React + TypeScript + Tailwind CSS)**:
   - **Order Execution Terminal**: Interactive order submission with instant pre-validation as you type, quick-pick scenarios, and deterministic approval/rejection decision cards.
   - **Audit Trail & Order Ledger**: Filterable, sortable historical ledger with full audit dossier for every order.
   - **Risk Rules & Engine Manager**: Interactive card editor allowing users to configure limits and restricted securities on the fly.
   - **Risk Analytics**: Telemetry dashboard tracking daily notional exposure, approval rates, and decision distribution charts.

2. **9 Deterministic Pre-Trade Risk Gates**:
   - **RISK-01 (Max Order Value)**: Caps single-order notional value (default: $10,000.00).
   - **RISK-02 (Compliance Blacklist)**: Prohibits restricted symbols (e.g., TSLA, GME, AMC).
   - **RISK-03 (Quantity Validity)**: Enforces strictly positive integer unit sizing.
   - **RISK-04 (Price Validity)**: Enforces positive decimal pricing.
   - **RISK-05 (Penny Stock Floor)**: Protects against illiquid microcaps and sub-dollar volatility by rejecting prices below minimum (default: $1.00).
   - **RISK-06 (Position Quantity Cap)**: Limits maximum shares per order (default: 10,000 shares).
   - **RISK-07 (Fat-Finger Ceiling)**: Rejects abnormally elevated prices (default: $50,000.00 max).
   - **RISK-08 (Daily Order Count)**: Cumulative daily order throttle (default: 50 orders/day).
   - **RISK-09 (Daily Notional Limit)**: Cumulative portfolio notional cap (default: $500,000.00/day).

3. **Exhaustive Non-Short-Circuiting Evaluation**:
   - Rather than stopping on the first failure, the engine evaluates **all 9 rules simultaneously** to provide a complete diagnostic audit trail in a single response.

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend development/builds)

### 2. Setup Python Environment

```bash
# In project root
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Run the Unified Application

The React frontend is compiled directly into FastAPI's static assets:

```bash
uvicorn app.main:app --reload
```

- Open **[http://localhost:8000](http://localhost:8000)** for the **Trading Dashboard**.
- Open **[http://localhost:8000/docs](http://localhost:8000/docs)** for the **Swagger OpenAPI Specification**.

---

## Frontend Development (Optional)

If modifying the frontend source code:

```bash
cd frontend
npm install
npm run dev      # Starts Vite dev server with proxy at http://localhost:5173
npm run build    # Compiles production bundle directly to ../app/static/
```

---

## Automated Test Suite

Run the full pytest suite (124 tests):

```bash
.venv/bin/python -m pytest tests/ -v
```

- **Unit tests**: `tests/unit/` (models, state machine, risk rules 01 through 09)
- **Integration tests**: `tests/integration/` (order lifecycle, REST API, SPA routing)

---

## API Reference

All backend endpoints are hosted under `/api`:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/orders` | Submit and evaluate order against all 9 risk gates |
| `GET` | `/api/orders` | Retrieve order audit history ledger |
| `GET` | `/api/orders/{id}` | Inspect full risk dossier for a single order |
| `GET` | `/api/risk-config` | View active risk thresholds and restricted list |
| `PUT` | `/api/risk-config` | Update risk thresholds dynamically |
| `GET` | `/api/risk-rules` | Retrieve metadata and status for all 9 rules |
| `GET` | `/api/orders/stats/summary` | Aggregate daily and all-time risk telemetry |
| `GET` | `/api/health` | Health check probe |
