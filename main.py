"""Command line interface for CFG to CNF conversion and CYK parsing."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

from src.parser import (
	build_parse_tree,
	convert_to_cnf,
	cyk_parse,
	format_tree,
	grammar_to_lines,
	parse_grammar,
	tokens_from_sentence,
)


def _build_argument_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Convierte una CFG a CNF y ejecuta el algoritmo CYK sobre una frase dada.",
	)
	parser.add_argument("grammar", type=Path, help="Ruta al archivo que contiene la gramática CFG")
	parser.add_argument(
		"sentence",
		nargs="?",
		help=(
			"Frase en inglés a evaluar. Si se omite, se leerá desde stdin \n"
			"(útil para frases con saltos de línea)."
		),
	)
	parser.add_argument(
		"--cnf-output",
		type=Path,
		help="Si se indica, se guardará la gramática convertida a CNF en el archivo especificado.",
	)
	parser.add_argument(
		"--lowercase",
		action="store_true",
		help="Convierte la frase a minúsculas antes de tokenizar (útil si la gramática usa minúsculas).",
	)
	parser.add_argument(
		"--show-cnf",
		action="store_true",
		help="Imprime la gramática en CNF por la salida estándar.",
	)
	parser.add_argument(
		"--tokens",
		nargs="*",
		help="Permite especificar los tokens manualmente. Ignora --lowercase y la frase libre.",
	)
	return parser


def main(argv: list[str] | None = None) -> int:
	parser = _build_argument_parser()
	args = parser.parse_args(argv)

	try:
		grammar_text = args.grammar.read_text(encoding="utf-8")
	except OSError as exc:
		parser.error(f"No se pudo leer la gramática: {exc}")

	try:
		grammar = parse_grammar(grammar_text)
	except Exception as exc:  # noqa: BLE001 - mostrar error al usuario final
		parser.error(f"Error al analizar la gramática: {exc}")

	cnf_grammar = convert_to_cnf(grammar)

	if args.cnf_output is not None:
		try:
			args.cnf_output.write_text("\n".join(grammar_to_lines(cnf_grammar)) + "\n", encoding="utf-8")
		except OSError as exc:
			parser.error(f"No se pudo escribir la gramática CNF: {exc}")

	if args.show_cnf:
		print("Gramática en CNF:")
		print("\n".join(grammar_to_lines(cnf_grammar)))
		print()

	if args.tokens:
		tokens = args.tokens
	else:
		sentence = args.sentence
		if sentence is None:
			sentence = sys.stdin.read()
		tokens = tokens_from_sentence(sentence, lowercase=args.lowercase)

	start_time = time.perf_counter()
	accepted, table, back = cyk_parse(cnf_grammar, tokens)
	elapsed = time.perf_counter() - start_time

	verdict = "SI" if accepted else "NO"
	print(f"Tokens: {tokens}")
	print(f"Pertenece al lenguaje: {verdict}")
	print(f"Tiempo CYK: {elapsed:.6f} s")

	if accepted:
		tree = build_parse_tree(tokens, back, cnf_grammar.start_symbol)
		print("Parse tree:")
		print(format_tree(tree))
	else:
		print("No se puede construir un parse tree porque la cadena no pertenece al lenguaje.")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
