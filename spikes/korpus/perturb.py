"""Stoerungen echter Gutachten: dieselbe Wahrheit, anderes PDF.

    python perturb.py <pdf_ordner> <ausgabeordner> [rot90 scale70 raster150]

  rot90     Inhalt um 90 Grad gedreht gespeichert, /Rotate 90 stellt ihn aufrecht (L2)
  scale70   jede Seite auf 70 % verkleinert (A3 als A4 gedruckt): alle pt-Schwellen unter Druck
  raster150 jede Seite als Bild mit 150 dpi, ohne Textlage (Scan ohne OCR, L18)

Danach: regression.py --real <ausgabeordner>/<variante> (gleiche groundtruth/*.json).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pymupdf


def rot90(src: pymupdf.Document) -> pymupdf.Document:
    out = pymupdf.open()
    for p in src:
        r = p.rect
        q = out.new_page(width=r.height, height=r.width)
        # show_pdf_page ignoriert /Rotate der Quelle: deren Drehung hier mit ausgleichen
        q.show_pdf_page(q.rect, src, p.number, rotate=(90 - p.rotation) % 360)
        q.set_rotation(90)
    return out


def scale70(src: pymupdf.Document) -> pymupdf.Document:
    out = pymupdf.open()
    for p in src:
        q = out.new_page(width=p.rect.width * 0.7, height=p.rect.height * 0.7)
        q.show_pdf_page(q.rect, src, p.number, rotate=(-p.rotation) % 360)
    return out


def raster150(src: pymupdf.Document) -> pymupdf.Document:
    out = pymupdf.open()
    for p in src:
        q = out.new_page(width=p.rect.width, height=p.rect.height)
        q.insert_image(q.rect, pixmap=p.get_pixmap(dpi=150))
    return out


VARIANTS = {"rot90": rot90, "scale70": scale70, "raster150": raster150}


def main() -> None:
    src_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    names = sys.argv[3:] or list(VARIANTS)
    for v in names:
        (out_dir / v).mkdir(parents=True, exist_ok=True)
        for pdf in sorted(src_dir.glob("*.pdf")):
            doc = VARIANTS[v](pymupdf.open(pdf))
            doc.save(out_dir / v / pdf.name, garbage=3, deflate=True)
            print(v, pdf.name, doc.page_count)


if __name__ == "__main__":
    main()
