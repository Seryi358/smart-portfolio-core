"""async_providers.py — Descarga Paralela Asíncrona de Cotizaciones.

Sesión 5.3: Asincronismo y Descarga Paralela.

Conceptos demostrados:
- ``async / await``: funciones no bloqueantes para operaciones I/O.
- ``asyncio.gather``: ejecuta múltiples corrutinas en paralelo.
- ``asyncio.Semaphore``: limita conexiones simultáneas (respeto a rate limits).
- Backoff exponencial: reintento con espera creciente ante fallos transitorios.

Por qué importa:
    Descarga secuencial de 10 tickers × 0.4 s ≈ 4 s.
    Descarga paralela con concurrency=5 ≈ 0.5 s (ganancia ~8×).
"""
from __future__ import annotations

import asyncio
import hashlib
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence


# ---------------------------------------------------------------------------
# Simulación básica: sync vs async
# ---------------------------------------------------------------------------


def fetch_sync(name: str, min_delay: float = 0.2, max_delay: float = 0.6) -> str:
    """Simula una llamada I/O bloqueante (síncrona).

    En la práctica representa cualquier llamada a una API REST sin soporte async.

    Args:
        name: Identificador de la "descarga".
        min_delay: Mínimo tiempo de espera simulado en segundos.
        max_delay: Máximo tiempo de espera simulado en segundos.

    Returns:
        String descriptivo con el tiempo tardado.
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)
    return f"sync:{name} ({delay:.2f}s)"


async def fetch_async(name: str, min_delay: float = 0.2, max_delay: float = 0.6) -> str:
    """Simula una llamada I/O no bloqueante (asíncrona).

    Usa ``asyncio.sleep`` en lugar de ``time.sleep``, lo que permite
    que el event loop atienda otras tareas mientras espera.

    Args:
        name: Identificador de la "descarga".
        min_delay: Mínimo tiempo de espera simulado en segundos.
        max_delay: Máximo tiempo de espera simulado en segundos.

    Returns:
        String descriptivo con el tiempo tardado.
    """
    delay = random.uniform(min_delay, max_delay)
    await asyncio.sleep(delay)
    return f"async:{name} ({delay:.2f}s)"


def run_sync(names: Sequence[str]) -> list[str]:
    """Ejecuta descargas de forma secuencial (bloqueante).

    Args:
        names: Lista de identificadores a descargar.

    Returns:
        Lista de resultados en el mismo orden.
    """
    start = time.perf_counter()
    results = [fetch_sync(n) for n in names]
    elapsed = time.perf_counter() - start
    print(f"[sync ] elapsed: {elapsed:.2f}s para {len(names)} items")
    return results


async def run_async(names: Sequence[str]) -> list[str]:
    """Ejecuta descargas concurrentemente con asyncio.gather.

    Args:
        names: Lista de identificadores a descargar.

    Returns:
        Lista de resultados en el mismo orden que ``names``.
    """
    start = time.perf_counter()
    results = await asyncio.gather(*(fetch_async(n) for n in names))
    elapsed = time.perf_counter() - start
    print(f"[async] elapsed: {elapsed:.2f}s para {len(names)} items")
    return list(results)


# ---------------------------------------------------------------------------
# Control de concurrencia con Semáforo
# ---------------------------------------------------------------------------


async def fetch_async_limited(name: str, sem: asyncio.Semaphore) -> str:
    """Descarga asíncrona que respeta un límite de concurrencia.

    El semáforo actúa como "portero": solo permite que ``sem._value``
    corrutinas ejecuten su sección crítica al mismo tiempo.

    Args:
        name: Identificador de la descarga.
        sem: Semáforo compartido que controla la concurrencia máxima.

    Returns:
        String descriptivo con el tiempo tardado.
    """
    async with sem:
        delay = random.uniform(0.2, 0.6)
        await asyncio.sleep(delay)
        return f"{name} ({delay:.2f}s)"


async def run_async_limited(
    names: Sequence[str], concurrency: int = 4
) -> list[str]:
    """Ejecuta descargas con límite de conexiones simultáneas.

    Útil cuando la API tiene rate limits (ej. 5 req/s).

    Args:
        names: Lista de identificadores a descargar.
        concurrency: Número máximo de descargas simultáneas.

    Returns:
        Lista de resultados en el mismo orden que ``names``.
    """
    sem = asyncio.Semaphore(concurrency)
    start = time.perf_counter()
    results = await asyncio.gather(*(fetch_async_limited(n, sem) for n in names))
    elapsed = time.perf_counter() - start
    print(f"[async limited={concurrency}] elapsed: {elapsed:.2f}s para {len(names)} items")
    return list(results)


# ---------------------------------------------------------------------------
# Descarga paralela de múltiples tickers (stub de cotización)
# ---------------------------------------------------------------------------


async def _fetch_quote_stub(ticker: str, sem: asyncio.Semaphore) -> float:
    """Simula la descarga de una cotización con latencia de red.

    Genera un precio determinista a partir del hash del ticker,
    lo que permite tests reproducibles sin red real.

    Args:
        ticker: Símbolo del instrumento.
        sem: Semáforo de concurrencia.

    Returns:
        Precio simulado como float.
    """
    async with sem:
        await asyncio.sleep(0.15)
        digest = hashlib.md5(ticker.encode()).hexdigest()
        value = int(digest[:8], 16)
        return round((value % 10_000) / 100.0, 2)


async def fetch_many_quotes_async(
    tickers: Sequence[str], concurrency: int = 6
) -> Dict[str, float]:
    """Descarga precios para múltiples tickers en paralelo.

    Punto de entrada principal del módulo. En producción se reemplazaría
    ``_fetch_quote_stub`` por llamadas reales a una API de mercado.

    Args:
        tickers: Lista de símbolos a consultar.
        concurrency: Máximo de descargas simultáneas (default 6).

    Returns:
        Diccionario ``{ticker: precio}`` con los resultados.

    Ejemplo:
        >>> import asyncio
        >>> quotes = asyncio.run(fetch_many_quotes_async(["AAPL", "MSFT"]))
        >>> "AAPL" in quotes
        True
    """
    sem = asyncio.Semaphore(concurrency)
    prices = await asyncio.gather(*(_fetch_quote_stub(t, sem) for t in tickers))
    return {t: p for t, p in zip(tickers, prices)}


# ---------------------------------------------------------------------------
# Cliente HTTP asíncrono con reintentos y backoff exponencial
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class HttpClientConfig:
    """Configuración del cliente HTTP asíncrono.

    Attributes:
        timeout_s: Tiempo máximo de espera por petición en segundos.
        retries: Número de reintentos ante fallos transitorios.
        backoff_base_s: Tiempo base del backoff exponencial en segundos.
        concurrency: Máximo de peticiones simultáneas.
    """

    timeout_s: float = 10.0
    retries: int = 3
    backoff_base_s: float = 0.5
    concurrency: int = 5


class AsyncHttpClient:
    """Cliente HTTP mínimo con reintentos y control de concurrencia.

    Implementa el patrón de reintento con backoff exponencial + jitter:
        intento 1 → espera 0.5 s + jitter
        intento 2 → espera 1.0 s + jitter
        intento 3 → espera 2.0 s + jitter

    El jitter aleatorio evita el "thundering herd" (avalancha de reintentos
    sincronizados cuando múltiples clientes fallan al mismo tiempo).

    Uso:
        >>> config = HttpClientConfig(retries=2, concurrency=3)
        >>> client = AsyncHttpClient(config)
        >>> # client.get_json(session, url, params)  # requiere aiohttp.ClientSession
    """

    def __init__(self, config: HttpClientConfig) -> None:
        self._cfg = config
        self._sem = asyncio.Semaphore(config.concurrency)

    async def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Realiza una petición GET con reintentos y backoff exponencial.

        Args:
            url: URL de destino.
            params: Parámetros de query string (opcional).

        Returns:
            Respuesta JSON como diccionario.

        Raises:
            RuntimeError: Si se agotan todos los reintentos.
            ImportError: Si ``aiohttp`` no está instalado.
        """
        try:
            import aiohttp
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "aiohttp es necesario para AsyncHttpClient. "
                "Instálalo con: poetry add aiohttp"
            ) from exc

        timeout = aiohttp.ClientTimeout(total=self._cfg.timeout_s)
        last_exc: Optional[Exception] = None

        async with aiohttp.ClientSession() as session:
            for attempt in range(1, self._cfg.retries + 1):
                try:
                    async with self._sem:
                        async with session.get(
                            url, params=params, timeout=timeout
                        ) as resp:
                            if resp.status == 429:
                                raise RuntimeError("Rate limited (HTTP 429)")
                            resp.raise_for_status()
                            return await resp.json()
                except Exception as exc:
                    last_exc = exc
                    if attempt >= self._cfg.retries:
                        raise
                    backoff = self._cfg.backoff_base_s * (2 ** (attempt - 1))
                    jitter = random.uniform(0, 0.2)
                    await asyncio.sleep(backoff + jitter)

        raise RuntimeError("El bucle de reintentos terminó sin resultado.") from last_exc
