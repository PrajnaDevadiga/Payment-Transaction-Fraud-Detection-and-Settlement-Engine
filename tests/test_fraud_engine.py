import pytest
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

from src.fraud_engine import apply_fraud_rules
from src.loader import Merchant


def _validated_tx(
    transaction_id: str,
    merchant_id: str,
    customer_id: str,
    amount: str,
    time: datetime,
    payment_method: str,
    country: str,
    merchant_country: str,
) -> Dict[str, object]:
    return {
        "transaction_id": transaction_id,
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "transaction_amount": Decimal(amount),
        "transaction_time": time,
        "payment_method": payment_method.upper(),
        "country": country,
        "merchant_country": merchant_country,
    }


def test_high_value_transaction_flag():
    merchants: Dict[str, Merchant] = {
        "m1": Merchant("m1", "Merchant 1", "cat", "US", "ACTIVE"),
    }
    t = datetime(2026, 3, 21, 12, 0, 0)
    validated = [
        _validated_tx(
            "t1",
            "m1",
            "c1",
            "100000.01",
            t,
            "CARD",
            "US",
            "US",
        )
    ]

    processed = apply_fraud_rules(validated, merchants, logger=logging.getLogger("test"))
    assert processed[0]["transaction_status"] == "SUSPICIOUS"
    assert "HIGH_VALUE_TRANSACTION" in processed[0]["fraud_reason"]


def test_cross_border_transaction_flag():
    merchants: Dict[str, Merchant] = {
        "m1": Merchant("m1", "Merchant 1", "cat", "US", "ACTIVE"),
    }
    t = datetime(2026, 3, 21, 12, 0, 0)
    validated = [
        _validated_tx(
            "t1",
            "m1",
            "c1",
            "10",
            t,
            "CARD",
            "CA",
            "US",
        )
    ]

    processed = apply_fraud_rules(validated, merchants, logger=logging.getLogger("test"))
    assert processed[0]["transaction_status"] == "SUSPICIOUS"
    assert "CROSS_BORDER_TRANSACTION" in processed[0]["fraud_reason"]


def test_crypto_high_value_flag():
    merchants: Dict[str, Merchant] = {
        "m1": Merchant("m1", "Merchant 1", "cat", "US", "ACTIVE"),
    }
    t = datetime(2026, 3, 21, 12, 0, 0)
    validated = [
        _validated_tx(
            "t1",
            "m1",
            "c1",
            "50000.01",
            t,
            "CRYPTO",
            "US",
            "US",
        )
    ]

    processed = apply_fraud_rules(validated, merchants, logger=logging.getLogger("test"))
    assert processed[0]["transaction_status"] == "SUSPICIOUS"
    assert "CRYPTO_HIGH_VALUE" in processed[0]["fraud_reason"]


def test_multiple_fraud_rules_trigger():
    merchants: Dict[str, Merchant] = {
        "m1": Merchant("m1", "Merchant 1", "cat", "US", "ACTIVE"),
    }
    t = datetime(2026, 3, 21, 12, 0, 0)
    validated = [
        _validated_tx(
            "t1",
            "m1",
            "c1",
            "200000",
            t,
            "CRYPTO",
            "CA",
            "US",
        )
    ]

    processed = apply_fraud_rules(validated, merchants, logger=logging.getLogger("test"))
    tx = processed[0]
    assert tx["transaction_status"] == "SUSPICIOUS"
    assert "HIGH_VALUE_TRANSACTION" in tx["fraud_reason"]
    assert "CROSS_BORDER_TRANSACTION" in tx["fraud_reason"]
    assert "CRYPTO_HIGH_VALUE" in tx["fraud_reason"]


def test_rapid_transactions_flagged():
    merchants: Dict[str, Merchant] = {
        "m1": Merchant("m1", "Merchant 1", "cat", "US", "ACTIVE"),
    }
    base = datetime(2026, 3, 21, 12, 0, 0)
    validated = [
        _validated_tx("t1", "m1", "c1", "10", base + timedelta(seconds=0), "CARD", "US", "US"),
        _validated_tx("t2", "m1", "c1", "10", base + timedelta(seconds=30), "CARD", "US", "US"),
        _validated_tx("t3", "m1", "c1", "10", base + timedelta(seconds=60), "CARD", "US", "US"),
        _validated_tx("t4", "m1", "c1", "10", base + timedelta(seconds=90), "CARD", "US", "US"),
    ]

    processed = apply_fraud_rules(validated, merchants, logger=logging.getLogger("test"))
    status_by_id = {tx["transaction_id"]: tx["transaction_status"] for tx in processed}
    assert status_by_id["t4"] == "SUSPICIOUS"
    assert status_by_id["t1"] == "VALID"


def test_transactions_outside_window_not_flagged():
    merchants: Dict[str, Merchant] = {
        "m1": Merchant("m1", "Merchant 1", "cat", "US", "ACTIVE"),
    }
    base = datetime(2026, 3, 21, 12, 0, 0)
    # First 3 within 90 seconds, 4th arrives after 2 minutes window.
    validated = [
        _validated_tx("t1", "m1", "c1", "10", base + timedelta(seconds=0), "CARD", "US", "US"),
        _validated_tx("t2", "m1", "c1", "10", base + timedelta(seconds=30), "CARD", "US", "US"),
        _validated_tx("t3", "m1", "c1", "10", base + timedelta(seconds=60), "CARD", "US", "US"),
        _validated_tx("t4", "m1", "c1", "10", base + timedelta(seconds=121), "CARD", "US", "US"),
    ]

    processed = apply_fraud_rules(validated, merchants, logger=logging.getLogger("test"))
    status_by_id = {tx["transaction_id"]: tx["transaction_status"] for tx in processed}
    assert status_by_id["t4"] == "VALID"

