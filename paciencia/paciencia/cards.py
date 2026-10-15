"""Cartas, naipes e nomes falados."""

COPAS, OUROS, PAUS, ESPADAS = range(4)
SUITS = ("copas", "ouros", "paus", "espadas")
RED = (COPAS, OUROS)
RANK_NAMES = {1: "ás", 11: "valete", 12: "dama", 13: "rei"}


def rank_name(rank):
    return RANK_NAMES.get(rank, str(rank))


def cap(text):
    return text[:1].upper() + text[1:]


def plural(n, word, words=None):
    return "%d %s" % (n, word if n == 1 else (words or word + "s"))


def join(parts):
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + " e " + parts[-1]


class Card:
    __slots__ = ("rank", "suit", "up")

    def __init__(self, rank, suit, up=False):
        self.rank = rank
        self.suit = suit
        self.up = up

    @property
    def red(self):
        return self.suit in RED

    @property
    def name(self):
        """ "dama de copas", "7 de paus"."""
        return "%s de %s" % (rank_name(self.rank), SUITS[self.suit])

    def to_list(self):
        return [self.rank, self.suit, 1 if self.up else 0]

    @classmethod
    def from_list(cls, data):
        rank, suit, up = data
        if not (1 <= rank <= 13 and 0 <= suit <= 3):
            raise ValueError("carta inválida: %r" % (data,))
        return cls(int(rank), int(suit), bool(up))

    def __repr__(self):
        return "Card(%s%s)" % (self.name, "" if self.up else ", virada")


def new_deck(suits=(COPAS, OUROS, PAUS, ESPADAS), copies=1):
    """Cartas viradas para baixo, ainda sem embaralhar."""
    return [Card(rank, suit) for _ in range(copies) for suit in suits for rank in range(1, 14)]


def alternating(cards):
    """Sequência descendente alternando cor (Klondike, FreeCell)."""
    return all(a.up and b.up and a.rank == b.rank + 1 and a.red != b.red
               for a, b in zip(cards, cards[1:]))


def same_suit_run(cards):
    """Sequência descendente do mesmo naipe (Spider)."""
    return all(a.up and b.up and a.rank == b.rank + 1 and a.suit == b.suit
               for a, b in zip(cards, cards[1:]))
