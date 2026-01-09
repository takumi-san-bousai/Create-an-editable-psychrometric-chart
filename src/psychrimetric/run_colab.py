# src/psychrimetric/colab_run.py
from __future__ import annotations

import argparse
from pathlib import Path

from .epw_io import load_epw
from .period_filter import split_by_month, split_by_seasons
from .render import render_density_svg
from .zone_registry import load_zones_config

DEFAULT_SEASONS = {"Winter": [12, 1, 2], "Spring": [3, 4, 5], "Summer": [6, 7, 8], "Fall": [9, 10, 11]}


def parse_list(s: str | None) -> list[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def main() -> None:
    p = argparse.ArgumentParser(description="Colab runner: EPW -> psychrometric SVGs (monthly/seasonal)")
    p.add_argument("--epw", required=True, help="Path to EPW file")
    p.add_argument("--out_dir", required=True, help="Output directory")
    p.add_argument("--mode", choices=["monthly", "seasonal", "Yearly", "All"], default="All")
    p.add_argument("--zones", default="", help="zones.json path (optional)")
    p.add_argument("--select_zones", default="", help="Comma-separated zone names to draw")
    p.add_argument("--add_points", action="store_true", help="Overlay points")
    args = p.parse_args()

    epw_path = Path(args.epw)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    zones = None
    selected = parse_list(args.select_zones)
    if args.zones:
        zones = load_zones_config(args.zones)

    df, meta = load_epw(epw_path)

    if args.mode in ("monthly", "All"):
        for m, d in split_by_month(df).items():
            if len(d) == 0:
                continue
            out_svg = out_dir / f"{meta.location}_M{m:02d}.svg"
            render_density_svg(
                d,
                out_svg,
                title=f"{meta.location} / Month {m:02d} (N={len(d)})",
                zones=zones,
                selected_zone_names=selected,
                add_scatter=args.add_points,
            )

    if args.mode in ("seasonal", "All"):
        by_season = split_by_seasons(df, DEFAULT_SEASONS)
        for name, d in by_season.items():
            if len(d) == 0:
                continue
            out_svg = out_dir / f"{meta.location}_{name}.svg"
            render_density_svg(
                d,
                out_svg,
                title=f"{meta.location} / {name} (N={len(d)})",
                zones=zones,
                selected_zone_names=selected,
                add_scatter=args.add_points,
            )

    if args.mode in ("Yearly", "All"):
        out_svg = out_dir / f"{meta.location}_Yearly.svg"
        render_density_svg(
            df,
            out_svg,
            title=f"{meta.location} / Yearly (N={len(df)})",
            zones=zones,
            selected_zone_names=selected,
            add_scatter=args.add_points,
        )


if __name__ == "__main__":
    main()
