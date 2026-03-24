# Payment Transaction Fraud Detection & Settlement Engine (Python)

## Project Description
This project processes payment transactions for a fintech workflow:
1) validate incoming records, 2) apply rule-based fraud detection, 3) aggregate settlement amounts per merchant, and 4) generate output reports.

Inputs:
- `merchants.csv` (merchant metadata)
- `transactions.csv` (raw transactions)

Outputs:
- `outputs/processed_transactions.csv`
- `outputs/merchant_settlement_report.csv`
- `outputs/fraud_summary.json`

## Business Rules

### Transaction Validation
A transaction is **ignored** (not included in further processing) if any rule triggers:
- `merchant_id` not found in `merchants.csv`
- merchant `status` is `BLOCKED`
- `transaction_amount` `<= 0`
- `transaction_time` cannot be parsed into a valid timestamp

Invalid records are logged to `logs/fraud_engine.log`.

### Fraud Detection Rules
A validated transaction is marked **SUSPICIOUS** if **any** fraud rule triggers:
- `HIGH_VALUE_TRANSACTION` if `transaction_amount > 100000`
- `CROSS_BORDER_TRANSACTION` if `transaction.country != merchant.country`
- `RAPID_TRANSACTIONS` if the same `customer_id` has **4th or later** transactions within any rolling 2-minute window
- `CRYPTO_HIGH_VALUE` if `payment_method == CRYPTO` and `transaction_amount > 50000`

If no rule triggers, the transaction is `VALID`.

### Settlement Rules
Only `VALID` transactions participate in settlement:
- `settlement_amount = sum(transaction_amount)` over `VALID` transactions per merchant

## Assumptions
- `transaction_time` parsing supports:
  - ISO-8601 like `2026-03-21T12:34:56` and `2026-03-21T12:34:56Z`
  - `YYYY-MM-DD HH:MM:SS` and `YYYY/MM/DD HH:MM:SS` and `YYYY-MM-DD HH:MM`
- Fraud `fraud_flag` is exported to CSV as `True/False` (stringified by Python).
- Rapid rule semantics: for a qualifying burst of 4+ transactions within 2 minutes, the **4th and subsequent** transactions in that rolling window are flagged.

## How to Run the Program
Default behavior:
- It will read `data/merchants.csv` and `data/transactions.csv` if present
- Otherwise it falls back to `./merchants.csv` and `./transactions.csv`

Run:
```bash
python -m src.main
```

After running, check:
- `outputs/processed_transactions.csv`
- `outputs/merchant_settlement_report.csv`
- `outputs/fraud_summary.json`
- `logs/fraud_engine.log`

## Visualize Output (Non-Intrusive)
This project includes an optional text visualization for the fraud summary.
It does not modify existing pipeline behavior or outputs.

Run:
```bash
python -m src.visualize_output
```

This reads `outputs/fraud_summary.json` and writes:
- `outputs/fraud_summary_visualization.txt`
- `outputs/fraud_summary_graph.png`

## How to Run Unit Tests
Run:
```bash
pytest -q
```

## Edge Cases Handled
- Unknown merchants
- Blocked merchants
- Negative/zero transaction amounts
- Invalid timestamps (transaction rejected + logged)
- Multiple fraud rules triggering on the same transaction
- Rapid detection across a rolling 2-minute window

