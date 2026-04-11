from dataclasses import asdict
import csv
import json
from typing import Dict
from .modelos import Posicion
from .portafolio import Portafolio


class ReportadorFinanciero:
    """Genera reportes legibles a partir de un Portafolio."""

    def imprimir_resumen(self, portafolio: Portafolio,
                         precios_mercado: Dict[str, float]) -> None:
        """Imprime un resumen de las posiciones con sus valores actuales.

        Args:
            portafolio: Objeto Portafolio con posiciones.
            precios_mercado: Precios actuales de mercado por ticker.
        """
        print("\nResumen de posiciones:\n")
        cabecera = ("Ticker", "Tipo", "Sector", "Cantidad",
                    "Precio entrada", "Precio actual", "Valor actual",
                    "Ganancia/Pérdida")
        print("{:<10} {:<10} {:<15} {:>10} {:>15} {:>15} {:>15} {:>15}".format(*cabecera))
        print("-" * 110)
        for pos in portafolio.posiciones:
            ticker = pos.instrumento.ticker
            tipo = pos.instrumento.tipo
            sector = pos.instrumento.sector
            cantidad = pos.cantidad
            precio_entrada = pos.precio_entrada
            precio_actual = precios_mercado.get(ticker, 0.0)
            valor_actual = pos.calcular_valor_actual(precio_actual)
            ganancia = (precio_actual - precio_entrada) * cantidad
            print(f"{ticker:<10} {tipo:<10} {sector:<15} {cantidad:>10.2f} "
                  f"{precio_entrada:>15.2f} {precio_actual:>15.2f} {valor_actual:>15.2f} {ganancia:>15.2f}")

    def exportar_csv(self, portafolio: Portafolio,
                     precios_mercado: Dict[str, float], ruta: str) -> None:
        """Exporta el resumen a un archivo CSV."""
        campos = ["ticker", "tipo", "sector", "cantidad",
                  "precio_entrada", "precio_actual", "valor_actual",
                  "ganancia_perdida"]
        with open(ruta, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            for pos in portafolio.posiciones:
                ticker = pos.instrumento.ticker
                precio_actual = precios_mercado.get(ticker, 0.0)
                valor_actual = pos.calcular_valor_actual(precio_actual)
                ganancia = (precio_actual - pos.precio_entrada) * pos.cantidad
                writer.writerow({
                    "ticker": ticker,
                    "tipo": pos.instrumento.tipo,
                    "sector": pos.instrumento.sector,
                    "cantidad": pos.cantidad,
                    "precio_entrada": pos.precio_entrada,
                    "precio_actual": precio_actual,
                    "valor_actual": valor_actual,
                    "ganancia_perdida": ganancia,
                })

    def exportar_json(self, portafolio: Portafolio,
                      precios_mercado: Dict[str, float], ruta: str) -> None:
        """Exporta el resumen a un archivo JSON."""
        lista = []
        for pos in portafolio.posiciones:
            ticker = pos.instrumento.ticker
            precio_actual = precios_mercado.get(ticker, 0.0)
            valor_actual = pos.calcular_valor_actual(precio_actual)
            ganancia = (precio_actual - pos.precio_entrada) * pos.cantidad
            lista.append({
                "ticker": ticker,
                "tipo": pos.instrumento.tipo,
                "sector": pos.instrumento.sector,
                "cantidad": pos.cantidad,
                "precio_entrada": pos.precio_entrada,
                "precio_actual": precio_actual,
                "valor_actual": valor_actual,
                "ganancia_perdida": ganancia,
            })
        with open(ruta, mode="w", encoding="utf-8") as f:
            json.dump(lista, f, indent=4)
