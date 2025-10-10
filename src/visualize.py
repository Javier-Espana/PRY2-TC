"""Utilities to visualize parse trees as Graphviz DOT."""

from __future__ import annotations

from typing import List, Tuple, Union

Tree = Union[Tuple[str, str], Tuple[str, "Tree", "Tree"]]

__all__ = ["tree_to_dot"]


def tree_to_dot(tree: Tree) -> str:
    """Return a Graphviz DOT representation of the parse tree.

    The input tree format matches the structure returned by ``build_parse_tree``:
    - Terminal: (Head, token)
    - Non-terminal: (Head, left_subtree, right_subtree)
    """

    lines: List[str] = []
    lines.append("digraph ParseTree {")
    lines.append("  rankdir=TB;")
    lines.append("  node [shape=plaintext, fontsize=12];")

    counter = [0]

    def next_id() -> str:
        nid = f"n{counter[0]}"
        counter[0] += 1
        return nid

    def esc(label: str) -> str:
        return label.replace("\\", "\\\\").replace("\"", "\\\"")

    def emit(node: Tree) -> str:
        head = node[0]
        this_id = next_id()
        lines.append(f'  {this_id} [label="{esc(head)}"];')
        if len(node) == 2 and isinstance(node[1], str):
            # Terminal leaf: add child with token label (no extra quotes inside label)
            token = node[1]
            leaf_id = next_id()
            lines.append(f'  {leaf_id} [label="{esc(token)}"];')
            lines.append(f"  {this_id} -> {leaf_id};")
        else:
            left_id = emit(node[1])
            right_id = emit(node[2])
            lines.append(f"  {this_id} -> {left_id};")
            lines.append(f"  {this_id} -> {right_id};")
        return this_id

    emit(tree)
    lines.append("}")
    return "\n".join(lines) + "\n"
