# Campo Minado

O clássico, para o R36S acessível, jogável só com som e fala. Cada casa tem
um som (fechada, marcada, vazia e os números de 1 a 8 subindo de tom), que
vem da esquerda ou da direita conforme a coluna. Três níveis: fácil (9 por 9,
10 minas), médio (16 por 16, 40 minas) e difícil (16 por 30, 99 minas). A
primeira casa cavada nunca tem mina.

Feito em Python com a biblioteca do
[r36s-a11y-sdk](https://github.com/gogabs/r36s-a11y-sdk).

## Controles

| Botão | O quê |
|---|---|
| Direcional | Anda pela grade; fala a casa e a coluna (para os lados) ou a linha (para cima e para baixo) |
| B | Cava. Numa casa com número, abre as vizinhas se as marcas em volta batem com ele |
| A | Marca ou desmarca uma mina |
| Y | Minas que faltam, casas abertas e tempo |
| X | A casa e as oito em volta |
| Select / R2 | Lê a linha / a coluna inteira |
| L1 / R1 | Casa fechada anterior / seguinte |
| Start | Pausa: continuar, salvar e sair, ou sair sem salvar |

O tempo só corre depois da primeira escavação e para na pausa. O recorde de
cada nível é o menor tempo. Mais detalhes no menu **Como jogar** ou em
[docs/regras.md](docs/regras.md).

## Tela

A tela mostra a grade e a última fala como legenda, com cores de alto contraste.
É só um extra: tudo também é falado, e ela segue a opção de tela e a economia
de energia do sistema. Veja [docs/graficos.md](docs/graficos.md).

## Rodar

No PC (Windows), de dentro desta pasta:

```bat
python main.py
```

No console, da raiz do repositório: `./instalar.sh r36s ../r36s-a11y-sdk campo-minado`
(ou só `./instalar.sh` para instalar todos os jogos).

## Desenvolvimento

```bash
python3 -m unittest discover -s tests   # testes
python3 tools/gerar_sons.py             # sons provisórios
python3 tools/gerar_graficos.py         # imagens (precisa do Pillow, só no PC)
```

A lógica fica em `minado/` (`board.py` a grade, `run.py` a partida) e não
toca som nem fala; `main.py` liga a partida ao SDK, e `desenho.py` desenha
a grade.
