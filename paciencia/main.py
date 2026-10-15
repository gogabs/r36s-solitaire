#!/usr/bin/env python3
"""Paciência: Klondike, FreeCell e Spider, jogáveis só com som e fala."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# Instalado, a biblioteca vem junto do jogo; no repositório, usa a cópia da raiz.
if not os.path.isdir(os.path.join(HERE, "r36s_a11y")):
    sys.path.insert(1, os.path.join(HERE, ".."))

import r36s_a11y as a11y

from paciencia import GAMES, ORDER
from paciencia import texts as T
from paciencia.cards import plural
from paciencia.desenho import Renderer

game = a11y.Game(repeat=True)
SAVE_FILE = os.path.join(game.save_dir, "progresso.json")
sounds = {}
for f in sorted(os.listdir(os.path.join(game.dir, "sounds"))):
    base, ext = os.path.splitext(f)
    if ext.lower() in (".wav", ".ogg"):
        sounds[base] = game.sound.load(base, os.path.join("sounds", f))
menu_sounds = {"move": sounds.get("menu_mover"), "select": sounds.get("menu_confirmar")}

state = {"run": None, "kind": ORDER[0]}


# --- progresso ---------------------------------------------------------------
def load_progress():
    try:
        with open(SAVE_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    for g in ORDER:
        data.setdefault(g.ID, {"iniciadas": 0, "vitorias": 0, "melhor": None})
    return data


def save_progress(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


# --- partida salva (uma por jogo) ----------------------------------------------
def run_file(kind):
    return os.path.join(game.save_dir, "partida-%s.json" % kind.ID)


def has_saved_run(kind):
    return os.path.isfile(run_file(kind))


def save_run(run):
    """Arquivo temporário e troca, para um desligamento no meio não estragar o save."""
    path = run_file(type(run))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(run.to_dict(), f, ensure_ascii=False)
    os.replace(tmp, path)


def drop_saved_run(kind):
    try:
        os.remove(run_file(kind))
    except OSError:
        pass


# --- som e fala ----------------------------------------------------------------
class UI:
    def say(self, text, queue=False):
        game.say(text, queue=queue)

    def play(self, name, pan=None, pitch=1.0):
        sound = sounds.get(name)
        if sound is not None:
            sound.play(pan=pan, pitch=pitch)


ui = UI()


# --- fluxo ---------------------------------------------------------------------
def start_run(kind, **options):
    game_menu.close()
    data = load_progress()
    data[kind.ID]["iniciadas"] += 1
    save_progress(data)
    run = kind(ui, on_over=game_over, **options)
    state["run"] = run
    run.start()
    if has_saved_run(kind):
        game.say("A partida salva de %s continua guardada. Salvar esta substitui aquela." % kind.NAME,
                 queue=True)


def continue_run(kind):
    """Retoma a partida salva. O save é usado uma vez: sair do jogo ou escolher
    "Salvar e sair" grava de novo."""
    try:
        with open(run_file(kind), encoding="utf-8") as f:
            run = kind.from_dict(ui, json.load(f), on_over=game_over)
    except (OSError, ValueError) as exc:
        print("[paciencia] partida salva ilegível: %s" % exc, file=sys.stderr)
        drop_saved_run(kind)
        game_menu.close()
        game.say("Não deu para ler a partida salva. Ela foi descartada.",
                 on_done=lambda done: open_game_menu(kind))
        return
    drop_saved_run(kind)
    game_menu.close()
    state["run"] = run
    run.resume()


def better(kind, new, old):
    if old is None:
        return True
    return new < old if kind.ID == "freecell" else new > old


def game_over(summary):
    kind = GAMES[summary["jogo"]]
    data = load_progress()
    stats = data[kind.ID]
    stats["vitorias"] += 1
    # FreeCell: o melhor é o menor número de jogadas; nos outros, os pontos.
    value = summary["moves"] if kind.ID == "freecell" else summary["score"]
    record = better(kind, value, stats["melhor"])
    if record:
        stats["melhor"] = value
    save_progress(data)
    if kind.ID == "freecell":
        text = "Você venceu, em %s!" % plural(summary["moves"], "jogada")
    else:
        text = "Você venceu, com %d pontos, em %s!" % (summary["score"], plural(summary["moves"], "jogada"))
    if record:
        text += " Novo recorde!"
    text += " %s vitória%s no %s." % (stats["vitorias"], "" if stats["vitorias"] == 1 else "s", kind.NAME)
    state["run"] = None
    game.after(1.5, lambda: game.say(text, on_done=lambda done: open_game_menu(kind)))


def stats_text():
    data = load_progress()
    parts = []
    for kind in ORDER:
        s = data[kind.ID]
        text = "%s: %s, %s" % (kind.NAME, plural(s["iniciadas"], "partida"),
                               plural(s["vitorias"], "vitória"))
        if s["melhor"] is not None:
            text += ", melhor %s" % (plural(s["melhor"], "jogada") if kind.ID == "freecell"
                                     else "%d pontos" % s["melhor"])
        parts.append(text + ".")
    return " ".join(parts)


# --- menus -----------------------------------------------------------------------
def main_items():
    items = []
    for kind in ORDER:
        items.append(kind.NAME + (", com partida salva" if has_saved_run(kind) else ""))
    return items + ["Como jogar", "Estatísticas", "Sair"]


def open_main(index=0, announce_help=False):
    main_menu.items = main_items()
    main_menu.open(index=index, announce_help=announce_help)


def on_main(index, item):
    if index < len(ORDER):
        main_menu.close()
        open_game_menu(ORDER[index])
    elif item == "Como jogar":
        main_menu.close()
        help_menu.open()
    elif item == "Estatísticas":
        game.say(stats_text())
    else:
        game.quit()


main_menu = a11y.Menu(game, "Paciência", main_items(),
                      on_select=on_main, on_back=game.quit, sounds=menu_sounds)

NEW_GAMES = {
    "klondike": [("Novo jogo, comprando 1", {"draw": 1}), ("Novo jogo, comprando 3", {"draw": 3})],
    "freecell": [("Novo jogo", {})],
    "spider": [("Novo jogo, 1 naipe", {"suits": 1}), ("Novo jogo, 2 naipes", {"suits": 2}),
               ("Novo jogo, 4 naipes", {"suits": 4})],
}


def game_items(kind):
    items = ["Continuar partida salva"] if has_saved_run(kind) else []
    return items + [label for label, _ in NEW_GAMES[kind.ID]] + ["Voltar"]


def open_game_menu(kind):
    state["kind"] = kind
    game_menu.title = kind.NAME
    game_menu.items = game_items(kind)
    game_menu.open(announce_help=False)


def back_to_main():
    game_menu.close()
    open_main(ORDER.index(state["kind"]))


def on_game(index, item):
    kind = state["kind"]
    if item == "Continuar partida salva":
        continue_run(kind)
    elif item == "Voltar":
        back_to_main()
    else:
        start_run(kind, **dict(NEW_GAMES[kind.ID])[item])


game_menu = a11y.Menu(game, "Klondike", ["Voltar"], on_select=on_game,
                      on_back=back_to_main, sounds=menu_sounds)


def close_help():
    help_menu.close()
    open_main(len(ORDER))


help_menu = a11y.Menu(game, "Como jogar", [t for t, _ in T.HELP] + ["Voltar"],
                      on_select=lambda i, item: close_help() if item == "Voltar" else game.say(T.HELP[i][1]),
                      on_back=close_help, sounds=menu_sounds)


def on_pause(index, item):
    pause_menu.close()
    run = state["run"]
    if item == "Continuar":
        run.announce_pile()
        return
    state["run"] = None
    kind = type(run)
    if item == "Salvar e sair para o menu":
        save_run(run)
        game.say("Partida salva. Para voltar a ela, escolha Continuar partida salva.",
                 on_done=lambda done: open_game_menu(kind))
        return
    open_game_menu(kind)


pause_menu = a11y.Menu(game, "Pausa", ["Continuar", "Salvar e sair para o menu", "Sair sem salvar"],
                       on_select=on_pause, on_back=lambda: on_pause(0, "Continuar"),
                       sounds=menu_sounds)


# --- controles ---------------------------------------------------------------------
NAVIGATION = {"left": lambda r: r.step(-1), "right": lambda r: r.step(1),
              "up": lambda r: r.card_step(-1), "down": lambda r: r.card_step(1)}


@game.on_button
def button(b, st, ms):
    run = state["run"]
    if run is None or run.over:
        return
    if st == a11y.REPEAT:
        if b in NAVIGATION:
            NAVIGATION[b](run)
        return
    if st != a11y.DOWN:
        return
    if b in NAVIGATION:
        NAVIGATION[b](run)
    elif b == "b":
        run.press()
    elif b == "a":
        run.undo()
    elif b == "x":
        run.draw()
    elif b == "y":
        game.say(run.status_text())
    elif b == "r1":
        run.to_foundation()
    elif b == "l1":
        run.hint()
    elif b == "select":
        game.say(run.table_text())
    elif b == "r2":
        game.say(run.pile_text())
    elif b == "start":
        pause_menu.open()


@game.on_start
def start():
    open_main(announce_help=True)


@game.on_quit
def quit_saving():
    """Fechar o jogo no meio de uma partida (Sair, desligar, Fn + Start) guarda ela."""
    run = state["run"]
    if run is not None and not run.over:
        save_run(run)


# Tela opcional: mostra a mesa e a última fala como legenda. Desliga sozinha
# com a tela desligada no sistema ou se o vídeo falhar.
Renderer(game, lambda: state["run"])

game.run()
