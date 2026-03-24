import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Merchant:
    merchant_id: str
    merchant_name: str
    merchant_category: str
    country: str
    status: str  # ACTIVE / BLOCKED


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    merchant_id: str
    customer_id: str
    transaction_amount: Decimal
    transaction_time: datetime
    payment_method: str
    country: str


def _to_decimal(value: str) -> Decimal:
    # Decimal can parse "1000" or "1000.00" without losing exactness.
    return Decimal(value.strip())


def load_merchants(file_path: str) -> Dict[str, Merchant]:
    """
    Load merchants.csv into a dict keyed by merchant_id.
    """
    merchants: Dict[str, Merchant] = {}
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {
            "merchant_id",
            "merchant_name",
            "merchant_category",
            "country",
            "status",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"merchants.csv missing columns: {sorted(missing)}")

        for row in reader:
            merchant_id = (row.get("merchant_id") or "").strip()
            if not merchant_id:
                continue
            merchants[merchant_id] = Merchant(
                merchant_id=merchant_id,
                merchant_name=(row.get("merchant_name") or "").strip(),
                merchant_category=(row.get("merchant_category") or "").strip(),
                country=(row.get("country") or "").strip(),
                status=(row.get("status") or "").strip(),
            )

    return merchants


def load_transactions(file_path: str) -> List[Dict[str, Any]]:
    """
    Load transactions.csv into a list of dicts.

    Note: transaction_time is kept as a raw string for validation/parsing later.
    """
    transactions: List[Dict[str, Any]] = []
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {
            "transaction_id",
            "merchant_id",
            "customer_id",
            "transaction_amount",
            "transaction_time",
            "payment_method",
            "country",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"transactions.csv missing columns: {sorted(missing)}")

        for row in reader:
            tx = {
                "transaction_id": (row.get("transaction_id") or "").strip(),
                "merchant_id": (row.get("merchant_id") or "").strip(),
                "customer_id": (row.get("customer_id") or "").strip(),
                "transaction_amount": (row.get("transaction_amount") or "").strip(),
                "transaction_time": (row.get("transaction_time") or "").strip(),
                "payment_method": (row.get("payment_method") or "").strip(),
                "country": (row.get("country") or "").strip(),
            }
            transactions.append(tx)

    return transactions


def parse_transaction_amount(value: str) -> Optional[Decimal]:
    value = (value or "").strip()
    if value == "":
        return None
    try:
        return _to_decimal(value)
    except Exception:
        return None

