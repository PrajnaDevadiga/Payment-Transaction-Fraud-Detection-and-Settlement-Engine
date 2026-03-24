import logging
from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from src.loader import Merchant, Transaction, parse_transaction_amount


def _parse_transaction_time(value: str) -> Optional[datetime]:
    """
    Parse transaction_time from CSV.

    Supports:
    - ISO 8601 datetime (e.g. 2026-03-21T12:34:56 or 2026-03-21T12:34:56Z)
    - Common formats (e.g. 2026-03-21 12:34:56)
    """
    raw = (value or "").strip()
    if not raw:
        return None

    # Handle a trailing 'Z' in ISO-8601.
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    # Try ISO formats first.
    try:
        dt = datetime.fromisoformat(raw)
        # Normalize timezone-aware timestamps to naive UTC for comparisons.
        if dt.tzinfo is not None:
            dt = dt.astimezone(tz=None).replace(tzinfo=None)
        return dt
    except Exception:
        pass

    # Fallback formats without timezone.
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue

    return None


def _normalize_payment_method(value: str) -> str:
    return (value or "").strip().upper()


def validate_transactions(
    transactions: List[Dict[str, Any]],
    merchants: Dict[str, Merchant],
    logger: Optional[logging.Logger] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Validate transaction records.

    Returns:
      (validated_transactions, invalid_count)
    """
    logger = logger or logging.getLogger(__name__)

    validated: List[Dict[str, Any]] = []
    invalid_count = 0

    for tx in transactions:
        transaction_id = (tx.get("transaction_id") or "").strip()
        merchant_id = (tx.get("merchant_id") or "").strip()
        customer_id = (tx.get("customer_id") or "").strip()

        merchant = merchants.get(merchant_id)
        if merchant is None:
            invalid_count += 1
            logger.warning(
                "Invalid transaction rejected: unknown merchant_id=%s tx_id=%s",
                merchant_id,
                transaction_id,
            )
            continue
        if (merchant.status or "").strip().upper() == "BLOCKED":
            invalid_count += 1
            logger.warning(
                "Invalid transaction rejected: blocked merchant_id=%s tx_id=%s",
                merchant_id,
                transaction_id,
            )
            continue

        amount = parse_transaction_amount(str(tx.get("transaction_amount") or ""))
        if amount is None or amount <= 0:
            invalid_count += 1
            logger.warning(
                "Invalid transaction rejected: negative/invalid amount tx_id=%s merchant_id=%s amount=%s",
                transaction_id,
                merchant_id,
                tx.get("transaction_amount"),
            )
            continue

        dt = _parse_transaction_time(str(tx.get("transaction_time") or ""))
        if dt is None:
            invalid_count += 1
            logger.warning(
                "Invalid transaction rejected: invalid transaction_time tx_id=%s transaction_time=%s",
                transaction_id,
                tx.get("transaction_time"),
            )
            continue

        validated_tx: Dict[str, Any] = {
            "transaction_id": transaction_id,
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "transaction_amount": amount,
            "transaction_time": dt,
            "payment_method": _normalize_payment_method(str(tx.get("payment_method") or "")),
            "country": (tx.get("country") or "").strip(),
            "merchant_name": merchant.merchant_name,
            "merchant_country": merchant.country,
            "merchant_status": merchant.status,
        }
        validated.append(validated_tx)

    return validated, invalid_count


def transaction_to_csv_row(tx: Dict[str, Any]) -> Dict[str, str]:
    """
    Convert an in-memory validated/fraud-processed transaction into CSV-friendly strings.
    """
    dt: datetime = tx["transaction_time"]
    return {
        "transaction_id": str(tx["transaction_id"]),
        "merchant_id": str(tx["merchant_id"]),
        "customer_id": str(tx["customer_id"]),
        "transaction_amount": str(tx["transaction_amount"]),
        "transaction_time": dt.isoformat(),
        "fraud_flag": str(tx.get("fraud_flag", "")),
        "fraud_reason": str(tx.get("fraud_reason", "")),
        "transaction_status": str(tx.get("transaction_status", "")),
    }

