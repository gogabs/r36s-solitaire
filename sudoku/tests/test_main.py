"""O main.py inteiro: menus, nível, pausa, salvar e continuar, recorde."""
import json
import os
import unittest

import fakegame  # noqa: F401  (ajusta o caminho)
from fakegame import load_main

from helpers import SOLUTION, almost_solved
from sudoku.grade import Grid


class MainTest(unittest.TestCase):
    def setUp(self):
        self.game, self.main = load_main()

    def test_menu_and_help(self):
        g = self.game
        self.assertTrue(g.last.startswith("Sudoku. Jogar, 1 de 4."))
        g.press("down", "b", "b")
        self.assertTrue(g.last.startswith("Preencha a grade"))
        g.press("a")
        self.assertEqual(g.last, "Sudoku. Como jogar, 2 de 4")

    def test_play_pause_save_continue(self):
        g = self.game
        g.press("b")
        self.assertEqual(g.last, "Nível. Fácil: 40 dicas, 1 de 4")
        g.press("down", "b")
        self.assertTrue(g.last.startswith("Sudoku médio: 32 dicas, 49 casas"))
        run = self.main["state"]["run"]
        g.press("r1")
        self.assertTrue(g.last.startswith("Vazia, linha"))
        g.press("b")
        self.assertTrue(g.last[0] == "1")
        g.handlers["update"](3.0)
        self.assertEqual(run.elapsed, 3.0)
        g.press("start")
        g.handlers["update"](3.0)                 # pausado: o relógio para
        self.assertEqual(run.elapsed, 3.0)
        g.press("down", "b")
        self.assertEqual(g.last, "Sudoku. Continuar partida salva, 1 de 5")
        g.press("b")
        self.assertTrue(g.last.startswith("Sudoku médio retomado. Faltam 48 casas."))
        g.press("y")
        self.assertIn("Tempo: 3 segundos", g.last)
        for b, start in (("x", "Linha"), ("select", "Linha"), ("r2", "Coluna"), ("l2", "Bloco")):
            g.press(b)
            self.assertTrue(g.last.startswith(start), (b, g.last))
        g.handlers["quit"]()
        self.assertTrue(os.path.isfile(os.path.join(g.save_dir, "partida.json")))

    def test_win_records_time(self):
        g = self.game
        g.press("b", "b")                         # fácil
        run = self.main["state"]["run"]
        run.grid = Grid(almost_solved([(4, 4)]))
        run.elapsed = 42
        g.press(*["b"] * SOLUTION[40])
        self.assertTrue(run.over)
        with open(os.path.join(g.save_dir, "progresso.json"), encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["facil"], {"resolvidos": 1, "melhor": 42})
        self.assertIn("Sudoku resolvido em 42 segundos!", g.said)
        self.assertEqual(g.last, "Sudoku. Jogar, 1 de 4")
        g.press("down", "down", "b")
        self.assertEqual(g.last, "Fácil: 1 resolvido, recorde de 42 segundos. "
                                 "Médio: 0 resolvidos. Difícil: 0 resolvidos.")

    def test_broken_save_is_dropped(self):
        g = self.game
        with open(os.path.join(g.save_dir, "partida.json"), "w") as f:
            f.write("{}")
        self.main["open_main"]()
        g.press("b")
        self.assertIn("Não deu para ler a partida salva. Ela foi descartada.", g.said)
        self.assertEqual(g.last, "Sudoku. Jogar, 1 de 4")


if __name__ == "__main__":
    unittest.main()
