"""
Hypothesis property-based tests verifying core domain invariants (Phase 7).
"""

from decimal import Decimal
from hypothesis import given, strategies as st

from app.config import RiskConfig
from app.models.order import (
    InvalidStateTransitionError,
    OrderStatus,
    VALID_TRANSITIONS,
    validate_transition,
)
from app.services.risk_engine import (
    check_max_order_value,
    check_min_price,
    evaluate,
)


class TestHypothesisDomainInvariants:
    """Property-based verification of mathematical and state-machine invariants."""

    @given(
        quantity=st.integers(min_value=1, max_value=1_000_000),
        price=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("1000000.00"),
            places=2,
        ),
    )
    def test_positive_inputs_yield_positive_notional(
        self, quantity: int, price: Decimal
    ):
        notional = Decimal(quantity) * price
        assert notional > 0
        assert isinstance(notional, Decimal)

    @given(
        quantity=st.integers(min_value=1, max_value=20_000),
        price=st.decimals(
            min_value=Decimal("0.01"), max_value=Decimal("100000.00"), places=2
        ),
        symbol=st.sampled_from(["AAPL", "TSLA", "RELIANCE", "M&M", "UNKNOWN"]),
    )
    def test_evaluate_always_returns_nine_rules(
        self, quantity: int, price: Decimal, symbol: str
    ):
        config = RiskConfig()
        result = evaluate(
            quantity=quantity,
            price=price,
            symbol=symbol,
            config=config,
            daily_order_count=10,
            daily_notional=Decimal("1000.00"),
        )
        assert len(result.check_results) == 9
        # Check rule IDs are complete
        rule_ids = {c.rule_id for c in result.check_results}
        assert rule_ids == {f"RISK-0{i}" for i in range(1, 10)}

    @given(
        current_state=st.sampled_from(list(OrderStatus)),
        target_state=st.sampled_from(list(OrderStatus)),
    )
    def test_state_machine_transitions_obey_table(
        self, current_state: OrderStatus, target_state: OrderStatus
    ):
        allowed = VALID_TRANSITIONS.get(current_state, set())
        if target_state in allowed:
            validate_transition(current_state, target_state)  # Should not raise
        else:
            try:
                validate_transition(current_state, target_state)
                assert False, f"Expected InvalidStateTransitionError for {current_state} -> {target_state}"
            except InvalidStateTransitionError as exc:
                assert exc.current == current_state
                assert exc.target == target_state

    @given(
        qty=st.integers(min_value=1, max_value=1000),
        price=st.decimals(min_value=Decimal("1.00"), max_value=Decimal("500.00"), places=2),
        limit=st.decimals(min_value=Decimal("10.00"), max_value=Decimal("500000.00"), places=2),
    )
    def test_max_order_value_monotonicity(self, qty: int, price: Decimal, limit: Decimal):
        val = Decimal(qty) * price
        res = check_max_order_value(qty, price, limit)
        if val <= limit:
            assert res.passed is True
        else:
            assert res.passed is False
            assert "exceeds" in res.reason.lower()
