"""oracle_cli.py — Oráculo Financiero Interactivo

CLI que obtiene precios reales vía Yahoo Finance, entrena un modelo predictivo
de regresión lineal, genera reportes HTML profesionales con gráficas interactivas
y permite registrar posiciones con alertas de pérdida.
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / "src"))

from modelos import Instrumento, Posicion
from oracle import InstrumentoOracle
from portafolio import Portafolio
from providers import YahooFinanceClient
from reportes import ReportadorFinanciero


def solicitar_float(mensaje: str, default: float = None) -> float:
    while True:
        entrada = input(mensaje).strip()
        if not entrada and default is not None:
            return default
        try:
            return float(entrada)
        except ValueError:
            print("  Ingrese un número válido.")


def main() -> None:
    print("=" * 60)
    print("         ORÁCULO FINANCIERO — Smart Portfolio Core")
    print("=" * 60)

    ticker = input("\nTicker del instrumento (ej. AAPL, MSFT, GOOGL): ").strip().upper()
    tipo = input("Tipo de instrumento (ej. Acción, Bono, ETF): ").strip()
    sector = input("Sector económico (ej. Tecnología, Finanzas): ").strip()

    proveedor = YahooFinanceClient()
    oracle = InstrumentoOracle(
        ticker=ticker,
        tipo=tipo,
        sector=sector,
        data_provider=proveedor,
    )

    print(f"\nObteniendo datos de mercado para {ticker}...")
    try:
        precio_actual = oracle.obtener_precio_actual()
        print(f"  Precio actual:        ${precio_actual:,.2f}")

        print("  Entrenando modelo predictivo (regresión lineal)...")
        oracle.entrenar_modelo()
        precio_30d = oracle.predecir_precio(30)
        precio_90d = oracle.predecir_precio(90)
        tendencia = oracle.tendencia()

        print(f"  Predicción a  30 días: ${precio_30d:,.2f}")
        print(f"  Predicción a  90 días: ${precio_90d:,.2f}")
        print(f"  Tendencia detectada:   {tendencia.upper()}")

        # Obtener datos OHLCV para velas japonesas
        print("  Descargando datos OHLCV para gráficas...")
        datos_ohlcv = {ticker: proveedor.obtener_ohlcv(ticker, "1y")}

        # Preparar datos de predicción
        historial = proveedor.obtener_historia(ticker)
        ohlcv_data = datos_ohlcv[ticker]
        datos_prediccion = {
            ticker: {
                "historico": historial,
                "fechas_historico": ohlcv_data["dates"],
                "precio_actual": precio_actual,
                "prediccion_30d": precio_30d,
                "prediccion_90d": precio_90d,
                "tendencia": tendencia,
            }
        }

    except Exception as e:
        print(f"\nError al obtener datos: {e}")
        sys.exit(1)

    resultado = {
        "ticker": ticker,
        "tipo": tipo,
        "sector": sector,
        "precio_actual": round(precio_actual, 4),
        "prediccion_30d": round(precio_30d, 4),
        "prediccion_90d": round(precio_90d, 4),
        "tendencia": tendencia,
        "decision_compra": False,
        "posicion": None,
    }

    # Crear portafolio para el reporte
    portafolio = Portafolio()
    precios_mercado = {ticker: precio_actual}

    decision = input(f"\n¿Desea registrar una posición en {ticker}? (s/n): ").strip().lower()

    if decision == "s":
        cantidad = solicitar_float("  Cantidad de unidades: ")
        precio_entrada = solicitar_float(
            f"  Precio de entrada [Enter = precio actual ${precio_actual:.2f}]: ",
            default=precio_actual,
        )

        instrumento = Instrumento(ticker=ticker, tipo=tipo, sector=sector)
        pos = Posicion(
            instrumento=instrumento,
            _cantidad=cantidad,
            precio_entrada=precio_entrada,
        )

        valor_actual = pos.calcular_valor_actual(precio_actual)
        pnl = pos.calcular_ganancia_no_realizada(precio_actual)
        alerta = pos.tiene_alerta_perdida(precio_actual)

        print(f"\n  Valor actual de la posición: ${valor_actual:,.2f}")
        print(f"  Ganancia / Pérdida actual:   ${pnl:,.2f}")

        if alerta:
            print("  ⚠  ALERTA: la posición ya muestra una pérdida mayor al 10%")

        resultado["decision_compra"] = True
        resultado["posicion"] = {
            "cantidad": cantidad,
            "precio_entrada": precio_entrada,
            "valor_actual": round(valor_actual, 4),
            "pnl": round(pnl, 4),
            "alerta_perdida": alerta,
        }

        portafolio.agregar_posicion(pos)

    # Guardar JSON
    ruta_json = f"oracle_{ticker.lower()}.json"
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)
    print(f"\nResultado guardado en: {ruta_json}")

    # Generar reporte HTML con gráficas
    if portafolio.posiciones:
        ruta_html = f"oracle_{ticker.lower()}_reporte.html"
        reportador = ReportadorFinanciero()
        reportador.exportar_html(
            portafolio, precios_mercado, ruta_html,
            datos_ohlcv=datos_ohlcv,
            datos_prediccion=datos_prediccion,
        )
        print(f"Reporte HTML generado: {ruta_html}")
    else:
        # Generar reporte solo con gráficas de mercado (sin posiciones)
        ruta_html = f"oracle_{ticker.lower()}_reporte.html"
        instrumento = Instrumento(ticker=ticker, tipo=tipo, sector=sector)
        pos_temp = Posicion(instrumento=instrumento, _cantidad=1, precio_entrada=precio_actual)
        portafolio.agregar_posicion(pos_temp)
        reportador = ReportadorFinanciero()
        reportador.exportar_html(
            portafolio, precios_mercado, ruta_html,
            datos_ohlcv=datos_ohlcv,
            datos_prediccion=datos_prediccion,
        )
        print(f"Reporte HTML generado: {ruta_html}")

    print("=" * 60)


if __name__ == "__main__":
    main()
