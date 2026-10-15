import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from minado.run import Run  # noqa: E402


class FakeUI:
    def __init__(self):
        self.said, self.played = [], []

    def say(self, text, queue=False):
        self.said.append(text)

    def play(self, name, pan=None, pitch=1.0):
        self.played.append(name)

    @property
    def last(self):
        return self.said[-1]


def new(level="facil", seed=1, mines=None):
    """Partida nova; com `mines`, as minas ficam onde o teste mandar."""
    ui = FakeUI()
    over = []
    run = Run(ui, level=level, rng=random.Random(seed), on_over=over.append)
    run.start()
    if mines is not None:
        run.board.mines = set(mines)
        run.board.mine_count = len(mines)
    return run, ui, over
