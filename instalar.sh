#!/bin/bash
# Empacota os jogos com a biblioteca Python do SDK e instala no console.
#
#   ./instalar.sh [host-ssh] [pasta-do-sdk] [jogo...]
#   padrão: r36s, ../r36s-a11y-sdk (clone de github.com/gogabs/r36s-a11y-sdk)
#   e todos os jogos (paciencia campo-minado)
#
# Não reinicia nada: a galeria percebe os jogos novos sozinha. Com um jogo aberto,
# não instala, porque ele carrega os sons sob demanda da pasta instalada.
set -euo pipefail
HOST=${1:-r36s}
HERE=$(cd "$(dirname "$0")" && pwd)
SDK=${2:-$HERE/../r36s-a11y-sdk}
shift $(( $# < 2 ? $# : 2 ))
GAMES=("$@")
[ ${#GAMES[@]} -gt 0 ] || GAMES=(paciencia campo-minado sudoku)
SDK_PY="$SDK/python/r36s_a11y"
if [ ! -d "$SDK_PY" ]; then
  SDK_PY="$HERE/r36s_a11y"
fi
[ -d "$SDK_PY" ] || { echo "SDK não encontrado."; exit 1; }
echo "SDK selecionada: $SDK_PY"

for ID in "${GAMES[@]}"; do
  [ -f "$HERE/$ID/game.json" ] || { echo "Jogo desconhecido: $ID"; exit 1; }
  if ssh "$HOST" "for p in /proc/[0-9]*; do readlink \"\$p/cwd\"; done 2>/dev/null | grep -q '^/opt/a11y/games/$ID'"; then
    echo "$ID está aberto no console. Feche o jogo e rode de novo."
    exit 1
  fi
done

PKG=$(mktemp -d)
trap 'rm -rf "$PKG"' EXIT
for ID in "${GAMES[@]}"; do
  mkdir -p "$PKG/$ID"
  ( cd "$HERE/$ID" && cp -r game.json main.py sounds "$PKG/$ID/" )
  for d in "$HERE/$ID"/*/; do
    case "$(basename "$d")" in tests|tools|docs) ;; *) cp -r "$d" "$PKG/$ID/" ;; esac
  done
  cp -r "$SDK_PY" "$PKG/$ID/"
done
find "$PKG" -name __pycache__ -prune -exec rm -rf {} +

tar -C "$PKG" -czf - "${GAMES[@]}" | ssh "$HOST" "
  set -e; cd /opt/a11y/games
  rm -rf .solitarios.novo && mkdir .solitarios.novo
  tar -xzf - -C .solitarios.novo
  for ID in ${GAMES[*]}; do
    rm -rf \$ID && mv .solitarios.novo/\$ID . && echo \"instalado: \$ID, \$(ls \$ID/sounds | wc -l) sons\"
  done
  rmdir .solitarios.novo; df -h /opt/a11y | tail -1"
