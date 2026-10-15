# Tela da Paciência

A tela é um extra: tudo o que ela mostra também é falado, e o jogo inteiro
funciona com ela desligada. Ela segue as opções do sistema: `SCREEN=0`
desliga, e a economia de energia baixa os quadros por segundo (15, 10 ou 5).
Se o vídeo falhar, só os gráficos desligam.

## O que aparece

- **Barra de cima**: o jogo e a pontuação, as mesmas que o Y fala.
- **Mesa**: cartas grandes (72 × 100) no Klondike e no FreeCell, menores
  (58 × 80) no Spider, que tem dez colunas. As colunas apertam sozinhas para
  caber.
- **Foco**: moldura amarela grossa com contorno preto. A carta em foco aparece
  inteira, mesmo no meio de uma coluna.
- **Na mão**: as cartas pegas sobem um pouco, com moldura branca e a etiqueta
  "NA MÃO"; a pilha em foco ganha a etiqueta "CABE" quando aceita elas.
- **Legenda**: a última fala, em duas linhas, embaixo.

## Cores e contraste

Arte vetorial chapada, sem degradê. Contrastes pela fórmula da WCAG
(texto normal pede 4,5 para 1; formas, 3 para 1):

| Par | Cores | Contraste |
|---|---|---|
| Carta sobre o feltro | `#fbfbf7` / `#0d3b2e` | 12,0 |
| Naipe preto na carta | `#151515` / `#fbfbf7` | 17,6 |
| Naipe vermelho na carta | `#b8102a` / `#fbfbf7` | 6,4 |
| Letra da figura sobre o naipe claro | `#b8102a` / `#f7d9dd` | 5,1 |
| Foco sobre o feltro | `#ffd60a` / `#0d3b2e` | 8,8 |
| Texto na faixa amarela do menu | `#000000` / `#ffd60a` | 14,9 |
| Lugar vazio | `#86c2a5` / `#0a3024` | 7,0 |
| Texto da barra e da legenda | `#ffffff` / `#000000` | 21 |

A cor nunca é a única pista: copas, ouros, paus e espadas têm formas bem
diferentes, e o valor vem em letra grande no canto de cima, a parte que fica
à mostra com as cartas sobrepostas. O verso azul tem treliça e moldura branca
para não se confundir com uma carta aberta. O foco tem contorno preto por
dentro e por fora, então aparece tanto no feltro escuro quanto na carta
clara; a mão usa branco, para não brigar com o amarelo do foco.

## Gerar de novo

As cartas são PNG prontos em `graficos/`; o console não precisa do Pillow.
No PC, com o Pillow:

```bash
python3 tools/gerar_graficos.py     # graficos/cartas-g.png e cartas-p.png
python3 tools/previa.py prévias     # telas de exemplo em PNG
```
