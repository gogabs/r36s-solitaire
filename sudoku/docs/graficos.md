# Tela do Sudoku

A tela é um extra: tudo o que ela mostra também é falado, e o jogo inteiro
funciona com ela desligada. Ela segue as opções do sistema: `SCREEN=0`
desliga, e a economia de energia baixa os quadros por segundo (15, 10 ou 5).
Se o vídeo falhar, só os gráficos desligam.

## O que aparece

- **Barra de cima**: nível, linha e coluna do cursor, casas que faltam e o
  tempo, como o Y fala.
- **Grade**: casas de 42 pixels, com linhas finas entre as casas e grossas e
  claras entre os blocos.
- **Cursor**: moldura amarela grossa com contorno preto. A linha, a coluna e
  o bloco dele ficam num azul um pouco mais claro, e as casas com o mesmo
  número dele ficam verdes.
- **Número repetido**: a casa e as que ela repete ficam com fundo vermelho.
- **Legenda**: a última fala, em duas linhas, embaixo.

## Cores e contraste

Contrastes pela fórmula da WCAG (texto normal pede 4,5 para 1):

| Algarismo | Casa comum `#1c2530` | Dica `#2a3646` | Linha do cursor `#22364c` | Mesmo número `#1f4a33` | Repetido `#6a1a22` |
|---|---|---|---|---|---|
| Dica, branco negrito `#ffffff` | 15,5 | 12,2 | 12,4 | 10,1 | 11,8 |
| Seu, azul claro `#7cc4ff` | 8,3 | — | 6,6 | 5,4 | — |
| Seu repetido, rosa `#ffd6d2` | — | — | — | — | 8,9 |

A cor nunca é a única pista: a dica é negrito sobre casa mais clara, o seu
número é traço fino, e o repetido muda o fundo inteiro da casa. As linhas dos
blocos (`#c9d5e1`) têm 10,4 para 1 contra a casa, e o cursor (`#ffd60a`),
11,0.

## Gerar de novo

Os algarismos são um PNG pronto em `graficos/`; o console não precisa do
Pillow. No PC, com o Pillow:

```bash
python3 tools/gerar_graficos.py     # graficos/numeros-42.png
python3 tools/previa.py prévias     # telas de exemplo em PNG
```
