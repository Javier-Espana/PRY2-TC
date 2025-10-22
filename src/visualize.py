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


def tree_to_dot(tree: Tree, colorize: bool = True) -> str:
    """
    Convierte un árbol de análisis sintáctico a representación DOT de Graphviz.

    El formato del árbol de entrada coincide con la estructura retornada por
    build_parse_tree:
    - Nodo terminal: (cabecera, token)  
    - Nodo no terminal: (cabecera, subárbol_izquierdo, subárbol_derecho)

    Parámetros:
        tree: Árbol de análisis en formato recursivo
        colorize: Si es True, aplica colores distintivos a los nodos
        
    Retorna:
        str: Representación del árbol en formato DOT
        
    Esquema de colores (cuando colorize=True):
        - Símbolo inicial (S0): Azul (#4A90E2)
        - Variables no terminales: Verde (#50C878)
        - Terminales (palabras): Naranja (#FF9F40)
    """

    lines: List[str] = []
    # Configuración del grafo DOT
    lines.append("digraph ParseTree {")
    lines.append("  rankdir=TB;")  # Dirección de arriba hacia abajo
    lines.append("  node [fontsize=12, fontname=\"Arial\"];")
    
    # Estilos base según tipo de nodo (cuando colorize=True)
    if colorize:
        lines.append("  edge [color=\"#666666\", penwidth=1.5];")

    # Contador para generar IDs únicos de nodos
    counter = [0]
    is_root = [True]  # Flag para identificar el nodo raíz

    def next_id() -> str:
        """Genera el siguiente ID único para un nodo."""
        nid = f"n{counter[0]}"
        counter[0] += 1
        return nid

    def esc(label: str) -> str:
        """Escapa caracteres especiales para uso en etiquetas DOT."""
        return label.replace("\\", "\\\\").replace("\"", "\\\"")

    def get_node_style(label: str, is_terminal: bool, is_start: bool) -> str:
        """
        Determina el estilo del nodo según su tipo.
        
        Parámetros:
            label: Etiqueta del nodo
            is_terminal: Si es un nodo terminal (palabra)
            is_start: Si es el símbolo inicial (raíz del árbol)
            
        Retorna:
            String con los atributos de estilo DOT
        """
        if not colorize:
            return 'shape=plaintext'
        
        if is_start:
            # Símbolo inicial: azul, forma de cuadrado redondeado
            return 'shape=box, style="rounded,filled", fillcolor="#4A90E2", fontcolor=white, penwidth=2'
        elif is_terminal:
            # Terminales: naranja, forma ovalada
            return 'shape=ellipse, style=filled, fillcolor="#FF9F40", fontcolor=white, penwidth=1.5'
        else:
            # Variables: verde, forma de cuadrado
            return 'shape=box, style="rounded,filled", fillcolor="#50C878", fontcolor=white, penwidth=1.5'

    def emit(node: Tree) -> str:
        """
        Emite recursivamente los nodos del árbol en formato DOT.
        
        Retorna el ID del nodo emitido para conectarlo con su padre.
        """
        head = node[0]
        this_id = next_id()
        
        # Determinar si es el nodo raíz
        is_start_node = is_root[0]
        if is_root[0]:
            is_root[0] = False
        
        # Aplicar estilo al nodo de la variable/símbolo
        node_style = get_node_style(head, is_terminal=False, is_start=is_start_node)
        lines.append(f'  {this_id} [label="{esc(head)}", {node_style}];')
        
        if len(node) == 2 and isinstance(node[1], str):
            # Nodo hoja terminal: crear nodo hijo con el token
            token = node[1]
            leaf_id = next_id()
            terminal_style = get_node_style(token, is_terminal=True, is_start=False)
            lines.append(f'  {leaf_id} [label="{esc(token)}", {terminal_style}];')
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
