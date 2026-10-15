# Paciência

Três jogos de paciência para o R36S acessível, jogáveis só com som e fala:
**Klondike** (comprando 1 ou 3), **FreeCell** (com os jogos numerados do
Windows) e **Spider** (1, 2 ou 4 naipes). As pilhas soam da esquerda para a
direita na ordem da mesa, e cada carta é falada pelo nome: "dama de copas",
"7 de paus".

Feito em Python com a biblioteca do
[r36s-a11y-sdk](https://github.com/gogabs/r36s-a11y-sdk).

## Controles

| Botão | O quê |
|---|---|
| Esquerda / direita | Pilha anterior / seguinte (dá a volta) |
| Cima / baixo | Carta de baixo / de cima dentro da coluna |
| B | Pega a carta em foco (com as que estão sobre ela) ou solta o que está na mão. No estoque, compra |
| A | Desfaz a última jogada; com cartas na mão, devolve elas |
| X | Compra (Klondike) ou distribui uma carta em cada coluna (Spider) |
| Y | Pontos e situação da partida |
| R1 | Manda a carta de cima para a fundação |
| L1 | Dica: diz uma jogada e leva o foco até a carta |
| Select | Lê a mesa inteira |
| R2 | Lê a coluna em foco inteira |
| Start | Pausa: continuar, salvar e sair, ou sair sem salvar |

Com cartas na mão, ao passar por uma pilha que aceita elas, o jogo diz
"cabe". Regras de cada jogo: menu **Como jogar**, ou
[docs/regras.md](docs/regras.md).

## Tela

A tela mostra a mesa e a última fala como legenda, com cores de alto contraste.
É só um extra: tudo também é falado, e ela segue a opção de tela e a economia
de energia do sistema. Veja [docs/graficos.md](docs/graficos.md).

## Rodar

No PC (Windows), de dentro desta pasta:

```bat
python main.py
```

No console, da raiz do repositório: `./instalar.sh r36s ../r36s-a11y-sdk paciencia`
(ou só `./instalar.sh` para instalar todos os jogos).

## Desenvolvimento

```bash
python3 -m unittest discover -s tests   # testes
python3 tools/gerar_sons.py             # sons provisórios
python3 tools/gerar_graficos.py         # imagens (precisa do Pillow, só no PC)
```

A lógica fica em `paciencia/`: `base.py` tem o que os três jogos dividem
(pilhas, foco, pegar e soltar, desfazer, dica, leitura da mesa, partida
salva) e `klondike.py`, `freecell.py` e `spider.py` só as regras de cada um.
Ela não toca som nem fala; `main.py` liga a partida ao SDK, e `desenho.py`
desenha a mesa.
