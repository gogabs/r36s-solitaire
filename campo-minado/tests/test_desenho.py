"""A tela do Campo Minado, com gráficos de mentira: a grade cabe, cada casa usa
o desenho certo, as minas só aparecem quando o jogo fala delas, e a tela nunca
derruba o jogo."""
import os
import random
import tempfile
import unittest

from fakegfx import RecordingGfx

from minado import desenho as D
from minado.board import LEVEL_ORDER
from minado.run import Run

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


def frame(run=None, menu=None, caption=""):
    gfx = RecordingGfx(ROOT)
    sheets = {s: gfx.image("graficos/casas-%d.png" % s) for s in set(D.CELL.values())}
    D.draw_frame(gfx, sheets, D.Fonts(gfx), run, menu, caption)
    return gfx


def tiles(gfx, run):
    """{(linha, coluna): índice da casa na folha}, lido do que foi desenhado."""
    x0, y0, size = D.board_origin(run)
    out = {}
    for _, path, x, y, src in gfx.draws():
        out[((y - y0) // size, (x - x0) // size)] = src[0] // size
    return out


class DrawTest(unittest.TestCase):
    def test_every_level_fits(self):
        for level in LEVEL_ORDER:
            run = Run(UI(), level=level, rng=random.Random(1))
            x0, y0, size = D.board_origin(run)
            b = run.board
            self.assertGreaterEqual(x0, 5)
            self.assertLessEqual(x0 + b.cols * size, D.W - 5)
            self.assertGreaterEqual(y0, D.TOP_BAR + 5)
            self.assertLessEqual(y0 + b.rows * size, D.CAPTION_Y - 5)
            self.assertEqual(len(frame(run).draws()), b.rows * b.cols)

    def test_tiles_follow_the_board(self):
        rng = random.Random(4)
        for level in LEVEL_ORDER:
            run = Run(UI(), level=level, rng=rng)
            run.dig()
            b = run.board
            for _ in range(30):
                run.r, run.c = rng.randrange(b.rows), rng.randrange(b.cols)
                if (run.r, run.c) in b.mines:
                    run.flag()
                else:
                    run.dig()
            seen = tiles(frame(run), run)
            for (r, c), k in seen.items():
                self.assertEqual(k, D.tile_index(b.state(r, c)), (level, r, c))

    def test_only_the_exploded_mine_shows(self):
        ui = UI()
        run = Run(ui, level="facil", rng=random.Random(9))
        run.dig()
        mine = sorted(run.board.mines)[0]
        run.r, run.c = mine
        run.dig()
        self.assertTrue(run.over)
        seen = tiles(frame(run), run)
        exploded = [cell for cell, k in seen.items() if k == D.T_EXPLODED]
        self.assertEqual(exploded, [mine])
        self.assertIn("linha %d, coluna %d" % (mine[0] + 1, mine[1] + 1), ui.said[-1])

    def test_top_bar(self):
        run = Run(UI(), level="medio", rng=random.Random(1))
        run.elapsed = 83
        run.r, run.c = 2, 4
        texts = frame(run).texts()
        self.assertIn("Médio  ·  linha 3, coluna 5", texts)
        self.assertIn("minas 40  ·  1:23", texts)

    def test_menus(self):
        texts = frame(menu=Menu("Nível", ["Fácil", "Médio", "Difícil", "Voltar"], 2)).texts()
        self.assertIn("Difícil", texts)
        run = Run(UI(), level="facil", rng=random.Random(1))
        texts = frame(run, Menu("Pausa", ["Continuar", "Sair sem salvar"])).texts()
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
        self.sheets = {s: self.gfx.image("graficos/casas-%d.png" % s) for s in set(D.CELL.values())}
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
        state = {"run": Run(UI(), level="facil", rng=random.Random(1))}
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
