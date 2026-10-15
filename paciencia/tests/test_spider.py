import unittest

from helpers import cards, focus, new

from paciencia.base import COLUNA
from paciencia.cards import Card
from paciencia.spider import Spider


def clear(run):
    for p in run.piles:
        p.cards = []


class DealTest(unittest.TestCase):
    def test_deal(self):
        for suits in (1, 2, 4):
            run, ui, _ = new(Spider, suits=suits)
            on_table = sum(len(c.cards) for c in run.piles)
            self.assertEqual(on_table, 54)
            self.assertEqual(len(run.stock), 50)
            self.assertEqual(len({c.suit for c in run.stock + [x for p in run.piles for x in p.cards]}), suits)
        self.assertEqual(run.score, 500)


class RulesTest(unittest.TestCase):
    def setUp(self):
        self.run, self.ui, self.over = new(Spider, suits=2)
        clear(self.run)
        self.cols = self.run.piles

    def test_any_suit_on_top_but_runs_need_one_suit(self):
        run = self.run
        self.cols[0].cards = cards("9h 8s 7s")
        self.cols[1].cards = cards("9s")
        self.assertTrue(run.can_pick(self.cols[0], 1)[0])
        self.assertEqual(run.can_pick(self.cols[0], 0), (False, "Só sequências do mesmo naipe se movem juntas."))
        focus(run, self.cols[0])
        run.card_step(-1)
        run.press()
        run.step(1)
        run.press()
        self.assertEqual(len(self.cols[1].cards), 3)
        self.assertEqual(run.score, 499)

    def test_complete_run_leaves_and_flips(self):
        run = self.run
        self.cols[0].cards = [Card(4, 0)] + cards(" ".join("%ds" % r for r in range(13, 1, -1)))
        self.cols[1].cards = cards("1s")
        focus(run, self.cols[1])
        run.press()
        run.step(-1)
        run.press()
        self.assertEqual(run.done, [3])
        self.assertEqual(len(self.cols[0].cards), 1)
        self.assertTrue(self.cols[0].top.up)
        self.assertIn("Sequência completa de espadas na coluna 1! 1 de 8.", self.ui.last)
        self.assertEqual(run.score, 500 - 1 + 100)
        run.undo()
        self.assertEqual(run.done, [])
        self.assertEqual(len(self.cols[0].cards), 13)

    def test_deal_needs_no_empty_column(self):
        run = self.run
        run.stock = cards(" ".join(["5h"] * 10))
        for col in self.cols[1:]:
            col.cards = cards("9s")
        self.assertFalse(run.draw())
        self.assertEqual(self.ui.last, "Não dá para distribuir com coluna vazia: coluna 1.")
        self.cols[0].cards = cards("9s")
        self.assertTrue(run.draw())
        self.assertTrue(all(len(c.cards) == 2 for c in self.cols))
        self.assertIn("Era a última distribuição.", self.ui.last)
        self.assertFalse(run.draw())

    def test_win(self):
        run = self.run
        run.done = [3] * 7
        self.cols[0].cards = cards(" ".join("%dh" % r for r in range(13, 1, -1)))
        self.cols[1].cards = cards("1h")
        focus(run, self.cols[1])
        run.press()
        run.step(-1)
        run.press()
        self.assertTrue(run.over)
        self.assertTrue(self.over[0]["won"])

    def test_no_foundation_key(self):
        self.assertFalse(self.run.to_foundation())
        self.assertIn("saem sozinhas", self.ui.last)


class SaveTest(unittest.TestCase):
    def test_roundtrip_keeps_stock(self):
        run, ui, _ = new(Spider, suits=4)
        run.draw()
        data = run.to_dict()
        again = Spider.from_dict(ui, data)
        self.assertEqual(len(again.stock), 40)
        self.assertEqual(again.to_dict(), data)


if __name__ == "__main__":
    unittest.main()
