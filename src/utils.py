"""
Utilidades auxiliares diversas para el proyecto.

Este módulo contiene funciones de ayuda que no pertenecen específicamente
a ningún otro módulo pero que son útiles en múltiples contextos.
"""

from __future__ import annotations

from typing import List

__all__ = ["tokens_from_sentence"]


def tokens_from_sentence(sentence: str, lowercase: bool = False) -> List[str]:
    """
    Divide una oración en tokens usando espacios en blanco como separadores.

    Esta función es útil para tokenizar frases de entrada antes de procesarlas
    con el algoritmo CYK.

    Parámetros:
        sentence: Cadena de entrada a tokenizar
        lowercase: Si es True, convierte todos los tokens a minúsculas

    Retorna:
        List[str]: Lista de tokens extraídos de la oración
    """
    tokens = sentence.strip().split()
    if lowercase:
        tokens = [tok.lower() for tok in tokens]
    return tokens
