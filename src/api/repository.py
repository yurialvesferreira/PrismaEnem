"""
Camada de acesso a dados (Repository) dos microdados processados do ENEM.

Isola todo o acesso a DuckDB/Parquet dos endpoints HTTP: a API conhece apenas
os métodos públicos e as exceções de domínio deste módulo, o que permite
testar cada camada separadamente (ver tests/test_api.py).
"""
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Iterator, TypeVar

import duckdb
import logging
import os

logger = logging.getLogger(__name__)

PARQUET_FILENAME = "enem_processed.parquet"
# 26 estados + DF
MAX_UF_LIMIT = 27

_STATS_QUERY = """
    SELECT
        COUNT(*) as total_inscritos,
        AVG(CAST(MEDIA_GERAL AS FLOAT)) as media_geral,
        AVG(CAST(NU_NOTA_REDACAO AS FLOAT)) as media_redacao,
        AVG(CAST(NU_NOTA_MT AS FLOAT)) as media_matematica
    FROM enem_data
    WHERE MEDIA_GERAL > 0
"""

_RANKING_QUERY = """
    SELECT
        SG_UF_ESC as uf,
        AVG(CAST(MEDIA_GERAL AS FLOAT)) as media,
        COUNT(*) as total_alunos
    FROM enem_data
    WHERE SG_UF_ESC IS NOT NULL AND MEDIA_GERAL > 0
    GROUP BY SG_UF_ESC
    ORDER BY media DESC
"""

T = TypeVar("T")


class DatasetNotFoundError(Exception):
    """Não há dados processados para o ano solicitado."""

    def __init__(self, year: int):
        self.year = year
        super().__init__(f"Dados processados do ano {year} não encontrados.")


class DataQueryError(Exception):
    """Falha interna ao consultar os dados processados."""


@dataclass(frozen=True)
class EnemStats:
    total_inscritos: int
    media_geral: float
    media_redacao: float
    media_matematica: float


@dataclass(frozen=True)
class UfRanking:
    uf: str
    media: float
    total_alunos: int


class EnemRepository:
    """
    Repositório de leitura dos Parquets processados.

    Os dados são imutáveis após o ETL, então os agregados são cacheados em
    memória por (consulta, ano, mtime do arquivo): reprocessar um ano muda o
    mtime e invalida o cache automaticamente, sem reiniciar a API.
    """

    def __init__(self, processed_data_dir: str):
        self._root = os.path.abspath(processed_data_dir)
        # Acesso concorrente pode, no pior caso, recomputar um agregado em
        # duplicidade — aceitável para leituras idempotentes como estas.
        self._cache: dict[tuple[str, int, float], object] = {}

    # --- API pública ---------------------------------------------------

    def available_years(self) -> list[int]:
        """Anos com Parquet processado disponível para consulta."""
        years: list[int] = []
        if os.path.isdir(self._root):
            for entry in os.listdir(self._root):
                prefix, _, suffix = entry.partition('_')
                if prefix == 'enem' and suffix.isdigit() and \
                        os.path.exists(os.path.join(self._root, entry, PARQUET_FILENAME)):
                    years.append(int(suffix))
        return sorted(years)

    def get_stats(self, year: int) -> EnemStats:
        """Estatísticas gerais (inscritos e médias) de um ano."""
        def compute(con: duckdb.DuckDBPyConnection) -> EnemStats:
            row = con.execute(_STATS_QUERY).fetchone()
            return EnemStats(
                total_inscritos=row[0],
                media_geral=round(row[1], 2) if row[1] else 0.0,
                media_redacao=round(row[2], 2) if row[2] else 0.0,
                media_matematica=round(row[3], 2) if row[3] else 0.0,
            )

        return self._cached("stats", year, compute)

    def get_state_ranking(self, year: int, limit: int) -> list[UfRanking]:
        """Ranking de médias por UF. O ranking completo é cacheado e fatiado por limit."""
        def compute(con: duckdb.DuckDBPyConnection) -> list[UfRanking]:
            rows = con.execute(_RANKING_QUERY).fetchall()
            return [
                UfRanking(uf=uf, media=round(media, 2), total_alunos=total)
                for uf, media, total in rows
            ]

        ranking = self._cached("ranking", year, compute)
        return ranking[:limit]

    # --- Infraestrutura --------------------------------------------------

    def _parquet_path(self, year: int) -> str:
        path = os.path.join(self._root, f'enem_{year}', PARQUET_FILENAME)

        # Path Traversal Prevention (já mitigado pelo type hint 'int', mas explicitado aqui)
        if not os.path.abspath(path).startswith(self._root + os.sep):
            logger.error(f"Path Traversal detectado: {path}")
            raise DatasetNotFoundError(year)

        if not os.path.exists(path):
            raise DatasetNotFoundError(year)
        return path

    @contextmanager
    def _connection(self, parquet_path: str) -> Iterator[duckdb.DuckDBPyConnection]:
        """
        Conexão DuckDB efêmera com o Parquet registrado como a view 'enem_data'.
        O caminho entra pela API relacional do Python (nunca interpolado em SQL),
        eliminando qualquer risco de injeção, e a conexão é sempre fechada.
        """
        con = duckdb.connect(database=':memory:')
        try:
            # DDL (CREATE VIEW) não aceita prepared parameters no DuckDB; a API
            # relacional recebe o caminho como argumento Python, sem passar por SQL.
            con.register("enem_data", con.read_parquet(parquet_path))
            yield con
        finally:
            con.close()

    def _cached(self, kind: str, year: int, compute: Callable[[duckdb.DuckDBPyConnection], T]) -> T:
        parquet_path = self._parquet_path(year)
        key = (kind, year, os.path.getmtime(parquet_path))
        if key not in self._cache:
            try:
                with self._connection(parquet_path) as con:
                    self._cache[key] = compute(con)
            except Exception as exc:
                raise DataQueryError(f"Falha ao consultar '{kind}' do ano {year}: {exc}") from exc
            # Remove entradas obsoletas do mesmo (kind, year) — Parquet reprocessado
            for stale in [k for k in self._cache if k[:2] == (kind, year) and k != key]:
                del self._cache[stale]
        return self._cache[key]  # type: ignore[return-value]
