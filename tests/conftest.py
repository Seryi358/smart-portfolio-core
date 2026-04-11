# tests/conftest.py
import sys
from pathlib import Path

# Agrega /src al path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from modelos import Instrumento
from portafolio import Portafolio
from providers import MockMarketDataProvider


@pytest.fixture
def instrumento_test():
    return Instrumento(ticker="TSLA", tipo="Acción", sector="Automotriz")


@pytest.fixture
def portafolio_vacio():
    return Portafolio()


@pytest.fixture
def mock_provider():
    """Proveedor de datos simulado con precios e historias de prueba."""
    historia_alcista = [float(100 + i) for i in range(252)]
    historia_bajista = [float(351 - i) for i in range(252)]
    return MockMarketDataProvider(
        precios={"AAPL": 175.0, "MSFT": 300.0, "BAJISTA": 100.0},
        historias={
            "AAPL": historia_alcista,
            "BAJISTA": historia_bajista,
        },
    )
