from contextlib import contextmanager
from typing import Annotated, Iterator

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import duckdb
import os
import sys
import logging

# Configuração do Logger de Segurança
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adiciona o diretório raiz ao PYTHONPATH para importar configurações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from config.settings import settings

MIN_YEAR = 1998
MAX_YEAR = 2100
PARQUET_FILENAME = "enem_processed.parquet"
# 26 estados + DF
MAX_UF_LIMIT = 27

NOT_FOUND_RESPONSE = {404: {"description": "Dados processados do ano não encontrados."}}
ERROR_RESPONSES = {
    **NOT_FOUND_RESPONSE,
    500: {"description": "Erro interno do servidor."},
}

YearParam = Annotated[int, Path(ge=MIN_YEAR, le=MAX_YEAR, description="Ano do ENEM")]

app = FastAPI(
    title="PrismaEnem API",
    description="API de acesso aos microdados processados do ENEM.",
    version="1.0.0"
)

# Adiciona CORS para permitir acesso restrito do frontend (configurado no settings.py)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_parquet_path(year: int) -> str:
    """Resolve o caminho do Parquet processado ou levanta 404."""
    processed_root = os.path.abspath(settings.processed_data_dir)
    path = os.path.join(processed_root, f'enem_{year}', PARQUET_FILENAME)

    # Path Traversal Prevention (já mitigado pelo type hint 'int', mas explicitado aqui)
    if not os.path.abspath(path).startswith(processed_root + os.sep):
        logger.error(f"Path Traversal detectado: {path}")
        raise HTTPException(status_code=404, detail=f"Dados processados do ano {year} não encontrados.")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Dados processados do ano {year} não encontrados.")
    return path


@contextmanager
def enem_connection(parquet_path: str) -> Iterator[duckdb.DuckDBPyConnection]:
    """
    Abre uma conexão DuckDB efêmera com o Parquet registrado como a view 'enem_data'.
    O caminho entra pela API relacional do Python (nunca interpolado em SQL),
    eliminando qualquer risco de injeção, e a conexão é sempre fechada ao final.
    """
    con = duckdb.connect(database=':memory:')
    try:
        # DDL (CREATE VIEW) não aceita prepared parameters no DuckDB; a API
        # relacional recebe o caminho como argumento Python, sem passar por SQL.
        con.register("enem_data", con.read_parquet(parquet_path))
        yield con
    finally:
        con.close()


class StatsResponse(BaseModel):
    total_inscritos: int
    media_geral: float
    media_redacao: float
    media_matematica: float


class StateRanking(BaseModel):
    uf: str
    media: float
    total_alunos: int


class YearsResponse(BaseModel):
    years: list[int]


@app.get("/")
def read_root():
    return {"message": "Bem-vindo à PrismaEnem API! Acesse /docs para ver a documentação."}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/v1/enem/years", response_model=YearsResponse)
def list_available_years():
    """Lista os anos com dados processados disponíveis para consulta."""
    processed_root = os.path.abspath(settings.processed_data_dir)
    years: list[int] = []
    if os.path.isdir(processed_root):
        for entry in os.listdir(processed_root):
            prefix, _, suffix = entry.partition('_')
            if prefix == 'enem' and suffix.isdigit() and \
                    os.path.exists(os.path.join(processed_root, entry, PARQUET_FILENAME)):
                years.append(int(suffix))
    return YearsResponse(years=sorted(years))


@app.get("/api/v1/enem/{year}/stats", response_model=StatsResponse, responses=ERROR_RESPONSES)
def get_enem_stats(year: YearParam):
    """Retorna estatísticas gerais do ENEM para um ano específico."""
    parquet_path = get_parquet_path(year)

    try:
        with enem_connection(parquet_path) as con:
            # Query usa apenas o nome da view (literal fixo), sem interpolação de variáveis externas
            query = """
                SELECT
                    COUNT(*) as total_inscritos,
                    AVG(CAST(MEDIA_GERAL AS FLOAT)) as media_geral,
                    AVG(CAST(NU_NOTA_REDACAO AS FLOAT)) as media_redacao,
                    AVG(CAST(NU_NOTA_MT AS FLOAT)) as media_matematica
                FROM enem_data
                WHERE MEDIA_GERAL > 0
            """
            result = con.execute(query).fetchone()

        return StatsResponse(
            total_inscritos=result[0],
            media_geral=round(result[1], 2) if result[1] else 0.0,
            media_redacao=round(result[2], 2) if result[2] else 0.0,
            media_matematica=round(result[3], 2) if result[3] else 0.0
        )
    except Exception:
        logger.exception(f"Erro interno ao consultar stats do ano {year}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor ao processar os dados.")


@app.get("/api/v1/enem/{year}/states", response_model=list[StateRanking], responses=ERROR_RESPONSES)
def get_enem_states_ranking(
    year: YearParam,
    limit: Annotated[int, Query(ge=1, le=MAX_UF_LIMIT, description="Número de estados a retornar")] = 10,
):
    """Retorna o ranking de médias gerais por estado (UF)."""
    parquet_path = get_parquet_path(year)

    try:
        with enem_connection(parquet_path) as con:
            # Query usa apenas o nome da view e bind param para LIMIT — sem interpolação externa
            query = """
                SELECT
                    SG_UF_ESC as uf,
                    AVG(CAST(MEDIA_GERAL AS FLOAT)) as media,
                    COUNT(*) as total_alunos
                FROM enem_data
                WHERE SG_UF_ESC IS NOT NULL AND MEDIA_GERAL > 0
                GROUP BY SG_UF_ESC
                ORDER BY media DESC
                LIMIT ?
            """
            rows = con.execute(query, [limit]).fetchall()

        return [StateRanking(uf=uf, media=round(media, 2), total_alunos=total) for uf, media, total in rows]
    except Exception:
        logger.exception(f"Erro interno ao consultar states do ano {year} com limit {limit}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor ao buscar ranking.")


if __name__ == "__main__":
    import uvicorn
    # Para rodar manualmente: python -m src.api.main
    # Bind local por segurança; em containers o host é definido no CMD do Dockerfile.
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
