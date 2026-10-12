import random
import sys
from pathlib import Path

from nltk import PCFG, Nonterminal, Tree

GRAMMAR_PATH = Path(__file__).resolve().parent / "song.pcfg"

# Símbolos expandidos uma única vez por música e reutilizados em todas as
# ocorrências (ex.: o início comum das seções A).
REPEATED = {"PHRASE"}


def load_grammar(path=GRAMMAR_PATH):
    return PCFG.fromstring(Path(path).read_text(encoding="utf-8"))


def generate_tree(grammar, rng=random, repeated=REPEATED):
    cache = {}

    def expand(symbol):
        if not isinstance(symbol, Nonterminal):
            return symbol
        name = symbol.symbol()
        if name in cache:
            return cache[name]
        productions = grammar.productions(lhs=symbol)
        production = rng.choices(productions, [p.prob() for p in productions])[0]
        tree = Tree(name, [expand(s) for s in production.rhs()])
        if name in repeated:
            cache[name] = tree
        return tree

    return expand(grammar.start())


def generate(grammar, rng=random, repeated=REPEATED):
    return generate_tree(grammar, rng, repeated).leaves()


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
    print(" ".join(generate(load_grammar(), random.Random(seed))))
