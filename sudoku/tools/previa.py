#!/usr/bin/env python3
"""Gera prévias das telas do Sudoku em PNG, sem console (precisa do Pillow).

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

from sudoku import desenho as D  # noqa: E402
from sudoku.grade import Grid, generate  # noqa: E402
from sudoku.run import Run  # noqa: E402


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
    D.draw_frame(gfx, gfx.image(D.SHEET), D.Fonts(gfx), run, menu, caption)
    path = os.path.join(out, name + ".png")
    gfx.save(path)
    print(path)


def played(level, seed, fill):
    """Uma partida com `fill` casas já preenchidas certas."""
    rng = random.Random(seed)
    givens, solution = generate({"facil": 40, "medio": 32, "dificil": 26}[level], rng)
    ui = UI()
    run = Run(ui, level=level, grid=Grid(givens))
    empty = [i for i in range(81) if not givens[i]]
    for i in rng.sample(empty, fill):
        run.grid.values[i] = solution[i]
    return run, ui, solution


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    shot("1-menu", menu=FakeMenu("Sudoku", ["Continuar partida salva", "Novo jogo",
                                            "Como jogar", "Recordes", "Sair"], 1),
         caption="Sudoku. Novo jogo, 2 de 5.", out=out)
    for n, (level, fill) in enumerate((("facil", 12), ("medio", 20), ("dificil", 8)), 2):
        run, ui, _ = played(level, n, fill)
        run.elapsed = 37 + 80 * n
        run.r, run.c = 3, 4
        run.move(0, 1)
        shot("%d-%s" % (n, level), run=run, caption=ui.last, out=out)
    # um número repetido: a casa e a que ela repete ficam vermelhas
    run, ui, solution = played("facil", 7, 10)
    empty = [i for i in range(81) if not run.grid.values[i]]
    r, c = divmod(empty[len(empty) // 2], 9)
    run.r, run.c = r, c
    wrong = run.grid.get(r, (c + 1) % 9) or run.grid.get((r + 1) % 9, c) or 1
    run.grid.values[r * 9 + c] = wrong - 1   # B sobe para o número repetido
    run.step(1)
    shot("5-repetido", run=run, caption=ui.last, out=out)
    shot("6-pausa", run=run, menu=FakeMenu("Pausa", ["Continuar", "Salvar e sair para o menu",
                                                     "Sair sem salvar"], 0),
         caption="Pausa. Continuar, 1 de 3.", out=out)


if __name__ == "__main__":
    main()
