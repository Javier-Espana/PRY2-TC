"""
Conversión de gramáticas CFG a Forma Normal de Chomsky (CNF).

Este módulo implementa el algoritmo estándar para convertir gramáticas libres
de contexto a CNF, siguiendo estos pasos:
1. Añadir nuevo símbolo inicial
2. Eliminar símbolos inútiles
3. Eliminar producciones epsilon
4. Eliminar producciones unitarias
5. Reemplazar terminales en reglas largas
6. Binarizar reglas
"""

from __future__ import annotations

import re
from typing import Dict, List, Sequence, Set, Tuple

from .grammar import Grammar, RHS

__all__ = ["convert_to_cnf"]


def convert_to_cnf(grammar: Grammar) -> Grammar:
    """
    Convierte una gramática CFG a Forma Normal de Chomsky (CNF).
    
    Aplica la secuencia estándar de transformaciones para obtener una gramática
    equivalente en CNF, donde todas las producciones tienen la forma:
    - A -> BC (dos no terminales)
    - A -> a (un terminal)
    - S -> ε (solo para el símbolo inicial si acepta cadena vacía)
    
    Parámetros:
        grammar: Gramática CFG de entrada
        
    Retorna:
        Grammar: Gramática equivalente en CNF
    """
    g = grammar.clone()
    g = _add_new_start_symbol(g)        # Paso 1: Nuevo símbolo inicial
    g = _remove_useless_symbols(g)      # Paso 2: Eliminar símbolos inútiles  
    g = _remove_epsilon_productions(g)  # Paso 3: Eliminar producciones ε
    g = _remove_unit_productions(g)     # Paso 4: Eliminar producciones unitarias
    g = _replace_terminals_in_long_rules(g)  # Paso 5: Aislar terminales
    g = _binarise_rules(g)             # Paso 6: Binarizar reglas largas
    return g


def _add_new_start_symbol(g: Grammar) -> Grammar:
    """
    Añade un nuevo símbolo inicial para garantizar que no aparezca en el lado derecho.
    
    Esto es necesario para la CNF, donde el símbolo inicial no debe aparecer
    en el lado derecho de ninguna producción.
    """
    g2 = g.clone()
    original_start = g2.start_symbol
    fresh_start = _fresh_nonterminal(g2.nonterminals, base="S0")
    g2.nonterminals.add(fresh_start)
    g2.start_symbol = fresh_start
    g2.add_production(fresh_start, [original_start])
    return g2


def _remove_useless_symbols(g: Grammar) -> Grammar:
    """
    Elimina símbolos inútiles (no productivos y no alcanzables).
    
    Un símbolo es productivo si puede derivar una cadena de terminales.
    Un símbolo es alcanzable si puede ser derivado desde el símbolo inicial.
    """
    # Paso 1: Encontrar símbolos productivos usando punto fijo
    productive: Set[str] = set()
    changed = True
    while changed:
        changed = False
        for head, bodies in g.productions.items():
            if head in productive:
                continue
            # Un no terminal es productivo si tiene al menos una producción
            # donde todos los símbolos son terminales o no terminales ya productivos
            for body in bodies:
                if all(symbol in g.terminals or symbol in productive for symbol in body):
                    productive.add(head)
                    changed = True
                    break

    # Filtrar producciones manteniendo solo las que usan símbolos productivos
    productions_filtered: Dict[str, Set[RHS]] = {}
    for head, bodies in g.productions.items():
        if head not in productive:
            continue
        valid_bodies = {
            body
            for body in bodies
            if all(symbol in g.terminals or symbol in productive for symbol in body)
        }
        if valid_bodies:
            productions_filtered[head] = valid_bodies

    # Paso 2: Encontrar símbolos alcanzables desde el símbolo inicial
    reachable: Set[str] = {g.start_symbol}
    frontier = [g.start_symbol]
    while frontier:
        current = frontier.pop()
        for body in productions_filtered.get(current, set()):
            for symbol in body:
                if symbol in productions_filtered and symbol not in reachable:
                    reachable.add(symbol)
                    frontier.append(symbol)

    # Construir gramática final con solo símbolos útiles
    nonterminals = {nt for nt in productions_filtered if nt in reachable}
    productions = {
        head: {
            body
            for body in bodies
            if all(symbol in g.terminals or symbol in nonterminals for symbol in body)
        }
        for head, bodies in productions_filtered.items()
        if head in reachable
    }

    # Recopilar terminales utilizados
    terminals = {
        symbol
        for bodies in productions.values()
        for body in bodies
        for symbol in body
        if symbol not in productions
    }

    return Grammar(nonterminals=nonterminals, terminals=terminals, start_symbol=g.start_symbol, productions=productions)


def _remove_epsilon_productions(g: Grammar) -> Grammar:
    """
    Elimina las producciones epsilon (A -> ε) de la gramática.
    
    Para cada producción que contiene símbolos nullable, genera todas las
    combinaciones posibles donde algunos de esos símbolos se omiten,
    simulando el efecto de las producciones epsilon.
    """
    nullable = _nullable_symbols(g)
    start = g.start_symbol
    productions: Dict[str, Set[RHS]] = {head: set() for head in g.productions}

    # Generar nuevas producciones eliminando combinaciones de símbolos nullable
    for head, bodies in g.productions.items():
        for body in bodies:
            if not body:  # Saltar producciones epsilon originales
                continue
            # Encontrar posiciones de símbolos nullable
            nullable_positions = [idx for idx, symbol in enumerate(body) if symbol in nullable]
            count = len(nullable_positions)
            # Generar todas las combinaciones (2^count subconjuntos)
            for mask in range(1 << count):
                skip_positions = {
                    nullable_positions[pos]
                    for pos in range(count)
                    if (mask >> pos) & 1
                }
                new_body = [symbol for idx, symbol in enumerate(body) if idx not in skip_positions]
                if not new_body:
                    if head == start:
                        productions[head].add(())
                else:
                    productions[head].add(tuple(new_body))

    if start in nullable:
        productions[start].add(())

    nonterminals = set(productions.keys())
    terminals = {
        symbol
        for bodies in productions.values()
        for body in bodies
        for symbol in body
        if symbol not in nonterminals
    }

    return Grammar(nonterminals=nonterminals, terminals=terminals, start_symbol=start, productions=productions)


def _nullable_symbols(g: Grammar) -> Set[str]:
    """
    Encuentra todos los símbolos que pueden derivar la cadena vacía (ε).
    
    Un símbolo es nullable si:
    - Tiene una producción directa a ε, o
    - Tiene una producción donde todos los símbolos del lado derecho son nullable
    
    Retorna:
        Set[str]: Conjunto de símbolos nullable
    """
    nullable: Set[str] = set()
    changed = True
    while changed:
        changed = False
        for head, bodies in g.productions.items():
            if head in nullable:
                continue
            for body in bodies:
                # Producción vacía (ε) o todos los símbolos son nullable
                if not body or all(symbol in nullable for symbol in body):
                    nullable.add(head)
                    changed = True
                    break
    return nullable


def _remove_unit_productions(g: Grammar) -> Grammar:
    """
    Elimina producciones unitarias (A -> B donde B es un no terminal).
    
    Calcula la clausura transitiva de las producciones unitarias y luego
    reemplaza cada producción unitaria A -> B con las producciones A -> γ
    donde B -> γ es una producción no unitaria.
    """
    # Calcular clausura transitiva de producciones unitarias
    closure: Dict[str, Set[str]] = {}
    for head in g.productions:
        reachable: Set[str] = {head}
        stack = [head]
        while stack:
            current = stack.pop()
            for body in g.productions[current]:
                # Si es producción unitaria A -> B
                if len(body) == 1 and body[0] in g.productions and body[0] not in reachable:
                    reachable.add(body[0])
                    stack.append(body[0])
        closure[head] = reachable

    # Construir nuevas producciones eliminando las unitarias
    productions: Dict[str, Set[RHS]] = {head: set() for head in g.productions}
    for head, targets in closure.items():
        for target in targets:
            for body in g.productions[target]:
                # Saltar producciones unitarias en el resultado final
                if len(body) == 1 and body[0] in g.productions:
                    continue
                productions[head].add(body)

    nonterminals = set(productions.keys())
    terminals = {
        symbol
        for bodies in productions.values()
        for body in bodies
        for symbol in body
        if symbol not in nonterminals
    }

    return Grammar(nonterminals=nonterminals, terminals=terminals, start_symbol=g.start_symbol, productions=productions)


def _replace_terminals_in_long_rules(g: Grammar) -> Grammar:
    """
    Reemplaza terminales en producciones de longitud > 1 con nuevos no terminales.
    
    En CNF, los terminales solo pueden aparecer solos en el lado derecho.
    Para producciones como A -> aB, se crea un nuevo no terminal Ta y se 
    reemplaza por A -> TaB, Ta -> a.
    """
    productions: Dict[str, Set[RHS]] = {head: set() for head in g.productions}
    new_terminal_vars: Dict[str, str] = {}
    nonterminals = set(g.nonterminals)

    def get_var_for_terminal(symbol: str) -> str:
        """Obtiene o crea un no terminal para representar el terminal dado."""
        if symbol not in new_terminal_vars:
            candidate = _fresh_nonterminal(nonterminals, base=f"T_{_slug(symbol)}")
            new_terminal_vars[symbol] = candidate
            nonterminals.add(candidate)
            # Crear producción T_a -> a
            productions.setdefault(candidate, set()).add((symbol,))
        return new_terminal_vars[symbol]

    # Procesar todas las producciones
    for head, bodies in g.productions.items():
        for body in bodies:
            # Las producciones de longitud ≤ 1 se mantienen igual
            if len(body) <= 1:
                productions[head].add(body)
                continue
            # Reemplazar terminales con no terminales en producciones largas
            replaced = [get_var_for_terminal(symbol) if symbol in g.terminals else symbol for symbol in body]
            productions[head].add(tuple(replaced))

    terminals = set(g.terminals)
    return Grammar(nonterminals=nonterminals, terminals=terminals, start_symbol=g.start_symbol, productions=productions)


def _binarise_rules(g: Grammar) -> Grammar:
    """
    Convierte producciones de longitud > 2 en producciones binarias.
    
    Para una producción A -> BCD, se crean:
    A -> BX1, X1 -> CD
    
    Para A -> BCDE, se crean:
    A -> BX1, X1 -> CX2, X2 -> DE
    """
    productions: Dict[str, Set[RHS]] = {head: set() for head in g.productions}
    nonterminals = set(g.nonterminals)
    counter = 1

    def fresh_var() -> str:
        """Genera un nuevo nombre de variable único."""
        nonlocal counter
        while True:
            candidate = f"X{counter}"
            counter += 1
            if candidate not in nonterminals and candidate not in g.terminals:
                nonterminals.add(candidate)
                return candidate

    # Binarizar cada producción que tenga longitud > 2
    for head, bodies in g.productions.items():
        for body in bodies:
            # Las producciones de longitud ≤ 2 ya están en forma correcta
            if len(body) <= 2:
                productions[head].add(body)
                continue
            
            # Descomponer producción larga en cadena de producciones binarias
            symbols = list(body)
            left = symbols[0]
            rest = symbols[1:]
            current_head = head
            
            # Crear variables intermedias hasta que queden solo 2 símbolos
            while len(rest) > 1:
                new_var = fresh_var()
                productions[current_head].add((left, new_var))
                left = rest[0]
                rest = rest[1:]
                current_head = new_var
            # Última producción con los 2 símbolos restantes
            productions[current_head].add((left, rest[0]))

    terminals = set(g.terminals)
    return Grammar(nonterminals=nonterminals, terminals=terminals, start_symbol=g.start_symbol, productions=productions)


def _fresh_nonterminal(existing: Set[str], base: str = "X") -> str:
    """
    Genera un nombre de no terminal único que no esté en el conjunto dado.
    
    Parámetros:
        existing: Conjunto de nombres ya utilizados
        base: Prefijo base para el nuevo nombre
        
    Retorna:
        str: Nuevo nombre único (base, base1, base2, etc.)
    """
    if base not in existing:
        return base
    index = 1
    while f"{base}{index}" in existing:
        index += 1
    return f"{base}{index}"


def _slug(token: str) -> str:
    """
    Convierte un token en un identificador válido reemplazando caracteres especiales.
    
    Parámetros:
        token: Token de entrada
        
    Retorna:
        str: Versión "slugificada" del token para usar como parte de nombres de variables
    """
    return re.sub(r"[^0-9A-Za-z]+", "_", token) or "sym"
