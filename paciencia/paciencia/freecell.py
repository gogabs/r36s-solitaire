"""FreeCell: todas as cartas abertas, quatro células livres para guardar uma carta cada.

Os jogos são numerados como no FreeCell do Windows (1 a 32000): o mesmo número
dá sempre a mesma mesa. Sequências se movem juntas se houver espaço: até
(células livres + 1) × 2 elevado ao número de colunas vazias.
"""
from .base import CELULA, COLUNA, FUNDACAO, Pile, Solitaire, the
from .cards import COPAS, ESPADAS, OUROS, PAUS, SUITS, Card, alternating, cap, plural, rank_name

# ordem de naipes do embaralhador do Windows: paus, ouros, copas, espadas
MS_SUITS = (PAUS, OUROS, COPAS, ESPADAS)


def ms_deal(number):
    """As 8 colunas do jogo `number` do FreeCell da Microsoft."""
    state = number
    deck = list(range(52))
    cols = [[] for _ in range(8)]
    for i in range(52):
        state = (state * 214013 + 2531011) & 0x7FFFFFFF
        left = 52 - i
        j = (state >> 16) % left
        c = deck[j]
        deck[j] = deck[left - 1]
        cols[i % 8].append(Card(c // 4 + 1, MS_SUITS[c % 4], up=True))
    return cols


class FreeCell(Solitaire):
    ID = "freecell"
    NAME = "FreeCell"
    STOPS = (CELULA, FUNDACAO, COLUNA)
    NO_DRAW = "No FreeCell não há compra: todas as cartas já estão na mesa."

    def __init__(self, ui, rng=None, on_over=None, number=None, **options):
        super().__init__(ui, rng, on_over, **options)
        self.options["number"] = int(number) if number else self.rng.randint(1, 32000)

    def title(self):
        return "FreeCell, jogo %d" % self.options["number"]

    def setup(self):
        self.piles = [Pile(CELULA, "Célula %d" % (k + 1)) for k in range(4)]
        self.piles += [Pile(FUNDACAO, "Fundação de " + SUITS[s], suit=s) for s in range(4)]
        self.piles += [Pile(COLUNA, "Coluna %d" % (k + 1)) for k in range(8)]

    def deal(self):
        for col, cards in zip(self.kind(COLUNA), ms_deal(self.options["number"])):
            col.cards = cards

    def intro_text(self):
        return "Oito colunas, todas abertas, quatro células livres."

    # --- regras -----------------------------------------------------------------
    def max_move(self, to_empty=False):
        free = sum(1 for c in self.kind(CELULA) if not c.cards)
        empty = sum(1 for c in self.kind(COLUNA) if not c.cards) - (1 if to_empty else 0)
        return (free + 1) * 2 ** max(0, empty)

    def can_pick(self, pile, index):
        if pile.kind == FUNDACAO:
            return False, "No FreeCell, cartas da fundação não voltam."
        cards = pile.cards[index:]
        if not alternating(cards):
            return False, "Daqui para cima as cartas não estão em sequência de cores alternadas."
        limit = self.max_move()
        if len(cards) > limit:
            return False, "Com o espaço livre agora, dá para levar no máximo %s." % plural(limit, "carta")
        return True, None

    def can_drop(self, src, cards, dst):
        card = cards[0]
        if dst.kind == CELULA:
            if len(cards) > 1:
                return False, "Cada célula guarda uma carta só."
            if dst.cards:
                return False, "%s está ocupada." % dst.name
            return True, None
        if dst.kind == FUNDACAO:
            if len(cards) > 1:
                return False, "Só uma carta por vez vai para a fundação."
            if card.suit != dst.suit:
                return False, "Essa é a fundação de %s." % SUITS[dst.suit]
            need = len(dst.cards) + 1
            if card.rank != need:
                return False, "A fundação de %s precisa %s." % (
                    SUITS[dst.suit], ("da " if need == 12 else "do ") + rank_name(need))
            return True, None
        if not dst.cards:
            limit = self.max_move(to_empty=True)
            if len(cards) > limit:
                return False, "Para uma coluna vazia, dá para levar no máximo %s." % plural(limit, "carta")
            return True, None
        top = dst.top
        if top.rank != card.rank + 1 or top.red == card.red:
            return False, "Não cabe sobre %s: precisa de carta um número abaixo e de outra cor." % the(top)
        if len(cards) > self.max_move():
            return False, "Dá para levar no máximo %s agora." % plural(self.max_move(), "carta")
        return True, None

    def is_won(self):
        return all(len(f.cards) == 13 for f in self.kind(FUNDACAO))

    def after_move(self, src, dst, cards, flipped):
        self.score = sum(len(f.cards) for f in self.kind(FUNDACAO))
        return []

    def status_text(self):
        home = sum(len(f.cards) for f in self.kind(FUNDACAO))
        free = sum(1 for c in self.kind(CELULA) if not c.cards)
        empty = sum(1 for c in self.kind(COLUNA) if not c.cards)
        text = "Jogo %d. %s nas fundações, de 52. %s. %s livre%s" % (
            self.options["number"], plural(home, "carta"), cap(plural(self.moves, "jogada")),
            plural(free, "célula"), "" if free == 1 else "s")
        if empty:
            text += ", %s vazia%s" % (plural(empty, "coluna"), "" if empty == 1 else "s")
        return text + ". Dá para levar até %s de uma vez." % plural(self.max_move(), "carta")
