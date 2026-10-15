#!/usr/bin/env python3
"""Gera prévias das telas do Campo Minado em PNG, sem console (precisa do Pillow).

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

from minado import desenho as D  # noqa: E402
from minado.run import Run  # noqa: E402


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
    sheets = {s: gfx.image("graficos/casas-%d.png" % s) for s in set(D.CELL.values())}
    D.draw_frame(gfx, sheets, D.Fonts(gfx), run, menu, caption)
    path = os.path.join(out, name + ".png")
    gfx.save(path)
    print(path)


def safe_play(run, rng, steps):
    """Cava casas sem mina e marca algumas minas, como alguém jogando bem."""
    b = run.board
    run.dig()
    for _ in range(steps):
        closed = [(r, c) for r in range(b.rows) for c in range(b.cols)
                  if b.state(r, c) == "fechada"]
        safe = [x for x in closed if x not in b.mines]
        if len(safe) <= 3:
            break
        run.r, run.c = rng.choice(safe)
        run.dig()
    for cell in rng.sample(sorted(b.mines), min(len(b.mines), len(b.mines) // 2)):
        run.r, run.c = cell
        run.flag()


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    shot("1-menu", menu=FakeMenu("Campo Minado", ["Continuar partida salva", "Novo jogo",
                                                  "Como jogar", "Recordes", "Sair"], 1),
         caption="Campo Minado. Novo jogo, 2 de 5.", out=out)
    for n, level in enumerate(("facil", "medio", "dificil"), 2):
        ui = UI()
        rng = random.Random(n)
        run = Run(ui, level=level, rng=rng)
        run.start()
        safe_play(run, rng, {"facil": 4, "medio": 10, "dificil": 18}[level])
        run.elapsed = 37 + 50 * n
        b = run.board
        opened = sorted(b.opened)
        run.r, run.c = opened[len(opened) // 2]
        run.move(0, 0)
        shot("%d-%s" % (n, level), run=run, caption=ui.last, out=out)
    # a explosão: a mina que explodiu aparece; as outras, não
    ui = UI()
    run = Run(ui, level="facil", rng=random.Random(9))
    run.start()
    run.dig()
    run.r, run.c = sorted(run.board.mines)[0]
    run.dig()
    shot("5-explosao", run=run, caption=ui.last, out=out)
    shot("6-pausa", run=run, menu=FakeMenu("Pausa", ["Continuar", "Salvar e sair para o menu",
                                                     "Sair sem salvar"], 0),
         caption="Pausa. Continuar, 1 de 3.", out=out)


if __name__ == "__main__":
    main()
