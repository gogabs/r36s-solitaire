# Tela do Campo Minado

A tela é um extra: tudo o que ela mostra também é falado, e o jogo inteiro
funciona com ela desligada. Por isso, ao perder, ela mostra só a mina que
explodiu, que é a que o jogo fala. Ela segue as opções do sistema:
`SCREEN=0` desliga, e a economia de energia baixa os quadros por segundo
(15, 10 ou 5). Se o vídeo falhar, só os gráficos desligam.

## O que aparece

- **Barra de cima**: nível, linha e coluna do cursor, minas que faltam e o
  tempo, como o Y fala.
- **Grade**: casas de 42 pixels no fácil, 24 no médio e 21 no difícil.
- **Cursor**: moldura amarela grossa com contorno preto.
- **Legenda**: a última fala, em duas linhas, embaixo.

## Cores e contraste

Pixel art de casas em relevo: fechada é clara e saltada, aberta é escura e
lisa, então a diferença aparece até sem cor. Contrastes pela fórmula da WCAG
(texto normal pede 4,5 para 1; formas, 3 para 1):

| Par | Cores | Contraste |
|---|---|---|
| Fechada contra aberta | `#8fa3b8` / `#1c2530` | 6,0 |
| Fechada contra o fundo | `#8fa3b8` / `#0f1720` | 7,0 |
| Contorno da bandeira e mastro na casa fechada | `#000000` / `#8fa3b8` | 8,1 |
| Cursor sobre o fundo | `#ffd60a` / `#0f1720` | 12,8 |
| Texto na faixa amarela do menu | `#000000` / `#ffd60a` | 14,9 |

Cada número tem sua cor, todas com pelo menos 7 para 1 sobre a casa aberta
(`#1c2530`):

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| `#6cb4ff` 7,1 | `#5fd38d` 8,3 | `#ff9a92` 7,6 | `#c9a0ff` 7,3 | `#ffb454` 8,8 | `#4fd6d6` 8,8 | `#f2f2f2` 13,8 | `#b0b8c0` 7,7 |

A cor só ajuda: o algarismo está sempre lá, em negrito. O 2 verde e o 3
vermelho, que se confundem no daltonismo, diferem também em claridade. A
bandeira vermelha tem contorno preto, e a mina que explodiu é preta sobre
vermelho.

## Gerar de novo

As casas são PNG prontos em `graficos/`; o console não precisa do Pillow.
No PC, com o Pillow:

```bash
python3 tools/gerar_graficos.py     # graficos/casas-42.png, -24 e -21
python3 tools/previa.py prévias     # telas de exemplo em PNG
```
