# tests/test_models.py
import pytest
from src.modelos import Posicion
from tests.conftest import instrumento_test
from tests.conftest import portafolio_vacio

@pytest.mark.parametrize(
    "precio_entrada, precio_actual, cantidad, esperado",
    [
        (100, 150, 10, 500),
        (200, 180, 5, -100),
        (50, 50, 7, 0),
    ],


)
def test_calculo_pnl(
    precio_entrada,
    precio_actual,
    cantidad,
    esperado,
    instrumento_test,
):
    posicion = Posicion(
        instrumento=instrumento_test,
        _cantidad=cantidad,
        precio_entrada=precio_entrada,
    )

    pnl = posicion.calcular_ganancia_no_realizada(
        precio_actual=precio_actual
    )

    assert pnl == pytest.approx(esperado)