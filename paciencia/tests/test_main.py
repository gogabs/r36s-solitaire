"""O main.py inteiro: menus, nova partida, pausa, salvar e continuar."""
import os
import unittest

import fakegame  # noqa: F401  (ajusta o caminho)
from fakegame import load_main


class MainTest(unittest.TestCase):
    def setUp(self):
        self.game, self.main = load_main()

    def test_menu_and_help(self):
        g = self.game
        self.assertTrue(g.last.startswith("Paciência. Klondike, 1 de 6."))
        g.press("down", "down", "down", "b")
        self.assertTrue(g.last.startswith("Como jogar. Controles"))
        g.press("b")
        self.assertIn("Esquerda e direita", g.last)
        g.press("a")
        self.assertEqual(g.last, "Paciência. Como jogar, 4 de 6")

    def test_new_game_pause_save_and_continue(self):
        g = self.game
        g.press("b")                               # Klondike
        self.assertEqual(g.last, "Klondike. Novo jogo, comprando 1, 1 de 3")
        g.press("down", "b")                       # comprando 3
        self.assertTrue(g.said[-1].startswith("Klondike, comprando 3."))
        g.press("x")
        self.assertTrue(g.last.startswith("Comprou"))
        g.press("y")
        self.assertIn("1 jogada", g.last)
        g.press("start")
        self.assertTrue(g.last.startswith("Pausa. Continuar"))
        g.press("down", "b")
        self.assertTrue(os.path.isfile(os.path.join(g.save_dir, "partida-klondike.json")))
        self.assertEqual(g.last, "Klondike. Continuar partida salva, 1 de 4")
        g.press("b")
        self.assertTrue(g.last.startswith("Klondike, comprando 3 retomado, com 1 jogada."))
        self.assertFalse(os.path.isfile(os.path.join(g.save_dir, "partida-klondike.json")))
        g.handlers["quit"]()                        # fechar no meio guarda
        self.assertTrue(os.path.isfile(os.path.join(g.save_dir, "partida-klondike.json")))

    def test_main_menu_marks_saved_game_and_stats(self):
        g = self.game
        g.press("down", "b", "b")                  # FreeCell, novo jogo
        self.assertTrue(g.last.startswith("FreeCell, jogo"))
        g.press("start", "down", "b", "a")         # salva e volta ao menu principal
        self.assertEqual(g.last, "Paciência. FreeCell, com partida salva, 2 de 6")
        g.press("down", "down", "down", "b")
        self.assertIn("FreeCell: 1 partida, 0 vitórias.", g.last)

    def test_spider_and_quit_without_saving(self):
        g = self.game
        g.press("up", "up", "up", "up", "b")        # dá a volta até Spider
        g.press("down", "down", "b")               # 4 naipes
        self.assertTrue(g.said[-1].startswith("Spider, 4 naipes."))
        g.press("l1", "select", "r2", "a")
        g.press("start", "up", "b")                # Sair sem salvar
        self.assertEqual(g.last, "Spider. Novo jogo, 1 naipe, 1 de 4")
        self.assertFalse(os.path.isfile(os.path.join(g.save_dir, "partida-spider.json")))


if __name__ == "__main__":
    unittest.main()
