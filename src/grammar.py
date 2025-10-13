"""
Estructuras de datos principales para gramáticas libres de contexto.

Este módulo define las clases fundamentales para representar gramáticas CFG,
incluyendo no terminales, terminales, símbolo inicial y producciones.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Sequence, Set, Tuple

# Tipo para representar el lado derecho de una producción (secuencia de símbolos)
RHS = Tuple[str, ...]


@dataclass
class Grammar:
    """
    Representación de una gramática libre de contexto (CFG).

    Atributos:
        nonterminals: Conjunto de símbolos no terminales (variables)
        terminals: Conjunto de símbolos terminales
        start_symbol: Símbolo inicial de la gramática
        productions: Diccionario que mapea cada no terminal a un conjunto de producciones.
                    Cada producción es una tupla de símbolos. La tupla vacía representa ε.
    """

    nonterminals: Set[str]
    terminals: Set[str]
    start_symbol: str
    productions: Dict[str, Set[RHS]] = field(default_factory=dict)

    def clone(self) -> "Grammar":
        """
        Retorna una copia profunda de la gramática.
        
        Esto es útil cuando se necesita modificar una gramática sin alterar la original,
        como durante el proceso de conversión a CNF.
        
        Retorna:
            Grammar: Nueva instancia de gramática con los mismos datos
        """
        return Grammar(
            nonterminals=set(self.nonterminals),
            terminals=set(self.terminals),
            start_symbol=self.start_symbol,
            productions={head: set(bodies) for head, bodies in self.productions.items()},
        )

    def add_production(self, head: str, body: Sequence[str]) -> None:
        """
        Añade una producción de la forma head -> body a la gramática.
        
        Parámetros:
            head: Símbolo no terminal del lado izquierdo
            body: Secuencia de símbolos del lado derecho (puede estar vacía para ε)
        """
        self.productions.setdefault(head, set()).add(tuple(body))
        self.nonterminals.add(head)
