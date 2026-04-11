from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class MarketDataProvider(ABC):
    """Interfaz abstracta para proveedores de datos de mercado.

    Define el contrato que deben cumplir todos los proveedores,
    desacoplando la lógica de negocio de las fuentes de datos.
    """

    @abstractmethod
    def obtener_precio_actual(self, ticker: str) -> float:
        """Retorna el precio actual del instrumento.

        Args:
            ticker: Símbolo del instrumento (ej. "AAPL").

        Returns:
            Precio actual como float.
        """
        ...

    @abstractmethod
    def obtener_historia(self, ticker: str) -> List[float]:
        """Retorna el historial de precios de cierre del último año.

        Args:
            ticker: Símbolo del instrumento.

        Returns:
            Lista de precios de cierre ordenados cronológicamente.
        """
        ...


class YahooFinanceClient(MarketDataProvider):
    """Proveedor de datos usando la API de Yahoo Finance (yfinance)."""

    def obtener_precio_actual(self, ticker: str) -> float:
        """Obtiene el precio actual desde Yahoo Finance.

        Args:
            ticker: Símbolo del instrumento.

        Returns:
            Precio actual del instrumento.

        Raises:
            ValueError: Si no se puede obtener el precio.
        """
        import yfinance as yf  # importación diferida para no romper tests sin red
        instrumento = yf.Ticker(ticker)
        precio = instrumento.fast_info.last_price
        if precio is None:
            raise ValueError(f"No se pudo obtener el precio para '{ticker}'")
        return float(precio)

    def obtener_historia(self, ticker: str) -> List[float]:
        """Obtiene el historial de precios de cierre del último año.

        Args:
            ticker: Símbolo del instrumento.

        Returns:
            Lista de precios de cierre.

        Raises:
            ValueError: Si no hay historial disponible.
        """
        import yfinance as yf
        historial = yf.Ticker(ticker).history(period="1y")
        if historial.empty:
            raise ValueError(f"Sin historial disponible para '{ticker}'")
        return historial["Close"].tolist()


class MockMarketDataProvider(MarketDataProvider):
    """Proveedor de datos simulado para pruebas unitarias.

    Permite testear la lógica de negocio sin depender de APIs externas.

    Args:
        precios: Diccionario ticker → precio actual.
        historias: Diccionario ticker → lista de precios históricos (opcional).
    """

    def __init__(
        self,
        precios: Dict[str, float],
        historias: Optional[Dict[str, List[float]]] = None,
    ) -> None:
        self._precios = precios
        self._historias = historias or {}

    def obtener_precio_actual(self, ticker: str) -> float:
        """Retorna el precio simulado para el ticker dado.

        Raises:
            ValueError: Si el ticker no está en el diccionario de precios.
        """
        if ticker not in self._precios:
            raise ValueError(f"Sin precio definido para '{ticker}'")
        return float(self._precios[ticker])

    def obtener_historia(self, ticker: str) -> List[float]:
        """Retorna la historia simulada o una lista constante de 252 valores."""
        if ticker in self._historias:
            return list(self._historias[ticker])
        precio = self._precios.get(ticker, 100.0)
        return [float(precio)] * 252
