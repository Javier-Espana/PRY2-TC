"""
Capa de compatibilidad que expone la API pública del parser.

Este módulo actúa como punto de entrada unificado para todas las funcionalidades
del proyecto. El trabajo pesado se realiza en módulos especializados:
- grammar: Estructuras de datos para gramáticas
- grammar_io: Lectura y escritura de archivos de gramática  
- cnf: Conversión a Forma Normal de Chomsky
- cyk: Algoritmo CYK de análisis sintáctico
- utils: Utilidades diversas

Importar desde aquí mantiene el código externo estable mientras se beneficia
de una estructura interna modular.
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

