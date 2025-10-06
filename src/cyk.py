"""Implementation of the Cocke–Younger–Kasami (CYK) parsing algorithm."""

from __future__ import annotations

from typing import Dict, List, Sequence, Set, Tuple

from .grammar import Grammar

__all__ = ["is_cnf", "cyk_parse", "build_parse_tree", "format_tree"]


def is_cnf(grammar: Grammar) -> bool:
    start = grammar.start_symbol
    for head, bodies in grammar.productions.items():
        for body in bodies:
            if len(body) == 0:
                if head != start:
                    return False
            elif len(body) == 1:
                if body[0] not in grammar.terminals:
                    return False
            elif len(body) == 2:
                if not all(symbol in grammar.nonterminals for symbol in body):
                    return False
            else:
                return False
    return True


def cyk_parse(grammar: Grammar, tokens: Sequence[str]):
    """Run the CYK algorithm.

    Returns
    -------
    (accepted, table, backpointers):
        accepted:
            Boolean value indicating if the tokens belong to the language.
        table:
            Triangular table where ``table[i][l]`` is the set of variables that
            derive ``tokens[i:i+l]``.
        backpointers:
            Information necessary to reconstruct the parse tree.
    """

    if not is_cnf(grammar):
        raise ValueError("La gramática debe estar en CNF para usar CYK")

    n = len(tokens)
    if n == 0:
        accepts_empty = () in grammar.productions.get(grammar.start_symbol, set())
        return accepts_empty, [], {}

    table: List[List[Set[str]]] = [[set() for _ in range(n + 1)] for _ in range(n)]
    back: Dict[Tuple[int, int, str], Tuple] = {}

    inverse_unary: Dict[str, Set[str]] = {}
    inverse_binary: Dict[Tuple[str, str], Set[str]] = {}
    for head, bodies in grammar.productions.items():
        for body in bodies:
            if len(body) == 1:
                inverse_unary.setdefault(body[0], set()).add(head)
            elif len(body) == 2:
                inverse_binary.setdefault((body[0], body[1]), set()).add(head)

    for i, token in enumerate(tokens):
        for head in inverse_unary.get(token, set()):
            table[i][1].add(head)
            back[(i, 1, head)] = ("terminal", token)

    for span in range(2, n + 1):
        for i in range(0, n - span + 1):
            for split in range(1, span):
                left = table[i][split]
                right = table[i + split][span - split]
                if not left or not right:
                    continue
                for b in left:
                    for c in right:
                        for head in inverse_binary.get((b, c), set()):
                            if head not in table[i][span]:
                                table[i][span].add(head)
                                back[(i, span, head)] = ("split", split, b, c)

    accepted = grammar.start_symbol in table[0][n]
    return accepted, table, back


def build_parse_tree(tokens: Sequence[str], back: Dict[Tuple[int, int, str], Tuple], start_symbol: str):
    """Reconstruct a parse tree from backpointers."""

    key = (0, len(tokens), start_symbol)
    if key not in back:
        return None

    def _recurse(i: int, length: int, head: str):
        info = back[(i, length, head)]
        if info[0] == "terminal":
            return (head, info[1])
        _, split, left_head, right_head = info
        left = _recurse(i, split, left_head)
        right = _recurse(i + split, length - split, right_head)
        return (head, left, right)

    return _recurse(0, len(tokens), start_symbol)


def format_tree(tree, indent: int = 0) -> str:
    """Render a parse tree in a human friendly format."""

    if tree is None:
        return "(∅)"
    head = tree[0]
    if len(tree) == 2 and isinstance(tree[1], str):
        return f"{'  ' * indent}{head} -> '{tree[1]}'"
    left_str = format_tree(tree[1], indent + 1)
    right_str = format_tree(tree[2], indent + 1)
    return f"{'  ' * indent}{head}\n{left_str}\n{right_str}"
