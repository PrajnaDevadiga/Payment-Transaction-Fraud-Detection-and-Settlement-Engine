import logging
import os
from typing import Optional

from src.fraud_engine import apply_fraud_rules
from src.loader import load_merchants, load_transactions
from src.reporter import (
    write_fraud_summary,
    write_merchant_settlement_report,
    write_processed_transactions,
)
from src.settlement_engine import compute_merchant_settlements
from src.validator import validate_transactions


def _default_paths():
    """
    Prefer `data/` but fall back to workspace root for convenience.
    """
    root_merchants = os.path.join(os.getcwd(), "merchants.csv")
    root_transactions = os.path.join(os.getcwd(), "transactions.csv")
    data_dir = os.path.join(os.getcwd(), "data")
    data_merchants = os.path.join(data_dir, "merchants.csv")
    data_transactions = os.path.join(data_dir, "transactions.csv")

    merchants_path = data_merchants if os.path.exists(data_merchants) else root_merchants
    transactions_path = data_transactions if os.path.exists(data_transactions) else root_transactions
    return merchants_path, transactions_path


def configure_logging(log_file_path: str) -> logging.Logger:
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    logger = logging.getLogger("fraud_engine")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Avoid adding duplicate handlers if main is called multiple times in-process.
    if not logger.handlers:
        fh = logging.FileHandler(log_file_path, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


def run(
    merchants_path: Optional[str] = None,
    transactions_path: Optional[str] = None,
    outputs_dir: str = "outputs",
    logs_dir: str = "logs",
) -> None:
    merchants_path, transactions_path = (
        _default_paths() if merchants_path is None or transactions_path is None else (merchants_path, transactions_path)
    )

    logger = configure_logging(os.path.join(logs_dir, "fraud_engine.log"))

    merchants = load_merchants(merchants_path)
    transactions = load_transactions(transactions_path)

    validated_transactions, _invalid_count = validate_transactions(transactions, merchants, logger=logger)
    processed_transactions = apply_fraud_rules(validated_transactions, merchants, logger=logger)
    settlement_report = compute_merchant_settlements(processed_transactions, merchants)

    os.makedirs(outputs_dir, exist_ok=True)
    write_processed_transactions(
        processed_transactions,
        os.path.join(outputs_dir, "processed_transactions.csv"),
    )
    write_merchant_settlement_report(
        settlement_report,
        os.path.join(outputs_dir, "merchant_settlement_report.csv"),
    )
    write_fraud_summary(
        processed_transactions,
        os.path.join(outputs_dir, "fraud_summary.json"),
    )


if __name__ == "__main__":
    run()

