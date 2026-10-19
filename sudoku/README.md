# Sudoku

O clássico, para o R36S acessível, jogável só com som e fala. Cada número tem
um tom, do 1 mais grave ao 9 mais agudo; as dicas soam como sino e os seus
números como um toque suave, e o som vem da esquerda ou da direita conforme a
coluna. Três níveis: fácil (40 dicas), médio (32) e difícil (26). Toda grade
é sorteada na hora e tem uma solução só.

Feito em Python com a biblioteca do
[r36s-a11y-sdk](https://github.com/gogabs/r36s-a11y-sdk).

## Controles

| Botão | O quê |
|---|---|
| Direcional | Anda pela grade; fala a casa e a coluna (para os lados) ou a linha (para cima e para baixo), e o bloco ao entrar em outro |
| B / A | Aumenta / diminui o número da casa (vazia, 1 a 9, vazia); avisa se ele repete na linha, coluna ou bloco |
| X | Os números que cabem na casa |
| Y | Casas que faltam, números repetidos e tempo |
| Select / R2 / L2 | Lê a linha / a coluna / o bloco inteiro, com os números que faltam |
| L1 / R1 | Casa vazia anterior / seguinte |
| Start | Pausa: continuar, salvar e sair, ou sair sem salvar |

Linha, coluna ou bloco completo toca um sino. O recorde de cada nível é o
menor tempo. Mais detalhes no menu **Como jogar** ou em
[docs/regras.md](docs/regras.md).

## Tela

A tela mostra a grade e a última fala como legenda, com cores de alto
contraste. É só um extra: tudo também é falado, e ela segue a opção de tela e
a economia de energia do sistema. Veja [docs/graficos.md](docs/graficos.md).

## Rodar

No PC (Windows), de dentro desta pasta:

```bat
python main.py
```

No console, da raiz do repositório: `./instalar.sh r36s ../r36s-a11y-sdk sudoku`
(ou só `./instalar.sh` para instalar todos os jogos).

## Desenvolvimento

```bash
python3 -m unittest discover -s tests   # testes
python3 tools/gerar_sons.py             # sons provisórios
python3 tools/gerar_graficos.py         # imagens (precisa do Pillow, só no PC)
```

A lógica fica em `sudoku/` (`grade.py` a grade, as regras e o gerador,
`run.py` a partida) e não toca som nem fala; `main.py` liga a partida ao Mage Core,
e `desenho.py` desenha a grade.
