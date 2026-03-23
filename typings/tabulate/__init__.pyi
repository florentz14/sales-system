"""Stubs for tabulate (no upstream py.typed).

Incluye tipos usados para `tablefmt` personalizado (`Line`, `DataRow`, `TableFormat`).
En tiempo de ejecución son `namedtuple`; aquí se modelan como clases invocables.
"""

from typing import Any, Callable

# namedtuples en el paquete real; permiten construcción con argumentos posicionales.
Line: type[Any]
DataRow: type[Any]
TableFormat: type[Any]

def tabulate(
    tabular_data: Any = None,
    headers: Any = (),
    tablefmt: str | TableFormat = "simple",
    **kwargs: Any,
) -> str: ...

def tabulate_formats() -> list[str]: ...
def simple_separated_format(separator: str) -> Callable[..., str]: ...
