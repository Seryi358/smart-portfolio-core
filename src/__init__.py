"""smart-portfolio-core — Sistema de gestión de portafolios financieros.

Módulos:
    modelos           — Instrumento y Posicion (dominio).
    portafolio        — Portafolio y PosicionNoExisteError (agregado).
    reportes          — ReportadorFinanciero (CSV, JSON, HTML).
    providers         — MarketDataProvider + YahooFinanceClient + Mock.
    oracle            — InstrumentoOracle (ML con regresión lineal).
    domain            — Value Objects, DTOs y excepciones de dominio.
    config            — Settings / AppSettings para secretos y entorno.
    async_providers   — Descarga asíncrona y cliente HTTP con reintentos.
"""
