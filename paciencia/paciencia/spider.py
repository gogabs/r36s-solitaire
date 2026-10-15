"""Spider: dois baralhos, dez colunas, com 1, 2 ou 4 naipes.

Qualquer carta vai sobre outra um número acima, mas só sequências do mesmo
naipe se movem juntas. Uma sequência completa do rei ao ás do mesmo naipe sai
sozinha da mesa. X distribui uma carta em cada coluna (5 vezes por partida),
desde que nenhuma esteja vazia. Pontos como no Windows: começa com 500, -1 por
jogada, +100 por sequência completa.
"""
from .base import COLUNA, Pile, Solitaire, the
from .cards import COPAS, Card, ESPADAS, OUROS, PAUS, SUITS, cap, new_deck, plural, same_suit_run

SUIT_SETS = {1: (ESPADAS,), 2: (ESPADAS, COPAS), 4: (COPAS, OUROS, PAUS, ESPADAS)}


class Spider(Solitaire):
    ID = "spider"
    NAME = "Spider"
    STOPS = (COLUNA,)
    NO_FOUNDATION = "No Spider, as sequências completas, do rei ao ás do mesmo naipe, saem sozinhas."

    def __init__(self, ui, rng=None, on_over=None, suits=1, **options):
        options["suits"] = int(suits) if int(suits) in SUIT_SETS else 1
        self.stock = []
        self.done = []        # naipes das sequências completas, em ordem
        super().__init__(ui, rng, on_over, **options)
        self.score = 500

    def title(self):
        n = self.options["suits"]
        return "Spider, %s" % ("1 naipe" if n == 1 else "%d naipes" % n)

    def setup(self):
        self.piles = [Pile(COLUNA, "Coluna %d" % (k + 1)) for k in range(10)]

    def deal(self):
        suits = SUIT_SETS[self.options["suits"]]
        deck = new_deck(suits, copies=8 // len(suits))
        self.rng.shuffle(deck)
        for k, col in enumerate(self.piles):
            col.cards = [deck.pop() for _ in range(6 if k < 4 else 5)]
            col.top.up = True
        self.stock = deck

    def intro_text(self):
        return "Dez colunas; X distribui mais uma carta em cada, %s." % plural(self.deals_left(), "vez", "vezes")

    def deals_left(self):
        return len(self.stock) // 10

    # --- regras -----------------------------------------------------------------
    def can_pick(self, pile, index):
        cards = pile.cards[index:]
        if not cards[0].up:
            return False, "Essa carta está virada."
        if not same_suit_run(cards):
            return False, "Só sequências do mesmo naipe se movem juntas."
        return True, None

    def can_drop(self, src, cards, dst):
        if not dst.cards:
            return True, None
        if dst.top.rank != cards[0].rank + 1:
            return False, "Não cabe sobre %s: precisa de carta um número abaixo." % the(dst.top)
        return True, None

    def linked(self, below, card):
        return below.rank == card.rank + 1 and below.suit == card.suit

    def move_value(self, si, ci, ti):
        value = super().move_value(si, ci, ti)
        dst = self.piles[ti]
        if value > 0 and dst.cards and dst.top.suit == self.piles[si].cards[ci].suit:
            value += 15    # juntar no mesmo naipe vale mais
        return value

    def is_won(self):
        return len(self.done) == 8

    # --- sequências completas ---------------------------------------------------
    def collect(self):
        """Tira da mesa as sequências completas; devolve frases e quantas saíram."""
        parts = []
        for col in self.piles:
            run = col.cards[-13:]
            if len(run) == 13 and run[0].rank == 13 and same_suit_run(run):
                del col.cards[-13:]
                self.done.append(run[0].suit)
                self.score += 100
                self.ui.play("sequencia")
                text = "Sequência completa de %s %s! %d de 8." % (SUITS[run[0].suit], col.at(), len(self.done))
                flipped = self.flip(col)
                if flipped:
                    self.ui.play("virar", pan=self.pan(self.piles.index(col)))
                    text += " Virou %s." % the(flipped)
                parts.append(text)
        return parts

    def after_move(self, src, dst, cards, flipped):
        self.score -= 1
        return self.collect()

    # --- distribuir (X) ---------------------------------------------------------
    def draw(self):
        if not self.stock:
            return self._refuse("Não há mais cartas para distribuir.")
        empty = [p for p in self.piles if not p.cards]
        if empty:
            return self._refuse("Não dá para distribuir com coluna vazia: %s." % empty[0].lower)
        self.record("distribuição")
        self.held = None
        for col in self.piles:
            card = self.stock.pop()
            card.up = True
            col.cards.append(card)
        self.moves += 1
        self.score -= 1
        self.depth = len(self.pile.cards) - 1
        self.ui.play("comprar")
        parts = ["Distribuiu uma carta em cada coluna. %s" % (
            "Era a última distribuição." if not self.stock
            else "Restam %s." % plural(self.deals_left(), "distribuição", "distribuições"))]
        parts += self.collect()
        parts.append("%s." % self.describe(self.pile))
        self.ui.say(" ".join(parts))
        self.check_end()
        return True

    def no_hint_text(self):
        if self.stock:
            return "Nenhuma jogada que ajude. Distribua com X."
        return "Nenhuma jogada que ajude. Desfaça com A."

    # --- estado ------------------------------------------------------------------
    def extra_state(self):
        return {"stock": [c.to_list() for c in self.stock], "done": list(self.done)}

    def load_extra(self, data):
        self.stock = [Card.from_list(c) for c in data.get("stock", [])]
        self.done = [int(s) for s in data.get("done", [])]

    def table_text(self):
        text = super().table_text()
        text += " Sequências completas: %d de 8. %s." % (len(self.done), cap(plural(
            self.deals_left(), "distribuição restante", "distribuições restantes")))
        return text

    def status_text(self):
        return "%d pontos. %d de 8 sequências completas. %s. %s." % (
            self.score, len(self.done), cap(plural(self.moves, "jogada")),
            cap(plural(self.deals_left(), "distribuição restante", "distribuições restantes")))
