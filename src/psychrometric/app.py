try:
    import flet as ft
except Exception:
    print("[ERROR] 'flet' is not installed. Install with: pip install flet")
    raise SystemExit(1)

import os
import time
import tempfile
from pathlib import Path

try:
    # when run as a package: python -m psychrometric.app
    from .epw_io import load_epw
    from .render import render_density_svg
    from .period_filter import split_by_month, split_by_seasons
except Exception:
    # when run as a script: python src/psychrometric/app.py
    try:
        from psychrometric.epw_io import load_epw
        from psychrometric.render import render_density_svg
        from psychrometric.period_filter import split_by_month, split_by_seasons
    except Exception:
        raise

DEFAULT_SEASONS = {
    "Winter": [12, 1, 2],
    "Spring": [3, 4, 5],
    "Summer": [6, 7, 8],
    "Autumn": [9, 10, 11],
}


def main(page: ft.Page):
    page.title = "Psychrometric (Flet)"

    status = ft.Text("Ready")
    page.add(ft.Text("Hello — psychrometric Flet app."))

    # Use native tkinter file dialog for desktop builds (FilePicker may be unsupported)
    try:
        import tkinter as _tk
        from tkinter import filedialog as _filedialog
    except Exception:
        _tk = None
        _filedialog = None

    def _on_click(e: ft.Event):
        status.value = "Opening file picker..."
        page.update()

        if _filedialog is None:
            status.value = "tkinter not available: cannot open file dialog."
            page.update()
            return

        try:
            root = _tk.Tk()
            root.withdraw()
            epw_path = _filedialog.askopenfilename(
                title="Select EPW file",
                filetypes=[("EPW files", "*.epw"), ("All files", "*.*")],
            )
            root.destroy()
        except Exception as ex:
            status.value = f"File dialog error: {ex}"
            page.update()
            return

        if not epw_path:
            status.value = "No file selected."
            page.update()
            return

        status.value = f"Loading {Path(epw_path).name}..."
        page.update()

        try:
            df, meta = load_epw(epw_path)

            # Ask user where to save the generated SVGs (native dialog)
            out_dir = None
            if _filedialog is not None:
                try:
                    root2 = _tk.Tk()
                    root2.withdraw()
                    out_dir = _filedialog.askdirectory(title="Select Output Directory")
                    root2.destroy()
                except Exception:
                    out_dir = None

            if not out_dir:
                out_dir = tempfile.gettempdir()

            out_path = Path(out_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            loc_name = meta.location or "EPW"

            # 1. Yearly
            render_density_svg(df, out_path / f"{loc_name}_Yearly.svg", title=f"{loc_name} / Yearly")

            # 2. Seasonal
            for name, d in split_by_seasons(df, DEFAULT_SEASONS).items():
                if not d.empty:
                    render_density_svg(d, out_path / f"{loc_name}_{name}.svg", title=f"{loc_name} / {name}")

            # 3. Monthly
            for m, d in split_by_month(df).items():
                if not d.empty:
                    render_density_svg(d, out_path / f"{loc_name}_M{m:02d}.svg", title=f"{loc_name} / Month {m:02d}")

            status.value = f"Rendered all charts in: {out_path}"
            page.update()
            try:
                os.startfile(out_path)
            except Exception:
                status.value = f"Rendered in {out_path} (open manually)"
                page.update()
        except Exception as ex:
            status.value = f"Error: {ex}"
            page.update()

    btn = ft.Button("Make_graph!", on_click=_on_click)
    page.add(btn)
    page.add(status)


if __name__ == "__main__":
    ft.run(main)