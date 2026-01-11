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
except Exception:
    # when run as a script: python src/psychrometric/app.py
    try:
        from psychrometric.epw_io import load_epw
        from psychrometric.render import render_density_svg
    except Exception:
        raise


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

            # Ask user where to save the generated SVG (native dialog)
            save_path = None
            if _filedialog is not None:
                try:
                    root2 = _tk.Tk()
                    root2.withdraw()
                    suggested = Path(epw_path).stem + ".svg"
                    save_path = _filedialog.asksaveasfilename(
                        title="Save SVG as",
                        defaultextension=".svg",
                        initialfile=suggested,
                        filetypes=[("SVG files", "*.svg"), ("All files", "*.*")],
                    )
                    root2.destroy()
                except Exception:
                    save_path = None

            ts = int(time.time())
            if save_path:
                out_svg = Path(save_path)
                out_svg.parent.mkdir(parents=True, exist_ok=True)
            else:
                out_svg = Path(tempfile.gettempdir()) / f"psych_{ts}.svg"

            render_density_svg(df, out_svg, title=meta.location or "EPW chart")
            status.value = f"Rendered: {out_svg} (opening)"
            page.update()
            try:
                os.startfile(out_svg)
            except Exception:
                status.value = f"Rendered: {out_svg} (open manually)"
                page.update()
        except Exception as ex:
            status.value = f"Error: {ex}"
            page.update()

    btn = ft.Button("Make_graph!", on_click=_on_click)
    page.add(btn)
    page.add(status)


if __name__ == "__main__":
    ft.run(main)
