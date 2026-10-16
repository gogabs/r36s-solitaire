#!/usr/bin/env python3
"""Sudoku: preencha a grade sem repetir números, ouvindo cada casa."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# Instalado, a biblioteca vem junto do jogo; no repositório, usa a cópia da raiz.
if not os.path.isdir(os.path.join(HERE, "r36s_a11y")):
    sys.path.insert(1, os.path.join(HERE, ".."))

import r36s_a11y as a11y

from sudoku import texts as T
from sudoku.desenho import Renderer
from sudoku.grade import LEVEL_ORDER, LEVELS
from sudoku.run import Run, duration

game = a11y.Game(repeat=True)
SAVE_FILE = os.path.join(game.save_dir, "progresso.json")
RUN_FILE = os.path.join(game.save_dir, "partida.json")   # um espaço só
sounds = {}
for f in sorted(os.listdir(os.path.join(game.dir, "sounds"))):
    base, ext = os.path.splitext(f)
    if ext.lower() in (".wav", ".ogg"):
        sounds[base] = game.sound.load(base, os.path.join("sounds", f))
menu_sounds = {"move": sounds.get("menu_mover"), "select": sounds.get("menu_confirmar")}

state = {"run": None}


# --- progresso -------------------------------------------------------------
def load_progress():
    try:
        with open(SAVE_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    for level in LEVEL_ORDER:
        data.setdefault(level, {"resolvidos": 0, "melhor": None})
    return data


def save_progress(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


# --- partida salva -----------------------------------------------------------
def has_saved_run():
    return os.path.isfile(RUN_FILE)


def save_run(run):
    """Arquivo temporário e troca, para um desligamento no meio não estragar o save."""
    tmp = RUN_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(run.to_dict(), f, ensure_ascii=False)
    os.replace(tmp, RUN_FILE)


def drop_saved_run():
    try:
        os.remove(RUN_FILE)
    except OSError:
        pass


# --- som e fala --------------------------------------------------------------
class UI:
    def say(self, text, queue=False):
        game.say(text, queue=queue)

    def play(self, name, pan=None, pitch=1.0):
        sound = sounds.get(name)
        if sound is not None:
            sound.play(pan=pan, pitch=pitch)


ui = UI()


# --- fluxo -------------------------------------------------------------------
def start_run(level):
    level_menu.close()
    run = Run(ui, level=level, on_over=game_over)
    state["run"] = run
    run.start()
    if has_saved_run():
        game.say("A partida salva continua guardada. Salvar esta partida substitui aquela.",
                 queue=True)


def continue_run():
    """Retoma a partida salva. O save é usado uma vez: sair do jogo ou escolher
    "Salvar e sair" grava de novo."""
    try:
        with open(RUN_FILE, encoding="utf-8") as f:
            run = Run.from_dict(ui, json.load(f), on_over=game_over)
    except (OSError, ValueError) as exc:
        print("[sudoku] partida salva ilegível: %s" % exc, file=sys.stderr)
        drop_saved_run()
        main_menu.close()
        game.say("Não deu para ler a partida salva. Ela foi descartada.",
                 on_done=lambda done: open_main())
        return
    drop_saved_run()
    main_menu.close()
    state["run"] = run
    run.resume()


def game_over(summary):
    data = load_progress()
    stats = data[summary["level"]]
    stats["resolvidos"] += 1
    text = "Sudoku resolvido em %s!" % duration(summary["time"])
    best = stats["melhor"]
    if best is None or summary["time"] < best:
        stats["melhor"] = summary["time"]
        if best is not None:
            text += " Novo recorde! O anterior era %s." % duration(best)
    save_progress(data)
    state["run"] = None
    game.after(1.5, lambda: game.say(text, on_done=lambda done: open_main()))


def stats_text():
    data = load_progress()
    parts = []
    for level in LEVEL_ORDER:
        s = data[level]
        text = "%s: %d resolvido%s" % (LEVELS[level][0], s["resolvidos"],
                                       "" if s["resolvidos"] == 1 else "s")
        if s["melhor"] is not None:
            text += ", recorde de %s" % duration(s["melhor"])
        parts.append(text + ".")
    return " ".join(parts)


def main_items():
    if has_saved_run():
        return ["Continuar partida salva", "Novo jogo", "Como jogar", "Recordes", "Sair"]
    return ["Jogar", "Como jogar", "Recordes", "Sair"]


def open_main(item=None, announce_help=False):
    main_menu.items = main_items()
    index = main_menu.items.index(item) if item in main_menu.items else 0
    main_menu.open(index=index, announce_help=announce_help)


def on_main(index, item):
    if item == "Continuar partida salva":
        continue_run()
    elif item in ("Jogar", "Novo jogo"):
        main_menu.close()
        level_menu.open(announce_help=False)
    elif item == "Como jogar":
        main_menu.close()
        help_menu.open()
    elif item == "Recordes":
        game.say(stats_text())
    else:
        game.quit()


main_menu = a11y.Menu(game, "Sudoku", main_items(),
                      on_select=on_main, on_back=game.quit, sounds=menu_sounds)

LEVEL_ITEMS = ["%s: %d dicas" % LEVELS[k] for k in LEVEL_ORDER]


def close_levels():
    level_menu.close()
    open_main()


level_menu = a11y.Menu(game, "Nível", LEVEL_ITEMS + ["Voltar"],
                       on_select=lambda i, item: close_levels() if item == "Voltar" else start_run(LEVEL_ORDER[i]),
                       on_back=close_levels, sounds=menu_sounds)


def close_help():
    help_menu.close()
    open_main("Como jogar")


help_menu = a11y.Menu(game, "Como jogar", [t for t, _ in T.HELP] + ["Voltar"],
                      on_select=lambda i, item: close_help() if item == "Voltar" else game.say(T.HELP[i][1]),
                      on_back=close_help, sounds=menu_sounds)


def on_pause(index, item):
    pause_menu.close()
    run = state["run"]
    if item == "Continuar":
        run.play_cell()
        game.say("%s, %s." % (run.where(), run.cell_word()))
        return
    state["run"] = None
    if item == "Salvar e sair para o menu":
        save_run(run)
        game.say("Partida salva. Para voltar a ela, escolha Continuar partida salva no menu.",
                 on_done=lambda done: open_main())
        return
    open_main()


pause_menu = a11y.Menu(game, "Pausa", ["Continuar", "Salvar e sair para o menu", "Sair sem salvar"],
                       on_select=on_pause, on_back=lambda: on_pause(0, "Continuar"),
                       sounds=menu_sounds)


# --- controles ----------------------------------------------------------------
NAVIGATION = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


@game.on_button
def button(b, st, ms):
    run = state["run"]
    if run is None or run.over:
        return
    if st == a11y.REPEAT:
        if b in NAVIGATION:
            run.move(*NAVIGATION[b])
        return
    if st != a11y.DOWN:
        return
    if b in NAVIGATION:
        run.move(*NAVIGATION[b])
    elif b == "b":
        run.step(1)
    elif b == "a":
        run.step(-1)
    elif b == "y":
        game.say(run.status_text())
    elif b == "x":
        game.say(run.candidates_text())
    elif b == "select":
        game.say(run.row_text())
    elif b == "r2":
        game.say(run.column_text())
    elif b == "l2":
        game.say(run.box_text())
    elif b == "l1":
        run.jump(-1)
    elif b == "r1":
        run.jump(1)
    elif b == "start":
        pause_menu.open()


@game.on_update
def update(dt):
    run = state["run"]
    # game._focus: com a pausa aberta, o relógio para.
    if run is not None and not game._focus:
        run.tick(dt)


@game.on_start
def start():
    open_main(announce_help=True)


@game.on_quit
def quit_saving():
    """Fechar o jogo no meio de uma partida (Sair, desligar, Fn + Start) guarda ela."""
    run = state["run"]
    if run is not None and not run.over:
        save_run(run)


# Tela opcional: mostra a grade e a última fala como legenda. Desliga sozinha
# com a tela desligada no sistema ou se o vídeo falhar.
Renderer(game, lambda: state["run"])

game.run()
