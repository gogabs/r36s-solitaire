# Solitários (r36s-solitaire)

Jogos solitaire para o R36S acessível, jogáveis só com som e fala. Cada pasta
é um jogo da galeria:

| Pasta | Jogo |
|---|---|
| [`paciencia/`](paciencia/) | **Paciência**: Klondike, FreeCell e Spider sobre uma base comum |
| [`campo-minado/`](campo-minado/) | **Campo Minado**: fácil, médio e difícil |
| [`sudoku/`](sudoku/) | **Sudoku**: fácil, médio e difícil, com grades sorteadas |

Feitos em Python com a biblioteca do
[r36s-a11y-sdk](https://github.com/gogabs/r36s-a11y-sdk). A cópia de reserva da
biblioteca fica em `r36s_a11y/`, na raiz, e serve a todos os jogos
([origem e atualização](SDK-ORIGIN.md)).

## Controles comuns

Start pausa, com continuar, salvar e sair, ou sair sem salvar; fechar o jogo
no meio de uma partida guarda ela. Y fala a pontuação. Os controles de cada
jogo estão no README da pasta e no menu **Como jogar**.

Os jogos também têm tela, com cores de alto contraste, mas ela é só um
extra: nada aparece nela sem ser falado.

## Instalar no console

Com o SDK clonado ao lado deste repositório:

```bash
./instalar.sh                                     # todos os jogos
./instalar.sh r36s ../r36s-a11y-sdk campo-minado  # só um
```

## Desenvolvimento

Cada jogo tem seus testes e seu gerador de sons provisórios:

```bash
cd paciencia && python3 -m unittest discover -s tests && python3 tools/gerar_sons.py
```

Para um jogo novo, crie uma pasta com `game.json`, `main.py` (que acha a
biblioteca na raiz, como os outros) e `tests/`, e acrescente-a na lista do
CI em `.github/workflows/testes.yml` e em `instalar.sh`.
