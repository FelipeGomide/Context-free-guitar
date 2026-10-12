from dataclasses import dataclass

# Cada levada é uma grade que se repete ao longo da música. Cada caractere é
# um passo (semicolcheia quando steps_per_beat = 4, colcheia quando = 2);
# espaços separam compassos e são só para leitura.
#
#   acordes: X = ataque forte, x = ataque fraco, . = nada
#   baixo:   R = fundamental, F = quinta (minúsculas = ataque fraco), . = nada
#
# Cada ataque dura até o próximo ataque da mesma linha, multiplicado por
# legato (1 = ligado, valores menores = mais curto/abafado). Ataques de acorde
# a até `anticipate` passos de uma troca de acorde já tocam o acorde seguinte.


@dataclass(frozen=True)
class Groove:
    meter: tuple
    steps_per_beat: int
    chords: str
    bass: str
    legato: float
    bass_legato: float
    anticipate: int


GROOVES = {
    # Batida do João Gilberto: polegar no tempo alternando fundamental e
    # quinta, dedos no padrão sincopado de dois compassos.
    "BOSSA": Groove(
        meter=(2, 4), steps_per_beat=4,
        chords="X..X..X. ..X..X..",
        bass="R...F... R...F...",
        legato=0.8, bass_legato=0.9, anticipate=2,
    ),
    # Blocado, como em "Na Baixa do Sapateiro": baixo e acorde atacados
    # juntos (as quatro notas de uma vez). Primeiro compasso sincopado,
    # segundo exatamente nos tempos.
    "BLOCADO": Groove(
        meter=(2, 4), steps_per_beat=4,
        chords="X.X..X.. X...X.X.",
        bass="R.R..F.. R...F.F.",
        legato=0.85, bass_legato=0.85, anticipate=0,
    ),
    # Valsa no clima do Jobim ("Chovendo na Roseira"): baixo longo no 1 e
    # acordes no 2 e no 3 (marcando o pulso), com o último ataque do segundo
    # compasso antecipando o próximo acorde. Passo = colcheia.
    "VALSA": Groove(
        meter=(3, 4), steps_per_beat=2,
        chords="..X.X. ..X.xX",
        bass="R..... F.....",
        legato=0.9, bass_legato=0.95, anticipate=1,
    ),
    # Samba-pop sincopado, como em "Linha do Equador": acordes curtos e
    # abafados em semicolcheias e baixo sincopado.
    "DJAVAN": Groove(
        meter=(4, 4), steps_per_beat=4,
        chords="..X.X..X.X..X.X.",
        bass="R..R..F.R.....F.",
        legato=0.45, bass_legato=0.6, anticipate=2,
    ),
    # Samba: baixo de surdo (1 leve, 2 forte na quinta) e acordes sincopados
    # em dois compassos, acentuando as síncopes e com os demais ataques leves.
    "SAMBA": Groove(
        meter=(2, 4), steps_per_beat=4,
        chords="x.xX.x.X .x.Xx.X.",
        bass="r...F... r...F...",
        legato=0.8, bass_legato=0.9, anticipate=2,
    ),
}


def hits(pattern):
    """Ataques de uma linha da grade: (passo, símbolo, passos até o próximo
    ataque), e o tamanho do ciclo em passos."""
    cells = pattern.replace(" ", "")
    positions = [i for i, c in enumerate(cells) if c != "."]
    result = []
    for k, i in enumerate(positions):
        gap = (positions[(k + 1) % len(positions)] - i) % len(cells) or len(cells)
        result.append((i, cells[i], gap))
    return result, len(cells)
