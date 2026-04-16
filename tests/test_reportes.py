"""tests/test_reportes.py — Tests para src/reportes.py.

Cubre la generación de reportes en formatos CSV, JSON y HTML,
incluyendo el caso con gráficas OHLCV y predicciones del oráculo.
"""
import csv
import json
from pathlib import Path

import pytest

from modelos import Instrumento, Posicion
from portafolio import Portafolio
from reportes import ReportadorFinanciero


# ─── Fixtures locales ─────────────────────────────────────────────────────────


@pytest.fixture
def portafolio_poblado(instrumento_test):
    """Portafolio con dos posiciones (una en ganancia, otra en pérdida)."""
    portafolio = Portafolio()
    portafolio.agregar_posicion(
        Posicion(instrumento=instrumento_test, cantidad=10, precio_entrada=100.0)
    )
    bono = Instrumento(ticker="US10Y", tipo="Bono", sector="Gobierno")
    portafolio.agregar_posicion(
        Posicion(instrumento=bono, cantidad=5, precio_entrada=100.0)
    )
    return portafolio


@pytest.fixture
def precios_mercado():
    """Precios de mercado para TSLA (ganancia) y US10Y (pérdida)."""
    return {"TSLA": 150.0, "US10Y": 95.0}


@pytest.fixture
def reportador():
    return ReportadorFinanciero()


# ─── imprimir_resumen ─────────────────────────────────────────────────────────


def test_imprimir_resumen_contiene_encabezados(
    reportador, portafolio_poblado, precios_mercado, capsys
):
    reportador.imprimir_resumen(portafolio_poblado, precios_mercado)
    salida = capsys.readouterr().out
    assert "Ticker" in salida
    assert "Ganancia" in salida


def test_imprimir_resumen_muestra_valores_calculados(
    reportador, portafolio_poblado, precios_mercado, capsys
):
    reportador.imprimir_resumen(portafolio_poblado, precios_mercado)
    salida = capsys.readouterr().out
    assert "TSLA" in salida
    assert "US10Y" in salida
    # 10 × 150 = 1500 (valor actual TSLA)
    assert "1500.00" in salida


# ─── exportar_csv ─────────────────────────────────────────────────────────────


def test_exportar_csv_genera_archivo(
    reportador, portafolio_poblado, precios_mercado, tmp_path
):
    ruta = tmp_path / "reporte.csv"
    reportador.exportar_csv(portafolio_poblado, precios_mercado, str(ruta))
    assert ruta.exists()


def test_exportar_csv_contiene_filas_esperadas(
    reportador, portafolio_poblado, precios_mercado, tmp_path
):
    ruta = tmp_path / "reporte.csv"
    reportador.exportar_csv(portafolio_poblado, precios_mercado, str(ruta))
    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    assert len(filas) == 2
    tickers = {f["ticker"] for f in filas}
    assert tickers == {"TSLA", "US10Y"}


def test_exportar_csv_valor_actual_correcto(
    reportador, portafolio_poblado, precios_mercado, tmp_path
):
    ruta = tmp_path / "reporte.csv"
    reportador.exportar_csv(portafolio_poblado, precios_mercado, str(ruta))
    with open(ruta, encoding="utf-8") as f:
        filas = {f["ticker"]: f for f in csv.DictReader(f)}
    # TSLA: 10 × 150 = 1500
    assert float(filas["TSLA"]["valor_actual"]) == pytest.approx(1500.0)
    # US10Y: 5 × 95 = 475
    assert float(filas["US10Y"]["valor_actual"]) == pytest.approx(475.0)


# ─── exportar_json ────────────────────────────────────────────────────────────


def test_exportar_json_genera_archivo_valido(
    reportador, portafolio_poblado, precios_mercado, tmp_path
):
    ruta = tmp_path / "reporte.json"
    reportador.exportar_json(portafolio_poblado, precios_mercado, str(ruta))
    with open(ruta, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 2


def test_exportar_json_calcula_ganancia_y_perdida(
    reportador, portafolio_poblado, precios_mercado, tmp_path
):
    ruta = tmp_path / "reporte.json"
    reportador.exportar_json(portafolio_poblado, precios_mercado, str(ruta))
    with open(ruta, encoding="utf-8") as f:
        data = {item["ticker"]: item for item in json.load(f)}
    # TSLA: (150 − 100) × 10 = +500
    assert data["TSLA"]["ganancia_perdida"] == pytest.approx(500.0)
    # US10Y: (95 − 100) × 5 = −25
    assert data["US10Y"]["ganancia_perdida"] == pytest.approx(-25.0)


# ─── exportar_html ────────────────────────────────────────────────────────────


def test_exportar_html_sin_graficas_extras(
    reportador, portafolio_poblado, precios_mercado, tmp_path
):
    ruta = tmp_path / "reporte.html"
    reportador.exportar_html(portafolio_poblado, precios_mercado, str(ruta))
    contenido = ruta.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in contenido
    assert "Smart Portfolio" in contenido
    assert "TSLA" in contenido
    assert "US10Y" in contenido


def test_exportar_html_kpis_reflejan_totales(
    reportador, portafolio_poblado, precios_mercado, tmp_path
):
    ruta = tmp_path / "reporte.html"
    reportador.exportar_html(portafolio_poblado, precios_mercado, str(ruta))
    contenido = ruta.read_text(encoding="utf-8")
    # Valor total = 1500 + 475 = 1975
    assert "1,975.00" in contenido
    # Ganancia total = +500 − 25 = +475
    assert "475.00" in contenido


def test_exportar_html_incluye_plotly_cdn(
    reportador, portafolio_poblado, precios_mercado, tmp_path
):
    ruta = tmp_path / "reporte.html"
    reportador.exportar_html(portafolio_poblado, precios_mercado, str(ruta))
    contenido = ruta.read_text(encoding="utf-8")
    assert "plotly" in contenido.lower()


def test_exportar_html_con_velas_y_prediccion(
    reportador, portafolio_poblado, precios_mercado, tmp_path
):
    ruta = tmp_path / "reporte.html"
    datos_ohlcv = {
        "TSLA": {
            "dates": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "open": [149.0, 150.0, 151.0],
            "high": [151.0, 152.0, 153.0],
            "low": [148.0, 149.0, 150.0],
            "close": [150.0, 151.0, 150.5],
            "volume": [1_000_000, 1_100_000, 900_000],
        }
    }
    datos_pred = {
        "TSLA": {
            "historico": [140.0, 145.0, 150.0],
            "fechas_historico": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "precio_actual": 150.0,
            "prediccion_30d": 160.0,
            "prediccion_90d": 175.0,
            "tendencia": "alcista",
        }
    }
    reportador.exportar_html(
        portafolio_poblado, precios_mercado, str(ruta),
        datos_ohlcv=datos_ohlcv, datos_prediccion=datos_pred,
    )
    contenido = ruta.read_text(encoding="utf-8")
    assert "Velas Japonesas" in contenido
    # Plotly escapa los caracteres Unicode a \\u00f3 dentro del JSON
    assert ("Predicción" in contenido) or ("Predicci\\u00f3n" in contenido)
    assert "ALCISTA" in contenido


def test_exportar_html_portafolio_vacio(reportador, tmp_path):
    """Un portafolio vacío no debe lanzar excepciones al exportar."""
    portafolio_vacio = Portafolio()
    ruta = tmp_path / "reporte_vacio.html"
    reportador.exportar_html(portafolio_vacio, {}, str(ruta))
    contenido = ruta.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in contenido
