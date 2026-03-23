"""Validación de entradas reutilizable (Pydantic) para CLI y otros puntos de entrada."""

from __future__ import annotations

from pydantic import ValidationError

from app.schemas.user import UserCreate


def user_create_from_cli(
    username: str,
    password: str,
    role_names: list[str],
) -> tuple[UserCreate | None, str | None]:
    """
    Valida datos de alta de usuario. Devuelve (modelo, None) o (None, mensaje de error).
    """
    try:
        u = UserCreate(
            username=username.strip(),
            password=password,
            role_names=role_names,
        )
    except ValidationError as e:
        parts: list[str] = []
        for err in e.errors():
            loc = ".".join(str(x) for x in err.get("loc", ()))
            msg = err.get("msg", "inválido")
            parts.append(f"{loc}: {msg}" if loc else msg)
        return None, "; ".join(parts) if parts else str(e)
    if not u.username:
        return None, "El nombre de usuario no puede estar vacío."
    return u, None


def parse_role_names_csv(raw: str) -> list[str]:
    """Lista de nombres de rol a partir de texto separado por comas."""
    return [p.strip() for p in raw.split(",") if p.strip()]
