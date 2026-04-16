"""main.py — Demo de Smart Portfolio Core con datos reales de mercado.

Construye un portafolio de ejemplo, descarga precios y datos OHLCV desde
Yahoo Finance, entrena el oráculo predictivo para cada ticker y genera
reportes en CSV, JSON y HTML con gráficas interactivas (pie de sectores,
barras de P&L, velas japonesas y curva de predicción).

Si algún ticker no está disponible en Yahoo Finance, cae de forma elegante
a un precio de referencia definido en ``PRECIOS_FALLBACK`` y omite las
gráficas de ese instrumento, dejando los demás reportes funcionales.
"""
import sys
from pathlib import Path
from typing import Dict, Tuple

sys.path.append(str(Path(__file__).resolve().parent / "src"))

from modelos import Instrumento, Posicion
from oracle import InstrumentoOracle
from portafolio import Portafolio
from providers import YahooFinanceClient
from reportes import ReportadorFinanciero


PRECIOS_FALLBACK: Dict[str, float] = {
    "AAPL": 175.30,
    "MSFT": 420.00,
}


def construir_portafolio() -> Portafolio:
    """Arma el portafolio demo con dos posiciones en tecnología."""
    apple = Instrumento(ticker="AAPL", tipo="Acción", sector="Tecnología")
    microsoft = Instrumento(ticker="MSFT", tipo="Acción", sector="Tecnología")
    fondo = Portafolio()
    fondo.agregar_posicion(
        Posicion(instrumento=apple, cantidad=10, precio_entrada=150.0)
    )
    fondo.agregar_posicion(
        Posicion(instrumento=microsoft, cantidad=5, precio_entrada=380.0)
    )
    return fondo


def enriquecer_con_mercado(
    portafolio: Portafolio, proveedor: YahooFinanceClient
) -> Tuple[Dict[str, float], Dict[str, dict], Dict[str, dict]]:
    """Descarga precio, OHLCV y predicción del oráculo por ticker.

    Args:
        portafolio: Portafolio cuyas posiciones se consultarán en Yahoo Finance.
        proveedor: Cliente concreto de ``MarketDataProvider``.

    Returns:
        Tupla ``(precios, datos_ohlcv, datos_prediccion)`` lista para
        alimentar a ``ReportadorFinanciero.exportar_html``. Si un ticker falla
        en Yahoo, su precio cae al valor de ``PRECIOS_FALLBACK`` y no se
        incluye en las gráficas de velas ni de predicción.
    """
    precios: Dict[str, float] = {}
    datos_ohlcv: Dict[str, dict] = {}
    datos_prediccion: Dict[str, dict] = {}

    for pos in portafolio.posiciones:
        ticker = pos.instrumento.ticker
        print(f"  · Descargando {ticker}...", end=" ", flush=True)
        try:
            precios[ticker] = proveedor.obtener_precio_actual(ticker)
            ohlcv = proveedor.obtener_ohlcv(ticker, "1y")
            historia = proveedor.obtener_historia(ticker)

            oracle = InstrumentoOracle(
                ticker=ticker,
                tipo=pos.instrumento.tipo,
                sector=pos.instrumento.sector,
                data_provider=proveedor,
            )
            oracle.entrenar_modelo()

            datos_ohlcv[ticker] = ohlcv
            datos_prediccion[ticker] = {
                "historico": historia,
                "fechas_historico": ohlcv["dates"],
                "precio_actual": precios[ticker],
                "prediccion_30d": oracle.predecir_precio(30),
                "prediccion_90d": oracle.predecir_precio(90),
                "tendencia": oracle.tendencia(),
            }
            print(f"${precios[ticker]:,.2f} ✓")
        except Exception as exc:
            fallback = PRECIOS_FALLBACK.get(ticker, pos.precio_entrada)
            precios[ticker] = fallback
            print(f"sin datos en Yahoo → usando fallback ${fallback:,.2f} ({exc})")

    return precios, datos_ohlcv, datos_prediccion


def main() -> None:
    print("=" * 60)
    print("   SMART PORTFOLIO CORE — Reporte con datos de mercado")
    print("=" * 60)

    portafolio = construir_portafolio()

    print("\nConsultando Yahoo Finance:")
    proveedor = YahooFinanceClient()
    precios, datos_ohlcv, datos_prediccion = enriquecer_con_mercado(
        portafolio, proveedor
    )

    reportador = ReportadorFinanciero()
    print()
    reportador.imprimir_resumen(portafolio, precios)

    reportador.exportar_csv(portafolio, precios, "resumen_portafolio.csv")
    reportador.exportar_json(portafolio, precios, "resumen_portafolio.json")
    reportador.exportar_html(
        portafolio,
        precios,
        "resumen_portafolio.html",
        datos_ohlcv=datos_ohlcv,
        datos_prediccion=datos_prediccion,
    )

    print("\nReportes generados:")
    print("  · resumen_portafolio.csv")
    print("  · resumen_portafolio.json")
    print("  · resumen_portafolio.html  (dashboard con velas y predicción)")
    print("=" * 60)


if __name__ == "__main__":
    main()
