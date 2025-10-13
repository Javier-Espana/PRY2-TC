"""
Utilidades para parseo y serialización de archivos de gramática.

Este módulo maneja la lectura de archivos de gramática en formato textual
y su conversión a objetos Grammar, así como la serialización de vuelta
a formato texto.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from .grammar import Grammar


__all__ = ["GrammarFormatError", "parse_grammar", "grammar_to_lines"]


class GrammarFormatError(ValueError):
    """Excepción lanzada cuando el archivo de descripción de gramática tiene formato inválido."""


# Patrones regex para parsear el formato de gramática
_HEADER_PATTERN = re.compile(r"^(Variables|Terminals|Start|Rules):")
_QUOTED_TOKEN = re.compile(r"""("([^"\\]|\\.)*"|'([^'\\]|\\.)*')""")


def parse_grammar(text: str) -> Grammar:
    """
    Parsea una gramática desde el formato textual descrito en el README.
    
    El formato esperado es:
    Variables: A, B, C
    Terminals: a, b, c
    Start: S
    Rules:
    S -> A B
    A -> a | ε
    
    Parámetros:
        text: Contenido del archivo de gramática
        
    Retorna:
        Grammar: Objeto gramática parseado
        
    Lanza:
        GrammarFormatError: Si el formato es inválido
    """

    # Procesar líneas eliminando comentarios y líneas vacías
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    if not lines:
        raise GrammarFormatError("El archivo de gramática está vacío")

    # Parsear encabezados (Variables, Terminals, Start, Rules)
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

    # Validar que todos los encabezados requeridos estén presentes
    if "Rules" not in header:
        raise GrammarFormatError("Falta la sección 'Rules:' en la gramática")

    if "Variables" not in header or "Terminals" not in header or "Start" not in header:
        raise GrammarFormatError("Los encabezados Variables, Terminals y Start son obligatorios")

    # Extraer conjuntos de símbolos
    variables = set(_split_csv(header["Variables"]))
    terminals = set(_split_csv(header["Terminals"]))
    start_symbol = header["Start"].strip()
    if start_symbol not in variables:
        raise GrammarFormatError("El símbolo inicial debe encontrarse en la lista de variables")

    # Procesar reglas de producción
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
        # Procesar alternativas separadas por |
        alternatives = [alt.strip() for alt in rhs.split("|") if alt.strip()]
        if not alternatives:
            raise GrammarFormatError(f"Regla sin alternativas para '{lhs}'")
        for alt in alternatives:
            # Manejo especial para producciones epsilon
            if alt in {"ε", "epsilon", "EPSILON"}:
                grammar.add_production(lhs, [])
                continue
            symbols = _split_symbols(alt)
            grammar.add_production(lhs, symbols)

    return grammar


def grammar_to_lines(grammar: Grammar) -> List[str]:
    """
    Serializa una gramática a una lista de líneas en formato similar al de entrada.
    
    Parámetros:
        grammar: Gramática a serializar
        
    Retorna:
        List[str]: Lista de líneas que representan la gramática
    """
    lines: List[str] = []
    # Generar encabezados
    lines.append("Variables: " + ", ".join(sorted(grammar.nonterminals)))
    lines.append("Terminals: " + ", ".join(sorted(grammar.terminals)))
    lines.append(f"Start: {grammar.start_symbol}")
    lines.append("Rules:")
    
    # Generar reglas de producción ordenadas
    for head in sorted(grammar.productions.keys()):
        alternatives = []
        for body in sorted(grammar.productions[head], key=lambda x: (len(x), x)):
            if not body:  # Producción epsilon
                alternatives.append("ε")
            else:
                alternatives.append(" ".join(body))
        lines.append(f"  {head} -> " + " | ".join(alternatives))
    return lines


def _split_csv(text: str) -> List[str]:
    """
    Divide una cadena separada por comas en tokens individuales.
    
    Maneja símbolos entrecomillados y elimina espacios en blanco.
    """
    tokens: List[str] = []
    for chunk in text.split(","):
        token = chunk.strip()
        if not token:
            continue
        tokens.append(_unquote(token))
    return tokens


def _split_symbols(text: str) -> List[str]:
    """
    Divide una cadena en símbolos individuales respetando las comillas.
    
    Maneja tanto símbolos simples separados por espacios como símbolos 
    entrecomillados que pueden contener espacios.
    """
    tokens: List[str] = []
    i = 0
    length = len(text)
    while i < length:
        # Saltar espacios en blanco
        if text[i].isspace():
            i += 1
            continue
        # Manejar símbolos entrecomillados
        if text[i] in {'"', "'"}:
            match = _QUOTED_TOKEN.match(text, i)
            if not match:
                raise GrammarFormatError(f"Símbolo entrecomillado sin cerrar en: {text[i:]}")
            tokens.append(_unquote(match.group(0)))
            i = match.end()
        else:
            # Símbolos simples (hasta el siguiente espacio)
            j = i
            while j < length and not text[j].isspace():
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def _unquote(token: str) -> str:
    """
    Elimina las comillas de un token y procesa secuencias de escape.
    
    Maneja tanto comillas simples como dobles y procesa secuencias de
    escape estándar como \n, \t, etc.
    """
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {'"', "'"}:
        inner = token[1:-1]
        # Procesar secuencias de escape Unicode
        return bytes(inner, "utf-8").decode("unicode_escape")
    return token
