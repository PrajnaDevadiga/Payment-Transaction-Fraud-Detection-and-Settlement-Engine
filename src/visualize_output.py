import argparse
import json
import os
from typing import Dict


def _build_bar(value: int, max_value: int, width: int = 32) -> str:
    if max_value <= 0:
        return ""
    filled = int(round((value / max_value) * width))
    return "#" * filled


def build_fraud_summary_text(summary: Dict[str, int]) -> str:
    metric_order = [
        ("total_transactions", "Total Transactions"),
        ("valid_transactions", "Valid Transactions"),
        ("fraud_transactions", "Fraud Transactions"),
        ("high_value_frauds", "High Value Frauds"),
        ("cross_border_frauds", "Cross Border Frauds"),
        ("rapid_transaction_frauds", "Rapid Transaction Frauds"),
    ]

    values = [int(summary.get(key, 0)) for key, _ in metric_order]
    max_value = max(values) if values else 0

    lines = ["Fraud Summary Visualization", "=" * 27, ""]
    for (key, label), value in zip(metric_order, values):
        bar = _build_bar(value, max_value)
        lines.append(f"{label:26} | {bar:<32} {value}")

    return "\n".join(lines) + "\n"


def write_fraud_summary_visualization(input_path: str, output_path: str) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    text = build_fraud_summary_text(summary)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)


def write_fraud_summary_graph(input_path: str, graph_output_path: str) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "matplotlib is required to generate graph output. "
            "Install it with: pip install matplotlib"
        ) from exc

    with open(input_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    metric_order = [
        ("total_transactions", "Total Transactions"),
        ("valid_transactions", "Valid Transactions"),
        ("fraud_transactions", "Fraud Transactions"),
        ("high_value_frauds", "High Value Frauds"),
        ("cross_border_frauds", "Cross Border Frauds"),
        ("rapid_transaction_frauds", "Rapid Transaction Frauds"),
    ]
    labels = [label for _, label in metric_order]
    values = [int(summary.get(key, 0)) for key, _ in metric_order]

    os.makedirs(os.path.dirname(graph_output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(labels, values, color="#3B82F6")
    ax.set_title("Fraud Summary Metrics")
    ax.set_ylabel("Count")
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right")

    # Show values above bars for readability.
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            str(value),
            ha="center",
            va="bottom",
        )

    fig.tight_layout()
    fig.savefig(graph_output_path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate text and graph visualizations from fraud_summary.json."
    )
    parser.add_argument(
        "--input",
        default=os.path.join("outputs", "fraud_summary.json"),
        help="Path to fraud_summary.json",
    )
    parser.add_argument(
        "--output",
        default=os.path.join("outputs", "fraud_summary_visualization.txt"),
        help="Output path for visualization text",
    )
    parser.add_argument(
        "--graph-output",
        default=os.path.join("outputs", "fraud_summary_graph.png"),
        help="Output path for visualization graph image",
    )
    args = parser.parse_args()

    write_fraud_summary_visualization(args.input, args.output)
    write_fraud_summary_graph(args.input, args.graph_output)
    print(f"Visualization written to: {args.output}")
    print(f"Graph written to: {args.graph_output}")


if __name__ == "__main__":
    main()
