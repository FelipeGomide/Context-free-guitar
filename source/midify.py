import random
from bisect import bisect_right

import pretty_midi

from .grooves import GROOVES, hits

PITCH_CLASSES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
LETTERS = "CDEFGAB"
LETTER_PCS = [0, 2, 4, 5, 7, 9, 11]
DEGREES = ["I", "II", "III", "IV", "V", "VI", "VII"]
SCALES = {"maior": [0, 2, 4, 5, 7, 9, 11], "menor": [0, 2, 3, 5, 7, 8, 10]}

# Qualidade do acorde pelas terças empilhadas da escala: (3ª, 5ª, 7ª) em semitons.
QUALITIES = {
    (4, 7, 11): "maj",
    (3, 7, 10): "min",
    (4, 7, 10): "dom",
    (3, 6, 10): "hdim",
}

# Cor abstrata da gramática (EXT) -> cifra, por qualidade.
COLORS = {
    "maj": {"7": "7M", "9": "7M(9)", "6": "6(9)", "11": "7M(#11)", "alt": "7M(9)"},
    "min": {"7": "m7", "9": "m7(9)", "6": "m6(9)", "11": "m7(11)", "alt": "m7(9)"},
    "dom": {"7": "7", "9": "7(9)", "6": "7(13)", "11": "7(4)(9)", "alt": "7(b9)"},
    "hdim": {"7": "m7(b5)", "9": "m7(b5)(9)", "6": "m7(b5)", "11": "m7(b5)(11)", "alt": "m7(b5)(9)"},
}

# Notas acima da fundamental. Violão pinçado: o polegar toca a fundamental no
# baixo e indicador, médio e anelar tocam no máximo três vozes. A 5ª justa só
# entra nos acordes sem tensão; com tensão ela sai.
INTERVALS = {
    "7M": [4, 7, 11],
    "7M(9)": [4, 11, 14],
    "6(9)": [4, 9, 14],
    "7M(#11)": [4, 11, 18],        # sem a 9ª
    "m7": [3, 7, 10],
    "m7(9)": [3, 10, 14],
    "m6(9)": [3, 9, 14],
    "m7(11)": [3, 10, 17],
    "7": [4, 7, 10],
    "7(9)": [4, 10, 14],
    "7(13)": [4, 10, 21],
    "7(4)(9)": [5, 10, 14],
    "7(b9)": [4, 10, 13],
    "7(b13)": [4, 10, 20],
    "m7(b5)": [3, 6, 10],
    "m7(b5)(9)": [6, 10, 14],      # sem a 3ª
    "m7(b5)(11)": [6, 10, 17],     # sem a 3ª
}

BASS_LOW = 40                      # E2: o baixo fica entre E2 e Eb3
UPPER_LOW, UPPER_HIGH = 52, 76     # região das vozes de cima (E3 a E5)
UPPER_CENTER = 64
VELOCITY = {"X": 85, "x": 62, "R": 90, "F": 90, "r": 68, "f": 68}

# Humanização do pinçado, em segundos (força em unidades de velocity MIDI).
FINGER_SPREAD = 0.008    # os três dedos não puxam no mesmo instante
THUMB_SPREAD = 0.006     # o polegar sai um pouco antes ou depois dos dedos
HIT_JITTER = 0.005       # o ataque inteiro cai um pouco fora da grade
VELOCITY_SPREAD = 6      # cada dedo puxa com uma força um pouco diferente


def analyze(root_pc, mode, degree):
    """Fundamental, qualidade e se a 11ª diatônica é aumentada (lídio)."""
    scale = list(SCALES[mode])
    if mode == "menor" and degree == "V":
        scale[6] = 11  # sensível: V maior na menor
    d = DEGREES.index(degree)

    def above(steps):
        i = d + steps
        return scale[i % 7] + 12 * (i // 7) - scale[d]

    quality = QUALITIES[(above(2), above(4), above(6))]
    return (root_pc + scale[d]) % 12, quality, above(10) == 18


def spell(root_pc, degree, pc):
    """Nome da nota com a letra do grau (ex.: VII de Lá maior = G#, não Ab)."""
    letter = (LETTERS.index(PITCH_CLASSES[root_pc][0]) + DEGREES.index(degree)) % 7
    offset = (pc - LETTER_PCS[letter] + 6) % 12 - 6
    return LETTERS[letter] + ("#" * offset if offset > 0 else "b" * -offset)


def build_chord(root_pc, mode, degree, ext):
    """Retorna (cifra, pitch class da fundamental, intervalos acima dela)."""
    chord_root, quality, lydian = analyze(root_pc, mode, degree)
    name = COLORS[quality][ext]
    if name == "7M(#11)" and not lydian:
        name = "7M(9)"
    if name == "m6(9)" and degree != "I":
        name = "m7(9)"
    if name == "7(b9)" and mode == "maior":
        name = "7(b13)"
    return spell(root_pc, degree, chord_root) + name, chord_root, INTERVALS[name]


def voice(chord_root, intervals, previous=None):
    """Baixo na fundamental e as vozes de cima com a menor movimentação
    possível em relação ao acorde anterior."""
    bass = BASS_LOW + (chord_root - BASS_LOW) % 12
    notes = sorted(chord_root + i for i in intervals)
    candidates = []
    for _ in range(len(notes)):
        low = notes[0] - 12 * ((notes[0] - UPPER_LOW) // 12)
        shifted = [n + low - notes[0] for n in notes]
        for octave in (0, 12):
            option = [n + octave for n in shifted]
            if option[-1] <= UPPER_HIGH:
                candidates.append(option)
        notes = sorted(notes[1:] + [notes[0] + 12])  # próxima inversão

    def cost(option):
        center = abs(sum(option) / len(option) - UPPER_CENTER)
        if previous is None:
            return (center, 0)
        motion = sum(min(abs(n - p) for p in previous) for n in option)
        return (motion, center)

    return bass, min(candidates, key=cost)


def parse(tokens):
    """Lê a sequência gerada pela gramática.

    Cabeçalho: levada bpm 'A:' tom modo 'B:' tom modo.
    Corpo: '[A]'/'[B]' abre uma seção e '|' abre um compasso; cada compasso
    tem um ou mais pares (grau, extensão), que dividem o compasso igualmente.

    Retorna (levada, bpm, {seção: (tom, modo)},
             [(seção, [[(grau, ext), ...], ...]), ...]).
    """
    groove, bpm = tokens[0], int(tokens[1])
    keys = {}
    i = 2
    while tokens[i].endswith(":"):
        label, root, mode = tokens[i:i + 3]
        keys[label[:-1]] = (PITCH_CLASSES.index(root), mode)
        i += 3

    sections = []
    for token in tokens[i:]:
        if token.startswith("["):
            sections.append((token[1:-1], []))
        elif token == "|":
            sections[-1][1].append([])
        else:
            sections[-1][1][-1].append(token)
    return groove, bpm, keys, [
        (name, [list(zip(bar[::2], bar[1::2])) for bar in bars])
        for name, bars in sections
    ]


def fifth(bass, intervals):
    """Quinta do acorde no baixo, na região do baixo. Nos meio-diminutos a
    quinta é diminuta e soa mal no baixo, então repete a fundamental."""
    if 6 in intervals:
        return bass
    return bass + 7 if bass + 7 <= BASS_LOW + 12 else bass - 5


def timeline(tokens):
    """Acordes no tempo, em passos da grade da levada:
    [(início, baixo, vozes de cima, intervalos, armadura)], total de passos."""
    groove_name, _, keys, sections = parse(tokens)
    groove = GROOVES[groove_name]
    bar_steps = groove.meter[0] * groove.steps_per_beat
    chords = []
    step = 0.0
    previous = None
    for name, bars in sections:
        root_pc, mode = keys[name]
        key_number = root_pc + (12 if mode == "menor" else 0)
        for bar in bars:
            for degree, ext in bar:
                _, chord_root, intervals = build_chord(root_pc, mode, degree, ext)
                bass, upper = voice(chord_root, intervals, previous)
                chords.append((step, bass, upper, intervals, key_number))
                previous = upper
                step += bar_steps / len(bar)
    return chords, step


def to_midi(tokens, program=24):
    """Toca a levada sorteada sobre os acordes, como violão pinçado: polegar
    no baixo e indicador, médio e anelar nas vozes de cima, em trilhas
    separadas. Programa 24 = violão de nylon (General MIDI).

    As pequenas variações de tempo e força vêm de um sorteio semeado pela
    própria sequência, então a mesma música gera sempre o mesmo MIDI."""
    groove_name, bpm, _, _ = parse(tokens)
    groove = GROOVES[groove_name]
    step_time = 60 / bpm / groove.steps_per_beat
    chords, total = timeline(tokens)
    starts = [c[0] for c in chords]

    def chord_at(step):
        return chords[max(bisect_right(starts, step) - 1, 0)]

    midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    midi.time_signature_changes.append(pretty_midi.TimeSignature(*groove.meter, 0))
    for i, (start, *_, key_number) in enumerate(chords):
        if i == 0 or key_number != chords[i - 1][4]:
            midi.key_signature_changes.append(pretty_midi.KeySignature(key_number, start * step_time))

    bass_track = pretty_midi.Instrument(program=program, name="Baixo")
    chord_track = pretty_midi.Instrument(program=program, name="Acordes")

    rng = random.Random(" ".join(tokens))
    hit_offsets = {}  # mesmo deslocamento para polegar e dedos no mesmo passo

    def play(track, pattern, legato, pitches_for, offset, spread):
        pattern_hits, cycle = hits(pattern)
        for cycle_start in range(0, int(total) + cycle, cycle):
            for position, symbol, gap in pattern_hits:
                step = cycle_start + position
                if step >= total:
                    return
                hit = hit_offsets.setdefault(step, rng.uniform(-HIT_JITTER, HIT_JITTER))
                end = min(step + gap * legato, total) * step_time + hit
                for pitch in pitches_for(chord_at(step + offset), symbol):
                    start = max(step * step_time + hit + rng.uniform(*spread), 0)
                    velocity = VELOCITY[symbol] + rng.randint(-VELOCITY_SPREAD, VELOCITY_SPREAD)
                    track.notes.append(pretty_midi.Note(
                        min(max(velocity, 1), 127), pitch, start, max(end, start + 0.02)))

    play(chord_track, groove.chords, groove.legato,
         lambda chord, _: chord[2], groove.anticipate, (0, FINGER_SPREAD))
    play(bass_track, groove.bass, groove.bass_legato,
         lambda chord, symbol: [chord[1] if symbol in "Rr" else fifth(chord[1], chord[3])],
         0, (-THUMB_SPREAD, THUMB_SPREAD))

    midi.instruments += [bass_track, chord_track]
    return midi


def chart(tokens):
    """Cifra legível: levada, tonalidades das seções e uma linha de compassos
    por seção."""
    groove_name, bpm, keys, sections = parse(tokens)
    numerator, denominator = GROOVES[groove_name].meter
    lines = [f"Levada: {groove_name}, {bpm} bpm, {numerator}/{denominator}"]
    lines += [f"{name}: {PITCH_CLASSES[root_pc]} {mode}" for name, (root_pc, mode) in keys.items()]
    lines.append("")
    for name, bars in sections:
        root_pc, mode = keys[name]
        cells = (" ".join(build_chord(root_pc, mode, d, e)[0] for d, e in bar) for bar in bars)
        lines.append(f"[{name}] | " + " | ".join(f"{c:<12}" for c in cells) + " |")
    return "\n".join(lines) + "\n"
