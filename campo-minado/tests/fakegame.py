"""Roda o main.py de um jogo com uma Game de mentira: botões entram por
press(), as falas ficam em said. Usa o Menu de verdade do SDK."""
import os
import runpy
import sys
import tempfile
import types

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
sys.path.insert(1, os.path.join(ROOT, ".."))   # a cópia da biblioteca na raiz do repositório

from r36s_a11y import menu as real_menu  # noqa: E402
from r36s_a11y.buttons import DOWN, REPEAT, UP  # noqa: E402


class FakeSound:
    def play(self, **kw):
        return None


class FakeAudio:
    def load(self, name, path):
        return FakeSound()


class FakeGame:
    instance = None

    def __init__(self, **kw):
        self.save_dir = tempfile.mkdtemp()
        self.dir = ROOT
        self.sound = FakeAudio()
        self.said = []
        self._focus = []
        self.handlers = {}
        self.timers = []
        self.running = True
        FakeGame.instance = self

    def _hook(name):
        def deco(self, fn):
            self.handlers[name] = fn
            return fn
        return deco

    on_button = _hook("button")
    on_start = _hook("start")
    on_quit = _hook("quit")
    on_update = _hook("update")
    on_axis = _hook("axis")

    def say(self, text, queue=False, on_done=None):
        self.said.append(text)
        if on_done:
            on_done(True)

    def after(self, seconds, fn):
        fn()

    def quit(self):
        self.running = False

    def push_focus(self, handler):
        self._focus.append(handler)

    def pop_focus(self, handler):
        if handler in self._focus:
            self._focus.remove(handler)

    def run(self):
        pass

    # --- para os testes ---
    def start(self):
        self.handlers["start"]()

    def press(self, *buttons):
        for b in buttons:
            if self._focus:
                self._focus[-1].handle_button(b, DOWN, 0)
            else:
                self.handlers["button"](b, DOWN, 0)

    @property
    def last(self):
        return self.said[-1]


def load_main():
    fake = types.ModuleType("r36s_a11y")
    fake.Game = FakeGame
    fake.Menu = real_menu.Menu
    fake.DOWN, fake.UP, fake.REPEAT = DOWN, UP, REPEAT
    real = sys.modules.get("r36s_a11y")
    sys.modules["r36s_a11y"] = fake
    try:
        module = runpy.run_path(os.path.join(ROOT, "main.py"), run_name="jogo")
    finally:
        if real is not None:
            sys.modules["r36s_a11y"] = real
    game = FakeGame.instance
    game.start()
    return game, module
