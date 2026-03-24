from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List


def compute_merchant_settlements(
    processed_transactions: List[Dict[str, Any]],
    merchants: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Create merchant-level settlement metrics.

    Report fields:
      - merchant_id
      - merchant_name
      - total_transactions
      - valid_transactions
      - fraud_transactions
      - settlement_amount
    """
    # Initialize from merchant list so merchants with 0 valid transactions still appear.
    stats: Dict[str, Dict[str, Any]] = {}
    for merchant_id, merchant in merchants.items():
        merchant_name = getattr(merchant, "merchant_name", "") if merchant is not None else ""
        stats[merchant_id] = {
            "merchant_id": merchant_id,
            "merchant_name": merchant_name,
            "total_transactions": 0,
            "valid_transactions": 0,
            "fraud_transactions": 0,
            "settlement_amount": Decimal("0"),
        }

    for tx in processed_transactions:
        merchant_id = tx["merchant_id"]
        if merchant_id not in stats:
            # Should not happen if validator used the same merchants map, but keep safe.
            continue

        stats[merchant_id]["total_transactions"] += 1
        status = tx.get("transaction_status")
        if status == "VALID":
            stats[merchant_id]["valid_transactions"] += 1
            stats[merchant_id]["settlement_amount"] += tx["transaction_amount"]
        elif status == "SUSPICIOUS":
            stats[merchant_id]["fraud_transactions"] += 1

    # Deterministic ordering for reproducible output.
    return [stats[mid] for mid in sorted(stats.keys())]

