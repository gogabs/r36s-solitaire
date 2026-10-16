"""Uma partida de Sudoku: o cursor, escrever os números, o tempo e o que é falado.

Não toca som nem fala direto: tudo passa por `ui`, que tem
    ui.say(texto, queue=False)
    ui.play(nome, pan=None, pitch=1.0)
Assim a partida inteira roda nos testes sem áudio.
"""
import random

from .grade import LEVELS, Grid, box_cells, box_of, col_cells, generate, row_cells


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


def cap(text):
    return text[:1].upper() + text[1:]


def complete_word(units):
    """ "linha 3" completa, "bloco 5" completo, "linha 3 e bloco 5" completos."""
    masculine = any(u.startswith("bloco") for u in units)
    return ("completo" if masculine else "completa") + ("s" if len(units) > 1 else "")


# onde o número repete, como é falado
PLACES = {"linha": "na linha", "coluna": "na coluna", "bloco": "no bloco"}


class Run:
    SAVE_VERSION = 1

    def __init__(self, ui, level="facil", rng=None, on_over=None, grid=None):
        if level not in LEVELS:
            raise ValueError("nível desconhecido: %r" % level)
        self.ui = ui
        self.level = level
        self.on_over = on_over
        if grid is None:
            givens, _ = generate(LEVELS[level][1], rng or random.Random())
            grid = Grid(givens)
        self.grid = grid
        self.r, self.c = 4, 4
        self.elapsed = 0.0
        self.over = False
        self.won = False

    @property
    def level_name(self):
        return LEVELS[self.level][0]

    def start(self):
        g = self.grid
        self.ui.play("inicio")
        self.ui.say("Sudoku %s: %s, %s para preencher. Você está na linha 5, coluna 5: %s." % (
            self.level_name.lower(), plural(81 - g.to_fill(), "dica"),
            plural(g.to_fill(), "casa"), self.cell_word()))

    # --- tempo -----------------------------------------------------------
    def tick(self, dt):
        if not self.over:
            self.elapsed += dt

    # --- sons e falas da casa ----------------------------------------------
    def pan(self, c=None):
        c = self.c if c is None else c
        return -0.9 + 1.8 * c / 8.0

    def play_cell(self, r=None, c=None):
        r = self.r if r is None else r
        c = self.c if c is None else c
        v = self.grid.get(r, c)
        if not v:
            name = "vazia"
        else:
            name = ("fixo_%d" if self.grid.fixed(r, c) else "num_%d") % v
        self.ui.play(name, pan=self.pan(c))

    def cell_word(self, r=None, c=None, detail=True):
        """ "vazia", "5" ou, com detail, "5 fixo" para as dicas."""
        r = self.r if r is None else r
        c = self.c if c is None else c
        v = self.grid.get(r, c)
        if not v:
            return "vazia"
        if detail and self.grid.fixed(r, c):
            return "%d fixo" % v
        return str(v)

    def where(self):
        return "linha %d, coluna %d" % (self.r + 1, self.c + 1)

    def box_name(self, b=None):
        b = box_of(self.r, self.c) if b is None else b
        return "bloco %d" % (b + 1)

    # --- cursor ------------------------------------------------------------
    def move(self, dr, dc):
        r, c = self.r + dr, self.c + dc
        if not (0 <= r < 9 and 0 <= c < 9):
            self.ui.play("borda", pan=self.pan())
            edge = ("linha %d" % (self.r + 1)) if dr else ("coluna %d" % (self.c + 1))
            self.ui.say("Borda, %s: %s." % (edge, self.cell_word()))
            return False
        old_box = box_of(self.r, self.c)
        self.r, self.c = r, c
        self.play_cell()
        text = "%s, %s" % (self.cell_word(), ("linha %d" % (r + 1)) if dr else ("coluna %d" % (c + 1)))
        if box_of(r, c) != old_box:
            text += ", %s" % self.box_name()
        self.ui.say(text + ".")
        return True

    def jump(self, delta):
        """L1 e R1: a casa vazia anterior ou seguinte, lendo como um texto."""
        here = self.r * 9 + self.c
        for k in range(1, 81):
            i = (here + delta * k) % 81
            r, c = divmod(i, 9)
            if not self.grid.get(r, c):
                self.r, self.c = r, c
                self.play_cell()
                self.ui.say("Vazia, %s." % self.where())
                return True
        self.ui.play("erro")
        self.ui.say("Não há outra casa vazia.")
        return False

    # --- escrever (B sobe, A desce) --------------------------------------------
    def step(self, delta):
        """Troca o número da casa: vazia, 1, 2... 9 e volta para vazia (B), ou ao
        contrário (A). Fala o número e onde ele repete, se repetir."""
        if self.over:
            return False
        g = self.grid
        if g.fixed(self.r, self.c):
            return self._refuse("%s: é uma dica, não muda." % self.cell_word())
        v = (g.get(self.r, self.c) + delta) % 10
        g.set(self.r, self.c, v)
        if not v:
            self.ui.play("apagar", pan=self.pan())
            self.ui.say("Vazia.")
            return True
        self.play_cell()
        clash = g.conflicts(self.r, self.c)
        if clash:
            self.ui.play("conflito", pan=self.pan())
            self.ui.say("%d, repete %s." % (v, join([PLACES[x] for x in clash])))
            return True
        done = self.completed_units()
        if 0 not in g.values and g.solved():
            self.ui.say("%d." % v)
            self.finish(True)
            return True
        if done:
            self.ui.play("completo", pan=self.pan())
            self.ui.say("%d. %s %s." % (v, cap(join(done)), complete_word(done)))
            return True
        if 0 not in g.values:
            self.ui.say("%d. Grade cheia, mas %s." % (v, self.conflicts_text()))
            return True
        self.ui.say("%d." % v)
        return True

    def completed_units(self):
        """Linha, coluna e bloco da casa que ficaram com 1 a 9."""
        g = self.grid
        out = []
        if g.unit_complete(row_cells(self.r)):
            out.append("linha %d" % (self.r + 1))
        if g.unit_complete(col_cells(self.c)):
            out.append("coluna %d" % (self.c + 1))
        b = box_of(self.r, self.c)
        if g.unit_complete(box_cells(b)):
            out.append(self.box_name(b))
        return out

    # --- informação (Y, X, Select, R2, L2) -----------------------------------------
    def conflicts_text(self):
        n = len(self.grid.conflict_cells())
        if not n:
            return "nenhuma casa repetida"
        return "%s com número repetido" % plural(n, "casa")

    def status_text(self):
        g = self.grid
        left = g.empty_count()
        text = "Falta%s %s, de %d. " % ("" if left == 1 else "m", plural(left, "casa"), g.to_fill())
        n = len(g.conflict_cells())
        if n:
            text += "%s. " % cap(self.conflicts_text())
        return text + "Tempo: %s. Nível %s." % (duration(self.elapsed), self.level_name.lower())

    def candidates_text(self):
        """X: os números que cabem nesta casa, olhando a linha, a coluna e o bloco."""
        g = self.grid
        here = "%s, %s" % (cap(self.where()), self.box_name())
        if g.fixed(self.r, self.c):
            return "%s: %s." % (here, self.cell_word())
        options = g.candidates(self.r, self.c)
        if not options:
            fits = "nenhum número cabe aqui sem repetir"
        elif len(options) == 1:
            fits = "só cabe o %d" % options[0]
        else:
            fits = "cabem %s" % join([str(d) for d in options])
        return "%s: %s; %s." % (here, self.cell_word(), fits)

    def unit_text(self, cells, label):
        """Uma linha, coluna ou bloco inteiro, juntando as vazias seguidas."""
        items = []
        blanks = 0
        for cell in cells + [None]:
            if cell is not None and not self.grid.get(*cell):
                blanks += 1
                continue
            if blanks:
                items.append("vazia" if blanks == 1 else plural(blanks, "vazia"))
                blanks = 0
            if cell is not None:
                items.append(self.cell_word(*cell, detail=False))
        missing = [d for d in range(1, 10) if d not in [self.grid.get(*x) for x in cells]]
        text = "%s: %s." % (label, ", ".join(items))
        if len(missing) == 1:
            text += " Falta o %d." % missing[0]
        elif 1 < len(missing) < 9:
            text += " Faltam: %s." % join([str(d) for d in missing])
        return text

    def row_text(self):
        return self.unit_text(row_cells(self.r), "Linha %d" % (self.r + 1))

    def column_text(self):
        return self.unit_text(col_cells(self.c), "Coluna %d" % (self.c + 1))

    def box_text(self):
        b = box_of(self.r, self.c)
        return self.unit_text(box_cells(b), cap(self.box_name(b)))

    # --- fim -----------------------------------------------------------------
    def finish(self, won):
        self.over = True
        self.won = won
        if won:
            self.ui.play("vitoria")
        if self.on_over:
            self.on_over({"level": self.level, "won": won, "time": self.elapsed})

    def _refuse(self, why):
        self.ui.play("erro")
        self.ui.say(why)
        return False

    # --- partida salva -----------------------------------------------------
    def to_dict(self):
        return {"versao": self.SAVE_VERSION, "level": self.level, "grid": self.grid.to_dict(),
                "cursor": [self.r, self.c], "elapsed": self.elapsed}

    @classmethod
    def from_dict(cls, ui, data, on_over=None):
        """Recria a partida salva por to_dict. ValueError se o arquivo não serve."""
        try:
            if data["versao"] != cls.SAVE_VERSION:
                raise ValueError("versão de save desconhecida")
            if data["level"] not in LEVELS:
                raise ValueError("nível desconhecido")
            run = cls(ui, level=data["level"], on_over=on_over, grid=Grid.from_dict(data["grid"]))
            run.r, run.c = int(data["cursor"][0]), int(data["cursor"][1])
            if not (0 <= run.r < 9 and 0 <= run.c < 9):
                raise ValueError("cursor fora da grade")
            run.elapsed = float(data["elapsed"])
        except (KeyError, TypeError, IndexError) as exc:
            raise ValueError("partida salva incompleta: %s" % exc)
        return run

    def resume(self):
        self.ui.play("inicio")
        self.play_cell()
        left = self.grid.empty_count()
        self.ui.say("Sudoku %s retomado. Falta%s %s. %s, %s." % (
            self.level_name.lower(), "" if left == 1 else "m", plural(left, "casa"),
            cap(self.where()), self.cell_word()))
