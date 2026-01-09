# src/psychrimetric/gui.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import filedialog, messagebox


@dataclass(frozen=True)
class GUISelection:
    epw_path: Path
    out_dir: Path
    run_monthly: bool
    run_seasonal: bool
    run_yearly: bool
    seasons_config: Optional[Path] = None


def popup_select() -> GUISelection:
    """
    GUIで EPW / 出力先 / 実行モード / seasons_config を選ばせる。
    """
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを表示しない

    messagebox.showinfo("psychrimetric", "EPWファイルを選択してください。")
    epw = filedialog.askopenfilename(
        title="Select EPW file",
        filetypes=[("EnergyPlus Weather", "*.epw"), ("All files", "*.*")],
    )
    if not epw:
        raise SystemExit("Cancelled: EPW not selected.")

    messagebox.showinfo("psychrimetric", "出力フォルダを選択してください。")
    out_dir = filedialog.askdirectory(title="Select output directory")
    if not out_dir:
        raise SystemExit("Cancelled: output directory not selected.")

    # モード選択（簡易）
    mode = tk.StringVar(value="Both")

    win = tk.Toplevel()
    win.title("Select mode")
    win.geometry("350x350")

    tk.Label(win, text="実行モードを選択してください").pack(pady=10)
    for v in ["Monthly", "Seasonal",  "Yearly", "All"]:
        tk.Radiobutton(win, text=v, variable=mode, value=v).pack(anchor="w", padx=30)

    seasons_path: list[Optional[str]] = [None]

    def choose_seasons_json():
        path = filedialog.askopenfilename(
            title="Select seasons JSON (optional)",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if path:
            seasons_path[0] = path

    tk.Button(win, text="特別な区切りを選択（JSONファイル）", command=choose_seasons_json).pack(pady=8)

    example_text = (
        "JSONフォーマット例:\n"
        "{\n"
        '  "Summer": [6, 7, 8],\n'
        '  "Winter": [12, 1, 2]\n'
        "}"
    )
    tk.Label(win, text=example_text, justify="left", fg="gray", font=("Consolas", 9)).pack(pady=0)

    def on_ok():
        win.destroy()

    tk.Button(win, text="OK", command=on_ok).pack(pady=8)

    win.grab_set()
    root.wait_window(win)

    m = mode.get()
    run_monthly = (m in ["Monthly", "All"])
    run_seasonal = (m in ["Seasonal", "All"])
    run_yearly = (m in ["Yearly", "All"])

    root.destroy()

    return GUISelection(
        epw_path=Path(epw),
        out_dir=Path(out_dir),
        run_monthly=run_monthly,
        run_seasonal=run_seasonal,
        run_yearly=run_yearly,
        seasons_config=Path(seasons_path[0]) if seasons_path[0] else None,
    )

""""
# ゾーン部分の追加
from psychrimetric.zone_registry import load_zones_config

selected_zones: list[str] = []
zones_cfg_path: list[str | None] = [None]
zone_entries = {}

def choose_zones_json():
    path = filedialog.askopenfilename(title="Select zones JSON (optional)", filetypes=[("JSON", "*.json")])
    if path:
        zones_cfg_path[0] = path
        nonlocal zone_entries
        zone_entries = load_zones_config(path)  # {name: ZoneEntry}

def open_zone_checkbox_dialog():
    if not zone_entries:
        messagebox.showinfo("zones", "zones config is not loaded.")
        return

    dlg = tk.Toplevel()
    dlg.title("Select zones")
    vars_map = {}

    for name in zone_entries.keys():
        v = tk.BooleanVar(value=False)
        vars_map[name] = v
        tk.Checkbutton(dlg, text=name, variable=v).pack(anchor="w")

    def ok():
        selected_zones.clear()
        for name, v in vars_map.items():
            if v.get():
                selected_zones.append(name)
        dlg.destroy()

    tk.Button(dlg, text="OK", command=ok).pack(pady=8)
    dlg.grab_set()
    root.wait_window(dlg)
"""