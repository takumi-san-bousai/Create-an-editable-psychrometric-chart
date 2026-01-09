# src/psychrimetric/app.py
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from .epw_io import load_epw
from .period_filter import split_by_month, split_by_seasons
from .render import render_density_svg
from .zone_registry import load_zones_config


DEFAULT_SEASONS = {"DJF": [12, 1, 2], "MAM": [3, 4, 5], "JJA": [6, 7, 8], "SON": [9, 10, 11]}


@dataclass
class AppState:
    last_out_dir: str | None = None
    last_zones_config: str | None = None
    last_selected_zones: list[str] | None = None
    last_mode: str | None = None  # "Monthly"|"Seasonal"|"Both"


def _state_path() -> Path:
    # ユーザーのホーム配下に保存（配布EXEでも書ける）
    base = Path.home() / ".psychrimetric"
    base.mkdir(parents=True, exist_ok=True)
    return base / "state.json"


def load_state() -> AppState:
    p = _state_path()
    if not p.exists():
        return AppState()
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return AppState(
            last_out_dir=d.get("last_out_dir"),
            last_zones_config=d.get("last_zones_config"),
            last_selected_zones=d.get("last_selected_zones") or [],
            last_mode=d.get("last_mode"),
        )
    except Exception:
        return AppState()


def save_state(st: AppState) -> None:
    p = _state_path()
    p.write_text(json.dumps(asdict(st), ensure_ascii=False, indent=2), encoding="utf-8")


def run_app() -> None:
    """
    GUIで選択→描画→SVG出力まで一気通貫。
    """
    # 選択GUI（あなたの gui.py を少し拡張して後述のGUISelectionを返す想定）
    from .gui_app import popup_select2  # 新規GUI（後述）

    state = load_state()
    sel = popup_select2(state)

    # 設定保存（次回用）
    state.last_out_dir = str(sel.out_dir)
    state.last_mode = sel.mode
    state.last_zones_config = str(sel.zones_config) if sel.zones_config else None
    state.last_selected_zones = sel.selected_zones or []
    save_state(state)

    #zones読み込み（任意）
    zones = None
    if sel.zones_config:
        zones = load_zones_config(sel.zones_config)

    df, meta = load_epw(sel.epw_path)
    

    # 月別
    if sel.mode in ("Monthly", "Both"):
        for m, d in split_by_month(df).items():
            if len(d) == 0:
                continue
            out = sel.out_dir / f"{meta.location}_M{m:02d}.svg"
            render_density_svg(
                d,
                out,
                title=f"{meta.location} / Month {m:02d} (N={len(d)})",
                zones=zones,
                selected_zone_names=sel.selected_zones,
                add_scatter=sel.add_points,
            )

    # 季節別
    if sel.mode in ("Seasonal", "Both"):
        seasons = DEFAULT_SEASONS
        # （将来）季節設定JSONもGUIで選べるようにするならここに追加
        by_season = split_by_seasons(df, seasons)
        for name, d in by_season.items():
            if len(d) == 0:
                continue
            out = sel.out_dir / f"{meta.location}_{name}.svg"
            render_density_svg(
                d,
                out,
                title=f"{meta.location} / {name} (N={len(d)})",
                zones=zones,
                selected_zone_names=sel.selected_zones,
                add_scatter=sel.add_points,
            )


def main() -> None:
    run_app()


if __name__ == "__main__":
    main()
