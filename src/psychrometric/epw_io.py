# src/psychrometric/epw_io.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EPWMeta:
    location: str = "unknown"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[float] = None  # EPW header timezone (hours)
    elevation_m: Optional[float] = None


def _parse_location_header(line: str) -> EPWMeta:
    # LOCATION,City,State,Country,DataSource,WMO,Lat,Lon,TZ,Elevation
    parts = [p.strip() for p in line.split(",")]
    if not parts or parts[0].upper() != "LOCATION":
        return EPWMeta()

    def _to_float(x: str) -> Optional[float]:
        try:
            return float(x)
        except Exception:
            return None

    location = parts[1] if len(parts) > 1 and parts[1] else "unknown"
    lat = _to_float(parts[6]) if len(parts) > 6 else None
    lon = _to_float(parts[7]) if len(parts) > 7 else None
    tz = _to_float(parts[8]) if len(parts) > 8 else None
    elev = _to_float(parts[9]) if len(parts) > 9 else None
    return EPWMeta(location=location, latitude=lat, longitude=lon, timezone=tz, elevation_m=elev)


def load_epw(epw_path: str | Path) -> tuple[pd.DataFrame, EPWMeta]:
    """
    EPWを読み込み、描画に必要な最小列を返す。

    Returns
    -------
    df columns:
      - dt: datetime (naive; EPW local standard time)
      - year, month
      - db_c: Dry Bulb [degC]
      - rh_pct: Relative Humidity [%]
      - p_kpa: Pressure [kPa]  (EPWはPa → kPaへ変換)
    meta:
      EPWヘッダのLOCATION情報（取れなければunknown）
    """
    epw_path = Path(epw_path)

    with epw_path.open("r", encoding="utf-8", errors="ignore") as f:
        header = [next(f).rstrip("\n") for _ in range(8)]
        meta = _parse_location_header(header[0]) if header else EPWMeta()

        # EPWデータ部（多数列）をそのまま読み、必要列だけ抜く
        raw = pd.read_csv(f, header=None)

    # EPWの一般的な列位置（0-index）
    # 0:Year,1:Month,2:Day,3:Hour,4:Minute,5:DataSource,6:DryBulb,7:DewPoint,8:RH,9:Pressure(Pa)
    needed = raw.iloc[:, [0, 1, 2, 3, 4, 6, 8, 9]].copy()
    needed.columns = ["year", "month", "day", "hour", "minute", "db_c", "rh_pct", "p_pa"]

    # 欠損コードをNaN化（代表的：db=99.9, rh=999, p=999999）
    needed["db_c"] = needed["db_c"].replace(99.9, np.nan).astype(float)
    needed["rh_pct"] = needed["rh_pct"].replace(999, np.nan).astype(float)
    needed["p_pa"] = needed["p_pa"].replace(999999, np.nan).astype(float)

    # 時刻生成：EPWのhour=24/minute=60を最低限ケア（厳密な“時間終端”解釈は後で調整可）
    y = needed["year"].astype(int)
    m = needed["month"].astype(int)
    d = needed["day"].astype(int)
    hh = needed["hour"].astype(int)
    mm = needed["minute"].astype(int)

    add_h = (mm == 60).astype(int)
    mm = mm.where(mm != 60, 0)
    hh = hh + add_h

    add_d = (hh == 24).astype(int)
    hh = hh.where(hh != 24, 0)

    base = pd.to_datetime(dict(year=y, month=m, day=d), errors="coerce")
    dt = base + pd.to_timedelta(add_d, unit="D") + pd.to_timedelta(hh, unit="h") + pd.to_timedelta(mm, unit="m")

    df = pd.DataFrame(
        {
            "dt": dt,
            "year": y,
            "month": m,
            "db_c": needed["db_c"],
            "rh_pct": needed["rh_pct"],
            "p_kpa": needed["p_pa"] / 1000.0,  # Pa -> kPa
        }
    )

    # 描画不能な行は落とす（dt, db, rhが必須）
    df = df.dropna(subset=["dt", "db_c", "rh_pct"]).reset_index(drop=True)

    # 圧力が全欠損なら標準大気圧へ
    if df["p_kpa"].notna().sum() == 0:
        df["p_kpa"] = 101.325

    return df, meta
