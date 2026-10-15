"""A tela da Paciência, com gráficos de mentira: tudo cabe na tela, o foco e a
mão aparecem, e a tela nunca derruba o jogo."""
import os
import random
import tempfile
import unittest

from fakegfx import RecordingGfx
from helpers import new

from paciencia import ORDER
from paciencia import desenho as D

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


class Menu:
    def __init__(self, title, items, index=0):
        self.title, self.items, self.index = title, items, index


def frame(run=None, menu=None, caption=""):
    gfx = RecordingGfx(ROOT)
    sheets = {k: gfx.image("graficos/cartas-%s.png" % k) for k in D.SIZES}
    D.draw_frame(gfx, sheets, D.Fonts(gfx), run, menu, caption)
    return gfx


class DrawTest(unittest.TestCase):
    def check_cards_on_screen(self, run, gfx):
        _, size = D.layout(run)
        w, h = D.SIZES[size]
        for _, path, x, y, src in gfx.draws():
            self.assertTrue(0 <= x and x + w <= D.W, (run.ID, x))
            self.assertTrue(D.TOP_BAR <= y and y + h <= D.CAPTION_Y, (run.ID, y, h))

    def test_random_play_fits(self):
        for kind in ORDER:
            for seed in range(3):
                rng = random.Random(seed)
                run, ui, _ = new(kind, seed=seed)
                for _ in range(150):
                    if run.over:
                        break
                    moves = run.legal_moves()
                    if moves and rng.random() < 0.7:
                        si, ci, ti = rng.choice(moves)
                        run.go_to(si, ci)
                        run.press()
                        if rng.random() < 0.8:
                            run.go_to(ti)
                            run.press()
                    else:
                        run.draw()
                    run.go_to(rng.randrange(len(run.piles)))
                    gfx = frame(run, caption=ui.last)
                    self.check_cards_on_screen(run, gfx)

    def test_top_bar_matches_speech(self):
        run, ui, _ = new(ORDER[0], seed=3)
        left, right = D.bar_text(run)
        texts = frame(run).texts()
        self.assertIn(left, texts)
        self.assertIn(right, texts)

    def test_held_cards_are_marked(self):
        run, ui, _ = new(ORDER[0], seed=1)
        while not run.legal_moves() and run.draw():
            pass
        si, ci, ti = run.legal_moves()[0]
        run.go_to(si, ci)
        run.press()
        self.assertIsNotNone(run.held)
        run.go_to(ti)
        texts = frame(run).texts()
        self.assertIn("NA MÃO", texts)
        self.assertIn("CABE", texts)

    def test_menu_keeps_selection_visible(self):
        items = ["Item %d" % k for k in range(20)]
        for index in (0, 7, 19):
            texts = frame(menu=Menu("Como jogar", items, index)).texts()
            self.assertIn(items[index], texts)
            self.assertIn("Como jogar", texts)

    def test_caption_shows_newest_speech(self):
        gfx = RecordingGfx(ROOT)
        long = " ".join("palavra%d" % k for k in range(80)) + " fim."
        lines = D.wrap(gfx, long, gfx.font(None, 18), D.W - 20)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("… "))
        self.assertTrue(lines[-1].endswith("fim."))


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
        self.sheets = {k: self.gfx.image("graficos/cartas-%s.png" % k) for k in D.SIZES}
        self.fonts = D.Fonts(self.gfx)
        return True


class RendererTest(unittest.TestCase):
    def setUp(self):
        self.saved_env = dict(os.environ)
        fd, self.conf = tempfile.mkstemp()
        os.close(fd)
        os.environ["A11Y_SISTEMA_CONF"] = self.conf
        os.environ.pop("A11Y_GRAPHICS", None)
        self.write_conf("SCREEN=1\n")

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.saved_env)
        os.remove(self.conf)

    def write_conf(self, text):
        with open(self.conf, "w") as f:
            f.write(text)

    def make(self, run=None):
        game = FakeGame()
        state = {"run": run}
        r = TestRenderer(game, lambda: state["run"])
        return game, state, r

    def test_draws_and_keeps_caption(self):
        game, state, r = self.make()
        game.say("Paciência. Klondike, 1 de 6.")
        self.assertEqual(game.said, ["Paciência. Klondike, 1 de 6."])
        r.update(1.0)
        self.assertEqual(r.gfx.frames, 1)
        self.assertIn("Paciência. Klondike, 1 de 6.", r.gfx.texts())
        game.say("Mais.", queue=True)
        self.assertEqual(r.caption, "Paciência. Klondike, 1 de 6. Mais.")

    def test_screen_off_and_switch_off(self):
        self.write_conf("SCREEN=0\n")
        game, state, r = self.make()
        r.update(1.0)
        self.assertIsNone(r.gfx)
        self.write_conf("SCREEN=1\n")
        os.environ["A11Y_GRAPHICS"] = "0"
        r.checked = -1.0
        r.update(1.0)
        self.assertIsNone(r.gfx)

    def test_energy_saving_lowers_frame_rate(self):
        self.write_conf("SCREEN=1\nENERGY=aggressive\n")
        game, state, r = self.make()
        r.update(0.25)
        frames = r.gfx.frames
        for _ in range(10):
            r.update(0.05)
        self.assertEqual(r.gfx.frames - frames, 2)   # 0.5 s a 5 quadros por segundo

    def test_failure_only_turns_graphics_off(self):
        game, state, r = self.make()
        r.broken = True
        r.update(1.0)
        self.assertTrue(r.failed)
        r.update(1.0)
        game.say("O jogo segue.")
        self.assertEqual(game.said[-1], "O jogo segue.")

    def test_finished_run_stays_until_menu(self):
        run, ui, _ = new(ORDER[0], seed=2)
        game, state, r = self.make(run)
        self.assertIs(r.scene()[0], run)
        state["run"] = None
        self.assertIs(r.scene()[0], run)
        game._focus.append(Menu("Paciência", ["Klondike"]))
        self.assertEqual(r.scene(), (None, game._focus[-1]))


if __name__ == "__main__":
    unittest.main()
