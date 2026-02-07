# tests/test_models.py
import pytest
from modelos import Posicion
from portafolio import Portafolio, PosicionNoExisteError


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
    instrumento_test,  # viene automáticamente de conftest.py
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


def test_remover_activo_inexistente_lanza_error(portafolio_vacio):
    with pytest.raises(PosicionNoExisteError):
        portafolio_vacio.remover_posicion(ticker="NFLX")

def test_portafolio_valor_total(portafolio_vacio, instrumento_test):
    """Prueba cálculo de valor total del portafolio."""
    pos = Posicion(instrumento=instrumento_test, _cantidad=10, precio_entrada=100)
    portafolio_vacio.agregar_posicion(pos)
    
    precios = {"TSLA": 150}
    valor = portafolio_vacio.valor_total(precios)
    assert valor == 1500

def test_portafolio_agregar_error(portafolio_vacio):
    """Prueba error al agregar objeto no Posicion."""
    with pytest.raises(TypeError):
        portafolio_vacio.agregar_posicion("invalid")


def test_posicion_validacion_tipos(instrumento_test):
    """Prueba validaciones de tipo en constructor de Posicion."""
    with pytest.raises(TypeError):
        Posicion(instrumento="Invalid", _cantidad=10, precio_entrada=100)
    with pytest.raises(TypeError):
        Posicion(instrumento=instrumento_test, _cantidad=10, precio_entrada="invalid")
    with pytest.raises(TypeError):
        Posicion(instrumento=instrumento_test, _cantidad="invalid", precio_entrada=100)


def test_posicion_validacion_cantidad_negativa(instrumento_test):
    """Prueba validación de cantidad negativa."""
    with pytest.raises(ValueError):
        Posicion(instrumento=instrumento_test, _cantidad=-10, precio_entrada=100)
    
    pos = Posicion(instrumento=instrumento_test, _cantidad=10, precio_entrada=100)
    with pytest.raises(ValueError):
        pos.cantidad = -5


def test_calcular_valor_actual(instrumento_test):
    """Prueba cálculo de valor actual y validación de tipo."""
    pos = Posicion(instrumento=instrumento_test, _cantidad=10, precio_entrada=100)
    assert pos.calcular_valor_actual(150) == 1500
    
    with pytest.raises(TypeError):
        pos.calcular_valor_actual("invalid")


def test_calcular_pnl_type_error(instrumento_test):
    """Prueba error de tipo en cálculo de PnL."""
    pos = Posicion(instrumento=instrumento_test, _cantidad=10, precio_entrada=100)
    with pytest.raises(TypeError):
        pos.calcular_ganancia_no_realizada("invalid")


def test_instrumento_inmutabilidad(instrumento_test):
    """Prueba que Instrumento sea inmutable."""
    from dataclasses import FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        instrumento_test.ticker = "NEW"

