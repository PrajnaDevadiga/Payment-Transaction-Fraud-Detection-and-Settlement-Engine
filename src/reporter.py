import csv
import json
from decimal import Decimal
from typing import Any, Dict, List


def _ensure_parent_dir(file_path: str) -> None:
    import os

    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_processed_transactions(
    processed_transactions: List[Dict[str, Any]],
    output_path: str,
) -> None:
    _ensure_parent_dir(output_path)

    fieldnames = [
        "transaction_id",
        "merchant_id",
        "customer_id",
        "transaction_amount",
        "transaction_time",
        "fraud_flag",
        "fraud_reason",
        "transaction_status",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tx in processed_transactions:
            dt = tx["transaction_time"]
            writer.writerow(
                {
                    "transaction_id": str(tx["transaction_id"]),
                    "merchant_id": str(tx["merchant_id"]),
                    "customer_id": str(tx["customer_id"]),
                    "transaction_amount": str(tx["transaction_amount"]),
                    "transaction_time": dt.isoformat(),
                    "fraud_flag": str(bool(tx.get("fraud_flag", False))),
                    "fraud_reason": str(tx.get("fraud_reason", "")),
                    "transaction_status": str(tx.get("transaction_status", "")),
                }
            )


def write_merchant_settlement_report(
    settlement_report: List[Dict[str, Any]],
    output_path: str,
) -> None:
    _ensure_parent_dir(output_path)
    fieldnames = [
        "merchant_id",
        "merchant_name",
        "total_transactions",
        "valid_transactions",
        "fraud_transactions",
        "settlement_amount",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in settlement_report:
            writer.writerow(
                {
                    "merchant_id": str(row["merchant_id"]),
                    "merchant_name": str(row["merchant_name"]),
                    "total_transactions": str(row["total_transactions"]),
                    "valid_transactions": str(row["valid_transactions"]),
                    "fraud_transactions": str(row["fraud_transactions"]),
                    "settlement_amount": str(row["settlement_amount"]),
                }
            )


def fraud_summary(
    processed_transactions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    total_transactions = len(processed_transactions)
    valid_transactions = sum(1 for tx in processed_transactions if tx.get("transaction_status") == "VALID")
    fraud_transactions = total_transactions - valid_transactions

    # Metrics based on rule codes present in fraud_reason_list / fraud_reason.
    def has_reason(tx: Dict[str, Any], code: str) -> bool:
        if "fraud_reason_list" in tx:
            return code in (tx.get("fraud_reason_list") or [])
        return code in (tx.get("fraud_reason") or "")

    high_value_frauds = sum(1 for tx in processed_transactions if has_reason(tx, "HIGH_VALUE_TRANSACTION"))
    cross_border_frauds = sum(
        1 for tx in processed_transactions if has_reason(tx, "CROSS_BORDER_TRANSACTION")
    )
    rapid_transaction_frauds = sum(
        1 for tx in processed_transactions if has_reason(tx, "RAPID_TRANSACTIONS")
    )

    return {
        "total_transactions": total_transactions,
        "valid_transactions": valid_transactions,
        "fraud_transactions": fraud_transactions,
        "high_value_frauds": high_value_frauds,
        "cross_border_frauds": cross_border_frauds,
        "rapid_transaction_frauds": rapid_transaction_frauds,
    }


def write_fraud_summary(
    processed_transactions: List[Dict[str, Any]],
    output_path: str,
) -> None:
    _ensure_parent_dir(output_path)
    summary = fraud_summary(processed_transactions)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

