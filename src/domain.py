"""domain.py — Value Objects, Excepciones de Dominio y DTOs con Pydantic.

Sesión 5.1: Validación y Modelos Confiables.

Patrón de defensa por capas:
  DTO (frontera externa) → Value Objects (dominio limpio) → Entidades (lógica)
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field, ValidationError, field_validator


# ---------------------------------------------------------------------------
# Excepciones de Dominio
# ---------------------------------------------------------------------------


class DomainError(ValueError):
    """Base para violaciones de reglas de negocio."""


class InvalidTickerError(DomainError):
    """Ticker vacío o con caracteres no permitidos."""


class InvalidQuantityError(DomainError):
    """Cantidad fuera de rango (debe ser entero positivo)."""


class InvalidPriceError(DomainError):
    """Precio inválido (debe ser finito y no negativo)."""


# ---------------------------------------------------------------------------
# Value Objects — tipos pequeños que encapsulan reglas e invariantes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Ticker:
    """Símbolo de un instrumento financiero.

    Invariantes:
    - No puede ser vacío.
    - Solo letras A–Z, dígitos 0–9, punto (.) y guión (-).
    - Se almacena siempre en mayúsculas.

    Ejemplo:
        >>> t = Ticker("aapl")
        >>> t.value
        'AAPL'
    """

    value: str

    def __post_init__(self) -> None:
        raw = (self.value or "").strip()
        if not raw:
            raise InvalidTickerError("El ticker no puede estar vacío.")
        norm = raw.upper()
        if not re.match(r"^[A-Z0-9.\-]+$", norm):
            raise InvalidTickerError(
                f"Ticker '{raw}' contiene caracteres no permitidos. "
                "Solo se aceptan A-Z, 0-9, '.' y '-'."
            )
        object.__setattr__(self, "value", norm)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Quantity:
    """Cantidad de unidades de un instrumento.

    Invariantes:
    - Debe ser entero (no bool).
    - Debe ser estrictamente positivo (> 0).

    Ejemplo:
        >>> q = Quantity(10)
        >>> q.value
        10
    """

    value: int

    def __post_init__(self) -> None:
        if isinstance(self.value, bool):
            raise InvalidQuantityError("La cantidad no puede ser booleana.")
        if not isinstance(self.value, int):
            raise InvalidQuantityError(
                f"La cantidad debe ser un entero, recibido: {type(self.value).__name__}."
            )
        if self.value <= 0:
            raise InvalidQuantityError(
                f"La cantidad debe ser mayor que 0, recibido: {self.value}."
            )


@dataclass(frozen=True, slots=True)
class Money:
    """Valor monetario.

    Invariantes:
    - Debe ser finito (excluye NaN e infinito).
    - Debe ser no negativo (>= 0).

    Ejemplo:
        >>> m = Money(150.75)
        >>> m.value
        150.75
    """

    value: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.value):
            raise InvalidPriceError(
                f"El precio debe ser un número finito, recibido: {self.value}."
            )
        if self.value < 0:
            raise InvalidPriceError(
                f"El precio no puede ser negativo, recibido: {self.value}."
            )


# ---------------------------------------------------------------------------
# DTO — Data Transfer Object con validación Pydantic en la frontera
# ---------------------------------------------------------------------------


class OrdenCompraDTO(BaseModel):
    """DTO que valida los datos de entrada al registrar una orden de compra.

    Actúa como primera línea de defensa (frontera del sistema).
    Los campos son validados automáticamente por Pydantic v2.

    Ejemplo:
        >>> dto = OrdenCompraDTO(ticker="aapl", cantidad=10, precio_entrada=150.0)
        >>> dto.ticker
        'AAPL'
    """

    ticker: str = Field(min_length=1, description="Símbolo del instrumento (ej. AAPL)")
    cantidad: int = Field(gt=0, description="Número de unidades, debe ser > 0")
    precio_entrada: float = Field(ge=0.0, description="Precio de entrada, debe ser >= 0")
    nombre: Optional[str] = Field(default=None, description="Nombre descriptivo (opcional)")

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        """Normaliza el ticker: elimina espacios y convierte a mayúsculas."""
        normalized = value.strip().upper()
        if not re.match(r"^[A-Z0-9.\-]+$", normalized):
            raise ValueError(
                f"Ticker '{value}' contiene caracteres no permitidos."
            )
        return normalized


# ---------------------------------------------------------------------------
# Mapper DTO → Dominio
# ---------------------------------------------------------------------------


def dto_a_posicion(dto: OrdenCompraDTO) -> dict:
    """Convierte un DTO validado a objetos de dominio.

    Aplica la segunda línea de defensa: Value Objects garantizan
    que el dominio interno nunca reciba datos inválidos.

    Args:
        dto: OrdenCompraDTO ya validado por Pydantic.

    Returns:
        Diccionario con los Value Objects instanciados:
        {"ticker": Ticker, "cantidad": Quantity, "precio_entrada": Money}

    Raises:
        DomainError: Si algún valor viola las invariantes del dominio.
    """
    ticker_vo = Ticker(dto.ticker)
    cantidad_vo = Quantity(dto.cantidad)
    precio_vo = Money(dto.precio_entrada)

    return {
        "ticker": ticker_vo,
        "cantidad": cantidad_vo,
        "precio_entrada": precio_vo,
        "nombre": dto.nombre or ticker_vo.value,
    }


# ---------------------------------------------------------------------------
# Utilidad para formatear errores de Pydantic de forma legible
# ---------------------------------------------------------------------------


def formato_error_pydantic(err: ValidationError) -> str:
    """Extrae el primer mensaje de error de una ValidationError de Pydantic.

    Args:
        err: Excepción de validación de Pydantic.

    Returns:
        Mensaje corto y legible para el usuario.
    """
    try:
        errors = err.errors()
        first = errors[0]
        loc = ".".join(str(x) for x in first.get("loc", []))
        msg = first.get("msg", str(err))
        return f"{loc}: {msg}" if loc else msg
    except Exception:
        return str(err).splitlines()[0]
