# tests/conftest.py
import sys
from pathlib import Path

# Agrega /src al path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from modelos import Instrumento
from portafolio import Portafolio


@pytest.fixture
def instrumento_test():
    return Instrumento(ticker="TSLA", tipo="Acción", sector="Automotriz")


@pytest.fixture
def portafolio_vacio():
    return Portafolio()
