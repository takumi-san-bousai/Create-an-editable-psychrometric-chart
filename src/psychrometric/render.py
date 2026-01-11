# src/psychrimetric/render.py
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from shimeri import PsychrometricCalculator, PsychrometricChart
from .svg_post import postprocess_svg

from .add import ZoneSpec, add_zone_polygon


def _pressure_kpa(df: pd.DataFrame, fallback_kpa: float = 101.325) -> float:
    p = pd.to_numeric(df.get("p_kpa", pd.Series([], dtype=float)), errors="coerce")
    v = float(p.median()) if np.isfinite(p.median()) else fallback_kpa
    return v


def render_density_svg(
    df: pd.DataFrame,
    out_svg: str | Path,
    title: str,
    *,
    colorscale: str = "Blues",  # 淡色カラースケール
    nbinsx: int = 40,
    nbinsy: int = 30,
    ncontours: int = 10,
    showscale: bool = False,
    opacity: float = 0.9,
    width: int = 900,
    height: int = 650,
    add_scatter: bool = False,
) -> Path:
    """
    df: columns = dt, db_c, rh_pct, p_kpa
    out: SVG path
    
    利用可能なカラースケール例:
    - 淡色系: "Blues", "Greens", "Greys", "Purples", "Reds", "BuGn", "BuPu", "GnBu", "OrRd", "PuBu", "PuRd", "RdPu", "YlGn", "YlOrBr", "YlOrRd"
    - 濃色系: "Turbo", "Viridis", "Plasma", "Inferno", "Magma", "Cividis"
    - 発散系: "RdBu", "RdGy", "PiYG", "PRGn", "PuOr", "BrBG", "RdYlBu", "RdYlGn", "Spectral"
    """
    if df.empty:
        raise ValueError("df is empty (no data to plot).")

    out_svg = Path(out_svg)
    out_svg.parent.mkdir(parents=True, exist_ok=True)

    p_kpa = _pressure_kpa(df)
    calc = PsychrometricCalculator(pressure=p_kpa)

    db = df["db_c"].to_numpy(dtype=float)
    rh = df["rh_pct"].to_numpy(dtype=float)

    # 2変数(db,rh) -> 全変数を算出（hr[g/kg], en[kJ/kg]が得られる）
    _, _, _, hr_gkg, en_kjkg = calc.get_all(db=db, rh=rh)

    chart = PsychrometricChart(pressure=p_kpa)

    # 密度（2D histogram contour）
    chart.add_histogram_2d_contour(
        en=en_kjkg,
        hr=hr_gkg,
        name="density", #固定
        nbinsx=nbinsx,
        nbinsy=nbinsy,
        ncontours=ncontours,
        contours_coloring="fill",
        colorscale=colorscale,
        showscale=showscale,
        opacity=opacity,
        hoverinfo="skip",
        showlegend=False,
    )

    # 任意：点群をうっすら重ねる（プレボではOFF推奨）
    if add_scatter:
        chart.add_points(
            en=en_kjkg,
            hr=hr_gkg,
            name="points",        # ★固定
            mode="markers",
            marker=dict(size=2, opacity=0.15),
            showlegend=False,
            hoverinfo="skip",
        )

    # 体裁（プレボ向け：白背景・黒文字・枠線）
    chart.update_layout(
        title=dict(text=title, x=0.01, xanchor="left"),
        width=width,
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Yu Gothic", size=10, color="black"),
        margin=dict(l=50, r=30, t=50, b=45),
    )
    chart.update_xaxes(showline=True, linecolor="black", mirror=True, ticks="inside", tickfont=dict(color="black"))
    chart.update_yaxes(showline=True, linecolor="black", mirror=True, ticks="inside", tickfont=dict(color="black"))

    # SVG出力（plotly + kaleido が必要）
    try:
        chart.write_image(str(out_svg), format="svg")
    except Exception as e:
        raise RuntimeError(
            "SVG export failed. Install kaleido (e.g., `pip install -U kaleido`) and retry."
        ) from e
    
    postprocess_svg(out_svg)

    return out_svg
