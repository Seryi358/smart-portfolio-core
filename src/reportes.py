from dataclasses import asdict
import csv
import json
from typing import Dict
from modelos import Posicion
from portafolio import Portafolio


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

    def exportar_html(self, portafolio: Portafolio,
                      precios_mercado: Dict[str, float], ruta: str) -> None:
        """Exporta el resumen a un archivo HTML simple."""
        html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Reporte Financiero</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
                th { background-color: #f2f2f2; text-align: center; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                tr:hover { background-color: #f1f1f1; }
                .text-left { text-align: left; }
                .ganancia { color: green; }
                .perdida { color: red; }
            </style>
        </head>
        <body>
            <h1>Resumen de Portafolio</h1>
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Tipo</th>
                        <th>Sector</th>
                        <th>Cantidad</th>
                        <th>Precio Entrada</th>
                        <th>Precio Actual</th>
                        <th>Valor Actual</th>
                        <th>Ganancia/Pérdida</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for pos in portafolio.posiciones:
            ticker = pos.instrumento.ticker
            tipo = pos.instrumento.tipo
            sector = pos.instrumento.sector
            cantidad = pos.cantidad
            precio_entrada = pos.precio_entrada
            precio_actual = precios_mercado.get(ticker, 0.0)
            valor_actual = pos.calcular_valor_actual(precio_actual)
            ganancia = (precio_actual - pos.precio_entrada) * pos.cantidad
            
            clase_pn = "ganancia" if ganancia >= 0 else "perdida"
            
            html += f"""
                    <tr>
                        <td class="text-left">{ticker}</td>
                        <td class="text-left">{tipo}</td>
                        <td class="text-left">{sector}</td>
                        <td>{cantidad:.2f}</td>
                        <td>{precio_entrada:.2f}</td>
                        <td>{precio_actual:.2f}</td>
                        <td>{valor_actual:.2f}</td>
                        <td class="{clase_pn}">{ganancia:.2f}</td>
                    </tr>
            """
            
        html += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        with open(ruta, mode="w", encoding="utf-8") as f:
            f.write(html)
