from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


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

    @abstractmethod
    def obtener_ohlcv(self, ticker: str, periodo: str = "1y") -> Dict[str, list]:
        """Retorna datos OHLCV (Open, High, Low, Close, Volume) para velas japonesas.

        Args:
            ticker: Símbolo del instrumento.
            periodo: Periodo de datos ("1mo", "3mo", "6mo", "1y").

        Returns:
            Diccionario con listas: dates, open, high, low, close, volume.
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

    def obtener_ohlcv(self, ticker: str, periodo: str = "1y") -> Dict[str, list]:
        """Obtiene datos OHLCV desde Yahoo Finance.

        Args:
            ticker: Símbolo del instrumento.
            periodo: Periodo de datos ("1mo", "3mo", "6mo", "1y").

        Returns:
            Diccionario con listas: dates, open, high, low, close, volume.
        """
        import yfinance as yf
        historial = yf.Ticker(ticker).history(period=periodo)
        if historial.empty:
            raise ValueError(f"Sin historial OHLCV disponible para '{ticker}'")
        return {
            "dates": [d.strftime("%Y-%m-%d") for d in historial.index],
            "open": historial["Open"].tolist(),
            "high": historial["High"].tolist(),
            "low": historial["Low"].tolist(),
            "close": historial["Close"].tolist(),
            "volume": historial["Volume"].tolist(),
        }


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

    def obtener_ohlcv(self, ticker: str, periodo: str = "1y") -> Dict[str, list]:
        """Retorna datos OHLCV simulados para pruebas."""
        precio = self._precios.get(ticker, 100.0)
        n = 252
        return {
            "dates": [f"2025-01-{i+1:02d}" for i in range(min(n, 28))],
            "open": [precio * 0.99] * min(n, 28),
            "high": [precio * 1.01] * min(n, 28),
            "low": [precio * 0.98] * min(n, 28),
            "close": [precio] * min(n, 28),
            "volume": [1000000] * min(n, 28),
        }
