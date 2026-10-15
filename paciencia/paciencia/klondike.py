"""Klondike: a paciência clássica, com compra de 1 ou de 3 cartas.

Pontos como no Windows: descarte para coluna +5, qualquer carta na fundação +10,
carta virada na coluna +5, fundação de volta para a coluna -15, e devolver o
descarte ao estoque -100 (comprando 1) ou -20 (comprando 3). Nunca abaixo de 0.
"""
from .base import COLUNA, DESCARTE, ESTOQUE, FUNDACAO, Pile, Solitaire, the
from .cards import SUITS, cap, join, new_deck, plural, rank_name


class Klondike(Solitaire):
    ID = "klondike"
    NAME = "Klondike"
    STOPS = (ESTOQUE, DESCARTE, FUNDACAO, COLUNA)

    def __init__(self, ui, rng=None, on_over=None, draw=1, **options):
        options["draw"] = 3 if int(draw) == 3 else 1
        self.passes = 0
        super().__init__(ui, rng, on_over, **options)

    @property
    def draw_count(self):
        return self.options["draw"]

    def title(self):
        return "Klondike, comprando %d" % self.draw_count

    def setup(self):
        self.stock = Pile(ESTOQUE, "Estoque", feminine=False)
        self.waste = Pile(DESCARTE, "Descarte", feminine=False)
        self.piles = [self.stock, self.waste]
        self.piles += [Pile(FUNDACAO, "Fundação de " + SUITS[s], suit=s) for s in range(4)]
        self.piles += [Pile(COLUNA, "Coluna %d" % (k + 1)) for k in range(7)]

    def deal(self):
        deck = new_deck()
        self.rng.shuffle(deck)
        for k, col in enumerate(self.kind(COLUNA)):
            col.cards = [deck.pop() for _ in range(k + 1)]
            col.top.up = True
        self.stock.cards = deck

    def intro_text(self):
        return "Sete colunas; a primeira tem 1 carta e a última 7, só a de cima aberta."

    # --- regras -----------------------------------------------------------------
    def can_pick(self, pile, index):
        if pile.kind == COLUNA and not pile.cards[index].up:
            return False, "Essa carta está virada."
        return True, None

    def can_drop(self, src, cards, dst):
        card = cards[0]
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
        if dst.kind == COLUNA:
            if not dst.cards:
                return (True, None) if card.rank == 13 else (False, "Coluna vazia só aceita rei.")
            top = dst.top
            if top.rank != card.rank + 1 or top.red == card.red:
                return False, "Não cabe sobre %s: precisa de carta um número abaixo e de outra cor." % (
                    the(top))
            return True, None
        return False, "Não dá para soltar cartas %s." % dst.at()

    def is_won(self):
        return all(len(f.cards) == 13 for f in self.kind(FUNDACAO))

    # --- compra (X) ------------------------------------------------------------
    def draw(self):
        if not self.stock.cards:
            if not self.waste.cards:
                return self._refuse("Estoque e descarte vazios.")
            self.record("descarte voltou para o estoque")
            self.stock.cards = [c for c in reversed(self.waste.cards)]
            for c in self.stock.cards:
                c.up = False
            self.waste.cards = []
            self.passes += 1
            self.score = max(0, self.score - (100 if self.draw_count == 1 else 20))
            self.ui.play("embaralhar")
            self.ui.say("O descarte voltou para o estoque: %s." % plural(len(self.stock.cards), "carta"))
            return True
        self.record("compra")
        drawn = []
        for _ in range(min(self.draw_count, len(self.stock.cards))):
            card = self.stock.cards.pop()
            card.up = True
            self.waste.cards.append(card)
            drawn.append(card)
        self.moves += 1
        self.held = None
        self.go_to(self.piles.index(self.waste))
        self.ui.play("comprar", pan=self.pan(self.piles.index(self.waste)))
        if len(drawn) == 1:
            text = "Comprou %s." % drawn[0].name
        else:
            text = "Comprou %s; em cima, %s." % (join([c.name for c in drawn]), drawn[-1].name)
        if not self.stock.cards:
            text += " Estoque vazio."
        self.ui.say(text)
        return True

    def no_hint_text(self):
        if self.stock.cards or self.waste.cards:
            return "Nenhuma jogada com as cartas abertas. Compre com X."
        return "Nenhuma jogada. Desfaça com A."

    # --- pontos ------------------------------------------------------------------
    def after_move(self, src, dst, cards, flipped):
        gained = 0
        if dst.kind == FUNDACAO:
            gained += 10
        elif src.kind == DESCARTE and dst.kind == COLUNA:
            gained += 5
        elif src.kind == FUNDACAO and dst.kind == COLUNA:
            gained -= 15
        if flipped:
            gained += 5
        self.score = max(0, self.score + gained)
        parts = []
        if self.ready_to_finish():
            parts.append(self.auto_finish())
        return [p for p in parts if p]

    def ready_to_finish(self):
        """Tudo aberto e nada no estoque nem no descarte: o resto vai sozinho."""
        return (not self.over and not self.stock.cards and not self.waste.cards
                and all(c.up for col in self.kind(COLUNA) for c in col.cards)
                and not self.is_won())

    def auto_finish(self):
        count = 0
        moved = True
        while moved:
            moved = False
            for col in self.kind(COLUNA):
                if not col.cards:
                    continue
                f = self.kind(FUNDACAO)[col.top.suit]
                if col.top.rank == len(f.cards) + 1:
                    f.cards.append(col.cards.pop())
                    self.score += 10
                    count += 1
                    moved = True
        self.ui.play("cascata")
        return "Tudo aberto: %s foram sozinhas para as fundações." % plural(count, "carta")

    def extra_state(self):
        return {"passes": self.passes}

    def load_extra(self, data):
        self.passes = int(data.get("passes", 0))

    def status_text(self):
        home = sum(len(f.cards) for f in self.kind(FUNDACAO))
        text = "%d pontos. %s nas fundações, de 52. %s. Estoque com %s" % (
            self.score, plural(home, "carta"), cap(plural(self.moves, "jogada")),
            plural(len(self.stock.cards), "carta"))
        if self.passes:
            text += ", %s pelo baralho" % plural(self.passes + 1, "volta")
        return text + "."

