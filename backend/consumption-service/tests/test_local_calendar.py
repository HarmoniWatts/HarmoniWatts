from datetime import date, datetime, timezone

from app.core.local_calendar import (
    local_hour_from_utc_timestamp,
    utc_range_for_local_calendar_day,
)

BOGOTA = "America/Bogota"  # UTC-5, sin horario de verano


def test_rango_utc_de_un_dia_en_bogota():
    start, end = utc_range_for_local_calendar_day(date(2026, 3, 10), BOGOTA)
    assert start == datetime(2026, 3, 10, 5, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 3, 11, 5, 0, tzinfo=timezone.utc)


def test_rango_utc_dura_23_horas_en_cambio_de_horario():
    start, end = utc_range_for_local_calendar_day(date(2026, 3, 8), "America/New_York")
    assert (end - start).total_seconds() == 23 * 3600


def test_hora_local_desde_timestamp_utc():
    ts = datetime(2026, 3, 10, 2, 30, tzinfo=timezone.utc)
    assert local_hour_from_utc_timestamp(ts, BOGOTA) == 21


def test_timestamp_naive_se_interpreta_como_utc():
    assert local_hour_from_utc_timestamp(datetime(2026, 3, 10, 12, 0), BOGOTA) == 7
