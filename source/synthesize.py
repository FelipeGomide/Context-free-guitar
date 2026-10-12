import argparse
import time
from pathlib import Path

import fluidsynth
import numpy as np
import soundfile

SAMPLE_RATE = 44100
# Ganho do FluidSynth (padrão dele: 0.2, baixo demais). Com 0.8 os picos das
# levadas ficam entre -8 e -5.6 dB no Live_HQ, com folga antes de distorcer.
GAIN = 0.8
TAIL = 2.0      # segundos renderizados depois do fim do MIDI (as notas soando)
SILENCE = 30    # amplitude (de 32767) abaixo da qual o final é cortado (~-60 dB)
BLOCK = 1024    # amostras por bloco de renderização

PROJECT_DIR = Path(__file__).resolve().parent.parent

# Onde procurar soundfonts quando nenhum é indicado: a pasta soundfonts/ do
# diretório atual e a do projeto (os de PREFERRED primeiro), depois os
# soundfonts GM que costumam vir com o FluidSynth no Linux.
# Nylon_Guitar.sf2 é só o preset 24 extraído do Live_HQ.sf2: soa igual e
# carrega muito mais rápido.
PREFERRED = ["Nylon_Guitar.sf2"]
SYSTEM_SOUNDFONTS = [
    Path("/usr/share/sounds/sf2/FluidR3_GM.sf2"),
    Path("/usr/share/soundfonts/FluidR3_GM.sf2"),
    Path("/usr/share/soundfonts/default.sf2"),
]


def find_soundfont(explicit=None):
    if explicit is not None:
        if not Path(explicit).is_file():
            raise FileNotFoundError(f"Soundfont não encontrado: {explicit}")
        return Path(explicit)
    for folder in (Path.cwd() / "soundfonts", PROJECT_DIR / "soundfonts"):
        for name in PREFERRED:
            if (folder / name).is_file():
                return folder / name
        found = sorted(folder.glob("*.sf2"))
        if found:
            return found[0]
    for path in SYSTEM_SOUNDFONTS:
        if path.is_file():
            return path
    raise FileNotFoundError(
        "Nenhum soundfont encontrado. Coloque um .sf2 em ./soundfonts/ ou use --soundfont.")


def _synth(soundfont):
    # reset-synth = 0: sem isso o player reinicia o sintetizador ao fim do MIDI
    # e corta a ressonância das últimas notas.
    synth = fluidsynth.Synth(gain=GAIN, samplerate=SAMPLE_RATE, **{"player.reset-synth": 0})
    if synth.sfload(str(soundfont)) == -1:
        synth.delete()
        raise RuntimeError(f"FluidSynth não conseguiu carregar {soundfont}")
    return synth


def render(midi_path, audio_path, soundfont=None):
    """Renderiza o MIDI em arquivo de áudio. O formato vem da extensão
    (.flac, .wav, .ogg)."""
    synth = _synth(find_soundfont(soundfont))
    player = fluidsynth.new_fluid_player(synth.synth)
    try:
        fluidsynth.fluid_player_add(player, str(midi_path).encode())
        fluidsynth.fluid_player_play(player)
        # Sem driver de áudio, o player avança conforme as amostras são geradas.
        blocks = []
        while fluidsynth.fluid_player_get_status(player) == fluidsynth.FLUID_PLAYER_PLAYING:
            blocks.append(synth.get_samples(BLOCK))
        for _ in range(int(TAIL * SAMPLE_RATE / BLOCK)):
            blocks.append(synth.get_samples(BLOCK))
    finally:
        fluidsynth.delete_fluid_player(player)
        synth.delete()
    audio = np.concatenate(blocks).reshape(-1, 2)
    loud = np.flatnonzero(np.abs(audio).max(axis=1) > SILENCE)
    if loud.size:
        audio = audio[:loud[-1] + SAMPLE_RATE // 10]  # corta o silêncio final
    soundfile.write(str(audio_path), audio, SAMPLE_RATE, subtype="PCM_16")
    return Path(audio_path)


def play(midi_path, soundfont=None):
    """Toca o MIDI na hora, pelo driver de áudio padrão do sistema."""
    synth = _synth(find_soundfont(soundfont))
    try:
        # Sem permissão de tempo real, a libfluidsynth avisaria a cada execução.
        synth.setting("audio.realtime-prio", 0)
        synth.setting("midi.realtime-prio", 0)
        synth.start()
        synth.play_midi_file(str(midi_path))
        fluidsynth.fluid_player_join(synth.player)
        time.sleep(0.5)  # deixa a última nota soar
    except KeyboardInterrupt:
        synth.play_midi_stop()
    finally:
        synth.delete()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Renderiza (e toca) uma música já gerada.")
    parser.add_argument("pasta", type=Path, help="pasta da música (com musica.mid)")
    parser.add_argument("--tocar", action="store_true", help="toca a música")
    parser.add_argument("--wav", action="store_true", help="gera WAV em vez de FLAC")
    parser.add_argument("--soundfont", type=Path)
    args = parser.parse_args()

    midi = args.pasta / "musica.mid"
    audio = render(midi, args.pasta / ("musica.wav" if args.wav else "musica.flac"), args.soundfont)
    print(f"Áudio salvo em {audio}")
    if args.tocar:
        play(midi, args.soundfont)
