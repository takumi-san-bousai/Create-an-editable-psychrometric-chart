# src/psychrimetric/zone_registry.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .add import ZoneSpec


@dataclass(frozen=True)
class ZoneStyle:
    fill_opacity: float = 0.18
    line_width: float = 1.5
    show_legend: bool = False


@dataclass(frozen=True)
class ZoneEntry:
    spec: ZoneSpec
    style: ZoneStyle


def load_zones_config(path: str | Path) -> Dict[str, ZoneEntry]:
    """
    zones.json を読み込み、{zone_name: ZoneEntry} を返す。

    zones.json 形式（例）:
    {
      "ASHRAE_like_summer": {
        "coord_type": "db_rh",
        "x": [23, 26, 26, 23],
        "y": [40, 40, 60, 60],
        "style": { "fill_opacity": 0.12, "line_width": 1.5 }
      }
    }

    Returns
    -------
    dict[str, ZoneEntry]
      - key: ゾーン名（GUIで表示する名前）
      - value.spec: ZoneSpec(coord_type, x, y, name="zone")
      - value.style: ZoneStyle(fill_opacity, line_width, show_legend)
    """
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("zones.json: top-level must be an object (dict).")

    out: Dict[str, ZoneEntry] = {}

    for zone_name, z in data.items():
        if not isinstance(zone_name, str) or not zone_name.strip():
            raise ValueError("zones.json: zone name must be a non-empty string.")
        if not isinstance(z, dict):
            raise ValueError(f"zones.json: zone '{zone_name}' must be an object.")

        coord_type = z.get("coord_type")
        if coord_type not in ("db_rh", "db_hr"):
            raise ValueError(f"zones.json: zone '{zone_name}': coord_type must be 'db_rh' or 'db_hr'.")

        x = z.get("x")
        y = z.get("y")
        if not isinstance(x, list) or not isinstance(y, list):
            raise ValueError(f"zones.json: zone '{zone_name}': x/y must be lists.")
        if len(x) != len(y):
            raise ValueError(f"zones.json: zone '{zone_name}': x and y must have same length.")
        if len(x) < 3:
            raise ValueError(f"zones.json: zone '{zone_name}': need at least 3 vertices.")

        # numeric check
        try:
            x2 = [float(v) for v in x]
            y2 = [float(v) for v in y]
        except Exception:
            raise ValueError(f"zones.json: zone '{zone_name}': x/y must be numeric arrays.")

        style_obj = z.get("style") or {}
        if not isinstance(style_obj, dict):
            raise ValueError(f"zones.json: zone '{zone_name}': style must be an object if provided.")

        def _get_float(key: str, default: float) -> float:
            v = style_obj.get(key, default)
            try:
                return float(v)
            except Exception:
                raise ValueError(f"zones.json: zone '{zone_name}': style.{key} must be a number.")

        fill_opacity = _get_float("fill_opacity", 0.18)
        line_width = _get_float("line_width", 1.5)
        show_legend = bool(style_obj.get("show_legend", False))

        # 重要：trace名は "zone" 固定（SVG後処理で zone レイヤーにまとめるため）
        spec = ZoneSpec(coord_type=coord_type, x=x2, y=y2, name="zone")
        style = ZoneStyle(fill_opacity=fill_opacity, line_width=line_width, show_legend=show_legend)

        out[zone_name] = ZoneEntry(spec=spec, style=style)

    return out
