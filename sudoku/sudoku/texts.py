"""Textos de ajuda, lidos no menu Como jogar."""

HELP = [
    ("Objetivo",
     "Preencha a grade de 9 por 9 com números de 1 a 9, sem repetir nenhum número na "
     "mesma linha, na mesma coluna ou no mesmo bloco. Os blocos são os nove quadrados "
     "de 3 por 3, numerados de 1 a 9 como um texto: 1, 2 e 3 em cima, 7, 8 e 9 embaixo. "
     "Algumas casas já vêm com número; essas são as dicas, ou números fixos, e não "
     "mudam. Cada partida tem uma solução só."),
    ("Controles",
     "O direcional anda pela grade; andando para os lados, o jogo fala a casa e a "
     "coluna, e para cima ou para baixo, a casa e a linha. Ao entrar em outro bloco, "
     "ele fala o bloco também. B aumenta o número da casa: vazia, 1, 2, até 9, e volta "
     "para vazia. A diminui. X fala os números que cabem na casa. Y fala quantas casas "
     "faltam e o tempo. Select lê a linha inteira, R2 a coluna e L2 o bloco, com os "
     "números que faltam. L1 e R1 pulam para a casa vazia anterior ou seguinte. Start "
     "pausa; dá para salvar e continuar depois."),
    ("Números repetidos",
     "Se o número que você escreveu já existe na linha, na coluna ou no bloco, o jogo "
     "toca um aviso e fala onde ele repete. O número fica lá até você trocar. Quando "
     "uma linha, coluna ou bloco fica com os nove números, toca um sino."),
    ("Sons",
     "Cada número tem um tom, do mais grave, o 1, ao mais agudo, o 9. As dicas soam "
     "como sino e os seus números como um toque suave; casa vazia é um sopro. O som "
     "vem da esquerda ou da direita conforme a coluna."),
    ("Níveis",
     "Fácil começa com 40 dicas, médio com 32 e difícil com 26. O recorde de cada "
     "nível é o menor tempo."),
]
