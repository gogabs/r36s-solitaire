"""Gráficos opcionais do Sudoku: a grade, o cursor e os menus.

Nada aqui é necessário para jogar: tudo o que aparece na tela também é falado
(regra do contrato). A tela segue a opção do sistema (SCREEN=0 desliga) e a
economia de energia (menos quadros por segundo), como no Campo Minado.

`draw_frame(gfx, ...)` só usa a API de desenho do SDK, então roda com o SDK de
verdade, com o gráfico de mentira dos testes e com o do gerador de prévias.

Cores pensadas para contraste (veja docs/graficos.md): dicas em branco sobre
casa um pouco mais clara, números do jogador em azul claro, número repetido em
rosa sobre vermelho escuro, linhas grossas claras entre os blocos e o cursor em
amarelo com contorno preto. A cor nunca é a única pista: dica e número do
jogador diferem também no fundo da casa, e o repetido também no fundo.
"""
import os
import time

from .grade import box_of

W, H = 640, 480
TOP_BAR = 34
CAPTION_Y = 430
CELL = 42                      # lado da casa, em pixels
X0 = (W - 9 * CELL) // 2
Y0 = TOP_BAR + (CAPTION_Y - TOP_BAR - 9 * CELL) // 2

BG = "#0f1720"
OPEN = "#1c2530"
GIVEN_BG = "#2a3646"
PEER = "#22364c"               # linha, coluna e bloco do cursor
SAME = "#1f4a33"               # casas com o mesmo número do cursor
CONFLICT_BG = "#6a1a22"
GIVEN = "#ffffff"
PLAYER = "#7cc4ff"
CONFLICT = "#ffd6d2"
THIN = "#3a4a5c"
THICK = "#c9d5e1"
FOCUS = "#ffd60a"
OUTLINE = "#000000"
BAR = "#000000"
TEXT = "#ffffff"
TEXT_DIM = "#c8d3de"
LINE = "#5d7186"

# linhas da folha graficos/numeros-42.png; colunas: 1 a 9
S_GIVEN, S_PLAYER, S_CONFLICT = 0, 1, 2
SHEET = "graficos/numeros-%d.png" % CELL


def digit_src(style, d):
    return ((d - 1) * CELL, style * CELL, CELL, CELL)


def cell_pos(r, c):
    return X0 + c * CELL, Y0 + r * CELL


def cell_look(run, r, c, conflicts):
    """(fundo, estilo do algarismo ou None) da casa."""
    g = run.grid
    v = g.get(r, c)
    style = None
    if v:
        style = S_GIVEN if g.fixed(r, c) else S_PLAYER
    if (r, c) in conflicts:
        return CONFLICT_BG, (S_CONFLICT if style == S_PLAYER else style)
    here = g.get(run.r, run.c)
    if v and here and v == here:
        return SAME, style
    if r == run.r or c == run.c or box_of(r, c) == box_of(run.r, run.c):
        return PEER, style
    return (GIVEN_BG if style == S_GIVEN else OPEN), style


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
def draw_board(gfx, sheet, fonts, run):
    gfx.clear(BG)
    g = run.grid
    top_bar(gfx, fonts, "%s  ·  linha %d, coluna %d" % (run.level_name, run.r + 1, run.c + 1),
            "faltam %d  ·  %s" % (g.empty_count(), clock(run.elapsed)))
    conflicts = g.conflict_cells()
    for r in range(9):
        for c in range(9):
            x, y = cell_pos(r, c)
            fill, style = cell_look(run, r, c, conflicts)
            gfx.rect(x, y, CELL, CELL, color=fill)
            if style is not None:
                gfx.draw(sheet, x, y, src=digit_src(style, g.get(r, c)))
    side = 9 * CELL
    for k in range(1, 9):
        if k % 3:
            gfx.line(X0 + k * CELL, Y0, X0 + k * CELL, Y0 + side, color=THIN)
            gfx.line(X0, Y0 + k * CELL, X0 + side, Y0 + k * CELL, color=THIN)
    for k in range(0, 10, 3):   # blocos: linhas grossas, por cima das finas
        gfx.rect(X0 + k * CELL - 1, Y0 - 1, 3, side + 3, color=THICK)
        gfx.rect(X0 - 1, Y0 + k * CELL - 1, side + 3, 3, color=THICK)
    x, y = cell_pos(run.r, run.c)
    ring(gfx, x + 2, y + 2, CELL - 4, CELL - 4, width=3)


def draw_menu(gfx, sheet, fonts, menu, overlay=False):
    items = menu.items
    if overlay:
        gfx.rect(70, 70, W - 140, CAPTION_Y - 110, color=(0, 0, 0, 235))
        gfx.rect(70, 70, W - 140, 3, color=FOCUS)
        top = 86
    else:
        gfx.clear(BG)
        x = W // 2 - 9 * CELL // 2
        for d in range(1, 10):   # uma fileira de 1 a 9, de enfeite
            gfx.rect(x + (d - 1) * CELL, 92, CELL, CELL, color=GIVEN_BG if d % 2 else OPEN)
            gfx.draw(sheet, x + (d - 1) * CELL, 92, src=digit_src(S_GIVEN if d % 2 else S_PLAYER, d))
        gfx.rect(x - 1, 91, 9 * CELL + 2, CELL + 2, color=THICK, fill=False)
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


def draw_frame(gfx, sheet, fonts, run, menu, caption):
    if run is not None:
        draw_board(gfx, sheet, fonts, run)
        if menu is not None:
            draw_menu(gfx, sheet, fonts, menu, overlay=True)
    elif menu is not None:
        draw_menu(gfx, sheet, fonts, menu)
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
        self.sheet = None
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
        gfx = Graphics("Sudoku", self.game.dir)
        if not gfx.open():
            self.failed = True
            return False
        self.gfx = gfx
        self.sheet = gfx.image(SHEET)
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
            draw_frame(self.gfx, self.sheet, self.fonts, run, menu, self.caption)
            self.gfx.end()
        except Exception as exc:   # gráfico com defeito não pode derrubar o jogo
            print("[sudoku] gráficos desligados: %s" % exc)
            self.failed = True
            self.close()
