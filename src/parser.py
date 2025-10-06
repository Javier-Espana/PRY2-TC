"""Thin compatibility layer exposing the public parser API.

All heavy lifting lives in specialised modules (``grammar``, ``grammar_io``,
``cnf``, ``cyk`` and ``utils``). Import from here to keep external code stable
while benefitting from a modular internal structure.
"""

from __future__ import annotations

from .cnf import convert_to_cnf
from .cyk import build_parse_tree, cyk_parse, format_tree, is_cnf
from .grammar import Grammar, RHS
from .grammar_io import GrammarFormatError, grammar_to_lines, parse_grammar
from .utils import tokens_from_sentence

__all__ = [
    "Grammar",
    "RHS",
    "GrammarFormatError",
    "parse_grammar",
    "grammar_to_lines",
    "convert_to_cnf",
    "is_cnf",
    "cyk_parse",
    "build_parse_tree",
    "format_tree",
    "tokens_from_sentence",
]

