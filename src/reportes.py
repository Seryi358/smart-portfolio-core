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
                      precios_mercado: Dict[str, float], ruta: str,
                      datos_ohlcv: Dict[str, Dict[str, list]] = None,
                      datos_prediccion: Dict[str, Dict] = None) -> None:
        """Exporta un reporte HTML profesional con gráficas interactivas Plotly.

        Args:
            portafolio: Portafolio con posiciones.
            precios_mercado: Precios actuales por ticker.
            ruta: Ruta del archivo HTML de salida.
            datos_ohlcv: Datos OHLCV por ticker para velas japonesas (opcional).
            datos_prediccion: Datos de predicción por ticker del oracle (opcional).
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        from datetime import datetime

        # --- Preparar datos de posiciones ---
        filas = []
        sectores = {}
        for pos in portafolio.posiciones:
            ticker = pos.instrumento.ticker
            precio_actual = precios_mercado.get(ticker, 0.0)
            valor_actual = pos.calcular_valor_actual(precio_actual)
            ganancia = (precio_actual - pos.precio_entrada) * pos.cantidad
            pct = (ganancia / (pos.precio_entrada * pos.cantidad) * 100) if pos.precio_entrada * pos.cantidad != 0 else 0
            filas.append({
                "ticker": ticker, "tipo": pos.instrumento.tipo,
                "sector": pos.instrumento.sector, "cantidad": pos.cantidad,
                "precio_entrada": pos.precio_entrada, "precio_actual": precio_actual,
                "valor_actual": valor_actual, "ganancia": ganancia, "pct": pct,
            })
            sectores[pos.instrumento.sector] = sectores.get(pos.instrumento.sector, 0) + valor_actual

        valor_total = sum(f["valor_actual"] for f in filas)
        ganancia_total = sum(f["ganancia"] for f in filas)
        costo_total = sum(f["precio_entrada"] * f["cantidad"] for f in filas)
        pct_total = (ganancia_total / costo_total * 100) if costo_total != 0 else 0

        # --- Gráfica 1: Distribución por sector (Pie) ---
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(sectores.keys()),
            values=list(sectores.values()),
            hole=0.45,
            marker=dict(colors=["#00d4aa", "#0088ff", "#ff6b35", "#ffd700",
                                "#ff4757", "#a55eea", "#2ed573", "#1e90ff"]),
            textinfo="label+percent",
            textfont=dict(size=13, color="#e0e0e0"),
        )])
        fig_pie.update_layout(
            title=dict(text="Distribución por Sector", font=dict(size=18, color="#e0e0e0")),
            paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
            legend=dict(font=dict(color="#b0b0b0")),
            margin=dict(t=60, b=30, l=30, r=30), height=380,
        )

        # --- Gráfica 2: Ganancia/Pérdida por posición (Barras) ---
        colores_pnl = ["#00d4aa" if f["ganancia"] >= 0 else "#ff4757" for f in filas]
        fig_bar = go.Figure(data=[go.Bar(
            x=[f["ticker"] for f in filas],
            y=[f["ganancia"] for f in filas],
            marker_color=colores_pnl,
            text=[f"${f['ganancia']:,.2f}" for f in filas],
            textposition="outside",
            textfont=dict(color="#e0e0e0", size=12),
        )])
        fig_bar.update_layout(
            title=dict(text="Ganancia / Pérdida por Posición", font=dict(size=18, color="#e0e0e0")),
            paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
            xaxis=dict(color="#b0b0b0", gridcolor="#2a2a4a"),
            yaxis=dict(color="#b0b0b0", gridcolor="#2a2a4a", title="USD"),
            margin=dict(t=60, b=40, l=60, r=30), height=380,
        )

        # --- Gráficas de velas japonesas ---
        figs_velas = {}
        if datos_ohlcv:
            for ticker, ohlcv in datos_ohlcv.items():
                fig_candle = make_subplots(
                    rows=2, cols=1, shared_xaxes=True,
                    vertical_spacing=0.03, row_heights=[0.75, 0.25],
                    subplot_titles=[f"{ticker} — Velas Japonesas", "Volumen"],
                )
                fig_candle.add_trace(go.Candlestick(
                    x=ohlcv["dates"], open=ohlcv["open"], high=ohlcv["high"],
                    low=ohlcv["low"], close=ohlcv["close"],
                    increasing=dict(line=dict(color="#00d4aa"), fillcolor="#00d4aa"),
                    decreasing=dict(line=dict(color="#ff4757"), fillcolor="#ff4757"),
                    name="Precio",
                ), row=1, col=1)
                vol_colors = ["#00d4aa" if ohlcv["close"][i] >= ohlcv["open"][i]
                              else "#ff4757" for i in range(len(ohlcv["close"]))]
                fig_candle.add_trace(go.Bar(
                    x=ohlcv["dates"], y=ohlcv["volume"],
                    marker_color=vol_colors, name="Volumen", showlegend=False,
                ), row=2, col=1)
                fig_candle.update_layout(
                    paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
                    font=dict(color="#e0e0e0"),
                    xaxis=dict(gridcolor="#2a2a4a",
                               rangeselector=dict(
                                   buttons=[
                                       dict(count=1, label="1M", step="month", stepmode="backward"),
                                       dict(count=3, label="3M", step="month", stepmode="backward"),
                                       dict(count=6, label="6M", step="month", stepmode="backward"),
                                       dict(step="all", label="1Y"),
                                   ],
                                   bgcolor="#16213e", activecolor="#0088ff",
                                   font=dict(color="#e0e0e0"),
                               ),
                               rangeslider=dict(visible=False)),
                    xaxis2=dict(gridcolor="#2a2a4a"),
                    yaxis=dict(gridcolor="#2a2a4a", title="Precio (USD)"),
                    yaxis2=dict(gridcolor="#2a2a4a", title="Volumen"),
                    margin=dict(t=60, b=30, l=60, r=30), height=520,
                    showlegend=False,
                )
                for ann in fig_candle.layout.annotations:
                    ann.font = dict(color="#e0e0e0", size=16)
                figs_velas[ticker] = fig_candle

        # --- Gráfica de predicción del oracle ---
        figs_pred = {}
        if datos_prediccion:
            for ticker, pred in datos_prediccion.items():
                fig_pred = go.Figure()
                hist = pred.get("historico", [])
                fechas_hist = pred.get("fechas_historico", [])
                if hist and fechas_hist:
                    fig_pred.add_trace(go.Scatter(
                        x=fechas_hist, y=hist, mode="lines",
                        name="Histórico", line=dict(color="#0088ff", width=2),
                    ))
                precio_actual_pred = pred.get("precio_actual", hist[-1] if hist else 0)
                pred_30 = pred.get("prediccion_30d", 0)
                pred_90 = pred.get("prediccion_90d", 0)
                ultima_fecha = fechas_hist[-1] if fechas_hist else "2025-01-01"
                from datetime import datetime, timedelta
                try:
                    base = datetime.strptime(ultima_fecha, "%Y-%m-%d")
                except ValueError:
                    base = datetime.now()
                fechas_pred = [ultima_fecha,
                               (base + timedelta(days=30)).strftime("%Y-%m-%d"),
                               (base + timedelta(days=90)).strftime("%Y-%m-%d")]
                fig_pred.add_trace(go.Scatter(
                    x=fechas_pred, y=[precio_actual_pred, pred_30, pred_90],
                    mode="lines+markers", name="Predicción",
                    line=dict(color="#ffd700", width=2, dash="dash"),
                    marker=dict(size=8, color="#ffd700"),
                ))
                tendencia = pred.get("tendencia", "neutral")
                color_tend = "#00d4aa" if tendencia == "alcista" else "#ff4757" if tendencia == "bajista" else "#ffd700"
                fig_pred.update_layout(
                    title=dict(text=f"{ticker} — Predicción ({tendencia.upper()})",
                               font=dict(size=18, color=color_tend)),
                    paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
                    xaxis=dict(color="#b0b0b0", gridcolor="#2a2a4a", title="Fecha"),
                    yaxis=dict(color="#b0b0b0", gridcolor="#2a2a4a", title="Precio (USD)"),
                    legend=dict(font=dict(color="#b0b0b0")),
                    margin=dict(t=60, b=40, l=60, r=30), height=420,
                )
                figs_pred[ticker] = fig_pred

        # --- Construir HTML ---
        fecha_reporte = datetime.now().strftime("%d/%m/%Y %H:%M")
        color_total = "#00d4aa" if ganancia_total >= 0 else "#ff4757"
        signo = "+" if ganancia_total >= 0 else ""
        flecha = "&#9650;" if ganancia_total >= 0 else "&#9660;"

        filas_html = ""
        for f in filas:
            color_g = "#00d4aa" if f["ganancia"] >= 0 else "#ff4757"
            signo_f = "+" if f["ganancia"] >= 0 else ""
            flecha_f = "&#9650;" if f["ganancia"] >= 0 else "&#9660;"
            filas_html += f"""
                <tr>
                    <td style="font-weight:600;color:#e0e0e0">{f['ticker']}</td>
                    <td>{f['tipo']}</td>
                    <td>{f['sector']}</td>
                    <td style="text-align:right">{f['cantidad']:,.2f}</td>
                    <td style="text-align:right">${f['precio_entrada']:,.2f}</td>
                    <td style="text-align:right">${f['precio_actual']:,.2f}</td>
                    <td style="text-align:right">${f['valor_actual']:,.2f}</td>
                    <td style="text-align:right;color:{color_g};font-weight:600">
                        {flecha_f} {signo_f}${abs(f['ganancia']):,.2f} ({signo_f}{f['pct']:.1f}%)
                    </td>
                </tr>"""

        graficas_html = ""
        graficas_html += f'<div class="chart-card">{fig_pie.to_html(full_html=False, include_plotlyjs=False)}</div>'
        graficas_html += f'<div class="chart-card">{fig_bar.to_html(full_html=False, include_plotlyjs=False)}</div>'
        for ticker, fig in figs_velas.items():
            graficas_html += f'<div class="chart-card full-width">{fig.to_html(full_html=False, include_plotlyjs=False)}</div>'
        for ticker, fig in figs_pred.items():
            graficas_html += f'<div class="chart-card full-width">{fig.to_html(full_html=False, include_plotlyjs=False)}</div>'

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Portfolio — Reporte Financiero</title>
    <script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0f0f23;
            color: #b0b0b0;
            min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 30px 20px; }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 16px;
            padding: 35px 40px;
            margin-bottom: 30px;
            border: 1px solid #2a2a4a;
        }}
        .header h1 {{
            font-size: 28px;
            color: #e0e0e0;
            margin-bottom: 6px;
            letter-spacing: -0.5px;
        }}
        .header .subtitle {{ color: #6b7280; font-size: 14px; }}
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-top: 25px;
        }}
        .kpi {{
            background: #16213e;
            border-radius: 12px;
            padding: 20px 24px;
            border: 1px solid #2a2a4a;
        }}
        .kpi .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #6b7280; }}
        .kpi .value {{ font-size: 26px; font-weight: 700; color: #e0e0e0; margin-top: 6px; }}
        .kpi .change {{ font-size: 14px; margin-top: 4px; }}
        .section-title {{
            font-size: 20px; color: #e0e0e0; margin: 35px 0 18px;
            padding-bottom: 10px; border-bottom: 1px solid #2a2a4a;
        }}
        table {{
            width: 100%; border-collapse: collapse;
            background: #1a1a2e; border-radius: 12px;
            overflow: hidden; border: 1px solid #2a2a4a;
        }}
        th {{
            background: #16213e; color: #6b7280;
            font-size: 11px; text-transform: uppercase;
            letter-spacing: 1px; padding: 14px 16px; text-align: left;
        }}
        td {{ padding: 14px 16px; border-top: 1px solid #2a2a4a; font-size: 14px; }}
        tr:hover {{ background: #16213e; }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-top: 10px;
        }}
        .chart-card {{
            background: #1a1a2e;
            border-radius: 12px;
            padding: 15px;
            border: 1px solid #2a2a4a;
            overflow: hidden;
        }}
        .chart-card.full-width {{ grid-column: 1 / -1; }}
        .footer {{
            text-align: center;
            color: #4a4a6a;
            font-size: 12px;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #2a2a4a;
        }}
        @media (max-width: 768px) {{
            .chart-grid {{ grid-template-columns: 1fr; }}
            .kpi-row {{ grid-template-columns: 1fr 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Smart Portfolio Core</h1>
            <div class="subtitle">Reporte generado el {fecha_reporte}</div>
            <div class="kpi-row">
                <div class="kpi">
                    <div class="label">Valor Total</div>
                    <div class="value">${valor_total:,.2f}</div>
                </div>
                <div class="kpi">
                    <div class="label">Costo Base</div>
                    <div class="value">${costo_total:,.2f}</div>
                </div>
                <div class="kpi">
                    <div class="label">Ganancia / Pérdida</div>
                    <div class="value" style="color:{color_total}">{flecha} {signo}${abs(ganancia_total):,.2f}</div>
                    <div class="change" style="color:{color_total}">{signo}{pct_total:.2f}%</div>
                </div>
                <div class="kpi">
                    <div class="label">Posiciones</div>
                    <div class="value">{len(filas)}</div>
                </div>
            </div>
        </div>

        <h2 class="section-title">Posiciones del Portafolio</h2>
        <table>
            <thead>
                <tr>
                    <th>Ticker</th><th>Tipo</th><th>Sector</th>
                    <th style="text-align:right">Cantidad</th>
                    <th style="text-align:right">Precio Entrada</th>
                    <th style="text-align:right">Precio Actual</th>
                    <th style="text-align:right">Valor Actual</th>
                    <th style="text-align:right">Ganancia / Pérdida</th>
                </tr>
            </thead>
            <tbody>{filas_html}
            </tbody>
        </table>

        <h2 class="section-title">Análisis del Portafolio</h2>
        <div class="chart-grid">
            {graficas_html}
        </div>

        <div class="footer">
            Smart Portfolio Core &mdash; Seminario de Programación &mdash; Business Intelligence
        </div>
    </div>
</body>
</html>"""

        with open(ruta, mode="w", encoding="utf-8") as f:
            f.write(html)
