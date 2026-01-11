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
    # when run as a package: python -m psychrimetric.app
    from .epw_io import load_epw
    from .render import render_density_svg
except Exception:
    # when run as a script: python src/psychrimetric/app.py
    try:
        from psychrometric.epw_io import load_epw
        from psychrometric.render import render_density_svg
    except Exception:
        raise


def main(page: ft.Page):
    page.title = "Psychrometric (Flet)"

    status = ft.Text("Ready")
    page.add(ft.Text("Hello — psychrometric Flet app."))

    # File picker (append to overlay so it can show dialog)
    def _on_pick(e: ft.FilePickerResultEvent):
        if not e.files:
            status.value = "No file selected."
            page.update()
            return

        epw_path = e.files[0].path
        status.value = f"Loading {Path(epw_path).name}..."
        page.update()

        try:
            df, meta = load_epw(epw_path)
            ts = int(time.time())
            out_svg = Path(tempfile.gettempdir()) / f"psych_{ts}.svg"
            render_density_svg(df, out_svg, title=meta.location or "EPW chart")
            status.value = f"Rendered: {out_svg} (opening)"
            page.update()
            # Open with default system viewer (Windows)
            try:
                os.startfile(out_svg)
            except Exception:
                status.value = f"Rendered: {out_svg} (open manually)"
                page.update()
        except Exception as ex:
            status.value = f"Error: {ex}"
            page.update()

    file_picker = ft.FilePicker(on_result=_on_pick)
    page.overlay.append(file_picker)

    btn = ft.ElevatedButton("Make_graph!", on_click=lambda e: file_picker.pick_files())
    page.add(btn)
    page.add(status)


if __name__ == "__main__":
    ft.app(target=main)
