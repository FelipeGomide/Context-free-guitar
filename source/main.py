import argparse
import random
from pathlib import Path

from .grammar import generate, load_grammar
from .midify import chart, to_midi
from .synthesize import play, render


def main(seed=None, out_dir=Path("out"), audio_format="flac", soundfont=None):
    """Gera uma música e salva cada etapa em <out_dir>/seed-<seed>/:
    gramatica.txt (símbolos gerados), cifra.txt, musica.mid e o áudio
    (musica.flac ou musica.wav)."""
    if seed is None:
        seed = random.randrange(1_000_000)  # sorteada, mas registrada no nome da pasta
    folder = Path(out_dir) / f"seed-{seed}"
    folder.mkdir(parents=True, exist_ok=True)

    tokens = generate(load_grammar(), random.Random(seed))
    (folder / "gramatica.txt").write_text(" ".join(tokens) + "\n", encoding="utf-8")
    (folder / "cifra.txt").write_text(chart(tokens), encoding="utf-8")
    to_midi(tokens).write(str(folder / "musica.mid"))
    render(folder / "musica.mid", folder / f"musica.{audio_format}", soundfont)
    return folder


def cli():
    parser = argparse.ArgumentParser(description="Gera uma música a partir da gramática.")
    parser.add_argument("seed", type=int, nargs="?", help="seed (sorteada se omitida)")
    parser.add_argument("--tocar", action="store_true", help="toca a música depois de gerar")
    parser.add_argument("--wav", action="store_true", help="gera WAV em vez de FLAC")
    parser.add_argument("--soundfont", type=Path, help="arquivo .sf2 (padrão: procura em ./soundfonts)")
    parser.add_argument("--saida", type=Path, default=Path("out"), help="pasta de saída (padrão: ./out)")
    args = parser.parse_args()

    folder = main(args.seed, args.saida, "wav" if args.wav else "flac", args.soundfont)
    print((folder / "cifra.txt").read_text(encoding="utf-8"))
    print(f"Arquivos salvos em {folder}")
    if args.tocar:
        play(folder / "musica.mid", args.soundfont)


if __name__ == "__main__":
    cli()
