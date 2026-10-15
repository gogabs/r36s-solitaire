import unittest

from helpers import new

from minado.run import Run, duration


class NavigationTest(unittest.TestCase):
    def test_start_in_the_middle(self):
        run, ui, _ = new()
        self.assertEqual((run.r, run.c), (4, 4))
        self.assertIn("9 linhas, 9 colunas, 10 minas", ui.said[0])

    def test_move_speaks_cell_and_axis(self):
        run, ui, _ = new()
        run.move(0, 1)
        self.assertEqual(ui.last, "fechada, coluna 6.")
        self.assertEqual(ui.played[-1], "fechada")
        run.move(-1, 0)
        self.assertEqual(ui.last, "fechada, linha 4.")

    def test_edge(self):
        run, ui, _ = new()
        run.r = 0
        self.assertFalse(run.move(-1, 0))
        self.assertEqual(ui.played[-1], "borda")
        self.assertEqual(ui.last, "Borda, linha 1: fechada.")
        self.assertEqual(run.r, 0)

    def test_jump_to_closed_cells(self):
        run, ui, _ = new(mines=[(8, 6), (8, 8)])
        run.r, run.c = 0, 0
        run.dig()
        self.assertFalse(run.over)
        run.jump(1)
        self.assertEqual((run.r, run.c), (8, 6))
        self.assertEqual(ui.last, "Fechada, linha 9, coluna 7.")
        run.jump(1)
        self.assertEqual((run.r, run.c), (8, 7))
        run.jump(-1)
        self.assertEqual((run.r, run.c), (8, 6))


class DigTest(unittest.TestCase):
    def test_first_dig_places_mines_and_starts_clock(self):
        run, ui, _ = new(seed=4)
        run.tick(5)
        self.assertEqual(run.elapsed, 0)
        run.dig()
        self.assertTrue(run.board.placed)
        self.assertTrue(ui.last.startswith("Abriu"))
        run.tick(2.5)
        self.assertEqual(run.elapsed, 2.5)

    def test_number_cell(self):
        run, ui, _ = new(mines=[(4, 5), (0, 0)])
        run.dig()
        self.assertEqual(ui.last, "1.")
        self.assertIn("num_1", ui.played)

    def test_mine_explodes(self):
        run, ui, over = new(mines=[(4, 4), (0, 0)])
        run.board.opened.add((8, 8))
        run.dig()
        self.assertTrue(run.over)
        self.assertFalse(over[0]["won"])
        self.assertIn("explosao", ui.played)
        self.assertTrue(ui.last.startswith("Bum! Mina na linha 5, coluna 5."))
        self.assertFalse(run.dig())

    def test_flagged_cell_is_not_dug(self):
        run, ui, _ = new()
        run.flag()
        self.assertFalse(run.dig())
        self.assertEqual(ui.last, "Casa marcada. Tire a marca com A antes de cavar.")
        self.assertFalse(run.board.placed)

    def test_win(self):
        run, ui, over = new(mines=[(0, 0)])
        run.dig()
        self.assertTrue(run.over)
        self.assertTrue(over[0]["won"])
        self.assertEqual(run.board.flags, {(0, 0)})
        self.assertIn("vitoria", ui.played)


class ChordTest(unittest.TestCase):
    def setUp(self):
        self.run, self.ui, self.over = new(mines=[(3, 3), (0, 8)])
        self.run.r, self.run.c = 4, 4
        self.run.board.opened.add((4, 4))       # 1, com a mina em cima à esquerda

    def test_needs_matching_flags(self):
        self.assertFalse(self.run.dig())
        self.assertEqual(self.ui.last, "1 mina em volta, 0 marcadas.")

    def test_opens_neighbors(self):
        run = self.run
        run.board.flags.add((3, 3))
        run.dig()
        self.assertTrue(self.ui.last.startswith("Abriu"))
        self.assertIn((5, 5), run.board.opened)

    def test_wrong_flag_explodes(self):
        run = self.run
        run.board.flags.add((5, 5))
        run.dig()
        self.assertTrue(run.over)
        self.assertEqual((run.r, run.c), (3, 3))


class FlagTest(unittest.TestCase):
    def test_flag_counts_down(self):
        run, ui, _ = new()
        run.flag()
        self.assertEqual(ui.last, "Marcada. Faltam 9 minas.")
        run.flag()
        self.assertEqual(ui.last, "Desmarcada. Faltam 10 minas.")

    def test_opened_cell_cannot_be_flagged(self):
        run, ui, _ = new(mines=[(0, 0)])
        run.board.opened.add((4, 4))
        self.assertFalse(run.flag())
        self.assertEqual(ui.last, "Casa já aberta: vazia.")

    def test_too_many_flags(self):
        run, ui, _ = new(mines=[(0, 0)])
        run.flag()
        run.move(0, 1)
        run.flag()
        self.assertEqual(run.mines_left_text(), "1 marca a mais que as minas")


class InfoTest(unittest.TestCase):
    def test_status(self):
        run, ui, _ = new(mines=[(4, 5), (0, 0)])
        run.dig()
        run.elapsed = 65
        self.assertEqual(run.status_text(),
                         "Faltam 2 minas, de 2. 1 de 79 casas abertas. Tempo: 1 minuto e 5 segundos. "
                         "Nível fácil.")

    def test_around(self):
        run, ui, _ = new(mines=[(3, 4), (0, 0)])
        run.board.opened |= {(4, 4), (5, 4)}
        run.board.flags.add((3, 4))
        self.assertEqual(
            run.around_text(),
            "Linha 5, coluna 5: 1. Em volta: 1 marcada: acima; 6 fechadas: acima à direita, à direita, "
            "abaixo à direita, abaixo à esquerda, à esquerda e acima à esquerda; 1 vazia: abaixo.")

    def test_row_and_column(self):
        run, ui, _ = new(mines=[(4, 8)])
        run.board.opened |= {(4, 0), (4, 1), (4, 7)}
        self.assertEqual(run.row_text(), "Linha 5: 2 vazias, 5 fechadas, 1, fechada.")
        self.assertEqual(run.column_text(), "Coluna 5: 9 fechadas.")

    def test_duration(self):
        self.assertEqual(duration(1), "1 segundo")
        self.assertEqual(duration(120), "2 minutos")
        self.assertEqual(duration(61.9), "1 minuto e 1 segundo")


class SaveTest(unittest.TestCase):
    def test_roundtrip(self):
        run, ui, _ = new(level="dificil", seed=3)
        run.dig()
        run.move(0, 1)
        run.flag()
        run.tick(12)
        data = run.to_dict()
        again = Run.from_dict(ui, data)
        self.assertEqual(again.to_dict(), data)
        again.resume()
        self.assertTrue(ui.last.startswith("Campo minado difícil retomado."))

    def test_level_mismatch(self):
        run, ui, _ = new()
        data = run.to_dict()
        data["level"] = "medio"
        with self.assertRaises(ValueError):
            Run.from_dict(ui, data)
        data = run.to_dict()
        del data["cursor"]
        with self.assertRaises(ValueError):
            Run.from_dict(ui, data)


if __name__ == "__main__":
    unittest.main()
