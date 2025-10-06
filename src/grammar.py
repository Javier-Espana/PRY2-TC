"""Core grammar data structures used across the project."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Sequence, Set, Tuple

RHS = Tuple[str, ...]


@dataclass
class Grammar:
    """Representation of a context-free grammar (CFG).

    Attributes
    ----------
    nonterminals:
        Set of variable symbols.
    terminals:
        Set of terminals.
    start_symbol:
        Distinguished start variable.
    productions:
        Mapping ``head -> set of bodies`` where each body is a tuple of symbols.
        The empty tuple represents the ε-production.
    """

    nonterminals: Set[str]
    terminals: Set[str]
    start_symbol: str
    productions: Dict[str, Set[RHS]] = field(default_factory=dict)

    def clone(self) -> "Grammar":
        """Return a deep copy of the grammar."""

        return Grammar(
            nonterminals=set(self.nonterminals),
            terminals=set(self.terminals),
            start_symbol=self.start_symbol,
            productions={head: set(bodies) for head, bodies in self.productions.items()},
        )

    def add_production(self, head: str, body: Sequence[str]) -> None:
        """Add the production ``head -> body`` to the grammar."""

        self.productions.setdefault(head, set()).add(tuple(body))
        self.nonterminals.add(head)
