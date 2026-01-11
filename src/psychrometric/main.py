"""
メイン実行部
epwデータを各描画を行って格納する
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .epw_io import load_epw
from .period_filter import split_by_month, split_by_seasons
from .render import render_density_svg
from .gui import popup_select


DEFAULT_SEASONS = {"Winter": [12, 1, 2], "Spring": [3, 4, 5], "Summer": [6, 7, 8], "Autumn": [9, 10, 11]} #北半球に寄せてるけどもまあいいかといいう感じ


def main():
    sel = popup_select()

    df, meta = load_epw(sel.epw_path)

    if sel.run_monthly:
        for m, d in split_by_month(df).items():
            if len(d) == 0:
                continue
            out = sel.out_dir / f"{meta.location}_M{m:02d}.svg"
            render_density_svg(d, out, f"{meta.location} / Month {m:02d} (N={len(d)})")

    if sel.run_seasonal:
        seasons = DEFAULT_SEASONS
        if sel.seasons_config:
            seasons = json.loads(Path(sel.seasons_config).read_text(encoding="utf-8"))

        for name, d in split_by_seasons(df, seasons).items():
            if len(d) == 0:
                continue
            out = sel.out_dir / f"{meta.location}_{name}.svg"
            render_density_svg(d, out, f"{meta.location} / {name} (N={len(d)})")

    if sel.run_yearly:
        out = sel.out_dir / f"{meta.location}_Yearly.svg"
        render_density_svg(df, out, f"{meta.location} / Yearly (N={len(df)})")
    

if __name__ == "__main__":
    # スクリプトとして直接実行された場合、親ディレクトリ(src)をパスに追加して
    # 'psychrimetric' パッケージが見つかるようにする
    if __package__ is None:
        sys.path.append(str(Path(__file__).parent.parent))
    main()
