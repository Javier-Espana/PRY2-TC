"""
Utilidades para visualizar árboles de análisis sintáctico como grafos DOT de Graphviz.

Este módulo permite convertir árboles de análisis sintáctico en formato DOT
para su visualización con herramientas como Graphviz.
"""

from __future__ import annotations

from typing import List, Tuple, Union

# Tipo recursivo para representar árboles de análisis sintáctico
Tree = Union[Tuple[str, str], Tuple[str, "Tree", "Tree"]]

__all__ = ["tree_to_dot"]


def tree_to_dot(tree: Tree) -> str:
    """
    Convierte un árbol de análisis sintáctico a representación DOT de Graphviz.

    El formato del árbol de entrada coincide con la estructura retornada por
    build_parse_tree:
    - Nodo terminal: (cabecera, token)  
    - Nodo no terminal: (cabecera, subárbol_izquierdo, subárbol_derecho)

    Parámetros:
        tree: Árbol de análisis en formato recursivo
        
    Retorna:
        str: Representación del árbol en formato DOT
    """

    lines: List[str] = []
    # Configuración del grafo DOT
    lines.append("digraph ParseTree {")
    lines.append("  rankdir=TB;")  # Dirección de arriba hacia abajo
    lines.append("  node [shape=plaintext, fontsize=12];")

    # Contador para generar IDs únicos de nodos
    counter = [0]

    def next_id() -> str:
        """Genera el siguiente ID único para un nodo."""
        nid = f"n{counter[0]}"
        counter[0] += 1
        return nid

    def esc(label: str) -> str:
        """Escapa caracteres especiales para uso en etiquetas DOT."""
        return label.replace("\\", "\\\\").replace("\"", "\\\"")

    def emit(node: Tree) -> str:
        """
        Emite recursivamente los nodos del árbol en formato DOT.
        
        Retorna el ID del nodo emitido para conectarlo con su padre.
        """
        head = node[0]
        this_id = next_id()
        lines.append(f'  {this_id} [label="{esc(head)}"];')
        
        if len(node) == 2 and isinstance(node[1], str):
            # Nodo hoja terminal: crear nodo hijo con el token
            token = node[1]
            leaf_id = next_id()
            lines.append(f'  {leaf_id} [label="{esc(token)}"];')
            lines.append(f"  {this_id} -> {leaf_id};")
        else:
            # Nodo interno: procesar hijos recursivamente
            left_id = emit(node[1])
            right_id = emit(node[2])
            lines.append(f"  {this_id} -> {left_id};")
            lines.append(f"  {this_id} -> {right_id};")
        return this_id

    # Generar el árbol completo y cerrar el grafo
    emit(tree)
    lines.append("}")
    return "\n".join(lines) + "\n"
