import unittest

from helpers import cards, focus, new

from paciencia.base import COLUNA, FUNDACAO
from paciencia.cards import Card
from paciencia.klondike import Klondike


def clear(run):
    for p in run.piles:
        p.cards = []


class DealTest(unittest.TestCase):
    def test_deal(self):
        run, ui, _ = new(Klondike)
        cols = run.kind(COLUNA)
        self.assertEqual([len(c.cards) for c in cols], [1, 2, 3, 4, 5, 6, 7])
        self.assertTrue(all(c.top.up and c.down_count() == len(c.cards) - 1 for c in cols))
        self.assertEqual(len(run.stock.cards), 24)
        self.assertIn("Klondike, comprando 1", ui.said[0])
        self.assertEqual(run.pile, cols[0])


class NavigationTest(unittest.TestCase):
    def test_left_right_wrap_through_all_piles(self):
        run, ui, _ = new(Klondike)
        run.step(1)
        self.assertEqual(run.pile, run.kind(COLUNA)[1])
        for _ in range(6):
            run.step(1)
        self.assertEqual(run.pile, run.stock)     # deu a volta
        self.assertEqual(ui.played[-1], "borda")
        self.assertTrue(ui.last.startswith("24 cartas no estoque"))

    def test_up_down_inside_column(self):
        run, ui, _ = new(Klondike)
        clear(run)
        col = run.kind(COLUNA)[2]
        col.cards = [Card(1, 0)] + cards("13s 12h 11c")
        focus(run, col)
        run.card_step(-1)
        self.assertEqual(ui.last, "dama de copas, 2 de 3.")
        run.card_step(-1)
        run.card_step(-1)
        self.assertEqual(ui.last, "Primeira aberta: rei de espadas, com 1 virada embaixo.")
        run.card_step(1)
        run.card_step(1)
        run.card_step(1)
        self.assertEqual(ui.last, "Carta de cima: valete de paus.")

    def test_describe(self):
        run, ui, _ = new(Klondike)
        clear(run)
        col = run.kind(COLUNA)[0]
        col.cards = [Card(1, 0), Card(2, 0)] + cards("9h 8s")
        self.assertEqual(run.describe(col), "8 de espadas, 2 abertas e 2 viradas, coluna 1")
        col.cards = [Card(1, 0)] + cards("9h")
        self.assertEqual(run.describe(col), "9 de copas, 1 virada, coluna 1")
        col.cards = cards("9h 8s")
        self.assertEqual(run.describe(col), "8 de espadas, 2 cartas, coluna 1")
        self.assertEqual(run.describe(run.kind(FUNDACAO)[0]), "Fundação de copas vazia")
        run.kind(FUNDACAO)[0].cards = cards("1h 2h")
        self.assertEqual(run.describe(run.kind(FUNDACAO)[0]), "2 de copas, fundação de copas")
        run.waste.cards = cards("5c 7d")
        self.assertEqual(run.describe(run.waste), "7 de ouros, 2 cartas, descarte")
        self.assertEqual(run.describe(run.stock), "Estoque vazio")

    def test_table_and_pile_text_say_cards_first(self):
        run, ui, _ = new(Klondike)
        clear(run)
        run.kind(COLUNA)[0].cards = [Card(1, 0), Card(2, 0)] + cards("9h 8s")
        run.kind(FUNDACAO)[0].cards = cards("1h")
        text = run.table_text()
        self.assertIn("Fundações: até o ás de copas; ouros vazia", text)
        self.assertIn("8 de espadas com 2 viradas, coluna 1; coluna 2 vazia", text)
        focus(run, run.kind(COLUNA)[0])
        self.assertEqual(run.pile_text(),
                         "De baixo para cima: 2 viradas, 9 de copas e 8 de espadas. Coluna 1.")


class MoveTest(unittest.TestCase):
    def setUp(self):
        self.run, self.ui, self.over = new(Klondike)
        clear(self.run)
        self.cols = self.run.kind(COLUNA)

    def test_pick_drop_sequence_and_flip(self):
        run = self.run
        self.cols[0].cards = [Card(5, 3)] + cards("9h 8s")
        self.cols[1].cards = cards("10c")
        focus(run, self.cols[0])
        run.card_step(-1)                 # foco no 9 de copas
        run.press()
        self.assertEqual(self.ui.last, "Pegou 9 de copas e mais 1 carta, até o 8 de espadas.")
        run.step(1)
        self.assertTrue(self.ui.last.endswith("Cabe."))
        run.press()
        self.assertEqual([c.name for c in self.cols[1].cards], ["10 de paus", "9 de copas", "8 de espadas"])
        self.assertTrue(self.cols[0].top.up)
        self.assertIn("Virou o 5 de espadas na coluna 1.", self.ui.last)
        self.assertEqual(run.score, 5)
        self.assertEqual(run.moves, 1)

    def test_refuse_same_color_and_keep_holding(self):
        run = self.run
        self.cols[0].cards = cards("9s")
        self.cols[1].cards = cards("10c")
        focus(run, self.cols[0])
        run.press()
        run.step(1)
        self.assertFalse(self.ui.last.endswith("Cabe."))
        self.assertFalse(run.press())
        self.assertIn("outra cor", self.ui.last)
        self.assertIsNotNone(run.held)
        run.undo()                        # A com carta na mão devolve
        self.assertIsNone(run.held)
        self.assertEqual(self.ui.last, "Devolveu para a coluna 1.")

    def test_empty_column_only_king(self):
        run = self.run
        self.cols[0].cards = cards("12h")
        focus(run, self.cols[0])
        run.press()
        run.step(1)
        self.assertFalse(run.press())
        self.assertEqual(self.ui.last, "Coluna vazia só aceita rei.")

    def test_foundation_by_suit_and_r1(self):
        run = self.run
        run.stock.cards = [Card(9, 3)]    # com estoque, nada termina sozinho
        self.cols[0].cards = cards("2h 1h")
        focus(run, self.cols[0])
        run.to_foundation()
        self.assertEqual(len(run.kind(FUNDACAO)[0].cards), 1)
        self.assertIn("Ás de copas na fundação de copas.", self.ui.last)
        self.assertEqual(run.pile, self.cols[0])    # o foco fica na coluna
        run.to_foundation()
        self.assertEqual(run.score, 20)
        self.cols[1].cards = cards("4h")
        focus(run, self.cols[1])
        self.assertFalse(run.to_foundation())
        self.assertEqual(self.ui.last, "O 4 de copas ainda não vai para a fundação.")

    def test_undo_restores_everything(self):
        run = self.run
        self.cols[0].cards = [Card(7, 1)] + cards("1s")
        focus(run, self.cols[0])
        run.to_foundation()
        self.assertTrue(self.cols[0].top.up)
        run.undo()
        self.assertEqual(len(self.cols[0].cards), 2)
        self.assertFalse(self.cols[0].cards[0].up)
        self.assertEqual(run.score, 0)
        self.assertEqual(run.moves, 0)
        self.assertTrue(self.ui.last.startswith("Desfeito: ás de espadas da coluna 1 para a fundação de espadas."))
        self.assertFalse(run.undo())
        self.assertEqual(self.ui.last, "Nada para desfazer.")


class DrawTest(unittest.TestCase):
    def test_draw_one_and_recycle(self):
        run, ui, _ = new(Klondike)
        run.stock.cards = [Card(3, 0), Card(4, 2)]
        run.draw()
        self.assertEqual(ui.last, "Comprou 4 de paus.")
        self.assertEqual(run.pile, run.waste)
        run.draw()
        self.assertEqual(ui.last, "Comprou 3 de copas. Estoque vazio.")
        run.score = 150
        run.draw()
        self.assertEqual(ui.last, "O descarte voltou para o estoque: 2 cartas.")
        self.assertEqual([c.rank for c in run.stock.cards], [3, 4])
        self.assertFalse(any(c.up for c in run.stock.cards))
        self.assertEqual(run.score, 50)
        run.draw()
        self.assertEqual(ui.last, "Comprou 4 de paus.")

    def test_draw_three(self):
        run, ui, _ = new(Klondike, draw=3)
        run.stock.cards = cards("1h 2h 3h 4h")
        for c in run.stock.cards:
            c.up = False
        run.draw()
        self.assertEqual(ui.last, "Comprou 4 de copas, 3 de copas e 2 de copas; em cima, 2 de copas.")
        self.assertEqual(run.waste.top.rank, 2)

    def test_b_on_stock_draws(self):
        run, ui, _ = new(Klondike)
        run.go_to(0)
        run.press()
        self.assertTrue(ui.last.startswith("Comprou"))


class EndTest(unittest.TestCase):
    def test_auto_finish_and_win(self):
        run, ui, over = new(Klondike)
        clear(run)
        f = run.kind(FUNDACAO)
        for s in range(4):
            f[s].cards = [Card(r, s, True) for r in range(1, 12)]
        cols = run.kind(COLUNA)
        cols[0].cards = cards("13h 12h")
        cols[1].cards = cards("13d 12d")
        cols[2].cards = cards("13c 12c")
        cols[3].cards = cards("13s 12s")
        focus(run, cols[3])
        run.card_step(-1)
        run.press()
        run.step(1)                       # coluna 5, vazia: rei pode
        run.press()
        self.assertTrue(run.over)
        self.assertTrue(over[0]["won"])
        self.assertIn("cascata", ui.played)
        self.assertIn("vitoria", ui.played)


class SaveTest(unittest.TestCase):
    def test_roundtrip(self):
        run, ui, _ = new(Klondike, draw=3)
        run.draw()
        run.step(1)
        data = run.to_dict()
        again = Klondike.from_dict(ui, data)
        self.assertEqual(again.to_dict(), data)
        self.assertEqual(again.draw_count, 3)
        again.resume()
        self.assertTrue(ui.last.startswith("Klondike, comprando 3 retomado, com 1 jogada."))

    def test_bad_save(self):
        run, ui, _ = new(Klondike)
        data = run.to_dict()
        del data["piles"]
        with self.assertRaises(ValueError):
            Klondike.from_dict(ui, data)
        data = run.to_dict()
        data["jogo"] = "spider"
        with self.assertRaises(ValueError):
            Klondike.from_dict(ui, data)


if __name__ == "__main__":
    unittest.main()
