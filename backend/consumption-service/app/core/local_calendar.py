"""Día civil en una zona IANA → rango en UTC para consultas Mongo (timestamps en UTC)."""

from __future__ import annotations

from datetime import date, datetime, timezone as dt_timezone

import pendulum


def utc_range_for_local_calendar_day(target_date: date, tz_name: str) -> tuple[datetime, datetime]:
    """
    Inicio inclusivo y fin exclusivo en UTC que corresponden al calendario `target_date`
    desde las 00:00 hasta las 24:00 en `tz_name`.
    """
    start_local = pendulum.datetime(
        target_date.year, target_date.month, target_date.day, 0, 0, 0, tz=tz_name
    )
    end_local = start_local.add(days=1)
    start_utc = start_local.in_timezone("UTC")
    end_utc = end_local.in_timezone("UTC")
    return (
        datetime.fromtimestamp(start_utc.timestamp(), tz=dt_timezone.utc),
        datetime.fromtimestamp(end_utc.timestamp(), tz=dt_timezone.utc),
    )


def local_hour_from_utc_timestamp(ts: datetime, tz_name: str) -> int:
    """Hora 0-23 del instante en la zona indicada."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=dt_timezone.utc)
    return pendulum.instance(ts).in_timezone(tz_name).hour
