"""Partidas inteiras com jogadas ao acaso: nada quebra, nenhuma carta some."""
import random
import unittest
from collections import Counter

from helpers import new

from paciencia import ORDER


def inventory(run):
    found = [tuple(c.to_list()[:2]) for p in run.piles for c in p.cards]
    if isinstance(getattr(run, "stock", None), list):     # Spider
        found += [tuple(c.to_list()[:2]) for c in run.stock]
    return Counter(found)


class RandomPlayTest(unittest.TestCase):
    def play(self, kind, seed, **options):
        rng = random.Random(seed)
        run, ui, over = new(kind, seed=seed, **options)
        total = sum(inventory(run).values())
        for _ in range(400):
            if run.over:
                break
            action = rng.random()
            if action < 0.15:
                run.draw()
            elif action < 0.25:
                run.undo()
            elif action < 0.35:
                run.hint()
            elif action < 0.4:
                run.to_foundation()
            else:
                moves = run.legal_moves()
                if moves:
                    si, ci, ti = rng.choice(moves)
                    run.go_to(si, ci)
                    self.assertTrue(run.press())
                    run.go_to(ti)
                    self.assertTrue(run.press(), ui.last)
            run.step(rng.choice((-1, 1)))
            run.card_step(rng.choice((-1, 1)))
            run.table_text()
            run.status_text()
            run.pile_text()
            done = len(getattr(run, "done", [])) * 13
            self.assertEqual(sum(inventory(run).values()) + done, total)
            again = kind.from_dict(ui, run.to_dict())
            self.assertEqual(again.to_dict(), run.to_dict())

    def test_all_games(self):
        for kind in ORDER:
            for seed in range(4):
                self.play(kind, seed)

    def test_following_hints_moves_forward(self):
        """Seguindo só as dicas, e comprando quando acabam, a partida anda."""
        for kind in ORDER:
            run, ui, over = new(kind, seed=5)
            for _ in range(300):
                if run.over:
                    break
                move = run.hint()
                if move is None:
                    if not run.draw():
                        break
                    continue
                si, ci, ti = move
                self.assertTrue(run.press())
                run.go_to(ti)
                self.assertTrue(run.press(), ui.last)
            self.assertGreater(run.moves, 5, kind.ID)


if __name__ == "__main__":
    unittest.main()
