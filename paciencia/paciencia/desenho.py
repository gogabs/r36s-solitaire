"""Gráficos opcionais da Paciência: a mesa, as cartas, o foco e os menus.

Nada aqui é necessário para jogar: tudo o que aparece na tela também é falado
(regra do contrato). A tela segue a opção do sistema (SCREEN=0 desliga) e a
economia de energia (menos quadros por segundo), como no Dead vs. Alive.

`draw_frame(gfx, ...)` só usa a API de desenho do Mage Core, então roda com o Mage Core de
verdade, com o gráfico de mentira dos testes e com o do gerador de prévias.

Cores pensadas para contraste (veja docs/graficos.md): cartas quase brancas
sobre feltro escuro, naipes vermelhos e pretos com formas diferentes (a cor
nunca é a única pista), e o foco em amarelo com contorno preto, que aparece
tanto sobre o feltro quanto sobre as cartas.
"""
import os
import time

from .base import CELULA, COLUNA, DESCARTE, ESTOQUE, FUNDACAO

W, H = 640, 480
SIZES = {"g": (72, 100), "p": (58, 80)}
RANK_LABELS = {1: "A", 11: "J", 12: "Q", 13: "K"}
RANK_LABELS.update({r: str(r) for r in range(2, 11)})

FELT = "#0d3b2e"
FACE = "#fbfbf7"
EDGE = "#1a1a1a"
RED = "#b8102a"
BLACK = "#151515"
RED_PALE = "#f7d9dd"
BLACK_PALE = "#dedede"
BACK = "#1f4f9e"
BACK_LINE = "#5a86d0"
BACK_EDGE = "#ffffff"
SLOT = "#86c2a5"
SLOT_FILL = "#0a3024"
FOCUS = "#ffd60a"
OUTLINE = "#000000"
BAR = "#000000"
TEXT = "#ffffff"
TEXT_DIM = "#c8ddd2"
HELD = "#ffffff"

TOP_BAR = 34
CAPTION_Y = 430
EXTRA_BACK, EXTRA_SLOT, EXTRA_FOUNDATION = 0, 1, 2


def card_src(size, rank, suit):
    w, h = SIZES[size]
    return ((rank - 1) * w, suit * h, w, h)


def extra_src(size, k):
    w, h = SIZES[size]
    return (k * w, 4 * h, w, h)


# --- disposição da mesa ------------------------------------------------------------
def layout(run):
    """{pilha: (x, y)}, o tamanho das cartas e onde as colunas acabam."""
    piles = run.piles
    pos = {}
    if run.ID == "spider":
        size = "p"
        for k, p in enumerate(piles):
            pos[k] = (6 + k * 63, TOP_BAR + 10)
        return pos, size
    size = "g"
    if run.ID == "klondike":
        xs = [12 + i * 88 for i in range(7)]
        top = {ESTOQUE: [0], DESCARTE: [1], FUNDACAO: [3, 4, 5, 6]}
    else:
        xs = [8 + i * 78 for i in range(8)]
        top = {CELULA: [0, 1, 2, 3], FUNDACAO: [4, 5, 6, 7]}
    counters = {}
    col = 0
    for k, p in enumerate(piles):
        if p.kind == COLUNA:
            pos[k] = (xs[col], TOP_BAR + 116)
            col += 1
        else:
            n = counters.get(p.kind, 0)
            counters[p.kind] = n + 1
            pos[k] = (xs[top[p.kind][n]], TOP_BAR + 8)
    return pos, size


def column_steps(pile, size, room):
    """Quanto cada carta virada e cada aberta desce, apertando se não couber."""
    w, h = SIZES[size]
    down = 10 if size == "g" else 8
    up = 26 if size == "g" else 22
    n_down = pile.down_count()
    n_up = len(pile.cards) - n_down
    def total(d, u):
        return n_down * d + max(0, n_up - 1) * u + h
    while total(down, up) > room and down > 4:
        down -= 1
    while total(down, up) > room and up > 10:
        up -= 1
    return down, up


def card_positions(pile, x, y, size):
    """[(x, y)] de cada carta da pilha."""
    if pile.kind != COLUNA:
        return [(x, y)] * len(pile.cards)
    down, up = column_steps(pile, size, CAPTION_Y - 4 - y)
    out = []
    cy = y
    for c in pile.cards:
        out.append((x, cy))
        cy += up if c.up else down
    return out


# --- desenho ----------------------------------------------------------------------
class Fonts:
    def __init__(self, gfx):
        self.gfx = gfx
        self.cache = {}

    def __call__(self, size):
        if size not in self.cache:
            self.cache[size] = self.gfx.font(None, size)
        return self.cache[size]


def ring(gfx, x, y, w, h, color=FOCUS, width=4):
    """Contorno grosso em volta da caixa, com uma linha preta por dentro e por
    fora: aparece em qualquer fundo, claro ou escuro."""
    for k in range(width + 2):
        d = k + 1
        c = OUTLINE if k in (0, width + 1) else color
        gfx.rect(x - d, y - d, w + 2 * d, h + 2 * d, color=c, fill=False)


def draw_card(gfx, sheet, size, card, x, y):
    if card.up:
        gfx.draw(sheet, x, y, src=card_src(size, card.rank, card.suit))
    else:
        gfx.draw(sheet, x, y, src=extra_src(size, EXTRA_BACK))


def wrap(gfx, text, font, width, lines=2):
    words = text.split()
    out, line = [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if gfx.measure(trial, font)[0] <= width or not line:
            line = trial
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    if len(out) > lines:   # a fala mais nova fica no fim: mostra o fim
        out = out[-lines:]
        out[0] = "… " + out[0]
    return out


def draw_caption(gfx, fonts, caption):
    gfx.rect(0, CAPTION_Y, W, H - CAPTION_Y, color=BAR)
    gfx.line(0, CAPTION_Y, W, CAPTION_Y, color=SLOT, width=2)
    for k, line in enumerate(wrap(gfx, caption or "", fonts(18), W - 20)):
        gfx.text(line, 10, CAPTION_Y + 4 + k * 23, font=fonts(18), color=TEXT)


def top_bar(gfx, fonts, left, right):
    gfx.rect(0, 0, W, TOP_BAR, color=BAR)
    gfx.text(left, 10, 5, font=fonts(20), color=TEXT)
    gfx.text(right, W - 10, 5, font=fonts(20), color=TEXT, align="right")


def bar_text(run):
    if run.ID == "klondike":
        return "Klondike, compra %d" % run.draw_count, "%d pontos  ·  estoque %d" % (
            run.score, len(run.stock.cards))
    if run.ID == "freecell":
        free = sum(1 for c in run.kind(CELULA) if not c.cards)
        return "FreeCell %d" % run.options["number"], "%d na fundação  ·  células livres %d" % (
            run.score, free)
    return "Spider, %d naipe%s" % (run.options["suits"], "" if run.options["suits"] == 1 else "s"), \
        "%d pontos  ·  %d/8  ·  distribui %d" % (run.score, len(run.done), run.deals_left())


def draw_table(gfx, sheets, fonts, run):
    gfx.clear(FELT)
    pos, size = layout(run)
    sheet = sheets[size]
    cw, ch = SIZES[size]
    left, right = bar_text(run)
    top_bar(gfx, fonts, left, right)
    focus_pile = run.stops[run.pos]
    held_pile, held_index = run.held if run.held is not None else (None, None)
    focus_box = None
    peek = None
    lifted = []
    for k, p in enumerate(run.piles):
        x, y = pos[k]
        if not p.cards:
            if p.kind == FUNDACAO:
                gfx.draw(sheet, x, y, src=extra_src(size, EXTRA_FOUNDATION + p.suit))
            else:
                gfx.draw(sheet, x, y, src=extra_src(size, EXTRA_SLOT))
            if k == focus_pile:
                focus_box = (x, y, cw, ch)
            continue
        if p.kind == DESCARTE:   # compra de 3: as três de cima em leque
            fan = p.cards[-3:] if run.options.get("draw") == 3 else p.cards[-1:]
            for j, c in enumerate(fan):
                draw_card(gfx, sheet, size, c, x + j * 18, y)
            top_x = x + (len(fan) - 1) * 18
            if k == focus_pile:
                focus_box = (top_x, y, cw, ch)
            if k == held_pile:
                lifted.append((p.cards[-1], top_x, y))
            continue
        if p.kind != COLUNA:
            draw_card(gfx, sheet, size, p.top, x, y)
            if k == focus_pile:
                focus_box = (x, y, cw, ch)
            if k == held_pile:
                lifted.append((p.top, x, y))
            continue
        spots = card_positions(p, x, y, size)
        for j, (c, (cx, cy)) in enumerate(zip(p.cards, spots)):
            if k == held_pile and j >= held_index:
                lifted.append((c, cx, cy))
                continue
            draw_card(gfx, sheet, size, c, cx, cy)
        if k == focus_pile:
            i = run.focus_index()
            fx, fy = spots[i]
            focus_box = (fx, fy, cw, ch)
            if i < len(p.cards) - 1 and run.held is None:
                peek = (p.cards[i], fx, fy)   # a carta em foco aparece inteira por cima
    if peek:
        draw_card(gfx, sheet, size, *peek)
    if focus_box:
        ring(gfx, *focus_box)
    if lifted:
        # cartas na mão: levantadas, com contorno branco e a etiqueta "na mão"
        _, lx, ly = lifted[0]
        dy = max(-14, TOP_BAR + 4 - ly)   # não sobe por cima da barra de cima
        lx, ly = lx + 8, ly + dy
        last_y = ly + (lifted[-1][2] - lifted[0][2])
        ring(gfx, lx, ly, cw, last_y - ly + ch, color=HELD, width=3)
        for c, cx, cy in lifted:
            draw_card(gfx, sheet, size, c, cx + 8, cy + dy)
        pill(gfx, fonts, "NA MÃO", lx, label_y(ly, last_y + ch), HELD)
    if run.held is not None and focus_box and focus_pile != held_pile:
        src = run.piles[held_pile]
        if run.can_drop(src, run.held_cards(), run.piles[focus_pile])[0]:
            fx, fy, fw, fh = focus_box
            pill(gfx, fonts, "CABE", fx, label_y(fy, fy + fh), FOCUS)
    return pos


def label_y(top, bottom):
    """Etiqueta acima da carta; sem espaço (fileira de cima), logo abaixo dela,
    para nunca tapar o valor da carta."""
    if top - 30 >= TOP_BAR + 2:
        return top - 30
    return bottom + 6


def pill(gfx, fonts, text, x, y, color):
    font = fonts(16)
    tw, th = gfx.measure(text, font)
    tw = tw or len(text) * 10
    gfx.rect(x - 2, y - 2, tw + 16, 26, color=OUTLINE)
    gfx.rect(x, y, tw + 12, 22, color=color)
    gfx.text(text, x + 6, y + 2, font=font, color=OUTLINE)


def draw_menu(gfx, sheets, fonts, menu, overlay=False):
    items = menu.items
    if overlay:
        gfx.rect(70, 70, W - 140, CAPTION_Y - 110, color=(0, 0, 0, 235))
        gfx.rect(70, 70, W - 140, 3, color=FOCUS)
        top = 86
    else:
        gfx.clear(FELT)
        sheet = sheets["g"]
        cw, ch = SIZES["g"]
        for j, suit in enumerate((0, 3, 1, 2)):    # quatro ases em leque
            gfx.draw(sheet, W // 2 - 2 * cw + j * (cw - 8) + 16, 48, src=card_src("g", 1, suit))
        top = 160
    gfx.text(menu.title, W // 2, top, font=fonts(30), color=TEXT, align="center")
    row = 32
    first = top + 46
    visible = max(1, (CAPTION_Y - 12 - first) // row)
    start = min(max(0, menu.index - visible + 1), max(0, len(items) - visible))
    for k in range(start, min(len(items), start + visible)):
        y = first + (k - start) * row
        if k == menu.index:
            gfx.rect(110, y - 2, W - 220, row - 4, color=FOCUS)
            gfx.text(items[k], W // 2, y + 2, font=fonts(22), color=OUTLINE, align="center")
        else:
            gfx.text(items[k], W // 2, y + 2, font=fonts(22), color=TEXT_DIM, align="center")


def draw_frame(gfx, sheets, fonts, run, menu, caption):
    if run is not None:
        draw_table(gfx, sheets, fonts, run)
        if menu is not None:
            draw_menu(gfx, sheets, fonts, menu, overlay=True)
    elif menu is not None:
        draw_menu(gfx, sheets, fonts, menu)
    else:
        gfx.clear(FELT)
    draw_caption(gfx, fonts, caption)


# --- ligação com o jogo ----------------------------------------------------------
def read_setting(key):
    try:
        with open(os.environ.get("A11Y_SISTEMA_CONF", "/opt/a11y/etc/sistema.conf")) as f:
            for line in f:
                k, sep, value = line.strip().partition("=")
                if sep and k == key:
                    return value.strip("'\"")
    except OSError:
        pass
    return None


def screen_on():
    if os.environ.get("A11Y_GRAPHICS") == "0":
        return False
    return read_setting("SCREEN") != "0"


def frame_interval():
    """15 quadros por segundo; menos na economia de energia. A mesa só muda
    quando um botão é apertado, então isso basta."""
    return {"moderate": 0.1, "aggressive": 0.2}.get(read_setting("ENERGY"), 1 / 15.0)


class Renderer:
    """Desenha em on_update, no ritmo de frame_interval. Uma falha de vídeo só
    desliga os gráficos: o jogo segue pelo som."""

    def __init__(self, game, get_run):
        self.game = game
        self.get_run = get_run
        self.caption = ""
        self.shown = None
        self._say = game.say
        game.say = self.say   # a legenda é sempre a última fala
        self.gfx = None
        self.sheets = None
        self.fonts = None
        self.failed = False
        self.enabled = False
        self.interval = 1 / 15.0
        self.due = 0.0
        self.checked = -1.0
        game.on_update(self.update)
        game.on_quit(self.close)

    def say(self, text, queue=False, on_done=None):
        self.caption = (self.caption + " " + text) if queue and self.caption else text
        self.caption = self.caption[-400:]
        self._say(text, queue=queue, on_done=on_done)

    def menu(self):
        focus = getattr(self.game, "_focus", [])
        return focus[-1] if focus else None

    def scene(self):
        """(partida, menu). Uma partida que acabou continua na tela enquanto o
        jogo fala o resultado, até o menu abrir."""
        run, menu = self.get_run(), self.menu()
        if run is not None:
            self.shown = run
        elif menu is not None:
            self.shown = None
        return self.shown, menu

    def open(self):
        from r36s_a11y.graphics import Graphics
        gfx = Graphics("Paciência", self.game.dir)
        if not gfx.open():
            self.failed = True
            return False
        self.gfx = gfx
        self.sheets = {name: gfx.image("graficos/cartas-%s.png" % name) for name in SIZES}
        self.fonts = Fonts(gfx)
        return True

    def close(self):
        if self.gfx is not None and self.gfx.available:
            self.gfx.close()
        self.gfx = None

    def update(self, dt):
        now = time.monotonic()
        if now - self.checked >= 0.5:
            self.checked = now
            self.enabled = screen_on()
            self.interval = frame_interval()
            if not self.enabled:
                self.close()
        if not self.enabled or self.failed:
            return
        self.due += dt
        if self.due < self.interval:
            return
        self.due = 0.0
        try:
            if self.gfx is None and not self.open():
                return
            run, menu = self.scene()
            self.gfx.begin()
            draw_frame(self.gfx, self.sheets, self.fonts, run, menu, self.caption)
            self.gfx.end()
        except Exception as exc:   # gráfico com defeito não pode derrubar o jogo
            print("[paciencia] gráficos desligados: %s" % exc)
            self.failed = True
            self.close()
