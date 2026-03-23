"""Stubs for tabulate (no upstream py.typed)."""

from typing import Any

def tabulate(
    tabular_data: Any = None,
    headers: Any = (),
    tablefmt: str = "simple",
    **kwargs: Any,
) -> str: ...
