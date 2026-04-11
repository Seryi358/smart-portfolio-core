"""tests/test_domain.py — Tests para src/domain.py (Sesión 5.1).

Cubre:
- Value Objects: Ticker, Quantity, Money
- Excepciones de dominio
- OrdenCompraDTO con validación Pydantic
- dto_a_posicion() mapper
- formato_error_pydantic()
"""
import pytest
from pydantic import ValidationError

from domain import (
    DomainError,
    InvalidPriceError,
    InvalidQuantityError,
    InvalidTickerError,
    Money,
    OrdenCompraDTO,
    Quantity,
    Ticker,
    dto_a_posicion,
    formato_error_pydantic,
)


# ---------------------------------------------------------------------------
# Value Object: Ticker
# ---------------------------------------------------------------------------


class TestTicker:
    def test_crea_ticker_valido(self):
        t = Ticker("AAPL")
        assert t.value == "AAPL"

    def test_normaliza_a_mayusculas(self):
        t = Ticker("msft")
        assert t.value == "MSFT"

    def test_elimina_espacios(self):
        t = Ticker("  googl  ")
        assert t.value == "GOOGL"

    def test_acepta_punto_y_guion(self):
        t = Ticker("BRK.B")
        assert t.value == "BRK.B"
        t2 = Ticker("BTC-USD")
        assert t2.value == "BTC-USD"

    def test_vacio_lanza_error(self):
        with pytest.raises(InvalidTickerError):
            Ticker("")

    def test_solo_espacios_lanza_error(self):
        with pytest.raises(InvalidTickerError):
            Ticker("   ")

    def test_caracter_invalido_lanza_error(self):
        with pytest.raises(InvalidTickerError):
            Ticker("AA PL")

    def test_str_retorna_value(self):
        assert str(Ticker("tsla")) == "TSLA"

    def test_es_inmutable(self):
        t = Ticker("AAPL")
        with pytest.raises(Exception):
            t.value = "MSFT"  # type: ignore[misc]

    def test_invalido_es_subclase_de_domain_error(self):
        with pytest.raises(DomainError):
            Ticker("")


# ---------------------------------------------------------------------------
# Value Object: Quantity
# ---------------------------------------------------------------------------


class TestQuantity:
    def test_crea_cantidad_valida(self):
        q = Quantity(10)
        assert q.value == 10

    def test_cantidad_uno_es_valida(self):
        assert Quantity(1).value == 1

    def test_cero_lanza_error(self):
        with pytest.raises(InvalidQuantityError):
            Quantity(0)

    def test_negativo_lanza_error(self):
        with pytest.raises(InvalidQuantityError):
            Quantity(-5)

    def test_float_lanza_error(self):
        with pytest.raises(InvalidQuantityError):
            Quantity(1.5)  # type: ignore[arg-type]

    def test_bool_lanza_error(self):
        with pytest.raises(InvalidQuantityError):
            Quantity(True)  # type: ignore[arg-type]

    def test_es_inmutable(self):
        q = Quantity(5)
        with pytest.raises(Exception):
            q.value = 10  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Value Object: Money
# ---------------------------------------------------------------------------


class TestMoney:
    def test_crea_precio_valido(self):
        m = Money(150.75)
        assert m.value == 150.75

    def test_precio_cero_es_valido(self):
        assert Money(0.0).value == 0.0

    def test_negativo_lanza_error(self):
        with pytest.raises(InvalidPriceError):
            Money(-1.0)

    def test_nan_lanza_error(self):
        import math
        with pytest.raises(InvalidPriceError):
            Money(math.nan)

    def test_infinito_lanza_error(self):
        import math
        with pytest.raises(InvalidPriceError):
            Money(math.inf)

    def test_es_inmutable(self):
        m = Money(100.0)
        with pytest.raises(Exception):
            m.value = 200.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DTO: OrdenCompraDTO
# ---------------------------------------------------------------------------


class TestOrdenCompraDTO:
    def test_crea_dto_valido(self):
        dto = OrdenCompraDTO(ticker="aapl", cantidad=10, precio_entrada=150.0)
        assert dto.ticker == "AAPL"
        assert dto.cantidad == 10
        assert dto.precio_entrada == 150.0

    def test_normaliza_ticker(self):
        dto = OrdenCompraDTO(ticker="  msft  ", cantidad=5, precio_entrada=300.0)
        assert dto.ticker == "MSFT"

    def test_nombre_opcional(self):
        dto = OrdenCompraDTO(ticker="TSLA", cantidad=3, precio_entrada=200.0)
        assert dto.nombre is None

    def test_nombre_opcional_con_valor(self):
        dto = OrdenCompraDTO(ticker="TSLA", cantidad=3, precio_entrada=200.0, nombre="Tesla")
        assert dto.nombre == "Tesla"

    def test_ticker_vacio_lanza_error(self):
        with pytest.raises(ValidationError):
            OrdenCompraDTO(ticker="", cantidad=5, precio_entrada=100.0)

    def test_cantidad_cero_lanza_error(self):
        with pytest.raises(ValidationError):
            OrdenCompraDTO(ticker="AAPL", cantidad=0, precio_entrada=100.0)

    def test_cantidad_negativa_lanza_error(self):
        with pytest.raises(ValidationError):
            OrdenCompraDTO(ticker="AAPL", cantidad=-1, precio_entrada=100.0)

    def test_precio_negativo_lanza_error(self):
        with pytest.raises(ValidationError):
            OrdenCompraDTO(ticker="AAPL", cantidad=5, precio_entrada=-10.0)


# ---------------------------------------------------------------------------
# Mapper: dto_a_posicion
# ---------------------------------------------------------------------------


class TestDtoAPosicion:
    def test_retorna_value_objects(self):
        dto = OrdenCompraDTO(ticker="NVDA", cantidad=2, precio_entrada=500.0)
        result = dto_a_posicion(dto)

        assert result["ticker"].value == "NVDA"
        assert result["cantidad"].value == 2
        assert result["precio_entrada"].value == 500.0

    def test_nombre_usa_ticker_si_no_se_provee(self):
        dto = OrdenCompraDTO(ticker="AMZN", cantidad=1, precio_entrada=180.0)
        result = dto_a_posicion(dto)
        assert result["nombre"] == "AMZN"

    def test_nombre_usa_valor_provisto(self):
        dto = OrdenCompraDTO(
            ticker="AMZN", cantidad=1, precio_entrada=180.0, nombre="Amazon"
        )
        result = dto_a_posicion(dto)
        assert result["nombre"] == "Amazon"


# ---------------------------------------------------------------------------
# Utilidad: formato_error_pydantic
# ---------------------------------------------------------------------------


class TestFormatoErrorPydantic:
    def test_retorna_string_corto(self):
        try:
            OrdenCompraDTO(ticker="", cantidad=0, precio_entrada=-1.0)
        except ValidationError as exc:
            msg = formato_error_pydantic(exc)
            assert isinstance(msg, str)
            assert len(msg) > 0
