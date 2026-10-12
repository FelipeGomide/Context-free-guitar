# Context-Free Guitar

Gera músicas de bossa nova para violão a partir de uma gramática livre de
contexto probabilística (PCFG). A gramática sorteia uma levada, um andamento,
as tonalidades e uma progressão de acordes na forma A A B A. Em seguida, o
programa transforma a progressão numa cifra, escreve um MIDI de violão
dedilhado e renderiza o áudio com um soundfont.

```
gramática → cifra → MIDI → áudio
```

As levadas disponíveis são `BOSSA`, `BLOCADO`, `VALSA`, `DJAVAN` e `SAMBA`.
Há uma música de exemplo para cada uma em [`examples/`](examples).

## Instalação

Requisitos:

- Python 3.10 ou mais recente;
- a biblioteca do [FluidSynth](https://www.fluidsynth.org/) (`libfluidsynth`),
  usada para gerar e tocar o áudio:
  - Debian/Ubuntu: `sudo apt install libfluidsynth3`
  - macOS: `brew install fluid-synth`

```bash
python -m venv .venv
.venv/bin/pip install -e .
```

Isso instala o comando `cfguitar` dentro do `.venv`.

## Uso

```bash
.venv/bin/cfguitar            # semente sorteada
.venv/bin/cfguitar 7          # semente fixa: sempre gera a mesma música
.venv/bin/cfguitar 7 --tocar  # gera e toca
```

O programa mostra a cifra no terminal:

```
Levada: DJAVAN, 70 bpm, 4/4
A: E maior
B: C maior

[A] | E7M(9)       | C#m7(9)      | D#m7(b5)     | F#m7(9) B7   |
[A] | E7M(9)       | C#m7(9)      | D#m7(b5)     | B7(4)(9) E7M |
[B] | Dm7(9)       | C7M(9)       | Em7(9)       | Em7(9)       |
[A] | E7M(9)       | C#m7(9)      | D#m7(b5)     | B7(9) E6(9)  |
```

Os arquivos ficam em `out/seed-<semente>/`:

| Arquivo | Conteúdo |
|---|---|
| `gramatica.txt` | a sequência gerada pela gramática |
| `cifra.txt` | a cifra |
| `musica.mid` | o MIDI (faixas de baixo e de acordes) |
| `musica.flac` | o áudio (`musica.wav` com `--wav`) |

Opções:

| Opção | Efeito |
|---|---|
| `--tocar` | toca a música depois de gerar |
| `--wav` | gera WAV em vez de FLAC |
| `--soundfont ARQUIVO` | usa outro soundfont `.sf2` (General MIDI) |
| `--saida PASTA` | pasta de saída (padrão: `./out`) |

Para renderizar ou tocar de novo uma música já gerada:

```bash
.venv/bin/python -m cfguitar.synthesize out/seed-7 --tocar
```

## Soundfont

Por padrão, o programa usa `soundfonts/Nylon_Guitar.sf2`, que contém só o
violão de náilon extraído do *Live HQ Natural SoundFont GM V3.0* (licença CC
BY). Créditos e detalhes estão em
[`soundfonts/README.md`](soundfonts/README.md). Se esse arquivo não existir, o
programa usa outro `.sf2` da pasta `soundfonts/` ou um soundfont GM do sistema
(como o `FluidR3_GM.sf2`).

## Estrutura

| Arquivo | Função |
|---|---|
| `source/song.pcfg` | a gramática (PCFG no formato do NLTK) |
| `source/grammar.py` | sorteia uma derivação da gramática |
| `source/midify.py` | monta os acordes, faz a condução de vozes e escreve o MIDI |
| `source/grooves.py` | as levadas, escritas como grades de texto |
| `source/synthesize.py` | renderiza e toca o áudio com o FluidSynth |
| `source/main.py` | o comando `cfguitar`, que liga as etapas |
