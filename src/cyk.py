"""
Implementación del algoritmo de análisis sintáctico Cocke-Younger-Kasami (CYK).

Este módulo contiene la implementación del algoritmo CYK para determinar si una
cadena de tokens pertenece al lenguaje generado por una gramática en CNF, así como
funciones para construir y formatear árboles de análisis sintáctico.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Set, Tuple

from .grammar import Grammar

__all__ = ["is_cnf", "cyk_parse", "build_parse_tree", "format_tree"]


def is_cnf(grammar: Grammar) -> bool:
    """
    Verifica si una gramática está en Forma Normal de Chomsky (CNF).
    
    Una gramática está en CNF si todas sus producciones tienen una de estas formas:
    - A -> BC (dos no terminales)
    - A -> a (un terminal)  
    - S -> ε (solo permitido para el símbolo inicial)
    
    Parámetros:
        grammar: Gramática a verificar
        
    Retorna:
        bool: True si la gramática está en CNF, False en caso contrario
    """
    start = grammar.start_symbol
    for head, bodies in grammar.productions.items():
        for body in bodies:
            if len(body) == 0:  # Producción ε
                if head != start:  # Solo permitida para el símbolo inicial
                    return False
            elif len(body) == 1:  # Producción A -> a
                if body[0] not in grammar.terminals:
                    return False
            elif len(body) == 2:  # Producción A -> BC
                if not all(symbol in grammar.nonterminals for symbol in body):
                    return False
            else:  # Longitud > 2, no permitida en CNF
                return False
    return True


def cyk_parse(grammar: Grammar, tokens: Sequence[str]):
    """
    Ejecuta el algoritmo CYK para determinar si los tokens pertenecen al lenguaje.
    
    El algoritmo CYK utiliza programación dinámica para llenar una tabla triangular
    donde cada entrada (i,l) contiene los no terminales que pueden derivar la
    subcadena tokens[i:i+l].

    Parámetros:
        grammar: Gramática en CNF 
        tokens: Secuencia de tokens a analizar

    Retorna:
        Tupla (accepted, table, backpointers) donde:
        - accepted: bool indicando si los tokens pertenecen al lenguaje
        - table: Tabla triangular donde table[i][l] contiene los no terminales
                que derivan tokens[i:i+l]  
        - backpointers: Información para reconstruir el árbol de análisis
    """

    if not is_cnf(grammar):
        raise ValueError("La gramática debe estar en CNF para usar CYK")

    n = len(tokens)
    # Caso especial: cadena vacía
    if n == 0:
        accepts_empty = () in grammar.productions.get(grammar.start_symbol, set())
        return accepts_empty, [], {}

    # Inicializar tabla CYK y diccionario de backpointers
    table: List[List[Set[str]]] = [[set() for _ in range(n + 1)] for _ in range(n)]
    back: Dict[Tuple[int, int, str], Tuple] = {}

    # Crear índices inversos para acceso eficiente a las producciones
    inverse_unary: Dict[str, Set[str]] = {}      # terminal -> {no terminales que lo derivan}
    inverse_binary: Dict[Tuple[str, str], Set[str]] = {}  # (A,B) -> {no terminales que derivan AB}
    for head, bodies in grammar.productions.items():
        for body in bodies:
            if len(body) == 1:  # A -> a
                inverse_unary.setdefault(body[0], set()).add(head)
            elif len(body) == 2:  # A -> BC
                inverse_binary.setdefault((body[0], body[1]), set()).add(head)

    # Paso 1: Llenar la diagonal (subcadenas de longitud 1)
    for i, token in enumerate(tokens):
        for head in inverse_unary.get(token, set()):
            table[i][1].add(head)
            back[(i, 1, head)] = ("terminal", token)

    # Paso 2: Llenar la tabla usando programación dinámica
    for span in range(2, n + 1):  # Para cada longitud de subcadena
        for i in range(0, n - span + 1):  # Para cada posición inicial
            for split in range(1, span):  # Para cada punto de división
                # Obtener no terminales que derivan las dos partes
                left = table[i][split]
                right = table[i + split][span - split]
                if not left or not right:
                    continue
                # Buscar producciones A -> BC donde B está en left y C en right
                for b in left:
                    for c in right:
                        for head in inverse_binary.get((b, c), set()):
                            if head not in table[i][span]:
                                table[i][span].add(head)
                                # Guardar información para reconstruir el árbol
                                back[(i, span, head)] = ("split", split, b, c)

    # Determinar si la cadena es aceptada
    accepted = grammar.start_symbol in table[0][n]
    return accepted, table, back


def build_parse_tree(tokens: Sequence[str], back: Dict[Tuple[int, int, str], Tuple], start_symbol: str):
    """
    Reconstruye un árbol de análisis sintáctico usando los backpointers del algoritmo CYK.
    
    Parámetros:
        tokens: Secuencia original de tokens
        back: Diccionario de backpointers generado por CYK
        start_symbol: Símbolo inicial de la gramática
        
    Retorna:
        Tree: Árbol de análisis en formato recursivo
    """

    key = (0, len(tokens), start_symbol)
    if key not in back:
        return None

    def _recurse(i: int, length: int, head: str):
        """Función recursiva para reconstruir el árbol desde los backpointers."""
        info = back[(i, length, head)]
        if info[0] == "terminal":
            # Nodo hoja: no terminal deriva un terminal
            return (head, info[1])
        # Nodo interno: no terminal deriva dos no terminales
        _, split, left_head, right_head = info
        left = _recurse(i, split, left_head)
        right = _recurse(i + split, length - split, right_head)
        return (head, left, right)

    return _recurse(0, len(tokens), start_symbol)


def format_tree(tree, indent: int = 0) -> str:
    """
    Formatea un árbol de análisis sintáctico para visualización legible.
    
    Parámetros:
        tree: Árbol en formato (nodo, hijo_izq, hijo_der) o (nodo, terminal)
        indent: Nivel de indentación para la visualización
        
    Retorna:
        str: Representación en cadena del árbol con indentación
    """
    if tree is None:
        return "(∅)"
    head = tree[0]
    # Nodo hoja (terminal)
    if len(tree) == 2 and isinstance(tree[1], str):
        return f"{'  ' * indent}{head} -> '{tree[1]}'"
    # Nodo interno (con dos hijos)
    left_str = format_tree(tree[1], indent + 1)
    right_str = format_tree(tree[2], indent + 1)
    return f"{'  ' * indent}{head}\n{left_str}\n{right_str}"
