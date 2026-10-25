# Aegis Pre-Trade Risk Management System & Indian Market Data Workstation

A high-performance pre-trade risk management engine, Indian market data workstation, and simulated portfolio accounting platform built with Python (FastAPI) and React (TypeScript + Tailwind CSS + TradingView Lightweight Charts).

> **Trading Simulator & Educational Platform.** Evaluates deterministic pre-trade risk controls without risking live market capital or requiring live broker credentials.

---

## Project Status: Production Ready (v0.3.0 Release 1 Complete)

This system provides institutional-grade pre-trade risk controls, real-time live market data streaming for Indian equities (NSE Cash / DhanHQ integration), interactive TradingView candlestick charting, preliminary stock screening, and a complete simulated portfolio accounting engine.

### Milestones & Capabilities

| Area / Module | Status | Technical Implementation |
|---|---|---|
| **Indian Market Workstation** | Completed | Live NSE Cash top 20 equity feed (Nifty 50 subset) with TradingView Lightweight Charts (v5) displaying 1m, 5m, and 1D candlesticks with real-time tick streaming. |
| **DhanHQ Integration** | Completed | Full adapter supporting DhanHQ WebSocket binary frame unpacking (`DhanPacketDecoder`) with deterministic mock provider fallback. |
| **Pre-Trade Risk Engine** | Completed | 9 non-short-circuiting risk gates with currency-aware profile limits (INR / USD), preview endpoint (`/api/orders/preview`), and strict concurrency serialization. |
| **Stock Screener** | Completed | Filter Indian equities by price, volume, and percentage change with preliminary risk gate advisory flags and one-click order staging. |
| **Simulated Accounting** | Completed | Strict paper trading sandbox: settlement of approved orders (`/api/orders/{id}/execute`), position tracking with volume-weighted average price (VWAP), cash balance updates, and real-time unrealized P&L calculation. |
| **Multi-Currency Support** | Completed | Strict isolation between legacy USD limits and Indian Rupee (`INR_DEFAULT` with ₹5,00,000 order cap). |
| **Automated Test Suite** | Completed | **161 automated tests** passing across unit, integration, concurrency race condition tests, and property-based invariants (Hypothesis). |

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

## Architecture & Data Flow

```
+-----------------------------------------------------------------------------------+
|                        React 18 + TypeScript Web Dashboard                        |
|   [Order Terminal]    [Audit Ledger]    [Risk Rules Manager]    [Risk Analytics]   |
+------------------------------------------+----------------------------------------+
                                           | HTTP / REST (Vite proxy / FastAPI)
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

## Demonstration Scenarios (For Faculty & Evaluators)

Within the **Order Execution Terminal** tab, use the built-in **Demonstration Test Scenarios** buttons to immediately test edge cases:

1. **✓ Valid Order (`AAPL 10 @ $150`)**: Passes all 9 risk gates; order transitions to `APPROVED`.
2. **✗ Penny Stock ($0.01) (`PENN 100 @ $0.01`)**: Triggers **RISK-05** rejection (sub-$1.00 microcap protection).
3. **✗ Restricted Symbol (`TSLA 5 @ $100`)**: Triggers **RISK-02** compliance blacklist rejection.
4. **✗ Fat-Finger Price (`AAPL 1 @ $60,000`)**: Triggers **RISK-07** price ceiling protection.
5. **✗ Exceeds Max Value (`MSFT 100 @ $250 = $25k`)**: Triggers **RISK-01** single-order notional cap ($10,000 limit).
6. **✓ Valid Sell (`NVDA 10 @ $120`)**: Verifies symmetry for sell-side order processing.

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

Run the full pytest suite (**161 tests**):

```bash
.venv/bin/python -m pytest tests/ -v
```

- **Unit tests**: `tests/unit/` (models, state machine, risk rules 01 through 09, mock market data provider, Dhan binary decoder, Hypothesis property-based tests)
- **Integration tests**: `tests/integration/` (order submission, execute and preview endpoints, market data API, stock screener, simulated portfolio settlement, concurrency race condition protections, SPA static file serving)

---

## API Reference

All backend endpoints are hosted under `/api` and `/ws`:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/orders` | Submit and evaluate order against all 9 risk gates |
| `POST` | `/api/orders/preview` | Dry-run pre-trade risk evaluation without persisting |
| `POST` | `/api/orders/{id}/execute` | Execute an approved order and settle into simulated portfolio |
| `GET` | `/api/orders` | Retrieve order audit history ledger |
| `GET` | `/api/orders/{id}` | Inspect full risk dossier for a single order |
| `GET` | `/api/market/status` | Current market feed health and telemetry |
| `GET` | `/api/market/instruments` | Active NSE Cash equity universe |
| `GET` | `/api/market/quotes` | Live snapshots for all universe instruments |
| `GET` | `/api/market/quotes/{symbol}` | Quote snapshot for a single symbol |
| `GET` | `/api/market/candles` | Historical OHLCV candles (1m, 5m, 1D) |
| `GET` | `/api/screener` | Stock screener with preliminary risk checks |
| `GET` | `/api/portfolio/summary` | Simulated account cash, portfolio value, and P&L |
| `GET` | `/api/portfolio/positions` | Open positions with average prices and P&L |
| `GET` | `/api/risk-config` | View active risk thresholds and restricted list |
| `PUT` | `/api/risk-config` | Update risk thresholds dynamically |
| `GET` | `/api/risk-rules` | Retrieve metadata and status for all 9 rules |
| `GET` | `/api/orders/stats/summary` | Aggregate daily and all-time risk telemetry |
| `GET` | `/api/health` | Health check probe |
| `WS` | `/ws/market` | WebSocket stream for real-time quote updates |
