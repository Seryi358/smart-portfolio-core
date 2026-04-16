import sys
from pathlib import Path

# Agregar src al path
sys.path.append(str(Path(__file__).resolve().parent / "src"))

from modelos import Instrumento, Posicion
from portafolio import Portafolio
from reportes import ReportadorFinanciero

def main() -> None:
    # 1. Definir activos
    apple = Instrumento(ticker="AAPL", tipo="Acción", sector="Tecnología")
    tesoro = Instrumento(ticker="US10Y", tipo="Bono", sector="Gobierno")

    # 2. Crear posiciones
    pos1 = Posicion(instrumento=apple, cantidad=10, precio_entrada=150.0)
    pos2 = Posicion(instrumento=tesoro, cantidad=5, precio_entrada=100.0)

    # 3. Gestionar portafolio
    fondo = Portafolio()
    fondo.agregar_posicion(pos1)
    fondo.agregar_posicion(pos2)

    # 4. Precios de mercado actuales (ejemplo)
    precios = {"AAPL": 175.3, "US10Y": 99.8}

    # 5. Reportar resultados
    reportador = ReportadorFinanciero()
    reportador.imprimir_resumen(fondo, precios)
    # Exportar a CSV y JSON
    reportador.exportar_csv(fondo, precios, "resumen_portafolio.csv")
    reportador.exportar_json(fondo, precios, "resumen_portafolio.json")

    # Exportar HTML con gráficas (sin datos OHLCV reales en este ejemplo)
    reportador.exportar_html(fondo, precios, "resumen_portafolio.html")
    print("Reportes generados: CSV, JSON y HTML.")

if __name__ == "__main__":
    main()
