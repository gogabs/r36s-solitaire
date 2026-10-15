import random
import unittest

import helpers  # noqa: F401

from minado.board import Board


class BoardTest(unittest.TestCase):
    def test_first_dig_is_safe_with_room(self):
        for seed in range(30):
            b = Board(9, 9, 10)
            b.place(random.Random(seed), (4, 4))
            self.assertEqual(len(b.mines), 10)
            self.assertFalse(b.mines & ({(4, 4)} | set(b.neighbors(4, 4))))
            self.assertEqual(b.count(4, 4), 0)

    def test_crowded_board_still_keeps_first_cell(self):
        b = Board(3, 3, 7)
        b.place(random.Random(1), (0, 0))
        self.assertNotIn((0, 0), b.mines)
        self.assertEqual(len(b.mines), 7)

    def test_flood_fill_stops_at_numbers(self):
        b = Board(3, 4, 1)
        b.mines = {(0, 3)}
        opened = b.open(2, 0)
        self.assertEqual(len(opened), 11)
        self.assertNotIn((0, 3), b.opened)
        self.assertEqual(b.state(0, 2), 1)
        self.assertTrue(b.cleared())

    def test_flood_fill_skips_flags(self):
        b = Board(1, 5, 1)
        b.mines = {(0, 4)}
        b.toggle_flag(0, 1)
        b.open(0, 0)
        self.assertEqual(b.opened, {(0, 0)})

    def test_roundtrip_and_validation(self):
        b = Board(9, 9, 10)
        b.place(random.Random(2), (0, 0))
        b.open(0, 0)
        b.toggle_flag(*sorted(b.mines)[0])
        again = Board.from_dict(b.to_dict())
        self.assertEqual(again.to_dict(), b.to_dict())
        data = b.to_dict()
        data["opened"].append(list(sorted(b.mines)[0]))
        with self.assertRaises(ValueError):
            Board.from_dict(data)
        data = b.to_dict()
        data["flags"] = [[9, 0]]
        with self.assertRaises(ValueError):
            Board.from_dict(data)


if __name__ == "__main__":
    unittest.main()
