"""A grade do Sudoku: as dicas, os números do jogador, as regras e o gerador.
Sem som nem fala.

Casas numeradas de 0 a 80, linha por linha; 0 é casa vazia.
"""
import random

LEVELS = {   # nome, quantas dicas
    "facil": ("Fácil", 40),
    "medio": ("Médio", 32),
    "dificil": ("Difícil", 26),
}
LEVEL_ORDER = ("facil", "medio", "dificil")
ALL = 0x3FE   # bits 1 a 9


def box_of(r, c):
    """O bloco 3 por 3 da casa, de 0 a 8, lendo como um texto."""
    return (r // 3) * 3 + c // 3


def row_cells(r):
    return [(r, c) for c in range(9)]


def col_cells(c):
    return [(r, c) for r in range(9)]


def box_cells(b):
    r0, c0 = (b // 3) * 3, (b % 3) * 3
    return [(r0 + i, c0 + j) for i in range(3) for j in range(3)]


def digits(mask):
    return [d for d in range(1, 10) if mask >> d & 1]


# --- resolver ------------------------------------------------------------------
def count_solutions(values, limit=2, rng=None, out=None):
    """Conta as soluções da grade (lista de 81), até `limit`. Com `rng`, tenta os
    números em ordem sorteada; com `out`, guarda nela a primeira solução."""
    cells = list(values)
    rows, cols, boxes = [0] * 9, [0] * 9, [0] * 9
    empty = []
    for i, v in enumerate(cells):
        r, c = divmod(i, 9)
        if v:
            bit = 1 << v
            b = box_of(r, c)
            if (rows[r] | cols[c] | boxes[b]) & bit:
                return 0
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
        else:
            empty.append(i)
    found = [0]

    def solve(left):
        if not left:
            found[0] += 1
            if out is not None and found[0] == 1:
                out[:] = cells
            return found[0] >= limit
        # a casa com menos opções primeiro
        best, best_mask, best_n = -1, 0, 10
        for k, i in enumerate(left):
            r, c = divmod(i, 9)
            mask = ALL & ~(rows[r] | cols[c] | boxes[box_of(r, c)])
            n = bin(mask).count("1")
            if n < best_n:
                best, best_mask, best_n = k, mask, n
                if n <= 1:
                    break
        if best_n == 0:
            return False
        i = left[best]
        rest = left[:best] + left[best + 1:]
        r, c = divmod(i, 9)
        b = box_of(r, c)
        options = digits(best_mask)
        if rng is not None:
            rng.shuffle(options)
        for d in options:
            bit = 1 << d
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
            cells[i] = d
            stop = solve(rest)
            rows[r] &= ~bit
            cols[c] &= ~bit
            boxes[b] &= ~bit
            cells[i] = 0
            if stop:
                return True
        return False

    solve(empty)
    return found[0]


def generate(clues, rng=None):
    """(dicas, solução): uma grade com solução única e `clues` dicas (ou um
    pouco mais, se tirar mais deixaria duas soluções)."""
    rng = rng or random.Random()
    solution = [0] * 81
    count_solutions([0] * 81, limit=1, rng=rng, out=solution)
    puzzle = list(solution)
    order = list(range(81))
    rng.shuffle(order)
    filled = 81
    for i in order:
        if filled <= clues:
            break
        keep = puzzle[i]
        puzzle[i] = 0
        if count_solutions(puzzle, limit=2) != 1:
            puzzle[i] = keep
        else:
            filled -= 1
    return puzzle, solution


# --- a grade de uma partida --------------------------------------------------------
class Grid:
    def __init__(self, givens):
        if len(givens) != 81:
            raise ValueError("a grade tem 81 casas")
        self.givens = [int(v) for v in givens]
        self.values = list(self.givens)
        for v in self.values:
            if not 0 <= v <= 9:
                raise ValueError("número fora de 0 a 9")

    def get(self, r, c):
        return self.values[r * 9 + c]

    def fixed(self, r, c):
        return self.givens[r * 9 + c] != 0

    def set(self, r, c, v):
        if self.fixed(r, c):
            raise ValueError("casa fixa")
        self.values[r * 9 + c] = v

    def empty_count(self):
        return self.values.count(0)

    def to_fill(self):
        return self.givens.count(0)

    def conflicts(self, r, c):
        """Onde o número da casa se repete: uma lista com "linha", "coluna" e "bloco"."""
        v = self.get(r, c)
        if not v:
            return []
        out = []
        for name, cells in (("linha", row_cells(r)), ("coluna", col_cells(c)),
                            ("bloco", box_cells(box_of(r, c)))):
            if any(self.get(*x) == v for x in cells if x != (r, c)):
                out.append(name)
        return out

    def conflict_cells(self):
        return {(r, c) for r in range(9) for c in range(9) if self.conflicts(r, c)}

    def candidates(self, r, c):
        """Os números que cabem na casa sem repetir (ignorando o que ela já tem)."""
        used = set()
        for x in row_cells(r) + col_cells(c) + box_cells(box_of(r, c)):
            if x != (r, c):
                used.add(self.get(*x))
        return [d for d in range(1, 10) if d not in used]

    def unit_complete(self, cells):
        return sorted(self.get(*x) for x in cells) == list(range(1, 10))

    def solved(self):
        return 0 not in self.values and not self.conflict_cells()

    def to_dict(self):
        return {"givens": "".join(map(str, self.givens)), "values": "".join(map(str, self.values))}

    @classmethod
    def from_dict(cls, data):
        givens, values = str(data["givens"]), str(data["values"])
        if len(givens) != 81 or len(values) != 81 or not (givens + values).isdigit():
            raise ValueError("grade salva com defeito")
        grid = cls([int(ch) for ch in givens])
        for i, ch in enumerate(values):
            v = int(ch)
            if grid.givens[i] and v != grid.givens[i]:
                raise ValueError("dica alterada numa partida salva")
            grid.values[i] = v
        if count_solutions(grid.givens, limit=2) != 1:
            raise ValueError("as dicas não têm solução única")
        return grid
