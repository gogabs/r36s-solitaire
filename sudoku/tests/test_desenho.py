"""A tela do Sudoku, com gráficos de mentira: a grade cabe, cada casa usa o
algarismo e o fundo certos, e a tela nunca derruba o jogo."""
import os
import tempfile
import unittest

from fakegfx import RecordingGfx
from helpers import PUZZLE

from sudoku import desenho as D
from sudoku.grade import Grid
from sudoku.run import Run

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


class UI:
    def __init__(self):
        self.said = []

    def say(self, text, queue=False):
        self.said.append(text)

    def play(self, *a, **kw):
        pass


class Menu:
    def __init__(self, title, items, index=0):
        self.title, self.items, self.index = title, items, index


def new_run():
    return Run(UI(), grid=Grid(PUZZLE))


def frame(run=None, menu=None, caption=""):
    gfx = RecordingGfx(ROOT)
    D.draw_frame(gfx, gfx.image(D.SHEET), D.Fonts(gfx), run, menu, caption)
    return gfx


def drawn(gfx):
    """{(linha, coluna): (estilo, algarismo)}, lido do que foi desenhado."""
    out = {}
    for _, path, x, y, src in gfx.draws():
        out[((y - D.Y0) // D.CELL, (x - D.X0) // D.CELL)] = (src[1] // D.CELL, src[0] // D.CELL + 1)
    return out


def fills(gfx):
    """{(linha, coluna): cor de fundo}."""
    out = {}
    for call in gfx.calls:
        if call[0] == "rect" and call[3] == call[4] == D.CELL:
            # a primeira é o fundo; depois vem a moldura do cursor
            out.setdefault(((call[2] - D.Y0) // D.CELL, (call[1] - D.X0) // D.CELL), call[5])
    return out


class DrawTest(unittest.TestCase):
    def test_grid_fits(self):
        self.assertGreaterEqual(D.X0, 5)
        self.assertLessEqual(D.X0 + 9 * D.CELL, D.W - 5)
        self.assertGreaterEqual(D.Y0, D.TOP_BAR + 5)
        self.assertLessEqual(D.Y0 + 9 * D.CELL, D.CAPTION_Y - 5)

    def test_digits_follow_the_grid(self):
        run = new_run()
        run.r, run.c = 0, 2
        run.step(1)
        run.step(1)          # 2, sem repetir
        run.r, run.c = 0, 3
        for _ in range(5):
            run.step(1)      # 5, repete na linha
        seen = drawn(frame(run))
        g = run.grid
        self.assertEqual(len(seen), 81 - g.empty_count())
        for (r, c), (style, d) in seen.items():
            self.assertEqual(d, g.get(r, c))
            if g.fixed(r, c):
                self.assertEqual(style, D.S_GIVEN)
        self.assertEqual(seen[(0, 2)], (D.S_PLAYER, 2))
        self.assertEqual(seen[(0, 3)], (D.S_CONFLICT, 5))
        backs = fills(frame(run))
        self.assertEqual(backs[(0, 3)], D.CONFLICT_BG)
        self.assertEqual(backs[(0, 0)], D.CONFLICT_BG)   # o 5 da dica que ele repete
        self.assertEqual(backs[(1, 5)], D.CONFLICT_BG)   # e o do bloco
        self.assertEqual(backs[(7, 8)], D.SAME)          # outro 5, sem repetir
        self.assertEqual(backs[(8, 8)], D.GIVEN_BG)      # dica longe do cursor
        self.assertEqual(backs[(8, 6)], D.OPEN)
        self.assertEqual(backs[(5, 3)], D.PEER)          # mesma coluna do cursor

    def test_top_bar(self):
        run = new_run()
        run.elapsed = 83
        run.r, run.c = 2, 4
        texts = frame(run).texts()
        self.assertIn("Fácil  ·  linha 3, coluna 5", texts)
        self.assertIn("faltam 51  ·  1:23", texts)

    def test_menus(self):
        texts = frame(menu=Menu("Nível", ["Fácil", "Médio", "Difícil", "Voltar"], 2)).texts()
        self.assertIn("Difícil", texts)
        texts = frame(new_run(), Menu("Pausa", ["Continuar", "Sair sem salvar"])).texts()
        self.assertIn("Pausa", texts)


class FakeGame:
    def __init__(self):
        self.dir = ROOT
        self._focus = []
        self.said = []
        self.updates, self.quits = [], []

    def on_update(self, fn):
        self.updates.append(fn)

    def on_quit(self, fn):
        self.quits.append(fn)

    def say(self, text, queue=False, on_done=None):
        self.said.append(text)


class TestRenderer(D.Renderer):
    def open(self):
        self.gfx = RecordingGfx(ROOT)
        self.gfx.fail = getattr(self, "broken", False)
        self.sheet = self.gfx.image(D.SHEET)
        self.fonts = D.Fonts(self.gfx)
        return True


class RendererTest(unittest.TestCase):
    def setUp(self):
        self.saved_env = dict(os.environ)
        fd, self.conf = tempfile.mkstemp()
        os.close(fd)
        os.environ["A11Y_SISTEMA_CONF"] = self.conf
        os.environ.pop("A11Y_GRAPHICS", None)
        with open(self.conf, "w") as f:
            f.write("SCREEN=1\n")

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.saved_env)
        os.remove(self.conf)

    def test_draws_with_caption_and_survives_failure(self):
        game = FakeGame()
        state = {"run": new_run()}
        r = TestRenderer(game, lambda: state["run"])
        game.say("Vazia, coluna 5.")
        r.update(1.0)
        self.assertEqual(r.gfx.frames, 1)
        self.assertIn("Vazia, coluna 5.", r.gfx.texts())
        r.close()
        r.broken = True
        r.update(1.0)
        self.assertTrue(r.failed)
        game.say("O jogo segue.")
        self.assertEqual(game.said[-1], "O jogo segue.")

    def test_screen_off(self):
        os.environ["A11Y_GRAPHICS"] = "0"
        game = FakeGame()
        r = TestRenderer(game, lambda: None)
        r.update(1.0)
        self.assertIsNone(r.gfx)


if __name__ == "__main__":
    unittest.main()
