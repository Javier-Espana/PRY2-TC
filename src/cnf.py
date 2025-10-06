"""Conversion of CFGs to Chomsky Normal Form (CNF)."""

from __future__ import annotations

import re
from typing import Dict, List, Sequence, Set, Tuple

from .grammar import Grammar, RHS

__all__ = ["convert_to_cnf"]


def convert_to_cnf(grammar: Grammar) -> Grammar:
    """Return an equivalent grammar in CNF following the standard pipeline."""

    g = grammar.clone()
    g = _add_new_start_symbol(g)
    g = _remove_useless_symbols(g)
    g = _remove_epsilon_productions(g)
    g = _remove_unit_productions(g)
    g = _replace_terminals_in_long_rules(g)
    g = _binarise_rules(g)
    return g


def _add_new_start_symbol(g: Grammar) -> Grammar:
    g2 = g.clone()
    original_start = g2.start_symbol
    fresh_start = _fresh_nonterminal(g2.nonterminals, base="S0")
    g2.nonterminals.add(fresh_start)
    g2.start_symbol = fresh_start
    g2.add_production(fresh_start, [original_start])
    return g2


def _remove_useless_symbols(g: Grammar) -> Grammar:
    productive: Set[str] = set()
    changed = True
    while changed:
        changed = False
        for head, bodies in g.productions.items():
            if head in productive:
                continue
            for body in bodies:
                if all(symbol in g.terminals or symbol in productive for symbol in body):
                    productive.add(head)
                    changed = True
                    break

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

    reachable: Set[str] = {g.start_symbol}
    frontier = [g.start_symbol]
    while frontier:
        current = frontier.pop()
        for body in productions_filtered.get(current, set()):
            for symbol in body:
                if symbol in productions_filtered and symbol not in reachable:
                    reachable.add(symbol)
                    frontier.append(symbol)

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

    terminals = {
        symbol
        for bodies in productions.values()
        for body in bodies
        for symbol in body
        if symbol not in productions
    }

    return Grammar(nonterminals=nonterminals, terminals=terminals, start_symbol=g.start_symbol, productions=productions)


def _remove_epsilon_productions(g: Grammar) -> Grammar:
    nullable = _nullable_symbols(g)
    start = g.start_symbol
    productions: Dict[str, Set[RHS]] = {head: set() for head in g.productions}

    for head, bodies in g.productions.items():
        for body in bodies:
            if not body:
                continue
            nullable_positions = [idx for idx, symbol in enumerate(body) if symbol in nullable]
            count = len(nullable_positions)
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
    nullable: Set[str] = set()
    changed = True
    while changed:
        changed = False
        for head, bodies in g.productions.items():
            if head in nullable:
                continue
            for body in bodies:
                if not body or all(symbol in nullable for symbol in body):
                    nullable.add(head)
                    changed = True
                    break
    return nullable


def _remove_unit_productions(g: Grammar) -> Grammar:
    closure: Dict[str, Set[str]] = {}
    for head in g.productions:
        reachable: Set[str] = {head}
        stack = [head]
        while stack:
            current = stack.pop()
            for body in g.productions[current]:
                if len(body) == 1 and body[0] in g.productions and body[0] not in reachable:
                    reachable.add(body[0])
                    stack.append(body[0])
        closure[head] = reachable

    productions: Dict[str, Set[RHS]] = {head: set() for head in g.productions}
    for head, targets in closure.items():
        for target in targets:
            for body in g.productions[target]:
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
    productions: Dict[str, Set[RHS]] = {head: set() for head in g.productions}
    new_terminal_vars: Dict[str, str] = {}
    nonterminals = set(g.nonterminals)

    def get_var_for_terminal(symbol: str) -> str:
        if symbol not in new_terminal_vars:
            candidate = _fresh_nonterminal(nonterminals, base=f"T_{_slug(symbol)}")
            new_terminal_vars[symbol] = candidate
            nonterminals.add(candidate)
            productions.setdefault(candidate, set()).add((symbol,))
        return new_terminal_vars[symbol]

    for head, bodies in g.productions.items():
        for body in bodies:
            if len(body) <= 1:
                productions[head].add(body)
                continue
            replaced = [get_var_for_terminal(symbol) if symbol in g.terminals else symbol for symbol in body]
            productions[head].add(tuple(replaced))

    terminals = set(g.terminals)
    return Grammar(nonterminals=nonterminals, terminals=terminals, start_symbol=g.start_symbol, productions=productions)


def _binarise_rules(g: Grammar) -> Grammar:
    productions: Dict[str, Set[RHS]] = {head: set() for head in g.productions}
    nonterminals = set(g.nonterminals)
    counter = 1

    def fresh_var() -> str:
        nonlocal counter
        while True:
            candidate = f"X{counter}"
            counter += 1
            if candidate not in nonterminals and candidate not in g.terminals:
                nonterminals.add(candidate)
                return candidate

    for head, bodies in g.productions.items():
        for body in bodies:
            if len(body) <= 2:
                productions[head].add(body)
                continue
            symbols = list(body)
            left = symbols[0]
            rest = symbols[1:]
            current_head = head
            while len(rest) > 1:
                new_var = fresh_var()
                productions[current_head].add((left, new_var))
                left = rest[0]
                rest = rest[1:]
                current_head = new_var
            productions[current_head].add((left, rest[0]))

    terminals = set(g.terminals)
    return Grammar(nonterminals=nonterminals, terminals=terminals, start_symbol=g.start_symbol, productions=productions)


def _fresh_nonterminal(existing: Set[str], base: str = "X") -> str:
    if base not in existing:
        return base
    index = 1
    while f"{base}{index}" in existing:
        index += 1
    return f"{base}{index}"


def _slug(token: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "_", token) or "sym"
