import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from sudoku.grade import Grid  # noqa: E402
from sudoku.run import Run  # noqa: E402

# Uma solução conhecida e um jogo com solução única tirado dela.
SOLUTION = [int(ch) for ch in (
    "534678912672195348198342567859761423426853791713924856961537284287419635345286179")]
PUZZLE = [int(ch) for ch in (
    "530070000600195000098000060800060003400803001700020006060000280000419005000080079")]


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


def new(givens=None, level="facil"):
    """Partida nova com a grade conhecida (ou a que o teste mandar)."""
    ui = FakeUI()
    over = []
    run = Run(ui, level=level, on_over=over.append, grid=Grid(givens or PUZZLE))
    run.start()
    return run, ui, over


def almost_solved(blank):
    """A solução com só as casas de `blank` vazias, todas fora das dicas."""
    givens = list(SOLUTION)
    for r, c in blank:
        givens[r * 9 + c] = 0
    return givens
