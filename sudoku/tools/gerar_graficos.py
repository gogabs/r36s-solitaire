#!/usr/bin/env python3
"""Gera a folha de algarismos do Sudoku (graficos/numeros-42.png). Precisa do
Pillow, mas só aqui, no PC: o console só carrega o PNG pronto.

    python3 tools/gerar_graficos.py

Três fileiras de 1 a 9, com fundo transparente (a cor da casa é desenhada por
baixo, no jogo): dica, em branco e negrito; número do jogador, em azul claro e
traço normal; e número repetido, em rosa, também em traço normal. Desenhados
em 4x e reduzidos, para bordas suaves.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from sudoku import desenho as D  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", D.SHEET)
SS = 4
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
STYLES = {D.S_GIVEN: (FONT_BOLD, D.GIVEN), D.S_PLAYER: (FONT, D.PLAYER),
          D.S_CONFLICT: (FONT, D.CONFLICT)}


def rgb(hexcolor, alpha=255):
    h = hexcolor.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def glyph(s, d, font_path, color):
    big = Image.new("RGBA", (s * SS, s * SS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(big)
    font = ImageFont.truetype(font_path, int(s * SS * 0.7))
    draw.text((s * SS / 2, s * SS / 2 + SS), str(d), font=font, fill=rgb(color), anchor="mm")
    return big.resize((s, s), Image.LANCZOS)


def sheet(s):
    img = Image.new("RGBA", (9 * s, len(STYLES) * s), (0, 0, 0, 0))
    for style, (font, color) in STYLES.items():
        for d in range(1, 10):
            img.paste(glyph(s, d, font, color), ((d - 1) * s, style * s))
    return img


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sheet(D.CELL).save(OUT, optimize=True)
    print("folha gerada em %s" % os.path.normpath(OUT))


if __name__ == "__main__":
    main()
