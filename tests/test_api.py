"""
Testes da API e do repositório.

Os endpoints são testados com um repositório fake injetado via
app.dependency_overrides — sem tocar em disco nem DuckDB. O repositório real
é testado separadamente contra um Parquet gerado em diretório temporário.
"""
import duckdb
import pytest
from fastapi.testclient import TestClient

from src.api.main import app, get_repository
from src.api.repository import (
    PARQUET_FILENAME,
    DataQueryError,
    DatasetNotFoundError,
    EnemRepository,
    EnemStats,
    UfRanking,
)

STATS_2023 = EnemStats(
    total_inscritos=1000,
    media_geral=600.5,
    media_redacao=700.0,
    media_matematica=550.25,
)

RANKING_2023 = [
    UfRanking(uf="SP", media=650.0, total_alunos=300),
    UfRanking(uf="MG", media=640.0, total_alunos=200),
    UfRanking(uf="RJ", media=630.0, total_alunos=100),
]


class StubRepository:
    """Dublê do EnemRepository com o mesmo contrato público."""

    def available_years(self):
        return [2022, 2023]

    def get_stats(self, year):
        if year == 2023:
            return STATS_2023
        if year == 2024:
            raise DataQueryError("falha simulada")
        raise DatasetNotFoundError(year)

    def get_state_ranking(self, year, limit):
        if year != 2023:
            raise DatasetNotFoundError(year)
        return RANKING_2023[:limit]


@pytest.fixture
def client():
    app.dependency_overrides[get_repository] = StubRepository
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# --- Endpoints (com repositório fake) ---------------------------------------

def test_years_lists_available_datasets(client):
    response = client.get("/api/v1/enem/years")
    assert response.status_code == 200
    assert response.json() == {"years": [2022, 2023]}
    assert "max-age" in response.headers["Cache-Control"]


def test_stats_returns_aggregates_with_cache_header(client):
    response = client.get("/api/v1/enem/2023/stats")
    assert response.status_code == 200
    assert response.json() == {
        "total_inscritos": 1000,
        "media_geral": 600.5,
        "media_redacao": 700.0,
        "media_matematica": 550.25,
    }
    assert response.headers["Cache-Control"] == "public, max-age=3600"


def test_states_respects_limit(client):
    response = client.get("/api/v1/enem/2023/states?limit=2")
    assert response.status_code == 200
    assert [entry["uf"] for entry in response.json()] == ["SP", "MG"]


def test_missing_year_returns_404(client):
    response = client.get("/api/v1/enem/2050/stats")
    assert response.status_code == 404
    assert "2050" in response.json()["detail"]


def test_year_out_of_range_returns_422(client):
    assert client.get("/api/v1/enem/1990/stats").status_code == 422


def test_limit_out_of_range_returns_422(client):
    assert client.get("/api/v1/enem/2023/states?limit=999").status_code == 422


def test_internal_error_returns_generic_500(client):
    response = client.get("/api/v1/enem/2024/stats")
    assert response.status_code == 500
    # Nenhum detalhe interno pode vazar para o cliente
    assert response.json() == {"detail": "Erro interno do servidor ao processar os dados."}


# --- Repositório real (com Parquet em diretório temporário) -----------------

def _write_parquet(processed_dir, year, rows):
    """rows: lista de tuplas (SG_UF_ESC, MEDIA_GERAL, NU_NOTA_REDACAO, NU_NOTA_MT)."""
    year_dir = processed_dir / f"enem_{year}"
    year_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = year_dir / PARQUET_FILENAME
    values = ", ".join(
        f"('{uf}', {media}, {redacao}, {mt})" for uf, media, redacao, mt in rows
    )
    con = duckdb.connect()
    try:
        con.execute(
            f"COPY (SELECT * FROM (VALUES {values}) "
            "AS t(SG_UF_ESC, MEDIA_GERAL, NU_NOTA_REDACAO, NU_NOTA_MT)) "
            f"TO '{parquet_path}' (FORMAT PARQUET)"
        )
    finally:
        con.close()
    return parquet_path


def test_repository_reads_real_parquet(tmp_path):
    _write_parquet(tmp_path, 2023, [
        ("SP", 700.0, 800.0, 600.0),
        ("SP", 500.0, 600.0, 400.0),
        ("MG", 660.0, 700.0, 500.0),
    ])
    repo = EnemRepository(str(tmp_path))

    assert repo.available_years() == [2023]

    stats = repo.get_stats(2023)
    assert stats.total_inscritos == 3
    assert stats.media_geral == pytest.approx(620.0)

    ranking = repo.get_state_ranking(2023, limit=10)
    assert [entry.uf for entry in ranking] == ["MG", "SP"]
    assert ranking[1].total_alunos == 2

    with pytest.raises(DatasetNotFoundError):
        repo.get_stats(1999)


def test_repository_cache_invalidates_on_reprocessing(tmp_path):
    parquet_path = _write_parquet(tmp_path, 2023, [("SP", 700.0, 800.0, 600.0)])
    repo = EnemRepository(str(tmp_path))
    assert repo.get_stats(2023).total_inscritos == 1

    # Simula um novo ETL: reescreve o Parquet com mais linhas e mtime futuro
    _write_parquet(tmp_path, 2023, [
        ("SP", 700.0, 800.0, 600.0),
        ("RJ", 650.0, 750.0, 550.0),
    ])
    import os
    future = os.path.getmtime(parquet_path) + 10
    os.utime(parquet_path, (future, future))

    assert repo.get_stats(2023).total_inscritos == 2
