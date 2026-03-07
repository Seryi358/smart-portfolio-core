"""tests/test_api.py — Tests de integración para la API FastAPI (Sesión 6).

Usa ``httpx`` con el ``TestClient`` de FastAPI para probar todos los
endpoints sin necesidad de levantar un servidor real.

Cubre:
- GET / (root)
- GET /health
- GET /version
- GET /instrument/{ticker}
- GET /history/{ticker}?days=N
- POST /portfolio/analyze
- POST /portfolio/validate
- POST /orden/registrar
"""
import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Endpoints informativos
# ---------------------------------------------------------------------------


class TestInfoEndpoints:
    def test_root_status_200(self):
        r = client.get("/")
        assert r.status_code == 200

    def test_root_contiene_message(self):
        r = client.get("/")
        assert "message" in r.json()

    def test_health_status_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_retorna_ok(self):
        r = client.get("/health")
        assert r.json()["status"] == "ok"

    def test_version_status_200(self):
        r = client.get("/version")
        assert r.status_code == 200

    def test_version_contiene_service(self):
        r = client.get("/version")
        assert "service" in r.json()
        assert "version" in r.json()


# ---------------------------------------------------------------------------
# Endpoints de instrumentos
# ---------------------------------------------------------------------------


class TestInstrumentEndpoints:
    def test_get_instrument_status_200(self):
        r = client.get("/instrument/AAPL")
        assert r.status_code == 200

    def test_get_instrument_normaliza_ticker(self):
        r = client.get("/instrument/msft")
        assert r.json()["ticker"] == "MSFT"

    def test_get_instrument_contiene_message(self):
        r = client.get("/instrument/NVDA")
        assert "message" in r.json()

    def test_get_history_status_200(self):
        r = client.get("/history/AAPL")
        assert r.status_code == 200

    def test_get_history_default_30_dias(self):
        r = client.get("/history/AAPL")
        assert r.json()["days_requested"] == 30

    def test_get_history_query_param_dias(self):
        r = client.get("/history/MSFT?days=60")
        assert r.json()["days_requested"] == 60

    def test_get_history_contiene_latest_price(self):
        r = client.get("/history/TSLA")
        data = r.json()
        assert "latest_price" in data
        assert data["latest_price"] is not None

    def test_get_history_dias_invalidos(self):
        r = client.get("/history/AAPL?days=0")
        assert r.status_code == 422

    def test_get_history_dias_excede_maximo(self):
        r = client.get("/history/AAPL?days=400")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /portfolio/analyze
# ---------------------------------------------------------------------------


class TestPortfolioAnalyze:
    def test_portafolio_valido(self):
        r = client.post(
            "/portfolio/analyze",
            json={"tickers": ["AAPL", "MSFT"], "weights": [0.6, 0.4]},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["valid_portfolio"] is True
        assert data["n_assets"] == 2

    def test_pesos_no_suman_uno(self):
        r = client.post(
            "/portfolio/analyze",
            json={"tickers": ["AAPL", "MSFT"], "weights": [0.3, 0.3]},
        )
        assert r.status_code == 200
        assert r.json()["valid_portfolio"] is False

    def test_longitudes_diferentes(self):
        r = client.post(
            "/portfolio/analyze",
            json={"tickers": ["AAPL", "MSFT"], "weights": [1.0]},
        )
        assert r.status_code == 422

    def test_normaliza_tickers_a_mayusculas(self):
        r = client.post(
            "/portfolio/analyze",
            json={"tickers": ["aapl", "msft"], "weights": [0.5, 0.5]},
        )
        assert r.status_code == 200
        tickers = r.json()["tickers"]
        assert "AAPL" in tickers
        assert "MSFT" in tickers

    def test_peso_negativo_lanza_error(self):
        r = client.post(
            "/portfolio/analyze",
            json={"tickers": ["AAPL", "MSFT"], "weights": [-0.5, 1.5]},
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /portfolio/validate
# ---------------------------------------------------------------------------


class TestPortfolioValidate:
    def test_portafolio_valido(self):
        r = client.post(
            "/portfolio/validate",
            json={"tickers": ["AAPL", "MSFT", "NVDA"], "weights": [0.4, 0.3, 0.3]},
        )
        assert r.status_code == 200
        assert r.json()["valid_portfolio"] is True

    def test_response_model_keys(self):
        r = client.post(
            "/portfolio/validate",
            json={"tickers": ["AAPL"], "weights": [1.0]},
        )
        data = r.json()
        assert "tickers" in data
        assert "total_weight" in data
        assert "valid_portfolio" in data


# ---------------------------------------------------------------------------
# POST /orden/registrar
# ---------------------------------------------------------------------------


class TestOrdenRegistrar:
    def test_orden_valida(self):
        r = client.post(
            "/orden/registrar",
            json={"ticker": "aapl", "cantidad": 10, "precio_entrada": 150.0},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["ticker"] == "AAPL"
        assert data["cantidad"] == 10
        assert data["valor_posicion"] == 1500.0

    def test_ticker_se_normaliza(self):
        r = client.post(
            "/orden/registrar",
            json={"ticker": "  msft  ", "cantidad": 5, "precio_entrada": 300.0},
        )
        assert r.status_code == 200
        assert r.json()["ticker"] == "MSFT"

    def test_nombre_opcional_default(self):
        r = client.post(
            "/orden/registrar",
            json={"ticker": "NVDA", "cantidad": 2, "precio_entrada": 500.0},
        )
        assert r.status_code == 200
        assert r.json()["nombre"] == "NVDA"

    def test_nombre_personalizado(self):
        r = client.post(
            "/orden/registrar",
            json={
                "ticker": "TSLA",
                "cantidad": 3,
                "precio_entrada": 200.0,
                "nombre": "Tesla",
            },
        )
        assert r.status_code == 200
        assert r.json()["nombre"] == "Tesla"

    def test_cantidad_cero_lanza_error(self):
        r = client.post(
            "/orden/registrar",
            json={"ticker": "AAPL", "cantidad": 0, "precio_entrada": 100.0},
        )
        assert r.status_code == 422

    def test_precio_negativo_lanza_error(self):
        r = client.post(
            "/orden/registrar",
            json={"ticker": "AAPL", "cantidad": 5, "precio_entrada": -10.0},
        )
        assert r.status_code == 422

    def test_ticker_vacio_lanza_error(self):
        r = client.post(
            "/orden/registrar",
            json={"ticker": "", "cantidad": 5, "precio_entrada": 100.0},
        )
        assert r.status_code == 422
