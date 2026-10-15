"""O main.py inteiro: menus, nível, pausa, salvar e continuar, recorde."""
import json
import os
import unittest

import fakegame  # noqa: F401  (ajusta o caminho)
from fakegame import load_main


class MainTest(unittest.TestCase):
    def setUp(self):
        self.game, self.main = load_main()

    def test_menu_and_help(self):
        g = self.game
        self.assertTrue(g.last.startswith("Campo Minado. Jogar, 1 de 4."))
        g.press("down", "b", "b")
        self.assertTrue(g.last.startswith("Abra todas as casas"))
        g.press("a")
        self.assertEqual(g.last, "Campo Minado. Como jogar, 2 de 4")

    def test_play_pause_save_continue(self):
        g = self.game
        g.press("b")
        self.assertEqual(g.last, "Nível. Fácil: 9 por 9, 10 minas, 1 de 4")
        g.press("down", "b")
        self.assertTrue(g.last.startswith("Campo minado médio: 16 linhas"))
        g.press("b")
        self.assertTrue(g.last.startswith("Abriu") or g.last[0].isdigit())
        run = self.main["state"]["run"]
        g.handlers["update"](3.0)
        self.assertEqual(run.elapsed, 3.0)
        g.press("start")
        g.handlers["update"](3.0)                 # pausado: o relógio para
        self.assertEqual(run.elapsed, 3.0)
        g.press("down", "b")
        self.assertEqual(g.last, "Campo Minado. Continuar partida salva, 1 de 5")
        g.press("b")
        self.assertTrue(g.last.startswith("Campo minado médio retomado."))
        g.press("y")
        self.assertIn("Tempo: 3 segundos", g.last)
        g.handlers["quit"]()
        self.assertTrue(os.path.isfile(os.path.join(g.save_dir, "partida.json")))

    def test_win_records_time(self):
        g = self.game
        g.press("b", "b")                         # fácil
        run = self.main["state"]["run"]
        run.board.mines = {(0, 0)}
        run.board.mine_count = 1
        run.elapsed = 42
        g.press("b")
        self.assertTrue(run.over)
        with open(os.path.join(g.save_dir, "progresso.json"), encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["facil"], {"partidas": 1, "vitorias": 1, "melhor": 42})
        self.assertIn("Campo limpo em 42 segundos!", g.said)
        self.assertEqual(g.last, "Campo Minado. Jogar, 1 de 4")
        g.press("down", "down", "b")
        self.assertEqual(g.last, "Fácil: 1 partida, 1 vitória, recorde de 42 segundos. "
                                 "Médio: 0 partidas, 0 vitórias. Difícil: 0 partidas, 0 vitórias.")

    def test_loss_goes_back_to_menu_after_speech(self):
        g = self.game
        g.press("b", "b")
        run = self.main["state"]["run"]
        run.board.mines = {(4, 4)}
        run.board.mine_count = 1
        run.board.opened.add((0, 0))
        g.press("b")
        self.assertTrue(any(t.startswith("Bum!") for t in g.said))
        self.assertEqual(g.said[-2], "Fim de jogo.")
        self.assertEqual(g.last, "Campo Minado. Jogar, 1 de 4")


if __name__ == "__main__":
    unittest.main()
