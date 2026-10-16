import random
import unittest

from helpers import PUZZLE, SOLUTION

from sudoku.grade import LEVELS, Grid, box_of, count_solutions, generate


class SolverTest(unittest.TestCase):
    def test_known_puzzle_has_one_solution(self):
        out = []
        self.assertEqual(count_solutions(PUZZLE, out=out), 1)
        self.assertEqual(out, SOLUTION)

    def test_empty_grid_has_many(self):
        self.assertEqual(count_solutions([0] * 81, limit=2), 2)

    def test_broken_grid_has_none(self):
        bad = list(PUZZLE)
        bad[2] = 5   # dois 5 na primeira linha
        self.assertEqual(count_solutions(bad), 0)


class GenerateTest(unittest.TestCase):
    def test_every_level_is_unique_and_matches_solution(self):
        for level, (_, clues) in LEVELS.items():
            for seed in range(5):
                puzzle, solution = generate(clues, random.Random(seed))
                self.assertEqual(81 - puzzle.count(0), clues, (level, seed))
                self.assertEqual(count_solutions(puzzle), 1)
                self.assertTrue(all(p in (0, s) for p, s in zip(puzzle, solution)))
                self.assertTrue(Grid(solution).solved())

    def test_same_seed_same_puzzle(self):
        self.assertEqual(generate(30, random.Random(3)), generate(30, random.Random(3)))


class GridTest(unittest.TestCase):
    def test_conflicts_and_candidates(self):
        g = Grid(PUZZLE)
        self.assertEqual(g.candidates(0, 2), [1, 2, 4])
        g.set(0, 2, 5)
        self.assertEqual(g.conflicts(0, 2), ["linha", "bloco"])
        self.assertEqual(g.conflict_cells(), {(0, 0), (0, 2)})
        g.set(0, 2, 0)
        self.assertEqual(g.conflicts(0, 2), [])
        with self.assertRaises(ValueError):
            g.set(0, 0, 1)

    def test_box_numbers(self):
        self.assertEqual(box_of(0, 0), 0)
        self.assertEqual(box_of(4, 5), 4)
        self.assertEqual(box_of(8, 6), 8)

    def test_roundtrip_and_validation(self):
        g = Grid(PUZZLE)
        g.set(0, 2, 4)
        again = Grid.from_dict(g.to_dict())
        self.assertEqual(again.values, g.values)
        self.assertEqual(again.givens, g.givens)
        data = g.to_dict()
        data["values"] = "9" + data["values"][1:]   # dica trocada
        with self.assertRaises(ValueError):
            Grid.from_dict(data)
        data = g.to_dict()
        data["givens"] = "0" * 81                  # sem solução única
        data["values"] = "0" * 81
        with self.assertRaises(ValueError):
            Grid.from_dict(data)
        with self.assertRaises(ValueError):
            Grid.from_dict({"givens": "abc", "values": "abc"})


if __name__ == "__main__":
    unittest.main()
