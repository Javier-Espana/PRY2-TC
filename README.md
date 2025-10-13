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

### Instalación de dependencias

En Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

En Linux/macOS (bash):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Ejecución del programa

Una vez instaladas las dependencias, el programa se ejecuta con:

```bash
python main.py <archivo_gramatica> "<frase_a_analizar>"
```

Ejemplo en Windows (PowerShell):
```powershell
python main.py examples\grammar_instructions.txt "she eats a cake"
```

Ejemplo en Linux/macOS (bash):
```bash
python main.py examples/grammar_instructions.txt "she eats a cake"
```

Argumentos relevantes:

- `--show-cnf` muestra la gramática transformada a CNF por la salida estándar.
- `--cnf-output archivo` guarda la gramática CNF en el archivo indicado.
- `--tokens` permite indicar manualmente los tokens (sin volver a tokenizar la
  frase).
- `--lowercase` convierte la oración a minúsculas antes de tokenizarla.
- `--tree-dot archivo.dot` exporta el árbol en formato Graphviz DOT cuando la frase es aceptada.
- `--tree-png archivo.png` renderiza directamente a PNG usando la librería Python `graphviz` y el binario de Graphviz (`dot`).

El programa imprime si la oración pertenece al lenguaje, el tiempo de ejecución
(y en nanosegundos se usa notación decimal) y, cuando procede, el árbol de
análisis.

## 🧪 Ejemplos de uso

Usando la gramática del enunciado incluida en `examples/grammar_instructions.txt`:

- 2 aceptadas y semánticamente correctas:
  - `she eats a cake`
  - `he drinks the juice`
- 2 aceptadas pero semánticamente extrañas (sintácticamente válidas):
  - `the oven drinks a soup`
  - `the knife eats the meat`
- 2 no aceptadas por la gramática:
  - `she eat a cake` (verbo fuera del inventario: falta la forma "eat" singular)
  - `drinks she the juice` (orden no permitido por la gramática)

El árbol de derivación se imprime con indentación. Ejemplo parcial:

```
S
  NP -> 'she'
  VP
    V -> 'eats'
    NP
      Det -> 'a'
      N -> 'cake'
```

### Exportar y visualizar el árbol (Graphviz)

Puedes generar un archivo DOT y luego renderizarlo como PNG/SVG si tienes Graphviz instalado.

1) Exportar DOT desde el programa:

```bash
python main.py <archivo_gramatica> "<frase>" --tree-dot <archivo_salida.dot>
```

Ejemplo en Windows (PowerShell):
```powershell
python main.py examples\grammar_instructions.txt "she eats a cake" --tree-dot tree.dot
```

Ejemplo en Linux/macOS (bash):
```bash
python main.py examples/grammar_instructions.txt "she eats a cake" --tree-dot tree.dot
```

2) Renderizar con Graphviz:

Windows (si `dot.exe` está en PATH):
```powershell
dot -Tpng tree.dot -o tree.png
```

Linux/macOS:
```bash
dot -Tsvg tree.dot -o tree.svg
```

Instalación de Graphviz:
- Windows: https://graphviz.org/download/ (agrega Graphviz\bin al PATH)
- Linux: `sudo apt-get install graphviz` o equivalente
- macOS: `brew install graphviz`

También puedes generar la imagen PNG directamente desde el programa con:

```bash
python main.py <archivo_gramatica> "<frase>" --tree-png <archivo_salida.png>
```

Ejemplo en Windows (PowerShell):
```powershell
python main.py examples\grammar_instructions.txt "she eats a cake" --tree-png tree.png
```

Ejemplo en Linux/macOS (bash):
```bash
python main.py examples/grammar_instructions.txt "she eats a cake" --tree-png tree.png
```

Requisitos para `--tree-png`:
- Paquete Python: `pip install graphviz` (ya está en `requirements.txt`)
- Binario Graphviz instalado en el sistema y accesible en PATH (`dot`)

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
├── main.py              # CLI principal
├── requirements.txt     # Dependencias del proyecto
├── src/
│   ├── __init__.py      # Punto de entrada del paquete
│   ├── parser.py        # Capa de compatibilidad / API pública
│   ├── grammar.py       # Modelo de la gramática
│   ├── grammar_io.py    # Parser y serialización de gramáticas
│   ├── cnf.py           # Conversión a Forma Normal de Chomsky
│   ├── cyk.py           # Algoritmo CYK y reconstrucción del árbol
│   ├── utils.py         # Utilidades auxiliares (tokenización, etc.)
│   └── visualize.py     # Generación de grafos DOT para Graphviz
├── README.md            # Este documento
└── examples/
    ├── grammar.txt              # Gramática de ejemplo
    └── grammar_instructions.txt # Gramática del enunciado del proyecto
```

> Nota: crea la carpeta `examples/` con tu propia gramática para ejecutar los
> ejemplos anteriores.
