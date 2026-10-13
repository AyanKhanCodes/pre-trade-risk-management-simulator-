# Pre-Trade Risk Management Simulator
## Software Verification & Testing (SV&T) Project Plan

**Project type:** Fourth-year Software Verification & Testing academic project  
**Project level:** Beginner-friendly MVP with room for advanced testing  
**Suggested duration:** 6–8 weeks  
**Primary goal:** Build a small, demonstrable application that evaluates simulated trading orders against configurable risk rules, while using the project to demonstrate a broad range of software testing techniques.

---

## 1. Project Summary

The **Pre-Trade Risk Management Simulator** is a web application that accepts simulated buy and sell orders and decides whether each order should be approved or rejected before execution.

The application is an educational simulator only. It does not connect to a real broker or exchange, use live market prices, or handle real money.

The project is designed to make software verification and testing visible: each business rule should have clear requirements, implementation, test cases, and evidence.

### Core invariant

> An order must never be executed unless it has passed every required risk check and is in the `APPROVED` state.

Treat this invariant as a central requirement and verify it with unit, integration, state-transition, property-based, regression, and concurrency tests.

## 2. Goals and Non-Goals

### Goals

- Submit simulated `BUY` and `SELL` orders through a simple interface.
- Validate orders using explicit, configurable risk rules.
- Store order history and show approval or rejection reasons.
- Enforce valid order-state transitions.
- Build an automated test suite with readable results.
- Demonstrate multiple SV&T methods with traceable requirements and evidence.
- Make the application easy to run locally and easy for another developer or coding agent to understand.

### Non-goals for the MVP

Do **not** implement these unless the project supervisor specifically requires them:

- Real broker or exchange integration
- Live market data or price prediction
- Real-money trading
- AI/ML trading decisions
- Microservices, Kafka, or Kubernetes
- Complex institutional margin calculations
- Elaborate authentication and role management

Keep the initial scope small. A well-tested, clearly documented application is more valuable for this project than a large application with weak testing.

## 3. Recommended Technology Stack

| Area | Recommended choice | Purpose |
|---|---|---|
| Backend | Python + FastAPI | REST API and application logic |
| Frontend | HTML, CSS, Bootstrap, and minimal JavaScript | Simple order form and order history |
| Database | SQLite | Local persistence for orders and configuration |
| Unit/API testing | pytest + FastAPI test client | Automated tests |
| Property-based testing | Hypothesis | Generate many inputs and verify general properties |
| API exploration | Postman or pytest | Manually inspect and automate API scenarios |
| Performance testing | Locust or k6 | Measure latency, throughput, and errors |
| Version control | Git + GitHub | Change tracking and regression workflow |

Use Python's `Decimal` type for monetary values; avoid binary floating-point arithmetic for order-value calculations.

## 4. MVP Functional Requirements

### FR-01: Submit an order

The user can submit an order containing:

- `symbol`: asset ticker, such as `AAPL`
- `side`: `BUY` or `SELL`
- `quantity`: positive whole number
- `price`: positive decimal price

The system assigns an order ID and stores the submitted order.

### FR-02: Validate the order

The risk engine evaluates the order against all required rules before approval.

### FR-03: Record the result

Each order stores its status and a useful reason when rejected. If multiple rules fail, the API may return all applicable reasons rather than only the first.

### FR-04: View order history

The user can list previous orders and inspect each order's input, status, and rejection reasons.

### FR-05: Execute an approved order

The simulator can mark an approved order as executed. An order that is not approved must not be executable.

### FR-06: Configure risk settings

For the MVP, risk limits can be configured through a simple settings file or database table. Avoid building a complex administration interface unless needed.

## 5. Risk Rules

Implement the first four rules as the minimum scope. Add the position-limit rule after the basic application and tests work.

| Rule ID | Rule | Example configuration | Expected rejection |
|---|---|---|---|
| RISK-01 | Maximum order value | `quantity × price <= 10000.00` | Order value exceeds limit |
| RISK-02 | Restricted symbol | `TSLA` is restricted in the example configuration | Symbol is restricted |
| RISK-03 | Quantity validity | `quantity > 0` | Quantity must be positive |
| RISK-04 | Price validity | `price > 0` | Price must be positive |
| RISK-05 (optional) | Maximum position size | Maximum position is 500 units | Order would exceed position limit |

### Important details

- The maximum order value is inclusive: an order worth exactly `$10,000.00` passes RISK-01; an order worth `$10,000.01` fails RISK-01.
- Validate input types and reject malformed values instead of silently coercing them.
- Use a documented policy for whether `SELL` orders are checked differently from `BUY` orders. For the MVP, apply the same basic value and input-validity rules to both sides.
- If RISK-05 is implemented, define how current positions are calculated and updated. For example, a current position of 480 units plus a 30-unit buy would exceed a 500-unit maximum.
- Keep the restricted-symbol list and limits configurable so tests can verify behavior with different settings.

## 6. Order Lifecycle and State Machine

Use these states:

- `CREATED`: order has been received and persisted.
- `VALIDATING`: the risk engine is evaluating the order.
- `APPROVED`: all required risk checks passed.
- `REJECTED`: one or more risk checks failed.
- `EXECUTED`: an approved order was marked executed by the simulator.

Expected transitions:

```text
CREATED -> VALIDATING
VALIDATING -> APPROVED
VALIDATING -> REJECTED
APPROVED -> EXECUTED
```

All other transitions should be rejected. In particular:

- `REJECTED -> EXECUTED` must fail.
- `CREATED -> EXECUTED` must fail.
- `VALIDATING -> EXECUTED` must fail.
- `EXECUTED -> APPROVED` must fail.
- An already executed order must not be executed a second time unless an explicit idempotency policy says otherwise.

Keep state-transition logic in one place rather than duplicating it across API routes.

## 7. Suggested Architecture

Use a small layered design:

```text
Browser UI
   |
   v
FastAPI routes / request validation
   |
   v
Order service
   |-------------------|
   v                   v
Risk engine        Order repository
                       |
                       v
                    SQLite
```

### Suggested responsibilities

- **API routes:** parse requests, call services, return HTTP responses.
- **Order service:** orchestrate creation, validation, status updates, and execution.
- **Risk engine:** evaluate rules and return structured results; avoid database or HTTP concerns where possible.
- **Repository:** read and write orders and configuration.
- **Frontend:** submit orders and display history/statuses.
- **Tests:** verify each layer and the end-to-end flow.

Keep the risk engine as a mostly pure component: given an order and risk configuration, it should return predictable validation results.

## 8. Suggested API Endpoints

Endpoint names can be adjusted, but document and test the final contract.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/orders` | Create and evaluate an order |
| `GET` | `/orders` | List order history |
| `GET` | `/orders/{order_id}` | Retrieve one order |
| `POST` | `/orders/{order_id}/execute` | Execute an approved order |
| `GET` | `/health` | Basic health check |
| `GET` | `/risk-config` | View active risk configuration, if exposed |

Example request:

```json
{
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 10,
  "price": "150.00"
}
```

Example successful response (illustrative; define the exact schema in the implementation):

```json
{
  "order_id": "generated-id",
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 10,
  "price": "150.00",
  "order_value": "1500.00",
  "status": "APPROVED",
  "rejection_reasons": []
}
```

Example rejected response (illustrative):

```json
{
  "order_id": "generated-id",
  "status": "REJECTED",
  "rejection_reasons": [
    "Order value exceeds the maximum allowed value of 10000.00"
  ]
}
```

Define a consistent policy for HTTP status codes. For example, syntactically invalid requests may return `422`, while a validly formed but risk-rejected order can be persisted and returned with a documented status. Do not confuse a risk rejection with an unexpected server error.

## 9. Testing Strategy

Testing is the main academic deliverable, not an afterthought. Every requirement should map to one or more tests.

### 9.1 Unit testing

Test individual risk rules and state-transition functions in isolation.

Examples:

- Valid order value passes.
- Order value above the limit fails.
- Restricted symbol fails.
- Zero or negative quantity fails.
- Zero or negative price fails.
- Only approved orders can transition to executed.

### 9.2 Boundary-value analysis

For a `$10,000.00` maximum order value, test:

| Quantity | Price | Order value | Expected result for RISK-01 |
|---:|---:|---:|---|
| 1 | `9999.99` | `9999.99` | Pass |
| 1 | `10000.00` | `10000.00` | Pass |
| 1 | `10000.01` | `10000.01` | Fail |

Also test quantity boundaries such as `-1`, `0`, and `1`.

### 9.3 Equivalence partitioning

Divide input data into classes expected to behave similarly:

- Quantity: negative, zero, valid positive, excessively large
- Price: negative, zero, valid positive, excessively large
- Symbol: allowed, restricted, malformed, missing
- Side: `BUY`, `SELL`, unsupported value
- Order value: below limit, exactly at limit, above limit

Choose representative values from each class and explain why they represent that class.

### 9.4 Decision-table testing

Create a table for combinations of risk-rule outcomes. Example:

| Valid quantity | Valid price | Allowed symbol | Value within limit | Expected result |
|---|---|---|---|---|
| Yes | Yes | Yes | Yes | Approve |
| No | Yes | Yes | Yes | Reject |
| Yes | No | Yes | Yes | Reject |
| Yes | Yes | No | Yes | Reject |
| Yes | Yes | Yes | No | Reject |
| No | No | No | No | Reject |

Verify that every failing rule is reflected in the returned rejection reasons if the API promises to report all failures.

### 9.5 State-transition testing

Test all allowed transitions and representative forbidden transitions. Build a transition table and ensure forbidden transitions do not mutate the stored order.

### 9.6 Integration testing

Verify the complete path:

`API request -> request validation -> order service -> risk engine -> database -> API response`

Include checks that:

- Created orders are persisted.
- Rejection reasons survive retrieval.
- An approved order can be executed.
- A rejected order cannot be executed.
- Database failures do not leave misleading success responses.

### 9.7 Property-based testing with Hypothesis

Generate many quantities, prices, symbols, and sides. Example properties:

- Any order with a non-positive quantity is never approved.
- Any order with a non-positive price is never approved.
- Any order whose value exceeds the configured maximum is never approved.
- A restricted symbol is never approved while that restriction is active.
- An order can reach `EXECUTED` only if it was previously `APPROVED`.

Be careful with generated decimal values and use `Decimal` consistently. Keep random seeds or failing examples in the test report when useful for reproducibility.

### 9.8 Regression testing

Whenever a defect is fixed:

1. Add a test that reproduces the defect.
2. Fix the implementation.
3. Run the new test.
4. Run the full suite.
5. Record the result in the change log or test report.

### 9.9 Security testing

For the MVP, test at least:

- Missing fields and malformed JSON
- Wrong data types and unexpected enum values
- Extremely large quantities/prices and overly long symbols
- SQL-injection-like strings in symbols or identifiers
- Attempts to execute rejected or nonexistent orders
- Error responses that accidentally expose stack traces or internal secrets

Do not claim the application is secure based only on these tests; describe them as scoped security checks.

### 9.10 Performance testing

Use Locust or k6 to measure:

- Requests per second or completed orders per second
- Median and 95th-percentile latency
- Error rate
- Behavior as concurrency increases

Set a modest target only after measuring the local baseline. Record the machine, configuration, test duration, concurrency, and actual results. Do not invent performance results.

### 9.11 Concurrency testing

If position limits or other shared limits are implemented, submit simultaneous orders that compete for the same remaining capacity.

Example: a position limit is 500, current position is 480, and two concurrent buy orders each request 15 units. The system must not approve both if that would create a position of 510. Use a transaction, lock, or other appropriate consistency mechanism and write a test that demonstrates the invariant.

If RISK-05 is deferred, still test duplicate execution requests and concurrent updates to the same order.

## 10. Requirement-to-Test Traceability

Maintain a traceability matrix from requirements to test cases.

| Requirement | Minimum verification |
|---|---|
| FR-01: Submit order | API integration test; valid/invalid request tests |
| FR-02: Risk validation | Unit tests for every risk rule; decision table |
| FR-03: Record result | Database integration test; rejection-reason tests |
| FR-04: Order history | API integration tests for list and detail |
| FR-05: Execute approved order | State-transition tests; negative tests for rejected orders |
| FR-06: Configure limits | Configuration tests; tests with changed limits |
| Core invariant | Property-based test; integration test; regression test |
| Performance goal | Load-test report with measured results |
| Concurrency consistency | Concurrent-order test if shared limits are implemented |

Give each test a stable ID, such as `UT-RISK-001`, `API-ORDER-001`, or `ST-EXEC-002`.

## 11. Development Timeline (6–8 Weeks)

### Week 1 — Requirements and design

- Confirm MVP scope with the supervisor.
- Write functional and non-functional requirements.
- Define risk rules and state transitions.
- Draw a simple architecture diagram.
- Create the repository, README, and issue/task list.
- Draft the requirement-to-test traceability matrix.

**Deliverable:** requirements, architecture, initial test plan.

### Week 2 — Basic application

- Create the FastAPI application.
- Define request/response schemas.
- Add SQLite persistence.
- Implement order submission and order history.
- Build a minimal frontend or use API docs initially.
- Add a health endpoint.

**Deliverable:** an order can be submitted and retrieved.

### Week 3 — Risk engine and lifecycle

- Implement the four required risk rules.
- Store approval/rejection results and reasons.
- Add the order state machine.
- Implement execution for approved orders only.
- Add configuration for limits and restricted symbols.
- Add unit tests as each feature is built.

**Deliverable:** complete basic risk-evaluation flow with core unit tests.

### Week 4 — Core SV&T methods

- Complete unit tests.
- Perform boundary-value analysis.
- Perform equivalence partitioning.
- Create and test decision tables.
- Add state-transition tests.
- Document expected versus actual results.

**Deliverable:** organized functional test suite and test-case evidence.

### Week 5 — Integration and property-based tests

- Add API/database integration tests.
- Add Hypothesis property-based tests.
- Add regression tests for discovered defects.
- Improve error handling and test isolation.

**Deliverable:** automated suite covering the main requirements and invariant.

### Week 6 — Security, performance, and concurrency

- Test malformed and hostile inputs.
- Run a baseline load test.
- Record latency, throughput, and error rate.
- Add concurrency tests for execution or shared limits.
- Fix and retest discovered issues.

**Deliverable:** security-test notes and measured performance report.

### Week 7 — Stabilization and documentation

- Run the full regression suite.
- Review traceability matrix for gaps.
- Clean up code and setup instructions.
- Capture test reports and screenshots.
- Document known limitations.

**Deliverable:** reproducible project and draft final report.

### Week 8 — Final demonstration (optional buffer)

- Perform a clean setup from the README.
- Run the final test suite.
- Rehearse the demo.
- Present results, limitations, and lessons learned.

**Deliverable:** final submission and demonstration.

For a strict six-week schedule, combine Weeks 7 and 8 and keep the optional position-limit feature out of scope.

## 12. Recommended Repository Layout

```text
pre-trade-risk-simulator/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── models/
│   │   └── order.py
│   ├── schemas/
│   │   └── order.py
│   ├── services/
│   │   ├── order_service.py
│   │   └── risk_engine.py
│   ├── repositories/
│   │   └── order_repository.py
│   ├── config.py
│   └── database.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── api/
│   ├── property/
│   ├── regression/
│   └── conftest.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── test-results/
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── test-plan.md
│   ├── traceability-matrix.md
│   └── performance-report.md
├── pyproject.toml
├── README.md
└── .gitignore
```

This is a suggested layout, not a requirement to create every file on day one. Start with the minimum needed and expand as the codebase grows.

## 13. Definition of Done

A feature is complete only when:

- Its requirement and expected behavior are documented.
- The implementation follows the architecture and coding conventions.
- Relevant positive, negative, and boundary tests exist.
- Tests pass locally.
- Error cases return understandable responses.
- No order can bypass required risk checks or execute from an invalid state.
- The README or relevant documentation is updated.
- Any known limitation is recorded rather than hidden.

The project is ready for final submission when:

- A clean local setup works from documented instructions.
- All core requirements have linked tests.
- The full automated suite passes, or any known failures are explicitly reported.
- The test report includes actual results and environment details.
- The demo can show both accepted and rejected orders.
- The core invariant is tested.
- Limitations and future improvements are documented.

## 14. Final Demo Script

Use this sequence in the presentation:

1. Submit a valid `AAPL` buy order worth less than `$10,000.00`; show it approved.
2. Execute the approved order; show its state change to `EXECUTED`.
3. Submit an order worth `$10,000.01`; show it rejected with a clear reason.
4. Submit an order for a restricted symbol such as `TSLA`; show rejection.
5. Demonstrate quantity and price validation for zero or negative values.
6. Show boundary-value test results for `$9,999.99`, `$10,000.00`, and `$10,000.01`.
7. Attempt to execute a rejected order; show that the transition is blocked.
8. Run the automated test suite and show the result.
9. Show one Hypothesis test and explain the property it verifies.
10. Present actual performance-test results and limitations. Never use fabricated measurements.

## 15. Suggested Final Report Structure

1. Introduction and motivation
2. Problem statement and project objectives
3. Scope and assumptions
4. Requirements specification
5. Architecture and design
6. Risk rules and state machine
7. Testing methodology
8. Test-case design and traceability
9. Implementation summary
10. Test execution results
11. Performance and security test results
12. Defects found and regression tests
13. Limitations and threats to validity
14. Conclusion and future work
15. References and appendices

## 16. Guidance for Coding Agents

This section is intended for an AI coding agent or a developer using an agentic coding workflow.

### Operating principles

- Read this plan and the repository README before changing code.
- Treat the **Core invariant** and the requirements in this document as authoritative project constraints.
- Prefer small, reviewable changes over a large one-shot implementation.
- Do not implement excluded features unless explicitly requested.
- Do not claim that tests, commands, or performance runs passed unless they were actually executed and their results observed.
- Do not fabricate screenshots, benchmark values, test reports, or coverage percentages.
- Keep API behavior, schemas, configuration, and documentation consistent.
- Use `Decimal` for money and explicit rounding/serialization rules.
- Keep risk decisions in the risk engine, not scattered across route handlers.
- Ensure a rejected order cannot be executed, including through direct API calls.
- If a requirement is ambiguous, document the assumption and choose the simplest safe behavior; ask the project owner if the ambiguity affects core correctness.
- Avoid unnecessary dependencies and infrastructure.

### Implementation sequence for an agent

1. Inspect the current repository and summarize its state.
2. Create or update requirements and the traceability matrix.
3. Set up the smallest runnable FastAPI application and test configuration.
4. Implement request/response schemas and SQLite persistence.
5. Implement risk rules as testable functions.
6. Implement the order service and explicit state transitions.
7. Add API endpoints and integration tests.
8. Add frontend behavior only after the API contract is stable.
9. Add boundary, equivalence-partition, decision-table, and state-transition tests.
10. Add Hypothesis tests and regression tests.
11. Add scoped security, performance, and concurrency tests.
12. Run the full test suite and report exact commands and results.
13. Update the README, setup instructions, limitations, and final evidence.

### Agent acceptance checklist

Before marking the MVP complete, verify all of the following:

- [ ] The application starts using documented instructions.
- [ ] SQLite data is created and orders persist across requests.
- [ ] Valid orders are approved.
- [ ] Every required risk rule has automated tests.
- [ ] Orders over the maximum value are rejected, including exact boundary behavior.
- [ ] Rejection reasons are stored and returned consistently.
- [ ] Only approved orders can be executed.
- [ ] Invalid state transitions do not change stored state.
- [ ] Money calculations use `Decimal`.
- [ ] API and database integration tests exist.
- [ ] Property-based tests cover the core invariant.
- [ ] The complete test suite has been run and results recorded.
- [ ] Performance results, if reported, come from an actual run.
- [ ] Documentation lists setup steps, test commands, scope, and known limitations.

### Recommended initial agent task

Start by scaffolding the project and writing tests for the risk engine before building the full UI. Implement only RISK-01 through RISK-04 first. Keep the project runnable after each step, and run tests after each meaningful change.

## 17. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Scope grows too large | Keep the MVP to four rules and one simple UI |
| Tests only cover happy paths | Require negative, boundary, and state-transition tests |
| Monetary precision errors | Use `Decimal` and test exact limit boundaries |
| Business logic gets duplicated | Centralize checks in the risk engine and transitions in one service |
| Test results are not reproducible | Record commands, configuration, environment, and test data |
| Concurrency bug in position limits | Use transactions/locking and simultaneous-order tests if RISK-05 is included |
| Demo depends on external services | Keep the MVP local, offline-friendly, and independent of brokers/exchanges |

## 18. First Steps

Begin with these tasks:

1. Create a Git repository named `pre-trade-risk-simulator`.
2. Create `README.md`, `docs/requirements.md`, and `docs/traceability-matrix.md`.
3. Set up FastAPI, pytest, and SQLite.
4. Implement and test RISK-01 through RISK-04.
5. Implement order persistence and the state machine.
6. Add the API integration tests.
7. Build the simple frontend after the core workflow is stable.

**Project success criterion:** A reviewer can run the application, submit both valid and invalid simulated orders, inspect stored results, run the automated tests, and see evidence that the system prevents orders from executing unless all required risk checks have passed.
