# src/psychrimetric/gui2.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import filedialog, messagebox

from .zone_registry import load_zones_config
from .app import AppState


@dataclass(frozen=True)
class GUISelection2:
    epw_path: Path
    out_dir: Path
    mode: str                 # "Monthly"|"Seasonal"|"Both"
    zones_config: Optional[Path]
    selected_zones: list[str]
    add_points: bool


def popup_select2(state: AppState) -> GUISelection2:
    root = tk.Tk()
    root.withdraw()

    # EPW
    messagebox.showinfo("psychrimetric", "EPWファイルを選択してください。")
    epw = filedialog.askopenfilename(
        title="Select EPW file",
        filetypes=[("EnergyPlus Weather", "*.epw"), ("All files", "*.*")],
    )
    if not epw:
        raise SystemExit("Cancelled: EPW not selected.")

    # out dir（前回値があれば初期案内）
    messagebox.showinfo("psychrimetric", "出力フォルダを選択してください。")
    out_dir = filedialog.askdirectory(title="Select output directory")
    if not out_dir:
        # 前回値がある場合はそれを採用する選択肢もあるが、ここではキャンセル扱い
        raise SystemExit("Cancelled: output directory not selected.")

    # 設定ウィンドウ
    win = tk.Toplevel()
    win.title("psychrimetric settings")
    win.geometry("420x520")

    mode_var = tk.StringVar(value=state.last_mode or "Both")
    tk.Label(win, text="実行モード").pack(pady=8)
    for v in ["Monthly", "Seasonal", "Both"]:
        tk.Radiobutton(win, text=v, variable=mode_var, value=v).pack(anchor="w", padx=30)

    add_points_var = tk.BooleanVar(value=False)
    tk.Checkbutton(win, text="点群(points)も重ねる", variable=add_points_var).pack(anchor="w", padx=30, pady=6)

    zones_path_var = tk.StringVar(value=state.last_zones_config or "")
    zones_loaded = {"zones": None}  # {name: ZoneEntry} or None
    selected_vars: dict[str, tk.BooleanVar] = {}

    tk.Label(win, text="zones.json（任意）").pack(pady=8)
    path_entry = tk.Entry(win, textvariable=zones_path_var, width=52)
    path_entry.pack(padx=10)

    frame = tk.Frame(win)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    canvas = tk.Canvas(frame)
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable = tk.Frame(canvas)

    scrollable.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.create_window((0, 0), window=scrollable, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def refresh_zone_checkboxes():
        # 既存ウィジェット削除
        for w in scrollable.winfo_children():
            w.destroy()
        selected_vars.clear()

        z = zones_loaded["zones"]
        if not z:
            tk.Label(scrollable, text="(zones.json未読み込み)").pack(anchor="w")
            return

        prev = set(state.last_selected_zones or [])
        for name in z.keys():
            v = tk.BooleanVar(value=(name in prev))
            selected_vars[name] = v
            tk.Checkbutton(scrollable, text=name, variable=v).pack(anchor="w")

    def choose_zones():
        path = filedialog.askopenfilename(title="Select zones JSON", filetypes=[("JSON", "*.json")])
        if not path:
            return
        zones_path_var.set(path)
        try:
            zones_loaded["zones"] = load_zones_config(path)
        except Exception as e:
            zones_loaded["zones"] = None
            messagebox.showerror("zones.json error", str(e))
        refresh_zone_checkboxes()

    tk.Button(win, text="zones.jsonを選択", command=choose_zones).pack(pady=6)

    # 前回のzonesがあればロード試行
    if state.last_zones_config:
        try:
            zones_loaded["zones"] = load_zones_config(state.last_zones_config)
        except Exception:
            zones_loaded["zones"] = None
    refresh_zone_checkboxes()

    result = {"ok": False}

    def on_ok():
        result["ok"] = True
        win.destroy()

    tk.Button(win, text="OK", command=on_ok).pack(pady=10)

    win.grab_set()
    root.wait_window(win)
    root.destroy()

    if not result["ok"]:
        raise SystemExit("Cancelled.")

    zones_cfg = zones_path_var.get().strip() or None
    selected = [n for n, v in selected_vars.items() if v.get()] if zones_loaded["zones"] else []

    return GUISelection2(
        epw_path=Path(epw),
        out_dir=Path(out_dir),
        mode=mode_var.get(),
        zones_config=Path(zones_cfg) if zones_cfg else None,
        selected_zones=selected,
        add_points=bool(add_points_var.get()),
    )
