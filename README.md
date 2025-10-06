# Conversión CFG a CNF y parsing CYK

Este proyecto implementa en Python la conversión de gramáticas libres de contexto (CFG)
a su Forma Normal de Chomsky (CNF) y el algoritmo de Cocke–Younger–Kasami (CYK) para
verificar si una oración pertenece al lenguaje descrito por la gramática y
construir su árbol de derivación.

## 📐 Diseño de la aplicación

- **Representación de la gramática**: la clase `Grammar` (en `src/grammar.py`)
  almacena el conjunto de variables, terminales, símbolo inicial y un diccionario
  de producciones. Cada producción se guarda como una tupla; la tupla vacía
  representa a `ε`.
- **Entrada de la gramática**: se utiliza un formato de texto con secciones
  `Variables`, `Terminals`, `Start` y `Rules`. Las reglas aceptan múltiples
  alternativas con `|` y permiten terminales entrecomillados para tokens con
  espacios.
- **Conversión a CNF**: se aplica un pipeline estándar (nuevo símbolo inicial,
  eliminación de símbolos inútiles, ε-producciones y unitarias, sustitución de
  terminales, binarización). Cada paso está implementado como una función pura en
  `src/cnf.py`.
- **CYK + programación dinámica**: la función `cyk_parse` (en `src/cyk.py`)
  triangular donde `table[i][l]` contiene las variables que derivan el span
  `tokens[i:i+l]`. Se almacenan apuntadores para reconstruir árboles.
- **Árbol de derivación**: `build_parse_tree` vuelve a recorrer los apuntadores
  para producir una estructura recursiva que `format_tree` imprime de forma
  legible.
- **Interfaz de línea de comandos**: `main.py` orquesta la lectura de la
  gramática, la conversión, la tokenización de la frase, la ejecución de CYK y
  la presentación de resultados (incluyendo el tiempo medido con
  `time.perf_counter`).

## ✅ Ejecución

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
python main.py grammar.txt "She eats a cake with a fork"
```

Argumentos relevantes:

- `--show-cnf` muestra la gramática transformada a CNF por la salida estándar.
- `--cnf-output archivo` guarda la gramática CNF en el archivo indicado.
- `--tokens` permite indicar manualmente los tokens (sin volver a tokenizar la
  frase).
- `--lowercase` convierte la oración a minúsculas antes de tokenizarla.

El programa imprime si la oración pertenece al lenguaje, el tiempo de ejecución
(y en nanosegundos se usa notación decimal) y, cuando procede, el árbol de
análisis.

## 🧪 Ejemplos de uso

Tomando la gramática del README (`grammar.txt` en la carpeta `examples`):

- Frases **aceptadas**:
  - `She eats a cake`
  - `She eats the cake with a fork`
  - `She eats a cake with a fork`
- Frases **rechazadas**:
  - `She cake eats`
  - `She eats`
  - `She eats fork`

El árbol de derivación se imprime con indentación. Ejemplo parcial:

```
S
  NP -> 'She'
  VP
    V -> 'eats'
    NP
      Det -> 'a'
      N -> 'cake'
```

## 💬 Discusión

- **Obstáculos**: manejar símbolos con espacios y reglas con múltiples
  alternativas requiere un analizador robusto; se solucionó permitiendo tokens
  entrecomillados y limpiando la entrada. La eliminación de ε-producciones y
  unitarias demanda cuidado para no perder derivaciones válidas; se implementó
  un cierre transitivo explícito.
- **Recomendaciones**: validar que la gramática de entrada esté bien formada y
  cubra todas las palabras que se pretenden reconocer. Para gramáticas grandes,
  conviene activar `--tokens` y proporcionar tokens preprocesados (por ejemplo,
  en minúsculas).
- **Extensiones futuras**: agregar más formatos de entrada (JSON/YAML), una
  interfaz gráfica y visualizaciones de árboles en formatos estándar (Graphviz).

## 📂 Estructura del proyecto

```
PRY2-TC/
├── main.py            # CLI principal
├── src/
│   ├── __init__.py    # Punto de entrada del paquete
│   ├── parser.py      # Capa de compatibilidad / API pública
│   ├── grammar.py     # Modelo de la gramática
│   ├── grammar_io.py  # Parser y serialización de gramáticas
│   ├── cnf.py         # Conversión a Forma Normal de Chomsky
│   ├── cyk.py         # Algoritmo CYK y reconstrucción del árbol
│   └── utils.py       # Utilidades auxiliares (tokenización, etc.)
├── README.md          # Este documento
└── examples/
    └── grammar.txt    # Gramática de ejemplo (ver instrucciones)
```

> Nota: crea la carpeta `examples/` con tu propia gramática para ejecutar los
> ejemplos anteriores.
