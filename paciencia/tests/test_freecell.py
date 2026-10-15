import unittest

from helpers import cards, focus, new

from paciencia.base import CELULA, COLUNA, FUNDACAO
from paciencia.freecell import FreeCell, ms_deal


def clear(run):
    for p in run.piles:
        p.cards = []


class DealTest(unittest.TestCase):
    def test_microsoft_game_1(self):
        cols = ms_deal(1)
        short = {1: "A", 10: "T", 11: "J", 12: "Q", 13: "K"}
        names = [short.get(c.rank, str(c.rank)) + "HDCS"[c.suit] for c in cols[0]]
        self.assertEqual(names, ["JD", "KD", "2S", "4C", "3S", "6D", "6S"])
        self.assertEqual([len(c) for c in cols], [7, 7, 7, 7, 6, 6, 6, 6])

    def test_number_is_kept(self):
        run, ui, _ = new(FreeCell, number=617)
        self.assertIn("FreeCell, jogo 617", ui.said[0])
        self.assertEqual(sum(len(c.cards) for c in run.kind(COLUNA)), 52)
        self.assertTrue(all(c.up for col in run.kind(COLUNA) for c in col.cards))


class RulesTest(unittest.TestCase):
    def setUp(self):
        self.run, self.ui, _ = new(FreeCell, number=1)
        clear(self.run)
        self.cols = self.run.kind(COLUNA)
        self.cells = self.run.kind(CELULA)

    def test_cell_holds_one_card(self):
        run = self.run
        self.cols[0].cards = cards("9h 8s")
        focus(run, self.cols[0])
        run.press()
        focus(run, self.cells[0])
        run.press()
        self.assertEqual(self.cells[0].top.name, "8 de espadas")
        focus(run, self.cols[0])
        run.press()
        focus(run, self.cells[0])
        self.assertFalse(run.press())
        self.assertEqual(self.ui.last, "Célula 1 está ocupada.")

    def test_supermove_limit(self):
        run = self.run
        for k in range(1, 8):
            self.cols[k].cards = cards("1h")       # nenhuma coluna vazia
        self.cols[0].cards = cards("13s 12h 11s 10h 9s 8h")
        for cell in self.cells[:3]:
            cell.cards = cards("2c")                # 1 célula livre: até 2 cartas
        self.assertEqual(run.max_move(), 2)
        ok, why = run.can_pick(self.cols[0], 3)
        self.assertFalse(ok)
        self.assertEqual(why, "Com o espaço livre agora, dá para levar no máximo 2 cartas.")
        self.assertTrue(run.can_pick(self.cols[0], 4)[0])

    def test_empty_column_counts_double(self):
        run = self.run
        for k in range(2, 8):
            self.cols[k].cards = cards("1h")
        self.assertEqual(run.max_move(), 20)               # 5 x 2 x 2
        self.assertEqual(run.max_move(to_empty=True), 10)

    def test_no_cards_back_from_foundation(self):
        run = self.run
        run.kind(FUNDACAO)[0].cards = cards("1h")
        focus(run, run.kind(FUNDACAO)[0])
        self.assertFalse(run.press())
        self.assertEqual(self.ui.last, "No FreeCell, cartas da fundação não voltam.")

    def test_x_has_no_draw(self):
        self.assertFalse(self.run.draw())
        self.assertIn("não há compra", self.ui.last)

    def test_score_counts_foundation(self):
        run = self.run
        self.cols[0].cards = cards("2h 1h")
        self.cols[1].cards = cards("13s")
        focus(run, self.cols[0])
        run.to_foundation()
        run.to_foundation()
        self.assertEqual(run.score, 2)
        self.assertIn("2 cartas nas fundações", run.status_text())


class SaveTest(unittest.TestCase):
    def test_roundtrip(self):
        run, ui, _ = new(FreeCell, number=99)
        run.hint()
        run.press()
        data = run.to_dict()
        again = FreeCell.from_dict(ui, data)
        self.assertEqual(again.options["number"], 99)
        self.assertEqual(again.to_dict(), data)


if __name__ == "__main__":
    unittest.main()
