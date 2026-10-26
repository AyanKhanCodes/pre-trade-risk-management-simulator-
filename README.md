# Aegis Pre-Trade Risk Management System & Indian Market Data Workstation

A high-performance pre-trade risk management engine, Indian equity market workstation, and simulated portfolio clearinghouse platform built with Python (FastAPI) and React (TypeScript + Tailwind CSS + TradingView Lightweight Charts).

> **Trading Simulator & Educational Platform.** Evaluates deterministic pre-trade risk controls without risking live market capital or requiring live broker credentials.

---

## Project Status: Production Ready (v0.4.0 Baseline)

This system provides institutional-grade pre-trade risk controls across both **BUY** and **SELL** order sides, real-time live market data streaming for Indian equities (NSE Cash / DhanHQ integration), interactive TradingView candlestick charting, preliminary stock screening, and an ACID-isolated simulated portfolio clearinghouse.

### Milestones & Capabilities

| Area / Module | Status | Technical Implementation |
|---|---|---|
| **Indian Market Workstation** | Completed | Live NSE Cash top 20 equity feed (Nifty 50 subset) with TradingView Lightweight Charts (v5) displaying 1m, 5m, and 1D candlesticks with real-time tick streaming. |
| **DhanHQ Integration** | Completed | Full adapter supporting DhanHQ WebSocket binary frame unpacking (`DhanPacketDecoder`) with deterministic mock provider fallback. |
| **Pre-Trade Risk Engine** | Completed | **12 non-short-circuiting risk gates** with single-currency Indian Rupee (INR ₹) profile (`INR_DEFAULT` with ₹5,00,000 max order cap, ₹50,00,000 daily notional limit). |
| **SELL-Side Risk Controls** | Completed | Authoritative inventory verification: Short-selling prohibition (`RISK-10`), dynamic open sell order reservations (`RISK-11`), and ledger integrity fail-safe (`RISK-12`). |
| **Holdings Telemetry Bar** | Completed | Live inventory tracking in the order entry terminal displaying `Position Held`, `Reserved by Open Sells`, and `Net Sellable Quantity` with 1-click "Sell Max Available". |
| **Stock Screener** | Completed | Filter Indian equities by price, volume, and percentage change with preliminary risk gate advisory flags and one-click order staging. |
| **Simulated Clearinghouse** | Completed | Strict paper trading sandbox: settlement of approved orders (`/api/orders/{id}/execute`), position tracking with volume-weighted average price (VWAP), cash balance updates, and real-time unrealized P&L calculation. |
| **Concurrency & ACID Isolation** | Completed | Mutex serialization (`async with _order_lock:`) wrapping order validation, reservation calculation, and portfolio settlement to prevent race conditions and over-allocation. |
| **Automated Test Suite** | Completed | **180 automated tests** passing across unit, integration, concurrency race condition tests, and property-based invariants (Hypothesis). |

---

## 12 Deterministic Pre-Trade Risk Gates

The risk engine evaluates all 12 rules in parallel without short-circuiting. If an order violates one or multiple rules, every failing gate is captured in the audit matrix.

| Rule ID | Gate Name | Applicable Side | Description & Default Threshold (INR ₹) |
|:---|:---|:---:|:---|
| **RISK-01** | **Max Order Notional** | `BOTH` | Single-order notional value cannot exceed limit (default: **₹5,00,000.00**). |
| **RISK-02** | **Compliance Blacklist** | `BOTH` | Blocks orders for restricted or surveillance symbols (e.g., `YESBANK`, `SUZLON`, `IDEA`). |
| **RISK-03** | **Quantity Validity** | `BOTH` | Enforces strictly positive integer sizing ($quantity \in \mathbb{Z}^+$). |
| **RISK-04** | **Price Validity** | `BOTH` | Enforces positive decimal pricing ($price > 0$). |
| **RISK-05** | **Penny Stock Floor** | `BOTH` | Rejects sub-rupee microcap volatility (price must be $\ge$ **₹1.00**). |
| **RISK-06** | **Position Quantity Cap** | `BOTH` | Limits maximum share count per order (default: **10,000 shares**). |
| **RISK-07** | **Fat-Finger Protection** | `BOTH` | Rejects erroneous execution prices above threshold (default: max **₹2,00,000.00** / share). |
| **RISK-08** | **Daily Order Count Throttle**| `BOTH` | Cumulative daily order submission limit (default: **100 orders/day**). |
| **RISK-09** | **Daily Notional Cap** | `BOTH` | Cumulative daily portfolio traded value limit (default: **₹50,00,000.00/day**). |
| **RISK-10** | **Available Holdings Check** | `SELL` | Prohibits naked short-selling. Rejects SELL orders when held position is $0$. (*Marked `NOT_APPLICABLE` for BUY orders*). |
| **RISK-11** | **Open Sell Order Reservation**| `SELL` | Prevents double-selling inventory reserved by pending approved SELL orders ($\text{Qty} \le \text{Sellable Qty} = \max(0, \text{Held Qty} - \text{Reserved Qty})$). |
| **RISK-12** | **Position Ledger Integrity** | `SELL` | Fail-safe verifying position ledger sanity and non-negative inventory ($\text{Held Qty} \ge 0$). |

---

## Order Lifecycle & Finite State Machine

The system enforces a strict finite state machine for all orders:

```
[ CREATED ]
     |
     v
[ VALIDATING ] ──> Evaluates 12 Risk Gates (ACID Isolated)
     |
     +─────────────+
     |             |
     v             v
[ APPROVED ]   [ REJECTED ] (Terminal State with Rejection Dossier)
     |
     v (User clicks "⚡ Simulate Execution" or calls /api/orders/{id}/execute)
[ EXECUTED ] ──> Settles cash balance and updates position holdings in simulated portfolio
```

> **Important Lifecycle Note:** An **`APPROVED`** order has passed all pre-trade risk checks. In simulated mode, it reserves sellable quantity (if SELL), but holdings and cash balance do not settle until the order transitions to **`EXECUTED`**.

---

## Architecture & Data Flow

```
+-----------------------------------------------------------------------------------+
|                        React 18 + TypeScript Web Dashboard                        |
|  [Market Workstation]  [Screener]  [Simulated Portfolio]  [Order Entry & Audits]  |
+------------------------------------------+----------------------------------------+
                                           | HTTP / WebSocket (Vite proxy / FastAPI)
                                           v
+-----------------------------------------------------------------------------------+
|                             FastAPI Backend Gateway                               |
|   /api/orders     /api/portfolio     /api/market     /api/risk-rules    /ws/market|
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                    Domain, Risk Engine & Holdings Telemetry Layer                 |
|   Order Service (Mutex Serialized)  <──>  Portfolio Service (Dynamic Reservations)|
|                                     │                                             |
|                                     v                                             |
|                   Risk Engine (12 Deterministic Risk Gates)                       |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                       Persistence Layer (aiosqlite / SQLite)                      |
|         • orders (id, symbol, side, notional, status, risk_checks, ...)            |
|         • simulated_account (cash_balance, portfolio_value)                       |
|         • simulated_positions (symbol, quantity, avg_price, unrealized_pnl)      |
+------------------------------------------+----------------------------------------+
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

# Install dependencies in editable mode
pip install -e ".[dev]"
```

### 3. Run the Application

```bash
# Launch FastAPI backend with integrated frontend static build
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- Open **[http://localhost:8000](http://localhost:8000)** for the **Trading Dashboard**.
- Open **[http://localhost:8000/docs](http://localhost:8000/docs)** for the **Interactive OpenAPI Specification**.

### 4. Frontend Development (Optional)

To run the Vite dev server with Hot Module Replacement (HMR):

```bash
cd frontend
npm install
npm run dev      # Starts Vite dev server at http://localhost:5173
npm run build    # Compiles production bundle directly into ../app/static/
```

---

## Demonstration Scenarios (For Faculty & Evaluators)

Within the **Order Execution Terminal**, built-in **Demonstration Test Scenarios** allow immediate testing of edge cases:

1. **✓ Valid Order (`RELIANCE 10 @ ₹2,945.50`)**: Passes all risk gates; transitions to `APPROVED`.
2. **✗ Penny Stock (`IDEA 100 @ ₹0.50`)**: Triggers **RISK-05** rejection (sub-₹1.00 microcap floor).
3. **✗ Restricted Symbol (`YESBANK 50 @ ₹20.00`)**: Triggers **RISK-02** compliance blacklist rejection.
4. **✗ Fat-Finger Price (`TCS 1 @ ₹2,50,000.00`)**: Triggers **RISK-07** price ceiling protection.
5. **✗ Exceeds Max Notional (`TCS 200 @ ₹3,850.00 = ₹7.7L`)**: Triggers **RISK-01** single-order cap (₹5,00,000 limit).
6. **✗ Short-Selling Attempt (`INFY 20 @ ₹1,820.00` with 0 held)**: Triggers **RISK-10** short-selling prohibition.
7. **✓ Valid Sell Lifecycle**:
   - Buy 50 shares of `RELIANCE` $\to$ click **"⚡ Simulate Execution"** to settle holdings.
   - Switch to **SELL**: Holdings Telemetry displays `Held: 50`, `Reserved: 0`, `Net Sellable: 50`.
   - Submit SELL 20 $\to$ transitions to `APPROVED`. Holdings Telemetry immediately updates to `Held: 50`, `Reserved: 20`, `Net Sellable: 30`.
   - Submitting another SELL for 40 shares triggers **RISK-11** rejection (exceeds net sellable quantity of 30).

---

## Automated Test Suite

Run the full pytest suite (**180 tests**):

```bash
.venv/bin/python -m pytest tests/ -v
```

```
============================= 180 passed in 0.88s ==============================
```

- **Unit tests**: `tests/unit/` (order model, state transitions, 12 risk rules, SELL-side verification, mock market data provider, Dhan binary packet decoder, Hypothesis invariants)
- **Integration tests**: `tests/integration/` (order submission, execute & preview endpoints, market data API, stock screener, simulated portfolio settlement, SELL-side reservation lifecycle, concurrency mutex protections, SPA static serving)

---

## API Reference

All backend endpoints are hosted under `/api` and `/ws`:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/orders` | Submit and evaluate order against all 12 pre-trade risk gates |
| `POST` | `/api/orders/preview` | Dry-run risk evaluation returning risk matrix and live holding telemetry |
| `POST` | `/api/orders/{id}/execute` | Settle an approved order into simulated portfolio cash & positions |
| `GET` | `/api/orders` | Retrieve order audit ledger history |
| `GET` | `/api/orders/{id}` | Inspect full 12-gate audit dossier for a single order |
| `GET` | `/api/portfolio/summary` | Simulated cash balance, portfolio valuation, and total unrealized P&L |
| `GET` | `/api/portfolio/positions` | List open positions with entry prices, market values, and P&L |
| `GET` | `/api/portfolio/positions/{symbol}` | Get held quantity, reserved sell quantity, and net sellable quantity for a symbol |
| `GET` | `/api/market/status` | Current market feed connectivity, provider, and latency telemetry |
| `GET` | `/api/market/instruments` | Active NSE Cash equity universe (Top 20 tickers) |
| `GET` | `/api/market/quotes` | Real-time quote snapshots for universe instruments |
| `GET` | `/api/market/quotes/{symbol}` | Quote snapshot for a single ticker |
| `GET` | `/api/market/candles` | Historical OHLCV candlesticks (1m, 5m, 1D) |
| `GET` | `/api/screener` | Stock screener with preliminary risk gate advisory flags |
| `GET` | `/api/risk-config` | View active risk thresholds and restricted symbols |
| `PUT` | `/api/risk-config` | Update risk thresholds dynamically |
| `GET` | `/api/risk-rules` | Retrieve metadata, scope (`BOTH`/`SELL`), and status for all 12 rules |
| `GET` | `/api/orders/stats/summary` | Aggregate daily and all-time risk telemetry |
| `GET` | `/api/health` | Service health probe |
| `WS` | `/ws/market` | WebSocket stream for live market quote ticks |
