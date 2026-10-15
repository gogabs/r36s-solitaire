"""A grade do Campo Minado: minas, casas abertas e marcas. Sem som nem fala."""

LEVELS = {
    "facil": ("Fácil", 9, 9, 10),
    "medio": ("Médio", 16, 16, 40),
    "dificil": ("Difícil", 16, 30, 99),
}
LEVEL_ORDER = ("facil", "medio", "dificil")

# (linha, coluna) relativos, com o nome falado, em sentido horário a partir de cima
NEIGHBORS = [((-1, 0), "acima"), ((-1, 1), "acima à direita"), ((0, 1), "à direita"),
             ((1, 1), "abaixo à direita"), ((1, 0), "abaixo"), ((1, -1), "abaixo à esquerda"),
             ((0, -1), "à esquerda"), ((-1, -1), "acima à esquerda")]


class Board:
    def __init__(self, rows, cols, mines):
        if not 0 < mines < rows * cols:
            raise ValueError("número de minas impossível")
        self.rows, self.cols, self.mine_count = rows, cols, mines
        self.mines = set()      # vazio até a primeira escavação
        self.opened = set()
        self.flags = set()

    @property
    def placed(self):
        return bool(self.mines)

    def inside(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def neighbors(self, r, c):
        return [(r + dr, c + dc) for (dr, dc), _ in NEIGHBORS if self.inside(r + dr, c + dc)]

    def place(self, rng, safe):
        """Sorteia as minas longe da primeira casa cavada (e das vizinhas, se couber)."""
        cells = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        keep = {safe} | set(self.neighbors(*safe))
        pool = [x for x in cells if x not in keep]
        if len(pool) < self.mine_count:
            pool = [x for x in cells if x != safe]
        self.mines = set(rng.sample(pool, self.mine_count))

    def count(self, r, c):
        return sum(1 for x in self.neighbors(r, c) if x in self.mines)

    def open(self, r, c):
        """Abre a casa; se for vazia (0), abre em volta até chegar nos números.
        Devolve as casas abertas agora. Não confere mina: quem chama confere."""
        if (r, c) in self.opened or (r, c) in self.flags:
            return []
        new = []
        stack = [(r, c)]
        while stack:
            cell = stack.pop()
            if cell in self.opened or cell in self.flags or cell in self.mines:
                continue
            self.opened.add(cell)
            new.append(cell)
            if self.count(*cell) == 0:
                stack.extend(x for x in self.neighbors(*cell) if x not in self.opened)
        return new

    def toggle_flag(self, r, c):
        if (r, c) in self.flags:
            self.flags.discard((r, c))
            return False
        self.flags.add((r, c))
        return True

    def safe_cells(self):
        return self.rows * self.cols - self.mine_count

    def cleared(self):
        return self.placed and len(self.opened) == self.safe_cells()

    def state(self, r, c):
        """ "fechada", "marcada", ou o número de minas em volta (0 a 8)."""
        if (r, c) in self.opened:
            return self.count(r, c)
        return "marcada" if (r, c) in self.flags else "fechada"

    def to_dict(self):
        return {"rows": self.rows, "cols": self.cols, "mine_count": self.mine_count,
                "mines": sorted(self.mines), "opened": sorted(self.opened), "flags": sorted(self.flags)}

    @classmethod
    def from_dict(cls, data):
        board = cls(int(data["rows"]), int(data["cols"]), int(data["mine_count"]))
        cells = lambda key: {(int(r), int(c)) for r, c in data[key]}  # noqa: E731
        board.mines, board.opened, board.flags = cells("mines"), cells("opened"), cells("flags")
        if board.mines and len(board.mines) != board.mine_count:
            raise ValueError("número de minas não confere")
        for cell in board.mines | board.opened | board.flags:
            if not board.inside(*cell):
                raise ValueError("casa fora da grade")
        if board.mines & board.opened:
            raise ValueError("mina aberta numa partida salva")
        return board
