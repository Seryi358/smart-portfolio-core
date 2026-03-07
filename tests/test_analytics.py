"""tests/test_analytics.py — Tests para src/analytics.py (Sesiones 5.4 + 5.5).

Cubre:
- simulate_prices
- equal_weight_portfolio
- bollinger_bands
- Portfolio: retornos, covarianza, volatilidad, performance, summary
- PortfolioOptimizer: simulate, max_sharpe, min_volatility
- generate_recommendation
"""
import numpy as np
import pandas as pd
import pytest

from analytics import (
    Portfolio,
    PortfolioOptimizer,
    bollinger_bands,
    equal_weight_portfolio,
    generate_recommendation,
    simulate_prices,
)


# ---------------------------------------------------------------------------
# simulate_prices
# ---------------------------------------------------------------------------


class TestSimulatePrices:
    def test_forma_correcta(self):
        df = simulate_prices(["A", "B", "C"], n_days=100)
        assert df.shape == (100, 3)

    def test_columnas_correctas(self):
        tickers = ["AAPL", "MSFT"]
        df = simulate_prices(tickers)
        assert list(df.columns) == tickers

    def test_reproducible_con_seed(self):
        df1 = simulate_prices(["X"], seed=1)
        df2 = simulate_prices(["X"], seed=1)
        pd.testing.assert_frame_equal(df1, df2)

    def test_diferentes_con_diferente_seed(self):
        df1 = simulate_prices(["X"], seed=1)
        df2 = simulate_prices(["X"], seed=2)
        assert not df1.equals(df2)


# ---------------------------------------------------------------------------
# equal_weight_portfolio
# ---------------------------------------------------------------------------


class TestEqualWeightPortfolio:
    def test_suma_uno(self):
        w = equal_weight_portfolio(5)
        assert np.isclose(w.sum(), 1.0)

    def test_longitud_correcta(self):
        w = equal_weight_portfolio(4)
        assert len(w) == 4

    def test_todos_iguales(self):
        w = equal_weight_portfolio(3)
        assert np.allclose(w, [1 / 3, 1 / 3, 1 / 3])

    def test_uno_solo(self):
        w = equal_weight_portfolio(1)
        assert np.isclose(w[0], 1.0)

    def test_cero_activos_lanza_error(self):
        with pytest.raises(ValueError):
            equal_weight_portfolio(0)


# ---------------------------------------------------------------------------
# bollinger_bands
# ---------------------------------------------------------------------------


class TestBollingerBands:
    def setup_method(self):
        self.prices = pd.Series([100.0 + i for i in range(30)])

    def test_columnas(self):
        bb = bollinger_bands(self.prices)
        assert list(bb.columns) == ["price", "ma", "upper", "lower"]

    def test_banda_superior_mayor_que_media(self):
        bb = bollinger_bands(self.prices).dropna()
        assert (bb["upper"] >= bb["ma"]).all()

    def test_banda_inferior_menor_que_media(self):
        bb = bollinger_bands(self.prices).dropna()
        assert (bb["lower"] <= bb["ma"]).all()

    def test_longitud_igual_a_serie(self):
        bb = bollinger_bands(self.prices)
        assert len(bb) == len(self.prices)


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_portfolio() -> Portfolio:
    prices = simulate_prices(["A", "B", "C"], n_days=100, seed=7)
    return Portfolio(prices)


class TestPortfolio:
    def test_retornos_calculados(self, sample_portfolio):
        # retornos = pct_change().dropna() → 99 filas para 100 días
        assert len(sample_portfolio.returns) == 99

    def test_raises_si_vacio(self):
        with pytest.raises(ValueError):
            Portfolio(pd.DataFrame())

    def test_expected_returns_shape(self, sample_portfolio):
        mu = sample_portfolio.expected_returns()
        assert len(mu) == 3

    def test_covariance_matrix_shape(self, sample_portfolio):
        cov = sample_portfolio.covariance_matrix()
        assert cov.shape == (3, 3)

    def test_volatility_positiva(self, sample_portfolio):
        vol = sample_portfolio.volatility()
        assert (vol > 0).all()

    def test_portfolio_performance_keys(self, sample_portfolio):
        w = equal_weight_portfolio(3)
        metrics = sample_portfolio.portfolio_performance(w)
        assert set(metrics.keys()) == {"expected_return", "volatility", "sharpe"}

    def test_portfolio_performance_volatilidad_positiva(self, sample_portfolio):
        w = equal_weight_portfolio(3)
        metrics = sample_portfolio.portfolio_performance(w)
        assert metrics["volatility"] >= 0

    def test_portfolio_performance_peso_incorrecto(self, sample_portfolio):
        with pytest.raises(ValueError):
            sample_portfolio.portfolio_performance(np.array([0.5, 0.5]))

    def test_summary_indices(self, sample_portfolio):
        s = sample_portfolio.summary()
        assert "expected_return" in s.index
        assert "volatility" in s.index
        assert "sharpe" in s.index


# ---------------------------------------------------------------------------
# PortfolioOptimizer
# ---------------------------------------------------------------------------


class TestPortfolioOptimizer:
    def test_simulate_forma(self, sample_portfolio):
        opt = PortfolioOptimizer(sample_portfolio)
        results, weights = opt.simulate(n_portfolios=50)
        assert results.shape == (50, 3)
        assert len(weights) == 50

    def test_simulate_columnas(self, sample_portfolio):
        opt = PortfolioOptimizer(sample_portfolio)
        results, _ = opt.simulate(n_portfolios=20)
        assert list(results.columns) == ["expected_return", "volatility", "sharpe"]

    def test_pesos_suman_uno(self, sample_portfolio):
        opt = PortfolioOptimizer(sample_portfolio)
        _, weights = opt.simulate(n_portfolios=10)
        for w in weights:
            assert np.isclose(w.sum(), 1.0)

    def test_max_sharpe_retorna_tupla(self, sample_portfolio):
        opt = PortfolioOptimizer(sample_portfolio)
        results, weights = opt.simulate(n_portfolios=100)
        metrics, w = PortfolioOptimizer.max_sharpe(results, weights)
        assert "sharpe" in metrics.index
        assert len(w) == 3

    def test_min_volatility_retorna_tupla(self, sample_portfolio):
        opt = PortfolioOptimizer(sample_portfolio)
        results, weights = opt.simulate(n_portfolios=100)
        metrics, w = PortfolioOptimizer.min_volatility(results, weights)
        assert "volatility" in metrics.index
        assert metrics["volatility"] > 0


# ---------------------------------------------------------------------------
# generate_recommendation
# ---------------------------------------------------------------------------


class TestGenerateRecommendation:
    def test_lista_no_vacia(self):
        w = np.array([0.5, 0.3, 0.2])
        m = {"expected_return": 0.10, "volatility": 0.18, "sharpe": 0.56}
        msgs = generate_recommendation(w, m)
        assert len(msgs) >= 1

    def test_detecta_concentracion(self):
        w = np.array([0.80, 0.10, 0.10])
        m = {"expected_return": 0.15, "volatility": 0.20, "sharpe": 0.65}
        msgs = generate_recommendation(w, m)
        assert any("concentrad" in msg.lower() for msg in msgs)

    def test_detecta_volatilidad_alta(self):
        w = np.array([0.4, 0.3, 0.3])
        m = {"expected_return": 0.20, "volatility": 0.40, "sharpe": 0.45}
        msgs = generate_recommendation(w, m)
        assert any("agresiv" in msg.lower() or "alta" in msg.lower() for msg in msgs)

    def test_detecta_volatilidad_baja(self):
        w = np.array([0.4, 0.3, 0.3])
        m = {"expected_return": 0.05, "volatility": 0.10, "sharpe": 0.30}
        msgs = generate_recommendation(w, m)
        assert any("defensiv" in msg.lower() or "baja" in msg.lower() for msg in msgs)

    def test_detecta_sharpe_excelente(self):
        w = np.array([0.4, 0.3, 0.3])
        m = {"expected_return": 0.25, "volatility": 0.18, "sharpe": 1.5}
        msgs = generate_recommendation(w, m)
        assert any("excelente" in msg.lower() for msg in msgs)

    def test_detecta_sharpe_debil(self):
        w = np.array([0.4, 0.3, 0.3])
        m = {"expected_return": 0.03, "volatility": 0.20, "sharpe": 0.10}
        msgs = generate_recommendation(w, m)
        assert any("débil" in msg.lower() or "debil" in msg.lower() for msg in msgs)

    def test_balanceado_mensaje_default(self):
        w = np.array([0.4, 0.3, 0.3])
        m = {"expected_return": 0.12, "volatility": 0.20, "sharpe": 0.6}
        msgs = generate_recommendation(w, m)
        assert any("balanceado" in msg.lower() for msg in msgs)
