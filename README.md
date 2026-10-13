# Pre-Trade Risk Management Simulator

A web application that accepts simulated buy and sell orders and decides whether each order should be approved or rejected before execution, based on configurable risk rules.

> **Educational simulator only.** Does not connect to real brokers, use live market data, or handle real money.

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip

### Setup

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Run the Application

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger UI.

### Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run unit tests only
python -m pytest tests/unit/ -v

# Run integration tests only
python -m pytest tests/integration/ -v
```

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/orders` | Create and evaluate an order |
| `GET` | `/orders` | List order history |
| `GET` | `/orders/{order_id}` | Retrieve one order |
| `GET` | `/health` | Health check |
| `GET` | `/risk-config` | View active risk configuration |

### Example: Submit an Order

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "side": "BUY", "quantity": 10, "price": "150.00"}'
```

## Risk Rules

| Rule | Description | Default Config |
|------|-------------|----------------|
| RISK-01 | Maximum order value | quantity × price ≤ $10,000.00 |
| RISK-02 | Restricted symbol | TSLA is restricted |
| RISK-03 | Quantity validity | Must be a positive integer |
| RISK-04 | Price validity | Must be a positive decimal |

## Order States

```
CREATED → VALIDATING → APPROVED → EXECUTED
                     → REJECTED
```

## Project Structure

```
app/
├── main.py              # FastAPI application
├── config.py            # Risk configuration
├── database.py          # SQLite setup
├── api/routes.py        # API endpoints
├── models/order.py      # Domain models & state machine
├── schemas/order.py     # Request/response schemas
├── services/
│   ├── order_service.py # Order orchestration
│   └── risk_engine.py   # Risk rule evaluation
└── repositories/
    └── order_repository.py  # Database operations
tests/
├── unit/                # Unit tests for risk engine, models, state transitions
└── integration/         # API integration tests
```

## Known Limitations

- SQLite is used for simplicity; not suitable for high-concurrency production use.
- No authentication or authorization.
- No real market data integration.
