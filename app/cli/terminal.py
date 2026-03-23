"""Utilidades de terminal para el CLI."""

from __future__ import annotations


def clear_screen() -> None:
    """Borra la pantalla (secuencias ANSI; compatible con consolas modernas, p. ej. Windows 10+)."""
    print("\033[2J\033[H", end="", flush=True)
