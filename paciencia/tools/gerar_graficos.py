#!/usr/bin/env python3
"""Gera as folhas de cartas da Paciência (graficos/*.png). Precisa do Pillow,
mas só aqui, no PC: o console só carrega os PNG prontos.

    python3 tools/gerar_graficos.py

Arte vetorial chapada, desenhada em 4x e reduzida (bordas suaves). Cada folha
tem 13 colunas (ás a rei) e 5 linhas: copas, ouros, paus, espadas, e uma linha
de extras: verso, lugar vazio, e o lugar vazio de cada fundação com o naipe
em marca d'água. A ordem é a mesma de paciencia/desenho.py.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from paciencia import desenho as D  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graficos")
SS = 4   # superamostragem
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def rgb(hexcolor, alpha=255):
    h = hexcolor.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def suit_shape(draw, suit, cx, cy, size, fill):
    """Naipe centrado em (cx, cy), cabendo num quadrado de lado `size`."""
    s = size / 2.0
    if suit == 1:      # ouros: losango
        draw.polygon([(cx, cy - s), (cx + s * 0.75, cy), (cx, cy + s), (cx - s * 0.75, cy)], fill=fill)
        return
    if suit in (0, 3):  # copas e espadas: dois círculos e um triângulo
        r = s * 0.52
        flip = -1 if suit == 3 else 1
        top = cy - s * 0.42 * flip
        for dx in (-r * 0.95, r * 0.95):
            draw.ellipse([cx + dx - r, top - r, cx + dx + r, top + r], fill=fill)
        tip = cy + s * 0.98 * flip
        base = top + r * 0.35 * flip
        draw.polygon([(cx - r * 1.95, base), (cx + r * 1.95, base), (cx, tip)], fill=fill)
        if suit == 3:   # cabo da espada
            draw.polygon([(cx, cy + s * 0.25), (cx - s * 0.35, cy + s), (cx + s * 0.35, cy + s)], fill=fill)
        return
    # paus: três círculos e cabo
    r = s * 0.40
    for dx, dy in ((0, -s * 0.48), (-s * 0.50, s * 0.10), (s * 0.50, s * 0.10)):
        draw.ellipse([cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r], fill=fill)
    draw.rectangle([cx - r * 0.45, cy - s * 0.2, cx + r * 0.45, cy + s * 0.3], fill=fill)
    draw.polygon([(cx, cy + s * 0.05), (cx - s * 0.38, cy + s), (cx + s * 0.38, cy + s)], fill=fill)


def rounded(draw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def card_face(w, h, rank, suit):
    W, H = w * SS, h * SS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ink = rgb(D.RED if suit in (0, 1) else D.BLACK)
    rounded(d, [0, 0, W - 1, H - 1], 6 * SS, fill=rgb(D.FACE), outline=rgb(D.EDGE), width=2 * SS)
    # faixa de cima, a que aparece com as cartas sobrepostas: valor grande e naipe
    label = D.RANK_LABELS[rank]
    size = int(h * 0.25) * SS
    font = ImageFont.truetype(FONT_BOLD, size)
    d.text((4 * SS, 1 * SS), label, font=font, fill=ink)
    strip = int(h * 0.24)
    suit_shape(d, suit, W - strip * 0.55 * SS, strip * 0.52 * SS, strip * 0.72 * SS, ink)
    # meio: naipe grande; nas figuras, a letra grande sobre o naipe claro
    cy = H * 0.62
    big = min(W, H) * 0.55
    if rank > 10:
        pale = rgb(D.RED_PALE if suit in (0, 1) else D.BLACK_PALE)
        suit_shape(d, suit, W / 2, cy, big, pale)
        f2 = ImageFont.truetype(FONT_BOLD, int(big * 0.8))
        d.text((W / 2, cy), label, font=f2, fill=ink, anchor="mm")
    else:
        suit_shape(d, suit, W / 2, cy, big, ink)
    return img.resize((w, h), Image.LANCZOS)


def card_back(w, h):
    W, H = w * SS, h * SS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rounded(d, [0, 0, W - 1, H - 1], 6 * SS, fill=rgb(D.BACK), outline=rgb(D.EDGE), width=2 * SS)
    m = 5 * SS
    inner = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    di = ImageDraw.Draw(inner)
    step = 10 * SS
    for k in range(-H, W + H, step):   # treliça diagonal
        di.line([(k, 0), (k + H, H)], fill=rgb(D.BACK_LINE), width=2 * SS)
        di.line([(k + H, 0), (k, H)], fill=rgb(D.BACK_LINE), width=2 * SS)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([m, m, W - m, H - m], radius=3 * SS, fill=255)
    img.paste(inner, (0, 0), Image.composite(inner, Image.new("RGBA", (W, H)), mask).split()[3])
    rounded(d, [m, m, W - m, H - m], 3 * SS, outline=rgb(D.BACK_EDGE), width=2 * SS)
    return img.resize((w, h), Image.LANCZOS)


def empty_slot(w, h, suit=None):
    W, H = w * SS, h * SS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rounded(d, [SS, SS, W - SS - 1, H - SS - 1], 6 * SS, fill=rgb(D.SLOT_FILL), outline=rgb(D.SLOT), width=2 * SS)
    if suit is not None:
        suit_shape(d, suit, W / 2, H / 2, min(W, H) * 0.5, rgb(D.SLOT))
    return img.resize((w, h), Image.LANCZOS)


def sheet(w, h):
    img = Image.new("RGBA", (w * 13, h * 5), (0, 0, 0, 0))
    for suit in range(4):
        for rank in range(1, 14):
            img.paste(card_face(w, h, rank, suit), ((rank - 1) * w, suit * h))
    extras = [card_back(w, h), empty_slot(w, h)] + [empty_slot(w, h, s) for s in range(4)]
    for k, part in enumerate(extras):
        img.paste(part, (k * w, 4 * h))
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, (w, h) in D.SIZES.items():
        sheet(w, h).save(os.path.join(OUT, "cartas-%s.png" % name), optimize=True)
    print("folhas geradas em %s" % os.path.normpath(OUT))


if __name__ == "__main__":
    main()
