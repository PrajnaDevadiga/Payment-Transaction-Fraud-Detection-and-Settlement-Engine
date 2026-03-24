from decimal import Decimal
from typing import Dict

from src.loader import Merchant
from src.settlement_engine import compute_merchant_settlements


def test_settlement_only_valid_transactions():
    merchants: Dict[str, Merchant] = {
        "m1": Merchant("m1", "Merchant 1", "cat", "US", "ACTIVE"),
    }
    processed_transactions = [
        {
            "transaction_id": "t1",
            "merchant_id": "m1",
            "transaction_amount": Decimal("10"),
            "transaction_status": "VALID",
        },
        {
            "transaction_id": "t2",
            "merchant_id": "m1",
            "transaction_amount": Decimal("20"),
            "transaction_status": "SUSPICIOUS",
        },
    ]

    report = compute_merchant_settlements(processed_transactions, merchants)
    assert report[0]["settlement_amount"] == Decimal("10")
    assert report[0]["valid_transactions"] == 1
    assert report[0]["fraud_transactions"] == 1


def test_settlement_amount_calculation():
    merchants: Dict[str, Merchant] = {
        "m1": Merchant("m1", "Merchant 1", "cat", "US", "ACTIVE"),
        "m2": Merchant("m2", "Merchant 2", "cat", "US", "ACTIVE"),
    }
    processed_transactions = [
        {
            "transaction_id": "t1",
            "merchant_id": "m1",
            "transaction_amount": Decimal("10.50"),
            "transaction_status": "VALID",
        },
        {
            "transaction_id": "t2",
            "merchant_id": "m1",
            "transaction_amount": Decimal("5.00"),
            "transaction_status": "VALID",
        },
        {
            "transaction_id": "t3",
            "merchant_id": "m1",
            "transaction_amount": Decimal("100.00"),
            "transaction_status": "SUSPICIOUS",
        },
        {
            "transaction_id": "t4",
            "merchant_id": "m2",
            "transaction_amount": Decimal("1.00"),
            "transaction_status": "VALID",
        },
    ]

    report = compute_merchant_settlements(processed_transactions, merchants)
    report_by_id = {r["merchant_id"]: r for r in report}
    assert report_by_id["m1"]["settlement_amount"] == Decimal("15.50")
    assert report_by_id["m1"]["total_transactions"] == 3
    assert report_by_id["m1"]["valid_transactions"] == 2
    assert report_by_id["m1"]["fraud_transactions"] == 1
    assert report_by_id["m2"]["settlement_amount"] == Decimal("1.00")

