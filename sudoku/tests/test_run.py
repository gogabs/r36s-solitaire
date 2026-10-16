import random
import unittest

from helpers import SOLUTION, almost_solved, new

from sudoku.run import Run, duration


class NavigationTest(unittest.TestCase):
    def test_start_in_the_middle(self):
        run, ui, _ = new()
        self.assertEqual((run.r, run.c), (4, 4))
        self.assertEqual(ui.said[0], "Sudoku fácil: 30 dicas, 51 casas para preencher. "
                                     "Você está na linha 5, coluna 5: vazia.")

    def test_new_run_generates_by_level(self):
        run = Run(None, level="dificil", rng=random.Random(2))
        self.assertEqual(run.grid.to_fill(), 81 - 26)

    def test_move_speaks_cell_axis_and_box(self):
        run, ui, _ = new()
        run.move(0, -1)
        self.assertEqual(ui.last, "8 fixo, coluna 4.")
        self.assertEqual(ui.played[-1], "fixo_8")
        run.move(0, -1)
        self.assertEqual(ui.last, "vazia, coluna 3, bloco 4.")
        self.assertEqual(ui.played[-1], "vazia")
        run.move(-1, 0)
        self.assertEqual(ui.last, "vazia, linha 4.")

    def test_edge(self):
        run, ui, _ = new()
        run.r = 0
        self.assertFalse(run.move(-1, 0))
        self.assertEqual(ui.played[-1], "borda")
        self.assertEqual(ui.last, "Borda, linha 1: 7 fixo.")

    def test_jump_to_empty_cells(self):
        run, ui, _ = new()
        run.r, run.c = 0, 0
        run.jump(1)
        self.assertEqual((run.r, run.c), (0, 2))
        self.assertEqual(ui.last, "Vazia, linha 1, coluna 3.")
        run.jump(-1)
        self.assertEqual((run.r, run.c), (8, 6))


class WriteTest(unittest.TestCase):
    def test_b_counts_up_and_a_down(self):
        run, ui, _ = new()
        run.r, run.c = 0, 2
        run.step(1)
        self.assertEqual(ui.last, "1.")
        self.assertEqual(ui.played[-1], "num_1")
        run.step(-1)
        self.assertEqual(ui.last, "Vazia.")
        self.assertEqual(ui.played[-1], "apagar")
        run.step(-1)
        self.assertEqual(run.grid.get(0, 2), 9)
        self.assertEqual(ui.last, "9, repete no bloco.")
        self.assertEqual(ui.played[-1], "conflito")

    def test_conflict_names_every_place(self):
        run, ui, _ = new()
        run.r, run.c = 0, 2
        for _ in range(5):
            run.step(1)
        self.assertEqual(ui.last, "5, repete na linha e no bloco.")

    def test_given_cannot_change(self):
        run, ui, _ = new()
        run.r, run.c = 0, 0
        self.assertFalse(run.step(1))
        self.assertEqual(ui.last, "5 fixo: é uma dica, não muda.")
        self.assertEqual(ui.played[-1], "erro")
        self.assertEqual(run.grid.get(0, 0), 5)

    def test_completing_units(self):
        run, ui, over = new(almost_solved([(0, 0), (1, 1), (4, 4)]))
        run.r, run.c = 0, 0
        for _ in range(5):
            run.step(1)
        self.assertEqual(ui.last, "5. Linha 1 e coluna 1 completas.")
        self.assertEqual(ui.played[-1], "completo")
        self.assertEqual(over, [])

    def test_unit_words(self):
        run, ui, _ = new(almost_solved([(0, 0), (1, 1), (4, 4), (4, 0)]))
        run.r, run.c = 1, 1
        for _ in range(7):
            run.step(1)
        self.assertEqual(ui.last, "7. Linha 2 e coluna 2 completas.")
        run.r, run.c = 0, 0
        for _ in range(5):
            run.step(1)
        self.assertEqual(ui.last, "5. Linha 1 e bloco 1 completos.")
        run.r, run.c = 4, 0
        for _ in range(4):
            run.step(1)
        self.assertEqual(ui.last, "4. Coluna 1 e bloco 4 completos.")

    def test_win(self):
        run, ui, over = new(almost_solved([(4, 4)]))
        run.elapsed = 75
        for _ in range(SOLUTION[4 * 9 + 4]):
            run.step(1)
        self.assertTrue(run.over)
        self.assertEqual(over, [{"level": "facil", "won": True, "time": 75}])
        self.assertIn("vitoria", ui.played)
        self.assertFalse(run.step(1))

    def test_full_with_mistakes_is_not_a_win(self):
        givens = almost_solved([(0, 0), (0, 1)])   # 5 e 3
        run, ui, over = new(givens)
        run.r, run.c = 0, 0
        for _ in range(3):
            run.step(1)
        run.r, run.c = 0, 1
        for _ in range(5):
            run.step(1)
        self.assertFalse(run.over)
        self.assertTrue(ui.last.startswith("5, repete"))
        run.tick(1)
        self.assertEqual(run.status_text(), "Faltam 0 casas, de 2. 4 casas com número repetido. "
                                            "Tempo: 1 segundo. Nível fácil.")


class InfoTest(unittest.TestCase):
    def test_status(self):
        run, ui, _ = new()
        run.elapsed = 65
        self.assertEqual(run.status_text(), "Faltam 51 casas, de 51. Tempo: 1 minuto e 5 segundos. "
                                            "Nível fácil.")

    def test_candidates(self):
        run, ui, _ = new()
        run.r, run.c = 0, 2
        self.assertEqual(run.candidates_text(), "Linha 1, coluna 3, bloco 1: vazia; cabem 1, 2 e 4.")
        run.r, run.c = 0, 0
        self.assertEqual(run.candidates_text(), "Linha 1, coluna 1, bloco 1: 5 fixo.")
        run, ui, _ = new(almost_solved([(4, 4)]))
        self.assertEqual(run.candidates_text(), "Linha 5, coluna 5, bloco 5: vazia; só cabe o 5.")

    def test_row_column_box(self):
        run, ui, _ = new()
        run.r, run.c = 0, 0
        self.assertEqual(run.row_text(), "Linha 1: 5, 3, 2 vazias, 7, 4 vazias. Faltam: 1, 2, 4, 6, 8 e 9.")
        self.assertEqual(run.column_text(), "Coluna 1: 5, 6, vazia, 8, 4, 7, 3 vazias. Faltam: 1, 2, 3 e 9.")
        self.assertEqual(run.box_text(), "Bloco 1: 5, 3, vazia, 6, 2 vazias, vazia, 9, 8. Faltam: 1, 2, 4 e 7."
                         .replace("vazia, 6, 2 vazias, vazia", "vazia, 6, 3 vazias"))

    def test_duration(self):
        self.assertEqual(duration(1), "1 segundo")
        self.assertEqual(duration(120), "2 minutos")


class SaveTest(unittest.TestCase):
    def test_roundtrip(self):
        run, ui, _ = new()
        run.r, run.c = 0, 2
        run.step(1)
        run.tick(12)
        data = run.to_dict()
        again = Run.from_dict(ui, data)
        self.assertEqual(again.to_dict(), data)
        again.resume()
        self.assertEqual(ui.last, "Sudoku fácil retomado. Faltam 50 casas. Linha 1, coluna 3, 1.")

    def test_bad_save(self):
        run, ui, _ = new()
        data = run.to_dict()
        data["level"] = "impossivel"
        with self.assertRaises(ValueError):
            Run.from_dict(ui, data)
        data = run.to_dict()
        del data["cursor"]
        with self.assertRaises(ValueError):
            Run.from_dict(ui, data)
        data = run.to_dict()
        data["cursor"] = [9, 0]
        with self.assertRaises(ValueError):
            Run.from_dict(ui, data)


if __name__ == "__main__":
    unittest.main()
