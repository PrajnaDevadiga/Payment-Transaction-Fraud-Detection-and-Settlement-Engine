import logging
from typing import Dict

from src.loader import Merchant
from src.loader import load_merchants, load_transactions, parse_transaction_amount
from src.validator import validate_transactions


def test_invalid_merchant_rejected(tmp_path):
    merchants: Dict[str, Merchant] = {
        "m1": Merchant("m1", "Merchant 1", "cat", "US", "ACTIVE"),
    }
    txs = [
        {
            "transaction_id": "t1",
            "merchant_id": "unknown",
            "customer_id": "c1",
            "transaction_amount": "10",
            "transaction_time": "2026-03-21T12:00:00",
            "payment_method": "CARD",
            "country": "US",
        }
    ]

    logger = logging.getLogger("test_validator_1")
    validated, invalid_count = validate_transactions(txs, merchants, logger=logger)
    assert validated == []
    assert invalid_count == 1


def test_blocked_merchant_rejected(tmp_path):
    merchants: Dict[str, Merchant] = {
        "m1": Merchant("m1", "Merchant 1", "cat", "US", "BLOCKED"),
    }
    txs = [
        {
            "transaction_id": "t1",
            "merchant_id": "m1",
            "customer_id": "c1",
            "transaction_amount": "10",
            "transaction_time": "2026-03-21T12:00:00",
            "payment_method": "CARD",
            "country": "US",
        }
    ]

    logger = logging.getLogger("test_validator_2")
    validated, invalid_count = validate_transactions(txs, merchants, logger=logger)
    assert validated == []
    assert invalid_count == 1


def test_negative_amount_rejected(tmp_path):
    merchants: Dict[str, Merchant] = {
        "m1": Merchant("m1", "Merchant 1", "cat", "US", "ACTIVE"),
    }
    txs = [
        {
            "transaction_id": "t1",
            "merchant_id": "m1",
            "customer_id": "c1",
            "transaction_amount": "-5",
            "transaction_time": "2026-03-21T12:00:00",
            "payment_method": "CARD",
            "country": "US",
        }
    ]

    logger = logging.getLogger("test_validator_3")
    validated, invalid_count = validate_transactions(txs, merchants, logger=logger)
    assert validated == []
    assert invalid_count == 1


def test_invalid_timestamp_handling(tmp_path):
    merchants: Dict[str, Merchant] = {
        "m1": Merchant("m1", "Merchant 1", "cat", "US", "ACTIVE"),
    }
    txs = [
        {
            "transaction_id": "t1",
            "merchant_id": "m1",
            "customer_id": "c1",
            "transaction_amount": "10",
            "transaction_time": "not-a-time",
            "payment_method": "CARD",
            "country": "US",
        }
    ]

    logger = logging.getLogger("test_validator_4")
    validated, invalid_count = validate_transactions(txs, merchants, logger=logger)
    assert validated == []
    assert invalid_count == 1


def test_load_merchants_success_and_strip(tmp_path):
    merchants_csv = tmp_path / "merchants.csv"
    merchants_csv.write_text(
        "merchant_id,merchant_name,merchant_category,country,status\n"
        " m1 , Merchant 1 ,cat1, US ,ACTIVE\n"
        "m2,Merchant 2,cat2,CA,BLOCKED\n",
        encoding="utf-8",
    )

    merchants = load_merchants(str(merchants_csv))
    assert set(merchants.keys()) == {"m1", "m2"}
    assert merchants["m1"].merchant_name == "Merchant 1"
    assert merchants["m1"].country == "US"
    assert merchants["m2"].status == "BLOCKED"


def test_load_merchants_missing_columns_raises(tmp_path):
    merchants_csv = tmp_path / "merchants.csv"
    merchants_csv.write_text(
        "merchant_id,merchant_name,country,status\n"
        "m1,Merchant 1,US,ACTIVE\n",
        encoding="utf-8",
    )

    try:
        load_merchants(str(merchants_csv))
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "missing columns" in str(e)


def test_load_transactions_success(tmp_path):
    tx_csv = tmp_path / "transactions.csv"
    tx_csv.write_text(
        "transaction_id,merchant_id,customer_id,transaction_amount,transaction_time,payment_method,country\n"
        "t1,m1,c1,10,2026-03-21T12:00:00,CARD,US\n",
        encoding="utf-8",
    )

    txs = load_transactions(str(tx_csv))
    assert len(txs) == 1
    assert txs[0]["transaction_id"] == "t1"
    assert txs[0]["transaction_amount"] == "10"
    assert txs[0]["payment_method"] == "CARD"


def test_parse_transaction_amount_invalid_returns_none():
    assert parse_transaction_amount("") is None
    assert parse_transaction_amount("   ") is None
    assert parse_transaction_amount("not-a-number") is None

