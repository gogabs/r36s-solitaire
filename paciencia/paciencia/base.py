"""O que Klondike, FreeCell e Spider têm em comum: pilhas, foco, pegar e soltar,
desfazer, dica, leitura da mesa e partida salva.

Não toca som nem fala direto: tudo passa por `ui`, que tem
    ui.say(texto, queue=False)
    ui.play(nome, pan=None, pitch=1.0)
Assim a partida inteira roda nos testes sem áudio.

Cada jogo é uma subclasse que monta as pilhas (`setup`), dá as cartas (`deal`)
e diz o que pode ser pego (`can_pick`) e onde pode ser solto (`can_drop`).
"""
import random

from .cards import Card, cap, join, plural

ESTOQUE, DESCARTE, FUNDACAO, CELULA, COLUNA = "estoque", "descarte", "fundacao", "celula", "coluna"
MAX_UNDO = 300


class Pile:
    def __init__(self, kind, name, feminine=True, suit=None):
        self.kind = kind
        self.name = name            # "Coluna 3", "Fundação de copas", "Descarte"
        self.feminine = feminine
        self.suit = suit
        self.cards = []

    @property
    def top(self):
        return self.cards[-1] if self.cards else None

    def first_up(self):
        for i, c in enumerate(self.cards):
            if c.up:
                return i
        return len(self.cards)

    def down_count(self):
        return self.first_up()

    @property
    def lower(self):
        return self.name[0].lower() + self.name[1:]

    def at(self):
        """ "na coluna 3", "no descarte"."""
        return ("na " if self.feminine else "no ") + self.lower

    def of(self):
        """ "da coluna 3", "do descarte"."""
        return ("da " if self.feminine else "do ") + self.lower

    def to(self):
        """ "para a coluna 3", "para o descarte"."""
        return ("para a " if self.feminine else "para o ") + self.lower

    def suit_name(self):
        """ "copas", para a fundação de copas."""
        return self.name.split(" ", 2)[-1]


def the(card):
    """ "a dama de copas", "o 7 de paus"."""
    return ("a " if card.rank == 12 else "o ") + card.name


def cards_text(cards):
    """ "dama de copas" ou "dama de copas e mais 2 cartas, até o 10 de paus"."""
    if len(cards) == 1:
        return cards[0].name
    return "%s e mais %s, até %s" % (cards[0].name, plural(len(cards) - 1, "carta"), the(cards[-1]))


class Solitaire:
    ID = ""
    NAME = ""
    STOPS = (ESTOQUE, DESCARTE, FUNDACAO, CELULA, COLUNA)   # pilhas por onde o foco passa
    NO_DRAW = "Este jogo não tem compra."
    SAVE_VERSION = 1

    def __init__(self, ui, rng=None, on_over=None, **options):
        self.ui = ui
        self.rng = rng or random.Random()
        self.on_over = on_over
        self.options = options
        self.piles = []
        self.score = 0
        self.moves = 0
        self.pos = 0          # índice em self.stops
        self.depth = 0        # carta em foco dentro de uma coluna
        self.held = None      # (pilha, índice da carta) que está na mão
        self.history = []     # (estado, descrição) antes de cada jogada
        self.last_move = None  # (de, para, quantas cartas), para a dica não mandar voltar
        self.over = False
        self.won = False
        self.setup()
        self.stops = [i for i, p in enumerate(self.piles) if p.kind in self.STOPS]

    # --- o que cada jogo define ---------------------------------------------
    def setup(self):
        raise NotImplementedError

    def deal(self):
        raise NotImplementedError

    def can_pick(self, pile, index):
        """(True, None) ou (False, motivo falado)."""
        raise NotImplementedError

    def can_drop(self, src, cards, dst):
        raise NotImplementedError

    def is_won(self):
        raise NotImplementedError

    def status_text(self):
        raise NotImplementedError

    def intro_text(self):
        return ""

    def draw(self):
        self.ui.play("erro")
        self.ui.say(self.NO_DRAW)
        return False

    def after_move(self, src, dst, cards, flipped):
        """Pontos e regras depois de uma jogada; devolve frases a anunciar."""
        return []

    def extra_state(self):
        return {}

    def load_extra(self, data):
        pass

    def no_hint_text(self):
        return "Não achei jogada que ajude. Desfaça com A."

    # --- pilhas -----------------------------------------------------------------
    def kind(self, kind):
        return [p for p in self.piles if p.kind == kind]

    @property
    def pile(self):
        return self.piles[self.stops[self.pos]]

    def pan(self, pile_index):
        """Da esquerda (-0,9) para a direita (0,9), pela ordem das paradas."""
        stops = self.stops
        k = stops.index(pile_index) if pile_index in stops else 0
        return -0.9 + 1.8 * k / max(1, len(stops) - 1)

    def focus_index(self):
        p = self.pile
        if not p.cards:
            return None
        if p.kind == COLUNA:
            return max(p.first_up(), min(self.depth, len(p.cards) - 1))
        return len(p.cards) - 1

    def held_cards(self):
        if self.held is None:
            return []
        pi, ci = self.held
        return self.piles[pi].cards[ci:]

    # --- falas ------------------------------------------------------------------
    def describe(self, p):
        """Primeiro as cartas, depois o lugar: "8 de espadas, 2 abertas e 2 viradas, coluna 1"."""
        if p.kind == ESTOQUE:
            return ("%s %s" % (plural(len(p.cards), "carta"), p.at())) if p.cards else p.name + " vazio"
        if not p.cards:
            return "%s %s" % (p.name, "vazia" if p.feminine else "vazio")
        text = p.top.name
        if p.kind == COLUNA:
            up = len(p.cards) - p.first_up()
            if p.down_count():
                if up > 1:
                    text += ", %d abertas e %s" % (up, plural(p.down_count(), "virada"))
                else:
                    text += ", %s" % plural(p.down_count(), "virada")
            elif up > 1:
                text += ", %d cartas" % up
        elif p.kind == DESCARTE and len(p.cards) > 1:
            text += ", %s" % plural(len(p.cards), "carta")
        return "%s, %s" % (cap(text), p.lower)

    def announce_pile(self, prefix=""):
        p = self.pile
        text = prefix + self.describe(p)
        if self.held is not None and self.stops[self.pos] != self.held[0]:
            src = self.piles[self.held[0]]
            if self.can_drop(src, self.held_cards(), p)[0]:
                text += ". Cabe"
                self.ui.play("cabe", pan=self.pan(self.stops[self.pos]))
        self.ui.say(text + ".")

    # --- navegação ------------------------------------------------------------
    def step(self, delta):
        """Esquerda e direita: a pilha anterior ou a seguinte, dando a volta."""
        n = len(self.stops)
        new = self.pos + delta
        wrapped = not 0 <= new < n
        self.pos = new % n
        self.depth = len(self.pile.cards) - 1
        self.ui.play("borda" if wrapped else "mover", pan=self.pan(self.stops[self.pos]))
        self.announce_pile()

    def card_step(self, delta):
        """Cima (-1) e baixo (+1): a carta de baixo ou a de cima dentro da coluna."""
        p = self.pile
        pan = self.pan(self.stops[self.pos])
        if p.kind != COLUNA or not p.cards:
            self.ui.play("borda", pan=pan)
            self.ui.say(self.describe(p) + ".")
            return
        i = self.focus_index()
        new = i + delta
        first = p.first_up()
        up = len(p.cards) - first
        if new < first:
            self.ui.play("borda", pan=pan)
            text = "Primeira aberta: %s" % p.cards[i].name
            if p.down_count():
                text += ", com %s embaixo" % plural(p.down_count(), "virada")
            self.ui.say(text + ".")
            return
        if new >= len(p.cards):
            self.ui.play("borda", pan=pan)
            self.ui.say("Carta de cima: %s." % p.cards[i].name)
            return
        self.depth = new
        self.ui.play("carta", pan=pan, pitch=1.0 + 0.05 * (new - first))
        self.ui.say("%s, %d de %d." % (p.cards[new].name, new - first + 1, up))

    def go_to(self, pile_index, card_index=None):
        if pile_index in self.stops:
            self.pos = self.stops.index(pile_index)
        p = self.piles[pile_index]
        self.depth = len(p.cards) - 1 if card_index is None else card_index

    # --- pegar e soltar ---------------------------------------------------------
    def press(self):
        """B: pega a carta em foco, ou solta o que está na mão aqui."""
        if self.held is None:
            return self.pick()
        return self.drop(self.stops[self.pos])

    def pick(self):
        p = self.pile
        pi = self.stops[self.pos]
        if p.kind == ESTOQUE:
            return self.draw()
        if not p.cards:
            return self._refuse("%s está %s." % (p.name, "vazia" if p.feminine else "vazio"))
        ci = self.focus_index()
        ok, why = self.can_pick(p, ci)
        if not ok:
            return self._refuse(why)
        self.held = (pi, ci)
        self.ui.play("pegar", pan=self.pan(pi))
        self.ui.say("Pegou %s." % cards_text(p.cards[ci:]))
        return True

    def cancel(self):
        if self.held is None:
            return False
        pi = self.held[0]
        self.held = None
        self.ui.play("soltar", pan=self.pan(pi))
        self.ui.say("Devolveu %s." % self.piles[pi].to())
        return True

    def drop(self, target):
        si, ci = self.held
        if target == si:
            return self.cancel()
        src, dst = self.piles[si], self.piles[target]
        cards = src.cards[ci:]
        ok, why = self.can_drop(src, cards, dst)
        if not ok:
            return self._refuse(why)
        self.held = None
        self.move(si, ci, target)
        return True

    def move(self, si, ci, ti, quiet=False):
        """Faz a jogada (já validada), anuncia e confere a vitória."""
        src, dst = self.piles[si], self.piles[ti]
        cards = src.cards[ci:]
        below = dst.top
        self.record("%s %s %s" % (cards_text(cards), src.of(), dst.to()))
        del src.cards[ci:]
        dst.cards.extend(cards)
        self.moves += 1
        self.last_move = (si, ti, len(cards))
        flipped = self.flip(src)
        text = "%s %s" % (cap(cards_text(cards)), dst.at())
        if dst.kind == COLUNA:
            text += ", sobre %s" % the(below) if below else ", que estava vazia"
        parts = [text + "."]
        if flipped:
            parts.append("Virou %s %s." % (the(flipped), src.at()))
        parts += self.after_move(src, dst, cards, flipped)
        self.ui.play("fundacao" if dst.kind == FUNDACAO else "soltar", pan=self.pan(ti))
        if flipped:
            self.ui.play("virar", pan=self.pan(si))
        self.depth = len(self.pile.cards) - 1
        if not quiet:
            self.ui.say(" ".join(parts))
        self.check_end()
        return parts

    def flip(self, pile):
        if pile.kind == COLUNA and pile.cards and not pile.top.up:
            pile.top.up = True
            return pile.top
        return None

    def _refuse(self, why):
        self.ui.play("erro")
        self.ui.say(why)
        return False

    def check_end(self):
        if not self.over and self.is_won():
            self.finish(True)

    def finish(self, won):
        self.over = True
        self.won = won
        self.held = None
        self.ui.play("vitoria" if won else "fim")
        if self.on_over:
            self.on_over(self.summary())

    def summary(self):
        return {"jogo": self.ID, "won": self.won, "score": self.score, "moves": self.moves,
                "options": dict(self.options)}

    # --- fundação (R1) --------------------------------------------------------
    def to_foundation(self):
        """Manda a carta de cima da pilha em foco (ou a da mão) para a fundação dela."""
        foundations = self.kind(FUNDACAO)
        if not foundations:
            return self._refuse(self.NO_FOUNDATION)
        if self.held is not None:
            si, ci = self.held
        else:
            si = self.stops[self.pos]
            ci = len(self.piles[si].cards) - 1
        src = self.piles[si]
        if ci < 0 or src.kind == ESTOQUE:
            return self._refuse("Não há carta aqui para a fundação.")
        cards = src.cards[ci:]
        if len(cards) > 1:
            return self._refuse("Só uma carta por vez vai para a fundação.")
        for f in foundations:
            if self.can_drop(src, cards, f)[0]:
                self.held = None
                self.move(si, ci, self.piles.index(f))
                return True
        return self._refuse("%s ainda não vai para a fundação." % cap(the(cards[0])))

    NO_FOUNDATION = "Não há fundação neste jogo."

    # --- dica (L1) ---------------------------------------------------------------
    def legal_moves(self):
        moves = []
        for si, src in enumerate(self.piles):
            if src.kind == ESTOQUE or not src.cards:
                continue
            first = src.first_up() if src.kind == COLUNA else len(src.cards) - 1
            for ci in range(first, len(src.cards)):
                if not self.can_pick(src, ci)[0]:
                    continue
                for ti, dst in enumerate(self.piles):
                    if ti != si and dst.kind not in (ESTOQUE, DESCARTE) \
                            and self.can_drop(src, src.cards[ci:], dst)[0]:
                        moves.append((si, ci, ti))
        return moves

    def move_value(self, si, ci, ti):
        """Quanto uma jogada ajuda; 0 ou menos fica fora das dicas."""
        src, dst = self.piles[si], self.piles[ti]
        if src.kind == FUNDACAO:
            return 0
        if dst.kind == FUNDACAO:
            return 100
        if src.kind == COLUNA:
            if ci > 0 and not src.cards[ci - 1].up:
                return 80
            if ci == 0:
                return 50 if dst.cards else 0
            if dst.kind == COLUNA and not self.linked(src.cards[ci - 1], src.cards[ci]):
                return 30 if dst.cards else 10
            return 0
        if dst.kind == COLUNA:
            return 60
        return 0

    def linked(self, below, card):
        """Se `card` já está em sequência sobre `below` (mexer nela não ajuda)."""
        return below.rank == card.rank + 1 and below.red != card.red

    def reverses(self, si, ci, ti):
        """Se a jogada só desfaz a anterior."""
        last = self.last_move
        return last is not None and (ti, si) == last[:2] and len(self.piles[si].cards) - ci == last[2]

    def hint(self):
        scored = [(self.move_value(*m), m) for m in self.legal_moves() if not self.reverses(*m)]
        scored = [s for s in scored if s[0] > 0]
        if not scored:
            self.ui.play("erro")
            self.ui.say(self.no_hint_text())
            return None
        best = max(s[0] for s in scored)
        si, ci, ti = [m for v, m in scored if v == best][0]
        src, dst = self.piles[si], self.piles[ti]
        self.held = None
        self.go_to(si, ci)
        self.ui.play("dica", pan=self.pan(si))
        self.ui.say("Dica: leve %s %s %s. O foco foi %s." % (
            cards_text(src.cards[ci:]), src.of(), dst.to(), src.to()))
        return (si, ci, ti)

    # --- leitura da mesa (Select) ----------------------------------------------
    def table_text(self):
        parts = []
        for kind, label in ((ESTOQUE, None), (DESCARTE, None), (CELULA, "Células"),
                            (FUNDACAO, "Fundações"), (COLUNA, "Colunas")):
            piles = self.kind(kind)
            if not piles:
                continue
            if label is None:
                parts.append(self.describe(piles[0]) + ".")
                continue
            items = []
            for p in piles:
                if not p.cards:
                    items.append("%s %s" % (p.suit_name() if kind == FUNDACAO else p.lower,
                                            "vazia" if p.feminine else "vazio"))
                elif kind == FUNDACAO:
                    items.append("até " + the(p.top))
                else:
                    top = p.top.name
                    if kind == COLUNA and p.down_count():
                        top += " com %d virada%s" % (p.down_count(), "" if p.down_count() == 1 else "s")
                    items.append("%s, %s" % (top, p.lower))
            if kind == FUNDACAO:
                parts.append("%s: %s." % (label, "; ".join(items)))
            else:
                parts.append(cap("; ".join(items)) + ".")
        return " ".join(parts)

    def pile_text(self):
        """A pilha em foco inteira, de baixo para cima."""
        p = self.pile
        if p.kind != COLUNA or not p.cards:
            return self.describe(p) + "."
        open_cards = [c.name for c in p.cards[p.first_up():]]
        text = "De baixo para cima: "
        if p.down_count():
            text += "%s, " % plural(p.down_count(), "virada")
        return "%s%s. %s." % (text, join(open_cards), p.name)

    # --- desfazer (A) ----------------------------------------------------------
    def snapshot(self):
        return {"piles": [[c.to_list() for c in p.cards] for p in self.piles],
                "score": self.score, "moves": self.moves, "extra": self.extra_state()}

    def restore(self, data):
        piles = data["piles"]
        if len(piles) != len(self.piles):
            raise ValueError("número de pilhas errado")
        for p, cards in zip(self.piles, piles):
            p.cards = [Card.from_list(c) for c in cards]
        self.score, self.moves = int(data["score"]), int(data["moves"])
        self.load_extra(data.get("extra", {}))

    def record(self, description):
        self.history.append((self.snapshot(), description))
        del self.history[:-MAX_UNDO]

    def undo(self):
        """A: devolve o que está na mão; sem nada na mão, desfaz a última jogada."""
        if self.cancel():
            return True
        if not self.history:
            return self._refuse("Nada para desfazer.")
        state, description = self.history.pop()
        self.restore(state)
        self.last_move = None
        self.depth = len(self.pile.cards) - 1
        self.ui.play("desfazer")
        self.ui.say("Desfeito: %s. %s." % (description, self.describe(self.pile)))
        return True

    # --- início e partida salva -------------------------------------------------
    def start(self):
        self.deal()
        self.ui.play("embaralhar")
        self.go_to(self.start_pile())
        self.ui.say("%s. %s %s" % (self.title(), self.intro_text(), self.describe(self.pile) + "."))

    def start_pile(self):
        return self.piles.index(self.kind(COLUNA)[0])

    def title(self):
        return self.NAME

    def to_dict(self):
        data = self.snapshot()
        data.update({"versao": self.SAVE_VERSION, "jogo": self.ID, "options": self.options,
                     "pos": self.pos, "depth": self.depth})
        return data

    @classmethod
    def from_dict(cls, ui, data, on_over=None):
        """Recria a partida salva por to_dict. ValueError se o arquivo não serve."""
        try:
            if data["versao"] != cls.SAVE_VERSION or data["jogo"] != cls.ID:
                raise ValueError("save de outro jogo ou versão")
            run = cls(ui, on_over=on_over, **data["options"])
            run.restore(data)
            run.pos = int(data["pos"]) % len(run.stops)
            run.depth = int(data["depth"])
        except (KeyError, TypeError, IndexError) as exc:
            raise ValueError("partida salva incompleta: %s" % exc)
        return run

    def resume(self):
        self.ui.play("embaralhar")
        self.ui.say("%s retomado, com %s. %s" % (
            self.title(), plural(self.moves, "jogada"), self.describe(self.pile) + "."))
