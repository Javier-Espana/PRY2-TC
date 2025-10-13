"""
Interfaz de línea de comandos para conversión de CFG a CNF y análisis CYK.

Este módulo proporciona la funcionalidad principal del programa, permitiendo al usuario:
- Cargar una gramática libre de contexto desde un archivo
- Convertirla automáticamente a Forma Normal de Chomsky (CNF)
- Ejecutar el algoritmo CYK para determinar si una frase pertenece al lenguaje
- Generar y exportar árboles de análisis sintáctico
"""

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
from src.visualize import tree_to_dot


def _build_argument_parser() -> argparse.ArgumentParser:
	"""
	Construye y configura el analizador de argumentos de línea de comandos.
	
	Retorna:
		argparse.ArgumentParser: Parser configurado con todos los argumentos disponibles
	"""
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
	parser.add_argument(
		"--tree-dot",
		type=Path,
		help="Si la cadena es aceptada, exporta el parse tree en formato Graphviz DOT al archivo indicado.",
	)
	parser.add_argument(
		"--tree-png",
		type=Path,
		help=(
			"Si la cadena es aceptada, renderiza el parse tree a PNG usando Graphviz. "
			"Requiere tener instalado el paquete Python 'graphviz' y la herramienta Graphviz (dot) en el sistema."
		),
	)
	return parser


def main(argv: list[str] | None = None) -> int:
	"""
	Función principal que ejecuta todo el flujo del programa.
	
	Parámetros:
		argv: Lista de argumentos de línea de comandos. Si es None, usa sys.argv
		
	Retorna:
		int: Código de salida (0 = éxito, >0 = error)
	"""
	parser = _build_argument_parser()
	args = parser.parse_args(argv)

	# Cargar y parsear la gramática desde el archivo
	try:
		grammar_text = args.grammar.read_text(encoding="utf-8")
	except OSError as exc:
		parser.error(f"No se pudo leer la gramática: {exc}")

	try:
		grammar = parse_grammar(grammar_text)
	except Exception as exc:  # noqa: BLE001 - mostrar error al usuario final
		parser.error(f"Error al analizar la gramática: {exc}")

	# Convertir la gramática a Forma Normal de Chomsky
	cnf_grammar = convert_to_cnf(grammar)

	# Guardar gramática CNF en archivo si se solicita
	if args.cnf_output is not None:
		try:
			args.cnf_output.write_text("\n".join(grammar_to_lines(cnf_grammar)) + "\n", encoding="utf-8")
		except OSError as exc:
			parser.error(f"No se pudo escribir la gramática CNF: {exc}")

	# Mostrar gramática CNF por pantalla si se solicita
	if args.show_cnf:
		print("Gramática en CNF:")
		print("\n".join(grammar_to_lines(cnf_grammar)))
		print()

	# Obtener tokens a analizar (ya sea de argumentos o tokenizando una frase)
	if args.tokens:
		tokens = args.tokens
	else:
		sentence = args.sentence
		if sentence is None:
			sentence = sys.stdin.read()
		tokens = tokens_from_sentence(sentence, lowercase=args.lowercase)

	# Ejecutar algoritmo CYK y medir tiempo de ejecución
	start_time = time.perf_counter()
	accepted, table, back = cyk_parse(cnf_grammar, tokens)
	elapsed = time.perf_counter() - start_time

	# Mostrar resultados del análisis
	verdict = "SÍ" if accepted else "NO"
	print(f"Tokens: {tokens}")
	print(f"Pertenece al lenguaje: {verdict}")
	print(f"Tiempo CYK: {elapsed:.6f} s")

	if accepted:
		# Construir y mostrar el árbol de análisis sintáctico
		tree = build_parse_tree(tokens, back, cnf_grammar.start_symbol)
		print("Parse tree:")
		print(format_tree(tree))

		# Generar representación DOT si se necesita para exportación
		dot = None
		if args.tree_dot or args.tree_png:
			dot = tree_to_dot(tree)

		# Exportar árbol en formato DOT si se solicita
		if args.tree_dot and dot is not None:
			try:
				args.tree_dot.write_text(dot, encoding="utf-8")
			except OSError as exc:
				parser.error(f"No se pudo escribir el archivo DOT: {exc}")

		# Exportar árbol como imagen PNG si se solicita
		if args.tree_png and dot is not None:
			try:
				import graphviz  # type: ignore
			except Exception:
				parser.error(
					"Falta la librería Python 'graphviz'. Instálala con: python -m pip install graphviz"
				)
			try:
				png_bytes = graphviz.Source(dot).pipe(format="png")
			except Exception as exc:  # incluye Ejecutable dot no encontrado
				parser.error(
					"No se pudo invocar Graphviz (dot). Asegúrate de instalar Graphviz y que 'dot' esté en PATH. "
					f"Detalle: {exc}"
				)
			try:
				args.tree_png.write_bytes(png_bytes)
			except OSError as exc:
				parser.error(f"No se pudo escribir el PNG: {exc}")
	else:
		print("No se puede construir un parse tree porque la cadena no pertenece al lenguaje.")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
