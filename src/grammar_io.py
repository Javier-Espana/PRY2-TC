"""Parsing and serialization utilities for grammar files."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from .grammar import Grammar


__all__ = ["GrammarFormatError", "parse_grammar", "grammar_to_lines"]


class GrammarFormatError(ValueError):
    """Raised when the grammar description file is malformed."""


_HEADER_PATTERN = re.compile(r"^(Variables|Terminals|Start|Rules):")
_QUOTED_TOKEN = re.compile(r"""("([^"\\]|\\.)*"|'([^'\\]|\\.)*')""")


def parse_grammar(text: str) -> Grammar:
    """Parse a grammar from the textual format described in the README."""

    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    if not lines:
        raise GrammarFormatError("El archivo de gramática está vacío")

    header: Dict[str, str] = {}
    rules_start_idx: Optional[int] = None
    for idx, line in enumerate(lines):
        match = _HEADER_PATTERN.match(line)
        if not match:
            if rules_start_idx is None:
                raise GrammarFormatError(
                    "Se esperaba una línea de encabezado (Variables/Terminals/Start/Rules)"
                )
            continue
        key = match.group(1)
        if key == "Rules":
            header[key] = ""
            rules_start_idx = idx + 1
            break
        header[key] = line.split(":", 1)[1].strip()

    if "Rules" not in header:
        raise GrammarFormatError("Falta la sección 'Rules:' en la gramática")

    if "Variables" not in header or "Terminals" not in header or "Start" not in header:
        raise GrammarFormatError("Los encabezados Variables, Terminals y Start son obligatorios")

    variables = set(_split_csv(header["Variables"]))
    terminals = set(_split_csv(header["Terminals"]))
    start_symbol = header["Start"].strip()
    if start_symbol not in variables:
        raise GrammarFormatError("El símbolo inicial debe encontrarse en la lista de variables")

    raw_rules = lines[rules_start_idx:] if rules_start_idx is not None else []
    if not raw_rules:
        raise GrammarFormatError("La sección de reglas está vacía")

    grammar = Grammar(nonterminals=set(variables), terminals=set(terminals), start_symbol=start_symbol)
    for raw in raw_rules:
        if not raw:
            continue
        if "->" not in raw:
            raise GrammarFormatError(f"Regla inválida: '{raw}'")
        lhs, rhs = [part.strip() for part in raw.split("->", 1)]
        if lhs not in variables:
            raise GrammarFormatError(f"'{lhs}' no es una variable declarada en Variables")
        alternatives = [alt.strip() for alt in rhs.split("|") if alt.strip()]
        if not alternatives:
            raise GrammarFormatError(f"Regla sin alternativas para '{lhs}'")
        for alt in alternatives:
            if alt in {"ε", "epsilon", "EPSILON"}:
                grammar.add_production(lhs, [])
                continue
            symbols = _split_symbols(alt)
            grammar.add_production(lhs, symbols)

    return grammar


def grammar_to_lines(grammar: Grammar) -> List[str]:
    """Serialize a grammar to a list of lines similar to the input format."""

    lines: List[str] = []
    lines.append("Variables: " + ", ".join(sorted(grammar.nonterminals)))
    lines.append("Terminals: " + ", ".join(sorted(grammar.terminals)))
    lines.append(f"Start: {grammar.start_symbol}")
    lines.append("Rules:")
    for head in sorted(grammar.productions.keys()):
        alternatives = []
        for body in sorted(grammar.productions[head], key=lambda x: (len(x), x)):
            if not body:
                alternatives.append("ε")
            else:
                alternatives.append(" ".join(body))
        lines.append(f"  {head} -> " + " | ".join(alternatives))
    return lines


def _split_csv(text: str) -> List[str]:
    tokens: List[str] = []
    for chunk in text.split(","):
        token = chunk.strip()
        if not token:
            continue
        tokens.append(_unquote(token))
    return tokens


def _split_symbols(text: str) -> List[str]:
    tokens: List[str] = []
    i = 0
    length = len(text)
    while i < length:
        if text[i].isspace():
            i += 1
            continue
        if text[i] in {'"', "'"}:
            match = _QUOTED_TOKEN.match(text, i)
            if not match:
                raise GrammarFormatError(f"Símbolo entrecomillado sin cerrar en: {text[i:]}")
            tokens.append(_unquote(match.group(0)))
            i = match.end()
        else:
            j = i
            while j < length and not text[j].isspace():
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def _unquote(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {'"', "'"}:
        inner = token[1:-1]
        return bytes(inner, "utf-8").decode("unicode_escape")
    return token
