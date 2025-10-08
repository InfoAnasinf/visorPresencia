from app.domain.entities.weekly_metrics import WeeklyMetrics


def test_weekly_metrics_total_hours_label():
    metrics = WeeklyMetrics(total_minutes=510, incomplete_days=1, worked_days=5)
    assert metrics.total_hours_label == "08:30"
    assert metrics.incomplete_days == 1
    assert metrics.worked_days == 5
