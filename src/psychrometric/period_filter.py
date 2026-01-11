# src/psychrimetric/period_filter.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping

import pandas as pd


@dataclass(frozen=True)
class Period:
    start: datetime | None = None  # inclusive
    end: datetime | None = None    # exclusive
    months: tuple[int, ...] | None = None  # 1..12
    hours: tuple[int, ...] | None = None  # 0..23


def filter_period(df: pd.DataFrame, period: Period) -> pd.DataFrame:
    """
    df: load_epw() の戻り（dt, month 列を含むこと）
    """
    out = df
    if period.months:
        months = set(period.months)
        out = out[out["month"].isin(months)]
    if period.hours:
        target_hours = set(period.hours)
        out = out[out["dt"].dt.hour.isin(target_hours)]
    if period.start is not None:
        out = out[out["dt"] >= period.start]
    if period.end is not None:
        out = out[out["dt"] < period.end]
    return out.reset_index(drop=True)


def split_by_month(df: pd.DataFrame) -> dict[int, pd.DataFrame]:
    return {m: df[df["month"] == m].reset_index(drop=True) for m in range(1, 13)}


def split_by_seasons(df: pd.DataFrame, seasons: Mapping[str, Iterable[int]]) -> dict[str, pd.DataFrame]:
    """
    seasons: {"DJF":[12,1,2], "MAM":[3,4,5], ...}
    """
    out: dict[str, pd.DataFrame] = {}
    for name, months in seasons.items():
        out[name] = df[df["month"].isin(list(months))].reset_index(drop=True)
    return out

def split_by_hours(df: pd.DataFrame, hours_map: Mapping[str, Iterable[int]]) -> dict[str, pd.DataFrame]:
    """
    hours_map: {"Daytime": [9, 10, ...], "Nighttime": [18, 19, ...]}
    """
    out: dict[str, pd.DataFrame] = {}
    for name, hours in hours_map.items():
        out[name] = df[df["dt"].dt.hour.isin(list(hours))].reset_index(drop=True)
    return out