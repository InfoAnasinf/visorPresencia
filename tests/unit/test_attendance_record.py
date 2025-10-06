from datetime import date, time

from app.domain.entities.attendance_record import AttendanceRecord


def test_timestamp_combines_date_and_time():
    record = AttendanceRecord(
        employee="Ana",
        date_value=date(2025, 1, 1),
        time_value=time(9, 0),
        punch_type="entrada",
    )

    assert record.timestamp.hour == 9
