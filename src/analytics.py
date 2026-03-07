"""analytics.py — Analítica Financiera y SmartPortfolio Engine.

Sesiones 5.4 + 5.5: Métricas cuantitativas y optimización de portafolio.

Flujo del sistema:
    simulate_prices / MarketDataProvider
        → Portfolio (retornos, covarianza)
        → PortfolioOptimizer (Monte Carlo)
        → generate_recommendation (reglas automáticas)

Métricas implementadas:
- Retornos simples diarios y anualizados
- Volatilidad anualizada (σ × √252)
- Matriz de covarianza anualizada
- Bandas de Bollinger (media móvil ± 2σ local)
- Sharpe Ratio: (E[Rp] - Rf) / σp
- Simulación Monte Carlo de portafolios (frontera eficiente)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Utilidades de datos sintéticos
# ---------------------------------------------------------------------------


def simulate_prices(
    tickers: List[str],
    n_days: int = 252,
    start_price: float = 100.0,
    seed: Optional[int] = 42,
) -> pd.DataFrame:
    """Genera series de precios sintéticos reproducibles.

    Cada serie es una caminata aleatoria con deriva positiva moderada,
    útil para demos y tests sin depender de datos reales.

    Args:
        tickers: Lista de símbolos.
        n_days: Número de días (default 252 ≈ 1 año bursátil).
        start_price: Precio inicial de todas las series.
        seed: Semilla aleatoria para reproducibilidad (None = aleatorio).

    Returns:
        DataFrame con una columna por ticker, indexado por entero (día).

    Ejemplo:
        >>> df = simulate_prices(["AAPL", "MSFT"])
        >>> df.shape
        (252, 2)
    """
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            ticker: start_price
            + np.cumsum(rng.normal(loc=0.08, scale=1.25, size=n_days))
            for ticker in tickers
        }
    )


def equal_weight_portfolio(n_assets: int) -> np.ndarray:
    """Calcula pesos iguales para un portafolio equi-ponderado.

    Args:
        n_assets: Número de activos.

    Returns:
        Array numpy con pesos que suman 1.0.

    Ejemplo:
        >>> w = equal_weight_portfolio(4)
        >>> float(w.sum())
        1.0
    """
    if n_assets <= 0:
        raise ValueError("n_assets debe ser mayor que 0.")
    return np.array([1.0 / n_assets] * n_assets)


# ---------------------------------------------------------------------------
# Indicadores técnicos
# ---------------------------------------------------------------------------


def bollinger_bands(
    prices: pd.Series,
    window: int = 20,
    n_std: float = 2.0,
) -> pd.DataFrame:
    """Calcula las Bandas de Bollinger para una serie de precios.

    Las bandas combinan una media móvil con una medida de volatilidad local:
    - Banda superior = MA + n_std × σ_local
    - Banda inferior = MA − n_std × σ_local

    Args:
        prices: Serie de precios de un solo activo.
        window: Ventana de la media móvil (default 20 días).
        n_std: Multiplicador de desviación estándar (default 2.0).

    Returns:
        DataFrame con columnas: price, ma, upper, lower.

    Ejemplo:
        >>> prices = pd.Series([100.0 + i for i in range(30)])
        >>> bb = bollinger_bands(prices)
        >>> list(bb.columns)
        ['price', 'ma', 'upper', 'lower']
    """
    ma = prices.rolling(window).mean()
    std = prices.rolling(window).std()
    return pd.DataFrame(
        {
            "price": prices,
            "ma": ma,
            "upper": ma + n_std * std,
            "lower": ma - n_std * std,
        }
    )


# ---------------------------------------------------------------------------
# Clase Portfolio — encapsula precios y deriva métricas de riesgo/retorno
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Portfolio:
    """Encapsula datos de precios y calcula métricas de riesgo y retorno.

    Al instanciarse calcula automáticamente la matriz de retornos diarios.

    Args:
        prices: DataFrame con precios de cierre; una columna por ticker.

    Raises:
        ValueError: Si ``prices`` está vacío.

    Ejemplo:
        >>> prices = simulate_prices(["A", "B"], n_days=50)
        >>> p = Portfolio(prices)
        >>> p.returns.shape
        (49, 2)
    """

    prices: pd.DataFrame
    returns: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        if self.prices.empty:
            raise ValueError("El DataFrame de precios no puede estar vacío.")
        self.returns = self.prices.pct_change().dropna()

    def expected_returns(self, annualization: int = 252) -> pd.Series:
        """Retornos esperados anualizados por ticker.

        Args:
            annualization: Factor de anualización (252 días bursátiles).

        Returns:
            Serie con retorno esperado anualizado por ticker.
        """
        return self.returns.mean() * annualization

    def covariance_matrix(self, annualization: int = 252) -> pd.DataFrame:
        """Matriz de covarianza anualizada.

        Args:
            annualization: Factor de anualización.

        Returns:
            DataFrame cuadrado (n_tickers × n_tickers).
        """
        return self.returns.cov() * annualization

    def volatility(self) -> pd.Series:
        """Volatilidad anualizada (desviación estándar × √252) por ticker.

        Returns:
            Serie con volatilidad anualizada por ticker.
        """
        return self.returns.std() * np.sqrt(252)

    def portfolio_performance(
        self,
        weights: np.ndarray,
        risk_free_rate: float = 0.02,
    ) -> Dict[str, float]:
        """Calcula retorno esperado, volatilidad y Sharpe Ratio para unos pesos dados.

        Fórmulas:
            E[Rp] = w^T · μ
            σp    = √(w^T · Σ · w)
            Sharpe = (E[Rp] − Rf) / σp

        Args:
            weights: Array de pesos con suma ≈ 1.0.
            risk_free_rate: Tasa libre de riesgo anual (default 2%).

        Returns:
            Diccionario con claves: expected_return, volatility, sharpe.

        Raises:
            ValueError: Si la longitud de ``weights`` no coincide con el número de activos.
        """
        n_assets = len(self.prices.columns)
        if len(weights) != n_assets:
            raise ValueError(
                f"Se esperaban {n_assets} pesos, recibidos {len(weights)}."
            )
        mu = self.expected_returns().values
        cov = self.covariance_matrix().values

        port_return = float(np.dot(weights, mu))
        port_vol = float(np.sqrt(weights.T @ cov @ weights))
        sharpe = (
            (port_return - risk_free_rate) / port_vol
            if port_vol > 0
            else float("nan")
        )
        return {
            "expected_return": port_return,
            "volatility": port_vol,
            "sharpe": sharpe,
        }

    def summary(self) -> pd.DataFrame:
        """Resumen de métricas por ticker: retorno esperado, volatilidad y Sharpe.

        Returns:
            DataFrame con filas [expected_return, volatility, sharpe] y columnas por ticker.
        """
        mu = self.expected_returns()
        vol = self.volatility()
        sharpe = mu / vol

        return pd.DataFrame(
            {"expected_return": mu, "volatility": vol, "sharpe": sharpe}
        ).T


# ---------------------------------------------------------------------------
# PortfolioOptimizer — Monte Carlo para encontrar la frontera eficiente
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class PortfolioOptimizer:
    """Optimizador de portafolio mediante simulación Monte Carlo.

    Genera ``n_portfolios`` combinaciones aleatorias de pesos y evalúa
    cada una calculando retorno, volatilidad y Sharpe Ratio.

    Con suficientes simulaciones (~5000) se traza una aproximación de
    la frontera eficiente de Markowitz.

    Args:
        portfolio: Instancia de ``Portfolio`` con los precios a optimizar.
        risk_free_rate: Tasa libre de riesgo anual (default 2%).

    Ejemplo:
        >>> prices = simulate_prices(["A", "B", "C"])
        >>> p = Portfolio(prices)
        >>> opt = PortfolioOptimizer(p)
        >>> results, weights = opt.simulate(n_portfolios=100)
        >>> "sharpe" in results.columns
        True
    """

    portfolio: Portfolio
    risk_free_rate: float = 0.02

    def simulate(
        self, n_portfolios: int = 5_000
    ) -> Tuple[pd.DataFrame, List[np.ndarray]]:
        """Simula portafolios aleatorios y evalúa sus métricas.

        Args:
            n_portfolios: Número de portafolios aleatorios a generar.

        Returns:
            Tupla (results_df, weights_list):
            - results_df: DataFrame con columnas expected_return, volatility, sharpe.
            - weights_list: Lista paralela de arrays de pesos.
        """
        mu = self.portfolio.expected_returns().values
        cov = self.portfolio.covariance_matrix().values
        n_assets = len(mu)

        records: List[Tuple[float, float, float]] = []
        weights_list: List[np.ndarray] = []
        rng = np.random.default_rng()

        for _ in range(n_portfolios):
            w = rng.random(n_assets)
            w = w / w.sum()

            port_return = float(np.dot(w, mu))
            port_vol = float(np.sqrt(w.T @ cov @ w))
            sharpe = (
                (port_return - self.risk_free_rate) / port_vol
                if port_vol > 0
                else float("nan")
            )

            records.append((port_return, port_vol, sharpe))
            weights_list.append(w)

        results = pd.DataFrame(
            records, columns=["expected_return", "volatility", "sharpe"]
        )
        return results, weights_list

    @staticmethod
    def max_sharpe(
        results: pd.DataFrame,
        weights_list: List[np.ndarray],
    ) -> Tuple[pd.Series, np.ndarray]:
        """Devuelve el portafolio con máximo Sharpe Ratio.

        Args:
            results: DataFrame devuelto por ``simulate()``.
            weights_list: Lista de pesos devuelta por ``simulate()``.

        Returns:
            Tupla (métricas, pesos) del portafolio óptimo por Sharpe.
        """
        idx = int(results["sharpe"].idxmax())
        return results.loc[idx], weights_list[idx]

    @staticmethod
    def min_volatility(
        results: pd.DataFrame,
        weights_list: List[np.ndarray],
    ) -> Tuple[pd.Series, np.ndarray]:
        """Devuelve el portafolio con mínima volatilidad.

        Args:
            results: DataFrame devuelto por ``simulate()``.
            weights_list: Lista de pesos devuelta por ``simulate()``.

        Returns:
            Tupla (métricas, pesos) del portafolio de mínima varianza.
        """
        idx = int(results["volatility"].idxmin())
        return results.loc[idx], weights_list[idx]


# ---------------------------------------------------------------------------
# Motor de recomendaciones automáticas
# ---------------------------------------------------------------------------


def generate_recommendation(
    weights: np.ndarray,
    metrics: Dict[str, float],
    concentration_threshold: float = 0.40,
) -> List[str]:
    """Genera recomendaciones textuales basadas en pesos y métricas del portafolio.

    Reglas aplicadas:
    1. Concentración: si algún activo supera ``concentration_threshold``.
    2. Volatilidad: < 15% = defensivo, > 35% = agresivo.
    3. Sharpe: > 1.0 = excelente desempeño ajustado, < 0.3 = débil.

    Args:
        weights: Array de pesos del portafolio.
        metrics: Diccionario con claves expected_return, volatility, sharpe.
        concentration_threshold: Fracción máxima aceptable en un solo activo.

    Returns:
        Lista de mensajes de recomendación. Nunca vacía.

    Ejemplo:
        >>> w = np.array([0.5, 0.3, 0.2])
        >>> m = {"expected_return": 0.12, "volatility": 0.18, "sharpe": 0.56}
        >>> msgs = generate_recommendation(w, m)
        >>> len(msgs) >= 1
        True
    """
    msgs: List[str] = []

    max_weight = float(np.max(weights))
    volatility = float(metrics.get("volatility", 0))
    sharpe = float(metrics.get("sharpe", 0))

    if max_weight > concentration_threshold:
        msgs.append(
            f"Portafolio muy concentrado: un activo tiene el {max_weight:.0%} del peso. "
            "Considera diversificar."
        )

    if volatility < 0.15:
        msgs.append("Portafolio defensivo: volatilidad baja (< 15%).")
    elif volatility > 0.35:
        msgs.append("Portafolio agresivo: volatilidad alta (> 35%). Considera reducir riesgo.")

    if sharpe > 1.0:
        msgs.append("Excelente desempeño ajustado por riesgo (Sharpe > 1.0).")
    elif sharpe < 0.3:
        msgs.append(
            "Desempeño ajustado por riesgo débil (Sharpe < 0.3). "
            "Revisa la composición del portafolio."
        )

    if not msgs:
        msgs.append("Portafolio balanceado según las reglas actuales.")

    return msgs
