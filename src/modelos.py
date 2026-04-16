"""modelos.py — Modelos de dominio: Instrumento y Posicion.

Define los objetos inmutables/mutables que representan los activos y
posiciones de un portafolio financiero, con validaciones defensivas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

Numero = Union[int, float]


@dataclass(frozen=True)
class Instrumento:
    """Representa un activo financiero de forma inmutable.

    Args:
        ticker: Sigla del instrumento (ej. "AAPL", "US10Y").
        tipo: Tipo de instrumento ("Acción", "Bono", etc.).
        sector: Sector económico ("Tecnología", "Gobierno", etc.).
    """

    ticker: str
    tipo: str
    sector: str


class Posicion:
    """Representa una posición en un instrumento financiero.

    Args:
        instrumento: Instancia de :class:`Instrumento` asociada a la posición.
        cantidad: Número de unidades compradas. Debe ser no negativo.
        precio_entrada: Precio al que se adquirió la posición.

    Raises:
        TypeError: Si alguno de los argumentos no cumple el tipo esperado.
        ValueError: Si ``cantidad`` es negativa.
    """

    def __init__(
        self,
        instrumento: Instrumento,
        cantidad: Numero,
        precio_entrada: Numero,
    ) -> None:
        if not isinstance(instrumento, Instrumento):
            raise TypeError("instrumento debe ser de tipo Instrumento")
        if isinstance(precio_entrada, bool) or not isinstance(precio_entrada, (int, float)):
            raise TypeError("precio_entrada debe ser numérico")
        self.instrumento = instrumento
        self.precio_entrada = float(precio_entrada)
        # Usa el setter para validar el valor inicial
        self.cantidad = cantidad

    @property
    def cantidad(self) -> float:
        """Cantidad de unidades de la posición."""
        return self._cantidad

    @cantidad.setter
    def cantidad(self, value: Numero) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("cantidad debe ser numérica")
        if value < 0:
            raise ValueError("cantidad no puede ser negativa")
        self._cantidad = float(value)

    def calcular_valor_actual(self, precio_mercado: Numero) -> float:
        """Calcula el valor actual de la posición.

        Args:
            precio_mercado: Precio actual del instrumento.

        Returns:
            Valor de la posición = cantidad × precio_mercado.
        """
        if isinstance(precio_mercado, bool) or not isinstance(precio_mercado, (int, float)):
            raise TypeError("precio_mercado debe ser numérico")
        return self._cantidad * float(precio_mercado)

    def calcular_ganancia_no_realizada(self, precio_actual: Numero) -> float:
        """Calcula la ganancia o pérdida no realizada (PnL).

        Args:
            precio_actual: Precio actual del instrumento.

        Returns:
            (precio_actual − precio_entrada) × cantidad.
        """
        if isinstance(precio_actual, bool) or not isinstance(precio_actual, (int, float)):
            raise TypeError("precio_actual debe ser numérico")
        return (float(precio_actual) - self.precio_entrada) * self._cantidad

    def tiene_alerta_perdida(self, precio_actual: Numero, umbral: float = 0.10) -> bool:
        """Indica si la pérdida no realizada supera el umbral porcentual.

        Args:
            precio_actual: Precio actual del instrumento.
            umbral: Porcentaje máximo de pérdida permitido (por defecto 10%).

        Returns:
            True si la pérdida porcentual es mayor que ``umbral``.
        """
        pnl = self.calcular_ganancia_no_realizada(precio_actual)
        costo_base = self.precio_entrada * self._cantidad
        if costo_base == 0:
            return False
        return (pnl / costo_base) < -umbral

    def __repr__(self) -> str:
        return (
            f"Posicion(instrumento={self.instrumento!r}, "
            f"cantidad={self._cantidad}, precio_entrada={self.precio_entrada})"
        )
