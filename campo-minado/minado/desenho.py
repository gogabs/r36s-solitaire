"""Gráficos opcionais do Campo Minado: a grade, o cursor e os menus.

Nada aqui é necessário para jogar: tudo o que aparece na tela também é falado
(regra do contrato). Por isso, ao perder, a tela mostra só a mina que explodiu,
que é a que o jogo fala; as outras continuam escondidas. A tela segue a opção
do sistema (SCREEN=0 desliga) e a economia de energia (menos quadros por
segundo), como no Dead vs. Alive.

`draw_frame(gfx, ...)` só usa a API de desenho do SDK, então roda com o SDK de
verdade, com o gráfico de mentira dos testes e com o do gerador de prévias.

Cores pensadas para contraste (veja docs/graficos.md): casas fechadas claras e
em relevo, abertas escuras e lisas, cada número com cor própria e contraste de
pelo menos 7 para 1 sobre a casa aberta (a cor nunca é a única pista: o
algarismo está lá), e o cursor em amarelo com contorno preto.
"""
import os
import time

from .board import LEVELS

W, H = 640, 480
TOP_BAR = 34
CAPTION_Y = 430
CELL = {"facil": 42, "medio": 24, "dificil": 21}   # lado da casa, em pixels

BG = "#0f1720"
CLOSED = "#8fa3b8"
CLOSED_LIGHT = "#c9d5e1"
CLOSED_DARK = "#4d6074"
OPEN = "#1c2530"
OPEN_LINE = "#2e3c4b"
NUMBERS = {1: "#6cb4ff", 2: "#5fd38d", 3: "#ff9a92", 4: "#c9a0ff",
           5: "#ffb454", 6: "#4fd6d6", 7: "#f2f2f2", 8: "#b0b8c0"}
FLAG = "#e8323c"
MINE = "#0b0b0b"
EXPLODED = "#e8323c"
FOCUS = "#ffd60a"
OUTLINE = "#000000"
BAR = "#000000"
TEXT = "#ffffff"
TEXT_DIM = "#c8d3de"
LINE = "#5d7186"

# ordem das casas na folha graficos/casas-<lado>.png
T_CLOSED, T_FLAG, T_OPEN0, T_EXPLODED = 0, 1, 2, 11
TILES = 12


def tile_src(size, k):
    return (k * size, 0, size, size)


def tile_index(state):
    if state == "fechada":
        return T_CLOSED
    if state == "marcada":
        return T_FLAG
    return T_OPEN0 + state


def board_origin(run):
    size = CELL[run.level]
    b = run.board
    x = (W - b.cols * size) // 2
    y = TOP_BAR + (CAPTION_Y - TOP_BAR - b.rows * size) // 2
    return x, y, size


# --- peças comuns ---------------------------------------------------------------
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


def wrap(gfx, text, font, width, lines=2):
    out, line = [], ""
    for word in text.split():
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
    gfx.line(0, CAPTION_Y, W, CAPTION_Y, color=LINE, width=2)
    for k, line in enumerate(wrap(gfx, caption or "", fonts(18), W - 20)):
        gfx.text(line, 10, CAPTION_Y + 4 + k * 23, font=fonts(18), color=TEXT)


def top_bar(gfx, fonts, left, right):
    gfx.rect(0, 0, W, TOP_BAR, color=BAR)
    gfx.text(left, 10, 5, font=fonts(20), color=TEXT)
    gfx.text(right, W - 10, 5, font=fonts(20), color=TEXT, align="right")


def clock(seconds):
    m, s = divmod(int(seconds), 60)
    return "%d:%02d" % (m, s)


# --- a grade ------------------------------------------------------------------------
def draw_board(gfx, sheets, fonts, run):
    gfx.clear(BG)
    b = run.board
    left = b.mine_count - len(b.flags)
    top_bar(gfx, fonts, "%s  ·  linha %d, coluna %d" % (run.level_name, run.r + 1, run.c + 1),
            "minas %d  ·  %s" % (left, clock(run.elapsed)))
    x0, y0, size = board_origin(run)
    sheet = sheets[size]
    exploded = (run.r, run.c) if run.over and not run.won else None
    gfx.rect(x0 - 2, y0 - 2, b.cols * size + 4, b.rows * size + 4, color=LINE, fill=False)
    for r in range(b.rows):
        for c in range(b.cols):
            k = T_EXPLODED if (r, c) == exploded else tile_index(b.state(r, c))
            gfx.draw(sheet, x0 + c * size, y0 + r * size, src=tile_src(size, k))
    ring(gfx, x0 + run.c * size, y0 + run.r * size, size, size, width=4 if size > 30 else 3)


def draw_menu(gfx, sheets, fonts, menu, overlay=False):
    items = menu.items
    if overlay:
        gfx.rect(70, 70, W - 140, CAPTION_Y - 110, color=(0, 0, 0, 235))
        gfx.rect(70, 70, W - 140, 3, color=FOCUS)
        top = 86
    else:
        gfx.clear(BG)
        size = CELL["facil"]
        sheet = sheets[size]
        row = [T_CLOSED, T_OPEN0 + 1, T_FLAG, T_OPEN0 + 2, T_OPEN0 + 3, T_CLOSED]
        x = W // 2 - len(row) * size // 2
        for j, k in enumerate(row):   # uma fileira de casas, de enfeite
            gfx.draw(sheet, x + j * size, 92, src=tile_src(size, k))
        top = 160
    gfx.text(menu.title, W // 2, top, font=fonts(30), color=TEXT, align="center")
    row_h = 32
    first = top + 46
    visible = max(1, (CAPTION_Y - 12 - first) // row_h)
    start = min(max(0, menu.index - visible + 1), max(0, len(items) - visible))
    for k in range(start, min(len(items), start + visible)):
        y = first + (k - start) * row_h
        if k == menu.index:
            gfx.rect(90, y - 2, W - 180, row_h - 4, color=FOCUS)
            gfx.text(items[k], W // 2, y + 2, font=fonts(22), color=OUTLINE, align="center")
        else:
            gfx.text(items[k], W // 2, y + 2, font=fonts(22), color=TEXT_DIM, align="center")


def draw_frame(gfx, sheets, fonts, run, menu, caption):
    if run is not None:
        draw_board(gfx, sheets, fonts, run)
        if menu is not None:
            draw_menu(gfx, sheets, fonts, menu, overlay=True)
    elif menu is not None:
        draw_menu(gfx, sheets, fonts, menu)
    else:
        gfx.clear(BG)
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
    """15 quadros por segundo; menos na economia de energia. A grade só muda
    com um botão (e o relógio, de segundo em segundo), então isso basta."""
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
        gfx = Graphics("Campo Minado", self.game.dir)
        if not gfx.open():
            self.failed = True
            return False
        self.gfx = gfx
        self.sheets = {size: gfx.image("graficos/casas-%d.png" % size) for size in set(CELL.values())}
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
            print("[campo-minado] gráficos desligados: %s" % exc)
            self.failed = True
            self.close()


assert set(CELL) == set(LEVELS)
