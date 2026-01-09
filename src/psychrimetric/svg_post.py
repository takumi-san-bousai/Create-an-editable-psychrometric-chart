# src/psychrimetric/svg_post.py
from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

def _q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"

def _find_trace_name(g_trace: ET.Element) -> str | None:
    """
    Plotly SVGでは trace group 内に <title> が入り、そこに trace名が含まれることが多い。
    それ以外に aria-label / data-name 等が付く場合もあるので拾えるだけ拾う。
    """
    # 1) <title> text
    for t in g_trace.findall(".//" + _q("title")):
        if t.text:
            txt = t.text.strip()
            # titleの中に name がそのまま入る/含まれることが多い
            # 例: "density", "points" を含むかチェック
            for key in ("density", "points", "zone"):
                if key in txt:
                    return key

    # 2) attributes (まれ)
    for attr in ("data-name", "aria-label", "id"):
        v = g_trace.attrib.get(attr)
        if v:
            v2 = v.lower()
            for key in ("density", "points", "zone"):
                if key in v2:
                    return key

    return None


def postprocess_svg(svg_path: str | Path) -> Path:
    """
    Plotly出力SVGを読み、トップレベルに以下の順でグループを作って要素を移動する。
      - chartborder
      - zone
      - density
      - points
      - text
    """
    svg_path = Path(svg_path)

    tree = ET.parse(svg_path)
    root = tree.getroot()

    # ルート直下の子を整理（後で順序を作り直す）
    children = list(root)

    # 新しいレイヤーを作成
    layers = {
        "chartborder": ET.Element(_q("g"), {"id": "chartborder"}),
        "zone":        ET.Element(_q("g"), {"id": "zone"}),
        "density":     ET.Element(_q("g"), {"id": "density"}),
        "points":      ET.Element(_q("g"), {"id": "points"}),
        "text":        ET.Element(_q("g"), {"id": "text"}),
    }

    # 既存の子を一旦全部rootから外す（順序再構築のため）
    for c in children:
        root.remove(c)

    def is_text_layer(elem: ET.Element) -> bool:
        cls = elem.attrib.get("class", "").lower()
        _id = elem.attrib.get("id", "").lower()
        # Plotlyでよくあるテキスト層
        if "gtitle" in cls or "annotation" in cls:
            return True
        if "title" in _id or "annotation" in _id:
            return True
        # 文字要素を含むなら text 扱い（乱暴だがプレボ向け）
        return elem.find(".//" + _q("text")) is not None

    def is_border_like(elem: ET.Element) -> bool:
        cls = elem.attrib.get("class", "").lower()
        _id = elem.attrib.get("id", "").lower()
        # 軸・枠・クリップ系
        keys = ("xaxislayer", "yaxislayer", "zerolinelayer", "gridlayer", "layer-above", "clips")
        if any(k in cls for k in keys):
            return True
        if any(k in _id for k in keys):
            return True
        # 背景 rect を含む場合も border側へ
        return elem.find(".//" + _q("rect")) is not None and "trace" not in cls

    # 子要素を分類して追加
    for elem in children:
        cls = elem.attrib.get("class", "").lower()

        # trace（プロットデータ）
        if "trace" in cls:
            name = _find_trace_name(elem)
            if name == "density":
                layers["density"].append(elem)
            elif name == "points":
                layers["points"].append(elem)
            elif name == "zone":
                layers["zone"].append(elem)
            else:
                # trace名が拾えない場合は zone に寄せる（安全）
                layers["zone"].append(elem)
            continue

        # テキスト
        if is_text_layer(elem):
            layers["text"].append(elem)
            continue

        # 枠・軸・背景
        if is_border_like(elem):
            layers["chartborder"].append(elem)
            continue

        # それ以外（不明）は chartborder に入れて見落としを防ぐ
        layers["chartborder"].append(elem)

    # ルートへ追加（順序：下→上）
    root.append(layers["chartborder"])
    root.append(layers["zone"])
    root.append(layers["density"])
    root.append(layers["points"])
    root.append(layers["text"])

    # 保存（上書き）
    tree.write(svg_path, encoding="utf-8", xml_declaration=True)
    return svg_path
