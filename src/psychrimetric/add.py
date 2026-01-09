from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

import numpy as np
import plotly.graph_objects as go

CoordType = Literal["db_rh", "db_hr"]


@dataclass(frozen=True)
class ZoneSpec:
    """
    ゾーン（快適域など）のポリゴン頂点定義。

    coord_type:
      - "db_rh": x=乾球温度[°C], y=相対湿度[%]
      - "db_hr": x=乾球温度[°C], y=絶対湿度[g/kg]
    """
    coord_type: CoordType
    x: Sequence[float]
    y: Sequence[float]
    name: str = "zone"


def add_zone_polygon(
    chart,
    zone: ZoneSpec,
    *,
    fill_opacity: float = 0.18,
    line_width: float = 1.5,
    show_legend: bool = False,
) -> None:
    """
    shimeri.PsychrometricChart にゾーン（ポリゴン）を追加する。

    仕様:
      - chart は shimeri.PsychrometricChart インスタンスを想定
      - chart._pc.get_all(...) を使って en/hr を算出
      - chart._skew_transform(en, hr) で座標変換
      - 追加される trace は必ず name="zone"（SVG後処理でグルーピング可能）
    """
    xs = np.asarray(zone.x, dtype=float)
    ys = np.asarray(zone.y, dtype=float)

    if xs.size < 3:
        raise ValueError("Zone polygon needs at least 3 vertices.")
    if xs.size != ys.size:
        raise ValueError("ZoneSpec.x and ZoneSpec.y must have the same length.")

    # close polygon if needed
    if xs[0] != xs[-1] or ys[0] != ys[-1]:
        xs = np.r_[xs, xs[0]]
        ys = np.r_[ys, ys[0]]

    # db/rh or db/hr -> en/hr
    if zone.coord_type == "db_rh":
        db = xs
        rh = ys
        _, _, _, hr_gkg, en_kjkg = chart._pc.get_all(db=db, rh=rh)
    elif zone.coord_type == "db_hr":
        db = xs
        hr_gkg = ys
        _, _, _, hr_gkg, en_kjkg = chart._pc.get_all(db=db, hr=hr_gkg)
    else:
        raise ValueError(f"Unknown coord_type: {zone.coord_type}")

    # transform to plot coords
    x_plot, y_plot = chart._skew_transform(np.asarray(en_kjkg), np.asarray(hr_gkg))

    # add filled polygon
    chart.add_trace(
        go.Scatter(
            x=x_plot,
            y=y_plot,
            name=zone.name,  # 既定 "zone"
            mode="lines",
            fill="toself",
            fillcolor=f"rgba(0,0,0,{fill_opacity})",
            line=dict(width=line_width),
            showlegend=show_legend,
            hoverinfo="skip",
        )
    )
