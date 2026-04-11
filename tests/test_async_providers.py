"""tests/test_async_providers.py — Tests para src/async_providers.py (Sesión 5.3)."""
import asyncio
import pytest

from async_providers import (
    HttpClientConfig,
    AsyncHttpClient,
    fetch_many_quotes_async,
    fetch_async,
    run_async,
    run_async_limited,
)


class TestFetchAsync:
    def test_retorna_string_con_nombre(self):
        result = asyncio.run(fetch_async("AAPL", min_delay=0.0, max_delay=0.0))
        assert "AAPL" in result

    def test_retorna_string_async(self):
        result = asyncio.run(fetch_async("X", min_delay=0.0, max_delay=0.0))
        assert result.startswith("async:")


class TestRunAsync:
    def test_longitud_correcta(self):
        names = ["A", "B", "C"]
        results = asyncio.run(run_async(names))
        assert len(results) == 3

    def test_cada_elemento_es_string(self):
        results = asyncio.run(run_async(["X"]))
        assert all(isinstance(r, str) for r in results)


class TestRunAsyncLimited:
    def test_longitud_correcta(self):
        names = ["A", "B", "C", "D"]
        results = asyncio.run(run_async_limited(names, concurrency=2))
        assert len(results) == 4

    def test_resultados_son_strings(self):
        results = asyncio.run(run_async_limited(["X", "Y"], concurrency=1))
        assert all(isinstance(r, str) for r in results)


class TestFetchManyQuotesAsync:
    def test_retorna_dict_con_todos_los_tickers(self):
        tickers = ["AAPL", "MSFT", "NVDA"]
        result = asyncio.run(fetch_many_quotes_async(tickers))
        assert set(result.keys()) == set(tickers)

    def test_precios_son_floats(self):
        result = asyncio.run(fetch_many_quotes_async(["TSLA"]))
        assert isinstance(result["TSLA"], float)

    def test_reproducible(self):
        # El stub usa hash del ticker → mismo ticker = mismo precio
        r1 = asyncio.run(fetch_many_quotes_async(["AAPL"]))
        r2 = asyncio.run(fetch_many_quotes_async(["AAPL"]))
        assert r1["AAPL"] == r2["AAPL"]

    def test_lista_vacia(self):
        result = asyncio.run(fetch_many_quotes_async([]))
        assert result == {}


class TestHttpClientConfig:
    def test_defaults(self):
        cfg = HttpClientConfig()
        assert cfg.timeout_s == 10.0
        assert cfg.retries == 3
        assert cfg.backoff_base_s == 0.5
        assert cfg.concurrency == 5

    def test_custom_values(self):
        cfg = HttpClientConfig(timeout_s=5.0, retries=2, concurrency=3)
        assert cfg.timeout_s == 5.0
        assert cfg.retries == 2
        assert cfg.concurrency == 3

    def test_es_inmutable(self):
        cfg = HttpClientConfig()
        with pytest.raises(Exception):
            cfg.retries = 10  # type: ignore[misc]


class TestAsyncHttpClient:
    def test_instancia_correctamente(self):
        cfg = HttpClientConfig(concurrency=3)
        client = AsyncHttpClient(cfg)
        assert client._cfg == cfg
