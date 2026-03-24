import logging
from collections import defaultdict, deque
from datetime import datetime
from decimal import Decimal
from typing import Any, Deque, Dict, Iterable, List, Optional, Set, Tuple

from src.loader import Merchant


def _add_fraud_reason(tx: Dict[str, Any], code: str) -> None:
    reasons: List[str] = tx.get("fraud_reason_list") or []
    reasons.append(code)
    tx["fraud_reason_list"] = reasons


def _finalize_fraud_fields(tx: Dict[str, Any]) -> None:
    reasons = tx.get("fraud_reason_list") or []
    tx["fraud_reason"] = ";".join(reasons)
    tx["fraud_flag"] = bool(reasons)
    tx["transaction_status"] = "SUSPICIOUS" if reasons else "VALID"


def apply_fraud_rules(
    validated_transactions: List[Dict[str, Any]],
    merchants: Dict[str, Merchant],
    logger: Optional[logging.Logger] = None,
) -> List[Dict[str, Any]]:
    """
    Apply fraud rules to transactions that already passed validation.

    Adds:
      - fraud_flag (bool)
      - fraud_reason (string of triggered rules)
      - transaction_status (VALID/SUSPICIOUS)
    """
    logger = logger or logging.getLogger(__name__)

    # Work on copies so callers can reuse validated records if needed.
    processed: List[Dict[str, Any]] = [dict(tx) for tx in validated_transactions]

    # Rule 1: High Amount Transaction
    for tx in processed:
        amount: Decimal = tx["transaction_amount"]
        if amount > Decimal("100000"):
            _add_fraud_reason(tx, "HIGH_VALUE_TRANSACTION")

    # Rule 2: Cross Country Payment
    for tx in processed:
        merchant_country = (tx.get("merchant_country") or "").strip()
        tx_country = (tx.get("country") or "").strip()
        if tx_country and merchant_country and tx_country != merchant_country:
            _add_fraud_reason(tx, "CROSS_BORDER_TRANSACTION")

    # Rule 4: Suspicious Payment Method
    for tx in processed:
        method = (tx.get("payment_method") or "").strip().upper()
        amount: Decimal = tx["transaction_amount"]
        if method == "CRYPTO" and amount > Decimal("50000"):
            _add_fraud_reason(tx, "CRYPTO_HIGH_VALUE")

    # Rule 3: Rapid Transactions
    rapid_flagged_ids = _compute_rapid_transactions_flagged(
        processed,
        window_seconds=120,
        threshold=4,  # "more than 3" within 2 minutes => 4th+ transaction
    )
    for tx in processed:
        if tx["transaction_id"] in rapid_flagged_ids:
            _add_fraud_reason(tx, "RAPID_TRANSACTIONS")

    for tx in processed:
        _finalize_fraud_fields(tx)

    return processed


def _compute_rapid_transactions_flagged(
    transactions: List[Dict[str, Any]],
    window_seconds: int,
    threshold: int,
) -> Set[str]:
    """
    Flag transactions where a single customer performs >= threshold transactions
    within any rolling window of `window_seconds`.

    With threshold=4, this flags the 4th and subsequent transactions in a qualifying window.
    """
    # Group by customer and sort by time.
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for tx in transactions:
        grouped[(tx.get("customer_id") or "").strip()].append(tx)

    flagged: Set[str] = set()
    window = deque()

    for customer_id, txs in grouped.items():
        # Reset per-customer window.
        window.clear()
        txs_sorted = sorted(
            txs,
            key=lambda t: (
                t.get("transaction_time"),
                str(t.get("transaction_id")),
            ),
        )

        for tx in txs_sorted:
            current_time: datetime = tx["transaction_time"]
            while window and (current_time - window[0]).total_seconds() > window_seconds:
                window.popleft()

            window.append(current_time)
            # After adding current, window size equals number of tx in the last window_seconds window.
            if len(window) >= threshold:
                flagged.add(tx["transaction_id"])

    return flagged

