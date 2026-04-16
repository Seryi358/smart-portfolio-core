# tests/test_providers.py
import pytest
from providers import MockMarketDataProvider
from oracle import InstrumentoOracle
from modelos import Instrumento, Posicion


# ─── MockMarketDataProvider ───────────────────────────────────────────────────

def test_mock_precio_actual(mock_provider):
    assert mock_provider.obtener_precio_actual("AAPL") == 175.0


def test_mock_precio_ticker_inexistente():
    provider = MockMarketDataProvider({})
    with pytest.raises(ValueError):
        provider.obtener_precio_actual("NFLX")


def test_mock_historia_explicita():
    historia = [100.0, 110.0, 120.0]
    provider = MockMarketDataProvider({"AAPL": 120.0}, {"AAPL": historia})
    assert provider.obtener_historia("AAPL") == historia


def test_mock_historia_default_longitud():
    """Sin historia explícita genera 252 valores constantes."""
    provider = MockMarketDataProvider({"AAPL": 150.0})
    hist = provider.obtener_historia("AAPL")
    assert len(hist) == 252
    assert all(p == 150.0 for p in hist)


# ─── InstrumentoOracle ────────────────────────────────────────────────────────

def test_oracle_precio_actual(mock_provider):
    oracle = InstrumentoOracle("AAPL", "Acción", "Tecnología", mock_provider)
    assert oracle.obtener_precio_actual() == 175.0


def test_oracle_tendencia_alcista(mock_provider):
    oracle = InstrumentoOracle("AAPL", "Acción", "Tecnología", mock_provider)
    assert oracle.tendencia() == "alcista"


def test_oracle_tendencia_bajista(mock_provider):
    oracle = InstrumentoOracle("BAJISTA", "Acción", "Tecnología", mock_provider)
    assert oracle.tendencia() == "bajista"


def test_oracle_prediccion_mayor_al_actual(mock_provider):
    """Con tendencia alcista, la predicción a 30 días debe superar el precio actual."""
    oracle = InstrumentoOracle("AAPL", "Acción", "Tecnología", mock_provider)
    precio_actual = mock_provider.obtener_precio_actual("AAPL")
    prediccion = oracle.predecir_precio(30)
    assert prediccion > precio_actual


def test_oracle_entrenar_modelo_idempotente(mock_provider):
    """Llamar entrenar_modelo dos veces no lanza error."""
    oracle = InstrumentoOracle("AAPL", "Acción", "Tecnología", mock_provider)
    oracle.entrenar_modelo()
    oracle.entrenar_modelo()
    assert oracle._modelo is not None


def test_oracle_tendencia_neutral():
    """Historia plana (precio constante) produce tendencia neutral."""
    historia_plana = [150.0] * 252
    provider = MockMarketDataProvider({"FLAT": 150.0}, {"FLAT": historia_plana})
    oracle = InstrumentoOracle("FLAT", "ETF", "Índice", provider)
    assert oracle.tendencia() == "neutral"


# ─── Posicion.tiene_alerta_perdida ────────────────────────────────────────────

def test_alerta_perdida_activa(instrumento_test):
    """Pérdida > 10% debe activar alerta."""
    pos = Posicion(instrumento=instrumento_test, cantidad=10, precio_entrada=100.0)
    assert pos.tiene_alerta_perdida(85.0) is True   # -15%


def test_alerta_perdida_inactiva(instrumento_test):
    """Pérdida < 10% no activa alerta."""
    pos = Posicion(instrumento=instrumento_test, cantidad=10, precio_entrada=100.0)
    assert pos.tiene_alerta_perdida(95.0) is False  # -5%


def test_alerta_perdida_exactamente_umbral(instrumento_test):
    """Pérdida exactamente en el umbral no activa alerta (condición estricta)."""
    pos = Posicion(instrumento=instrumento_test, cantidad=10, precio_entrada=100.0)
    assert pos.tiene_alerta_perdida(90.0) is False  # -10% exacto


def test_alerta_perdida_con_ganancia(instrumento_test):
    """Posición con ganancia nunca activa alerta."""
    pos = Posicion(instrumento=instrumento_test, cantidad=10, precio_entrada=100.0)
    assert pos.tiene_alerta_perdida(110.0) is False  # +10%


def test_alerta_perdida_cantidad_cero(instrumento_test):
    """Posición con cantidad 0 (costo_base = 0) retorna False sin dividir por cero."""
    pos = Posicion(instrumento=instrumento_test, cantidad=0, precio_entrada=100.0)
    assert pos.tiene_alerta_perdida(50.0) is False
