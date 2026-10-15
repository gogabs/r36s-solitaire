import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from paciencia.cards import Card  # noqa: E402


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


def new(kind, seed=1, **options):
    ui = FakeUI()
    over = []
    run = kind(ui, rng=random.Random(seed), on_over=over.append, **options)
    run.start()
    return run, ui, over


def cards(text):
    """ "13h 12s" -> [rei de copas, dama de espadas], abertas."""
    suits = {"h": 0, "d": 1, "c": 2, "s": 3}
    return [Card(int(t[:-1]), suits[t[-1]], up=True) for t in text.split()]


def focus(run, pile):
    run.go_to(run.piles.index(pile))
