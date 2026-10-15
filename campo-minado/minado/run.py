"""Uma partida de Campo Minado: o cursor, cavar, marcar, o tempo e o que é falado.

Não toca som nem fala direto: tudo passa por `ui`, que tem
    ui.say(texto, queue=False)
    ui.play(nome, pan=None, pitch=1.0)
Assim a partida inteira roda nos testes sem áudio.
"""
import random

from .board import LEVELS, NEIGHBORS, Board


def plural(n, word, words=None):
    return "%d %s" % (n, word if n == 1 else (words or word + "s"))


def join(parts):
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + " e " + parts[-1]


def duration(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    if not m:
        return plural(s, "segundo")
    if not s:
        return plural(m, "minuto")
    return "%s e %s" % (plural(m, "minuto"), plural(s, "segundo"))


def state_word(state):
    if state == 0:
        return "vazia"
    return str(state)


class Run:
    SAVE_VERSION = 1

    def __init__(self, ui, level="facil", rng=None, on_over=None):
        if level not in LEVELS:
            raise ValueError("nível desconhecido: %r" % level)
        self.ui = ui
        self.level = level
        self.rng = rng or random.Random()
        self.on_over = on_over
        _, rows, cols, mines = LEVELS[level]
        self.board = Board(rows, cols, mines)
        self.r, self.c = rows // 2, cols // 2
        self.elapsed = 0.0
        self.over = False
        self.won = False

    @property
    def level_name(self):
        return LEVELS[self.level][0]

    def start(self):
        b = self.board
        self.ui.play("inicio")
        self.ui.say("Campo minado %s: %d linhas, %d colunas, %s. A primeira casa cavada nunca "
                    "tem mina. Você está na linha %d, coluna %d." % (
                        self.level_name.lower(), b.rows, b.cols, plural(b.mine_count, "mina"),
                        self.r + 1, self.c + 1))

    # --- tempo -----------------------------------------------------------
    def tick(self, dt):
        """Conta o tempo só depois da primeira escavação e até a partida acabar."""
        if self.board.placed and not self.over:
            self.elapsed += dt

    # --- sons e falas da casa ----------------------------------------------
    def pan(self, c=None):
        c = self.c if c is None else c
        return -0.9 + 1.8 * c / max(1, self.board.cols - 1)

    def play_cell(self, r=None, c=None):
        r = self.r if r is None else r
        c = self.c if c is None else c
        state = self.board.state(r, c)
        name = state if isinstance(state, str) else "num_%d" % state
        # mais agudo em cima, mais grave embaixo
        pitch = 1.15 - 0.3 * r / max(1, self.board.rows - 1)
        self.ui.play(name, pan=self.pan(c), pitch=pitch)

    def cell_word(self, r=None, c=None):
        r = self.r if r is None else r
        c = self.c if c is None else c
        return state_word(self.board.state(r, c))

    def where(self):
        return "linha %d, coluna %d" % (self.r + 1, self.c + 1)

    # --- cursor ------------------------------------------------------------
    def move(self, dr, dc):
        r, c = self.r + dr, self.c + dc
        if not self.board.inside(r, c):
            self.ui.play("borda", pan=self.pan())
            edge = ("linha %d" % (self.r + 1)) if dr else ("coluna %d" % (self.c + 1))
            self.ui.say("Borda, %s: %s." % (edge, self.cell_word()))
            return False
        self.r, self.c = r, c
        self.play_cell()
        self.ui.say("%s, %s." % (self.cell_word(), ("linha %d" % (r + 1)) if dr else ("coluna %d" % (c + 1))))
        return True

    def jump(self, delta):
        """L1 e R1: a casa fechada (sem marca) anterior ou seguinte, lendo como um texto."""
        b = self.board
        total = b.rows * b.cols
        here = self.r * b.cols + self.c
        for k in range(1, total):
            i = (here + delta * k) % total
            cell = divmod(i, b.cols)
            if b.state(*cell) == "fechada":
                self.r, self.c = cell
                self.play_cell()
                self.ui.say("Fechada, %s." % self.where())
                return True
        self.ui.play("erro")
        self.ui.say("Não há outra casa fechada sem marca.")
        return False

    # --- cavar (B) -----------------------------------------------------------
    def dig(self):
        if self.over:
            return False
        b = self.board
        cell = (self.r, self.c)
        if cell in b.flags:
            return self._refuse("Casa marcada. Tire a marca com A antes de cavar.")
        if not b.placed:
            b.place(self.rng, cell)
        state = b.state(*cell)
        if state == "fechada":
            if cell in b.mines:
                self.explode(cell)
                return True
            self._opened(b.open(*cell))
            return True
        return self.chord(state)

    def chord(self, number):
        """B numa casa aberta: se as marcas em volta batem com o número, abre o resto."""
        b = self.board
        around = b.neighbors(self.r, self.c)
        closed = [x for x in around if b.state(*x) == "fechada"]
        flagged = sum(1 for x in around if x in b.flags)
        if number == 0 or not closed:
            return self._refuse("%s; não há nada fechado em volta." % state_word(number).capitalize())
        if flagged != number:
            return self._refuse("%s em volta, %s." % (
                plural(number, "mina"), plural(flagged, "marcada")))
        for x in closed:
            if x in b.mines:
                self.explode(x)
                return True
        new = []
        for x in closed:
            new += b.open(*x)
        self._opened(new, chord=True)
        return True

    def _opened(self, new, chord=False):
        b = self.board
        if len(new) > 1:
            self.ui.play("abrir_muitas", pan=self.pan())
            text = "Abriu %s. Aqui, %s." % (plural(len(new), "casa"), self.cell_word())
        else:
            self.ui.play("cavar", pan=self.pan())
            self.play_cell()
            text = "%s." % self.cell_word().capitalize()
            if chord:
                r, c = new[0]
                text = "Abriu linha %d, coluna %d: %s." % (r + 1, c + 1, self.cell_word(r, c))
        if b.cleared():
            self.ui.say(text)
            self.finish(True)
            return
        self.ui.say(text)

    def explode(self, cell):
        self.r, self.c = cell
        self.ui.play("explosao", pan=self.pan())
        b = self.board
        self.ui.say("Bum! Mina na %s. Você abriu %d de %d casas, em %s." % (
            self.where(), len(b.opened), b.safe_cells(), duration(self.elapsed)))
        self.finish(False)

    # --- marcar (A) --------------------------------------------------------------
    def flag(self):
        if self.over:
            return False
        b = self.board
        if (self.r, self.c) in b.opened:
            return self._refuse("Casa já aberta: %s." % self.cell_word())
        marked = b.toggle_flag(self.r, self.c)
        self.ui.play("marcar" if marked else "desmarcar", pan=self.pan())
        left = b.mine_count - len(b.flags)
        if marked:
            self.ui.say("Marcada. %s." % self.mines_left_text(left))
        else:
            self.ui.say("Desmarcada. %s." % self.mines_left_text(left))
        return True

    def mines_left_text(self, left=None):
        b = self.board
        left = b.mine_count - len(b.flags) if left is None else left
        if left < 0:
            return "%s a mais que as minas" % plural(-left, "marca")
        return "Falta%s %s" % ("" if left == 1 else "m", plural(left, "mina"))

    # --- informação (Y, X, Select, R2) -------------------------------------------
    def status_text(self):
        b = self.board
        return "%s, de %d. %d de %d casas abertas. Tempo: %s. Nível %s." % (
            self.mines_left_text(), b.mine_count, len(b.opened), b.safe_cells(),
            duration(self.elapsed), self.level_name.lower())

    def around_text(self):
        """X: a casa e as oito em volta, juntando as do mesmo jeito."""
        b = self.board
        groups = {}
        order = []
        for (dr, dc), name in NEIGHBORS:
            r, c = self.r + dr, self.c + dc
            if not b.inside(r, c):
                continue
            word = state_word(b.state(r, c))
            if word not in groups:
                groups[word] = []
                order.append(word)
            groups[word].append(name)
        parts = []
        for word in order:
            places = groups[word]
            if word in ("fechada", "marcada", "vazia"):
                label = plural(len(places), word)
            else:
                label = word
            parts.append("%s: %s" % (label, join(places)))
        return "%s: %s. Em volta: %s." % (cap(self.where()), self.cell_word(), "; ".join(parts))

    def line_text(self, cells, label):
        """Uma linha ou coluna inteira, juntando casas iguais seguidas."""
        items = []
        last, count = None, 0
        for cell in cells + [None]:
            word = self.cell_word(*cell) if cell else None
            if word == last:
                count += 1
                continue
            if last is not None:
                if count == 1:
                    items.append(last)
                elif last in ("fechada", "marcada", "vazia"):
                    items.append(plural(count, last))
                else:
                    items.append("%d vezes %s" % (count, last))
            last, count = word, 1
        return "%s: %s." % (label, ", ".join(items))

    def row_text(self):
        return self.line_text([(self.r, c) for c in range(self.board.cols)], "Linha %d" % (self.r + 1))

    def column_text(self):
        return self.line_text([(r, self.c) for r in range(self.board.rows)], "Coluna %d" % (self.c + 1))

    # --- fim -----------------------------------------------------------------
    def finish(self, won):
        self.over = True
        self.won = won
        b = self.board
        if won:
            b.flags = set(b.mines)
            self.ui.play("vitoria")
        if self.on_over:
            self.on_over({"level": self.level, "won": won, "time": self.elapsed,
                          "opened": len(b.opened), "safe": b.safe_cells()})

    def _refuse(self, why):
        self.ui.play("erro")
        self.ui.say(why)
        return False

    # --- partida salva -----------------------------------------------------
    def to_dict(self):
        return {"versao": self.SAVE_VERSION, "level": self.level, "board": self.board.to_dict(),
                "cursor": [self.r, self.c], "elapsed": self.elapsed}

    @classmethod
    def from_dict(cls, ui, data, on_over=None):
        """Recria a partida salva por to_dict. ValueError se o arquivo não serve."""
        try:
            if data["versao"] != cls.SAVE_VERSION:
                raise ValueError("versão de save desconhecida")
            run = cls(ui, level=data["level"], on_over=on_over)
            board = Board.from_dict(data["board"])
            if (board.rows, board.cols, board.mine_count) != LEVELS[run.level][1:]:
                raise ValueError("grade não confere com o nível")
            run.board = board
            run.r, run.c = int(data["cursor"][0]), int(data["cursor"][1])
            if not board.inside(run.r, run.c):
                raise ValueError("cursor fora da grade")
            run.elapsed = float(data["elapsed"])
        except (KeyError, TypeError, IndexError) as exc:
            raise ValueError("partida salva incompleta: %s" % exc)
        return run

    def resume(self):
        self.ui.play("inicio")
        self.play_cell()
        self.ui.say("Campo minado %s retomado. %s. %s, %s." % (
            self.level_name.lower(), self.mines_left_text(), cap(self.where()), self.cell_word()))


def cap(text):
    return text[:1].upper() + text[1:]
