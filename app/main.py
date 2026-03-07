"""app/main.py — SmartPortfolio API con FastAPI y Pydantic.

Sesión 6: FastAPI, Endpoints, Parámetros y Modelos Pydantic.

Arrancar el servidor:
    poetry run uvicorn app.main:app --reload

Documentación interactiva automática:
    http://127.0.0.1:8000/docs   (Swagger UI)
    http://127.0.0.1:8000/redoc  (ReDoc)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

# Permite importar módulos de src/ sin instalación de paquete
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from fastapi import FastAPI, HTTPException, Path as FPath, Query
from pydantic import BaseModel, Field, field_validator

from domain import OrdenCompraDTO, dto_a_posicion, formato_error_pydantic, DomainError

# ---------------------------------------------------------------------------
# Modelos Pydantic — entrada y salida de los endpoints
# ---------------------------------------------------------------------------


class PortfolioRequest(BaseModel):
    """Cuerpo de la petición para analizar/validar un portafolio.

    Ejemplo de payload:
        {
          "tickers": ["AAPL", "MSFT", "NVDA"],
          "weights": [0.5, 0.3, 0.2]
        }
    """

    tickers: List[str] = Field(
        min_length=1, description="Lista de símbolos del portafolio"
    )
    weights: List[float] = Field(
        min_length=1, description="Pesos correspondientes (deben sumar ~1.0)"
    )

    @field_validator("tickers")
    @classmethod
    def normalize_tickers(cls, values: List[str]) -> List[str]:
        return [v.strip().upper() for v in values]

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, values: List[float]) -> List[float]:
        for w in values:
            if w < 0:
                raise ValueError("Cada peso debe ser >= 0.")
        return values


class PortfolioAnalysisResponse(BaseModel):
    """Respuesta del análisis de portafolio."""

    tickers: List[str]
    weights: List[float]
    total_weight: float
    valid_portfolio: bool
    n_assets: int


class PortfolioValidateResponse(BaseModel):
    """Respuesta simplificada de validación de portafolio."""

    tickers: List[str]
    total_weight: float
    valid_portfolio: bool


class OrdenCompraRequest(BaseModel):
    """Cuerpo de la petición para registrar una orden de compra."""

    ticker: str = Field(min_length=1, description="Símbolo del instrumento")
    cantidad: int = Field(gt=0, description="Número de unidades (> 0)")
    precio_entrada: float = Field(ge=0.0, description="Precio de compra (>= 0)")
    nombre: Optional[str] = Field(default=None, description="Nombre descriptivo")


class OrdenCompraResponse(BaseModel):
    """Confirmación de la orden registrada con los Value Objects resueltos."""

    ticker: str
    cantidad: int
    precio_entrada: float
    nombre: str
    valor_posicion: float


class InstrumentResponse(BaseModel):
    """Información básica de un instrumento."""

    ticker: str
    message: str


class HistoryResponse(BaseModel):
    """Historial de precios solicitado."""

    ticker: str
    days_requested: int
    prices_available: int
    latest_price: Optional[float]


# ---------------------------------------------------------------------------
# Instancia FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SmartPortfolio API",
    description=(
        "API REST para análisis y optimización de portafolios financieros. "
        "Proyecto del Seminario de Programación — Maestría BI, Universidad Externado."
    ),
    version="0.2.0",
)


# ---------------------------------------------------------------------------
# Endpoints informativos (GET)
# ---------------------------------------------------------------------------


@app.get("/", tags=["Info"])
def root() -> dict:
    """Mensaje de bienvenida de la API."""
    return {"message": "SmartPortfolio API is running", "version": "0.2.0"}


@app.get("/health", tags=["Info"])
def health() -> dict:
    """Verificación de salud del servicio."""
    return {"status": "ok"}


@app.get("/version", tags=["Info"])
def version() -> dict:
    """Versión actual del servicio."""
    return {"service": "smartportfolio", "version": "0.2.0"}


# ---------------------------------------------------------------------------
# Endpoints de instrumentos (GET con path/query params)
# ---------------------------------------------------------------------------


@app.get("/instrument/{ticker}", response_model=InstrumentResponse, tags=["Instruments"])
def get_instrument(
    ticker: str = FPath(description="Símbolo del instrumento, ej. AAPL"),
) -> InstrumentResponse:
    """Devuelve información básica de un instrumento por su ticker.

    - **ticker**: símbolo en mayúsculas (ej. AAPL, MSFT, BTC-USD)
    """
    normalized = ticker.strip().upper()
    if not normalized:
        raise HTTPException(status_code=400, detail="El ticker no puede estar vacío.")
    return InstrumentResponse(
        ticker=normalized,
        message=f"Información solicitada para {normalized}",
    )


@app.get("/history/{ticker}", response_model=HistoryResponse, tags=["Instruments"])
def get_history(
    ticker: str = FPath(description="Símbolo del instrumento"),
    days: int = Query(default=30, gt=0, le=365, description="Número de días (1–365)"),
) -> HistoryResponse:
    """Devuelve el historial de precios simulado para un ticker.

    - **ticker**: símbolo del instrumento
    - **days**: número de días históricos (query param, default=30)
    """
    normalized = ticker.strip().upper()

    # Precios simulados (stub; en producción se usaría YahooFinanceClient)
    import hashlib

    seed = int(hashlib.md5(normalized.encode()).hexdigest()[:8], 16) % 10_000
    import numpy as np

    rng = np.random.default_rng(seed)
    prices = (100 + np.cumsum(rng.normal(0, 1, days))).tolist()

    return HistoryResponse(
        ticker=normalized,
        days_requested=days,
        prices_available=len(prices),
        latest_price=round(prices[-1], 2) if prices else None,
    )


# ---------------------------------------------------------------------------
# Endpoints de portafolio (POST con body Pydantic)
# ---------------------------------------------------------------------------


@app.post("/portfolio/analyze", response_model=PortfolioAnalysisResponse, tags=["Portfolio"])
def analyze_portfolio(data: PortfolioRequest) -> PortfolioAnalysisResponse:
    """Analiza un portafolio: verifica pesos, diversificación y validez.

    El cuerpo debe incluir listas paralelas de tickers y pesos.
    """
    if len(data.tickers) != len(data.weights):
        raise HTTPException(
            status_code=422,
            detail="Las listas 'tickers' y 'weights' deben tener la misma longitud.",
        )
    total_weight = sum(data.weights)
    return PortfolioAnalysisResponse(
        tickers=data.tickers,
        weights=data.weights,
        total_weight=round(total_weight, 6),
        valid_portfolio=abs(total_weight - 1.0) < 0.01,
        n_assets=len(data.tickers),
    )


@app.post("/portfolio/validate", response_model=PortfolioValidateResponse, tags=["Portfolio"])
def validate_portfolio(data: PortfolioRequest) -> PortfolioValidateResponse:
    """Validación simplificada: comprueba que los pesos sumen ~1.0.

    Demuestra el uso de ``response_model`` para documentación y
    serialización automática de la respuesta.
    """
    total_weight = sum(data.weights)
    return PortfolioValidateResponse(
        tickers=data.tickers,
        total_weight=round(total_weight, 6),
        valid_portfolio=abs(total_weight - 1.0) < 0.01,
    )


# ---------------------------------------------------------------------------
# Endpoint de órdenes (POST con validación de dominio completa)
# ---------------------------------------------------------------------------


@app.post("/orden/registrar", response_model=OrdenCompraResponse, tags=["Orders"])
def registrar_orden(data: OrdenCompraRequest) -> OrdenCompraResponse:
    """Registra una orden de compra aplicando validación de dominio completa.

    Flujo de defensa por capas:
    1. Pydantic valida el JSON recibido (tipos, rangos básicos).
    2. ``OrdenCompraDTO`` aplica reglas de negocio del dominio.
    3. ``dto_a_posicion()`` construye los Value Objects finales.

    Retorna la posición confirmada con el valor total calculado.
    """
    from pydantic import ValidationError

    try:
        dto = OrdenCompraDTO(
            ticker=data.ticker,
            cantidad=data.cantidad,
            precio_entrada=data.precio_entrada,
            nombre=data.nombre,
        )
        posicion = dto_a_posicion(dto)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422, detail=formato_error_pydantic(exc)
        )
    except DomainError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    valor = posicion["cantidad"].value * posicion["precio_entrada"].value
    return OrdenCompraResponse(
        ticker=posicion["ticker"].value,
        cantidad=posicion["cantidad"].value,
        precio_entrada=posicion["precio_entrada"].value,
        nombre=posicion["nombre"],
        valor_posicion=round(valor, 4),
    )
