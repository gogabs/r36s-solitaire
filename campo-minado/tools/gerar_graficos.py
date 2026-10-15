#!/usr/bin/env python3
"""Gera as folhas de casas do Campo Minado (graficos/casas-<lado>.png). Precisa
do Pillow, mas só aqui, no PC: o console só carrega os PNG prontos.

    python3 tools/gerar_graficos.py

Uma folha por tamanho de casa (um por nível), numa fileira só: fechada,
marcada, aberta de 0 a 8 e a mina que explodiu, na ordem de minado/desenho.py.
Bandeira e mina são desenhadas em 4x e reduzidas (bordas suaves); o relevo das
casas fechadas fica em pixels inteiros, nítido.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from minado import desenho as D  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graficos")
SS = 4
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def rgb(hexcolor, alpha=255):
    h = hexcolor.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def closed(s):
    img = Image.new("RGBA", (s, s), rgb(D.CLOSED))
    d = ImageDraw.Draw(img)
    e = max(2, s // 10)    # largura do relevo
    for k in range(e):
        d.line([(k, k), (s - 1 - k, k)], fill=rgb(D.CLOSED_LIGHT))       # cima
        d.line([(k, k), (k, s - 1 - k)], fill=rgb(D.CLOSED_LIGHT))       # esquerda
        d.line([(k, s - 1 - k), (s - 1 - k, s - 1 - k)], fill=rgb(D.CLOSED_DARK))
        d.line([(s - 1 - k, k), (s - 1 - k, s - 1 - k)], fill=rgb(D.CLOSED_DARK))
    return img


def opened(s, fill=D.OPEN):
    img = Image.new("RGBA", (s, s), rgb(fill))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, s - 1, s - 1], outline=rgb(D.OPEN_LINE))
    return img


def overlay(base, painter):
    """Desenha em 4x por cima da casa e reduz."""
    s = base.size[0]
    big = Image.new("RGBA", (s * SS, s * SS), (0, 0, 0, 0))
    painter(ImageDraw.Draw(big), s * SS)
    base.alpha_composite(big.resize((s, s), Image.LANCZOS))
    return base


def flag(d, S):
    pole_x = S * 0.42
    # base e mastro
    d.rectangle([S * 0.24, S * 0.74, S * 0.70, S * 0.82], fill=rgb(D.MINE))
    d.rectangle([pole_x - S * 0.035, S * 0.18, pole_x + S * 0.035, S * 0.78], fill=rgb(D.MINE))
    # bandeira: triângulo vermelho com contorno preto
    tri = [(pole_x + S * 0.03, S * 0.16), (S * 0.80, S * 0.33), (pole_x + S * 0.03, S * 0.52)]
    d.polygon(tri, fill=rgb(D.MINE))
    cx = sum(p[0] for p in tri) / 3
    cy = sum(p[1] for p in tri) / 3
    inner = [(cx + (x - cx) * 0.72, cy + (y - cy) * 0.72) for x, y in tri]
    d.polygon(inner, fill=rgb(D.FLAG))


def mine(d, S):
    c = S / 2.0
    r = S * 0.24
    w = S * 0.06
    for a, b in (((c, c - r * 1.55), (c, c + r * 1.55)), ((c - r * 1.55, c), (c + r * 1.55, c)),
                 ((c - r * 1.1, c - r * 1.1), (c + r * 1.1, c + r * 1.1)),
                 ((c - r * 1.1, c + r * 1.1), (c + r * 1.1, c - r * 1.1))):
        d.line([a, b], fill=rgb(D.MINE), width=int(w))
    d.ellipse([c - r, c - r, c + r, c + r], fill=rgb(D.MINE))
    g = r * 0.32
    d.ellipse([c - r * 0.45 - g, c - r * 0.45 - g, c - r * 0.45 + g, c - r * 0.45 + g],
              fill=(255, 255, 255, 255))


def number(s, n):
    img = opened(s)
    if n == 0:
        return img
    big = Image.new("RGBA", (s * SS, s * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    font = ImageFont.truetype(FONT_BOLD, int(s * SS * 0.72))
    d.text((s * SS / 2, s * SS / 2 + SS), str(n), font=font, fill=rgb(D.NUMBERS[n]), anchor="mm")
    img.alpha_composite(big.resize((s, s), Image.LANCZOS))
    return img


def sheet(s):
    tiles = [closed(s), overlay(closed(s), flag)]
    tiles += [number(s, n) for n in range(9)]
    tiles.append(overlay(opened(s, D.EXPLODED), mine))
    assert len(tiles) == D.TILES
    img = Image.new("RGBA", (s * len(tiles), s), (0, 0, 0, 0))
    for k, t in enumerate(tiles):
        img.paste(t, (k * s, 0))
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    for s in sorted(set(D.CELL.values())):
        sheet(s).save(os.path.join(OUT, "casas-%d.png" % s), optimize=True)
    print("folhas geradas em %s" % os.path.normpath(OUT))


if __name__ == "__main__":
    main()
