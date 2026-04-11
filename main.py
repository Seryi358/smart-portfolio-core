from src.modelos import Instrumento, Posicion
from src.portafolio import Portafolio
from src.reportes import ReportadorFinanciero

def main() -> None:
    # 1. Definir activos
    apple = Instrumento(ticker="AAPL", tipo="Acción", sector="Tecnología")
    tesoro = Instrumento(ticker="US10Y", tipo="Bono", sector="Gobierno")

    # 2. Crear posiciones
    pos1 = Posicion(instrumento=apple, _cantidad=10, precio_entrada=150.0)
    pos2 = Posicion(instrumento=tesoro, _cantidad=5, precio_entrada=100.0)

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

if __name__ == "__main__":
    main()
