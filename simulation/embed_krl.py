#!/usr/bin/env python3
"""Bettet KRL/Palettierung.src und KRL/Palettierung.dat in simulation/index.html ein.

Nach jeder Aenderung am KRL-Programm ausfuehren:
    python3 simulation/embed_krl.py

Die Simulation zeigt dann den aktuellen Programmtext mit Satzzeiger und
liest die Parameter aus der aktuellen Datenliste.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
HTML = ROOT / "simulation" / "index.html"
BLOCKS = {
    "krl-src": ROOT / "KRL" / "Palettierung.src",
    "krl-dat": ROOT / "KRL" / "Palettierung.dat",
}


def main() -> None:
    html = HTML.read_text(encoding="utf-8")
    for block_id, path in BLOCKS.items():
        text = path.read_text(encoding="ascii").replace("\r\n", "\n").strip("\n")
        if "</script" in text.lower():
            raise SystemExit(f"{path.name} enthaelt '</script' und kann nicht eingebettet werden")
        pattern = re.compile(
            r'(<script type="text/plain" id="%s">\n)(.*?)(\n</script>)' % re.escape(block_id),
            re.S,
        )
        html, n = pattern.subn(lambda m: m.group(1) + text + m.group(3), html)
        if n != 1:
            raise SystemExit(f"Block {block_id} nicht gefunden")
    HTML.write_text(html, encoding="utf-8")
    print(f"{HTML.relative_to(ROOT)} aktualisiert")


if __name__ == "__main__":
    main()
