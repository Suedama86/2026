from pathlib import Path

from training.scripts.sammanstall_kpi import summarize


def test_summarize_returns_expected_metrics() -> None:
    csv_path = Path("training/kpi_scorecard_template.csv")
    summary = summarize(csv_path)

    assert summary["runs"] == 2.0
    assert summary["success_rate_percent"] == 50.0
    assert summary["median_time_minutes"] == 12.25
    assert summary["avg_manual_interventions"] == 1.0
    assert summary["avg_confidence_score"] == 3.0
