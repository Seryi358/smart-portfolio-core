from typing import Optional

import numpy as np
from sklearn.linear_model import LinearRegression

from providers import MarketDataProvider


class InstrumentoOracle:
    """Instrumento financiero con capacidad predictiva mediante ML.

    Encapsula la lógica de obtención de datos y entrenamiento de un
    modelo de regresión lineal para proyectar precios futuros.

    Args:
        ticker: Símbolo del instrumento (ej. "AAPL").
        tipo: Tipo de instrumento ("Acción", "Bono", etc.).
        sector: Sector económico.
        data_provider: Implementación de MarketDataProvider a usar.
    """

    def __init__(
        self,
        ticker: str,
        tipo: str,
        sector: str,
        data_provider: MarketDataProvider,
    ) -> None:
        self.ticker = ticker
        self.tipo = tipo
        self.sector = sector
        self._data_provider = data_provider
        self._modelo: Optional[LinearRegression] = None
        self._n_datos: int = 0

    def obtener_precio_actual(self) -> float:
        """Obtiene el precio actual del proveedor de datos."""
        return self._data_provider.obtener_precio_actual(self.ticker)

    def entrenar_modelo(self) -> None:
        """Entrena un modelo de regresión lineal sobre el historial de precios."""
        historial = self._data_provider.obtener_historia(self.ticker)
        self._n_datos = len(historial)
        X = np.arange(self._n_datos).reshape(-1, 1)
        y = np.array(historial, dtype=float)
        self._modelo = LinearRegression()
        self._modelo.fit(X, y)

    def predecir_precio(self, dias_futuros: int = 30) -> float:
        """Proyecta el precio futuro usando el modelo entrenado.

        Args:
            dias_futuros: Número de días a proyectar desde hoy.

        Returns:
            Precio proyectado como float.
        """
        if self._modelo is None:
            self.entrenar_modelo()
        return float(self._modelo.predict([[self._n_datos + dias_futuros]])[0])

    def tendencia(self) -> str:
        """Clasifica la tendencia según el coeficiente del modelo.

        Returns:
            "alcista" si coeficiente > 0.05,
            "bajista" si coeficiente < -0.05,
            "neutral" en caso contrario.
        """
        if self._modelo is None:
            self.entrenar_modelo()
        coef = float(self._modelo.coef_[0])
        if coef > 0.05:
            return "alcista"
        if coef < -0.05:
            return "bajista"
        return "neutral"
