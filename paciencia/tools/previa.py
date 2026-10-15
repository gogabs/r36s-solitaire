#!/usr/bin/env python3
"""Gera prévias das telas da Paciência em PNG, sem console (precisa do Pillow).

    python3 tools/previa.py [pasta-de-saída]
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "..", "tools"))

from pilgfx import PilGfx  # noqa: E402

from paciencia import desenho as D  # noqa: E402
from paciencia.freecell import FreeCell  # noqa: E402
from paciencia.klondike import Klondike  # noqa: E402
from paciencia.spider import Spider  # noqa: E402


class UI:
    def __init__(self):
        self.last = ""

    def say(self, text, queue=False):
        self.last = text

    def play(self, *a, **kw):
        pass


class FakeMenu:
    def __init__(self, title, items, index=0):
        self.title, self.items, self.index = title, items, index


def shot(name, run=None, menu=None, caption="", out="."):
    gfx = PilGfx(ROOT)
    sheets = {k: gfx.image("graficos/cartas-%s.png" % k) for k in D.SIZES}
    D.draw_frame(gfx, sheets, D.Fonts(gfx), run, menu, caption)
    path = os.path.join(out, name + ".png")
    gfx.save(path)
    print(path)


def play_hints(run, n):
    for _ in range(n):
        m = run.hint()
        if m is None:
            if not run.draw():
                break
            continue
        run.press()
        run.go_to(m[2])
        run.press()


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    shot("1-menu", menu=FakeMenu("Paciência", ["Klondike", "FreeCell, com partida salva", "Spider",
                                               "Como jogar", "Estatísticas", "Sair"], 1),
         caption="Paciência. FreeCell, com partida salva, 2 de 6.", out=out)

    ui = UI()
    k = Klondike(ui, rng=random.Random(4), draw=3)
    k.start()
    play_hints(k, 14)
    k.go_to(k.piles.index(k.kind("coluna")[3]))
    k.depth = k.pile.first_up()
    shot("2-klondike-foco", run=k, caption=ui.last, out=out)
    moves = [m for m in k.legal_moves() if not k.reverses(*m)]
    while not moves and k.draw():   # compra até aparecer uma jogada
        moves = [m for m in k.legal_moves() if not k.reverses(*m)]
    if moves:   # pega a primeira jogada possível e para em cima do destino
        si, ci, ti = moves[0]
        k.go_to(si, ci)
        k.press()
        k.go_to(ti)
        k.announce_pile()
    else:
        print("sem jogada para a prévia 3", file=sys.stderr)
    shot("3-klondike-na-mao", run=k, caption=ui.last, out=out)

    f = FreeCell(ui, number=1941)
    f.start()
    play_hints(f, 10)
    shot("4-freecell", run=f, caption=ui.last, out=out)

    s = Spider(ui, rng=random.Random(2), suits=2)
    s.start()
    play_hints(s, 30)
    s.go_to(4)
    s.depth = s.pile.first_up()
    s.card_step(1)
    shot("5-spider", run=s, caption=ui.last, out=out)
    shot("6-pausa", run=s, menu=FakeMenu("Pausa", ["Continuar", "Salvar e sair para o menu",
                                                   "Sair sem salvar"], 0),
         caption="Pausa. Continuar, 1 de 3.", out=out)


if __name__ == "__main__":
    main()
