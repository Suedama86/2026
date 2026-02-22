from __future__ import annotations

import csv
import statistics
import sys
from pathlib import Path


def to_bool(value: str) -> bool:
    return value.strip().lower() in {"yes", "true", "1"}


def to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def summarize(csv_path: Path) -> dict[str, float]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Filen finns inte: {csv_path}")

    rows: list[dict[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        raise ValueError("CSV-filen innehåller inga datarader.")

    success_values = [to_bool(row.get("success", "")) for row in rows]
    time_values = [to_float(row.get("time_minutes", "")) for row in rows]
    intervention_values = [to_float(row.get("manual_interventions", "")) for row in rows]
    confidence_values = [to_float(row.get("confidence_score", "")) for row in rows]

    success_rate = (sum(success_values) / len(success_values)) * 100.0
    median_time = statistics.median(time_values)
    avg_interventions = statistics.mean(intervention_values)
    avg_confidence = statistics.mean(confidence_values)

    return {
        "runs": float(len(rows)),
        "success_rate_percent": success_rate,
        "median_time_minutes": median_time,
        "avg_manual_interventions": avg_interventions,
        "avg_confidence_score": avg_confidence,
    }


def print_summary(summary: dict[str, float]) -> None:
    print("=== KPI-sammanställning ===")
    print(f"Antal körningar: {int(summary['runs'])}")
    print(f"Andel lyckade: {summary['success_rate_percent']:.1f}%")
    print(f"Median tid: {summary['median_time_minutes']:.1f} min")
    print(f"Snitt manuella ingripanden: {summary['avg_manual_interventions']:.2f}")
    print(f"Snitt confidence score: {summary['avg_confidence_score']:.2f}")


def main() -> int:
    if len(sys.argv) != 2:
        print("Användning: python3 training/scripts/sammanstall_kpi.py <path-to-csv>")
        return 1

    csv_path = Path(sys.argv[1]).expanduser().resolve()
    summary = summarize(csv_path)
    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
