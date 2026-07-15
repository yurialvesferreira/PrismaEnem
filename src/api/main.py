from dataclasses import asdict
from typing import Annotated

from fastapi import Depends, FastAPI, Path, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import sys
import logging

# Configuração do Logger de Segurança
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adiciona o diretório raiz ao PYTHONPATH para importar configurações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from config.settings import settings
from src.api.repository import (
    MAX_UF_LIMIT,
    DataQueryError,
    DatasetNotFoundError,
    EnemRepository,
)

MIN_YEAR = 1998
MAX_YEAR = 2100

# Os agregados são imutáveis entre execuções do ETL — clientes e proxies podem
# cacheá-los com segurança. A lista de anos muda quando um novo ETL roda,
# então recebe um TTL curto.
CACHE_CONTROL_DATA = "public, max-age=3600"
CACHE_CONTROL_YEARS = "public, max-age=60"

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

_repository = EnemRepository(settings.processed_data_dir)


def get_repository() -> EnemRepository:
    """Dependência injetável — substituível nos testes via app.dependency_overrides."""
    return _repository


RepositoryDep = Annotated[EnemRepository, Depends(get_repository)]


# --- Exception handlers globais -------------------------------------------
# Centralizam o contrato de erro da API: endpoints não repetem try/except e
# nenhum detalhe interno (stack trace, caminhos) vaza para o cliente.

@app.exception_handler(DatasetNotFoundError)
async def dataset_not_found_handler(request: Request, exc: DatasetNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DataQueryError)
async def data_query_error_handler(request: Request, exc: DataQueryError):
    # Log completo internamente para debugging; mensagem genérica para o cliente
    logger.error("Erro interno ao consultar dados: %s", exc, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor ao processar os dados."},
    )


# --- Modelos de resposta ----------------------------------------------------

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


# --- Rotas -------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à PrismaEnem API! Acesse /docs para ver a documentação."}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/v1/enem/years", response_model=YearsResponse)
def list_available_years(repo: RepositoryDep, response: Response):
    """Lista os anos com dados processados disponíveis para consulta."""
    response.headers["Cache-Control"] = CACHE_CONTROL_YEARS
    return YearsResponse(years=repo.available_years())


@app.get("/api/v1/enem/{year}/stats", response_model=StatsResponse, responses=ERROR_RESPONSES)
def get_enem_stats(year: YearParam, repo: RepositoryDep, response: Response):
    """Retorna estatísticas gerais do ENEM para um ano específico."""
    stats = repo.get_stats(year)
    response.headers["Cache-Control"] = CACHE_CONTROL_DATA
    return StatsResponse(**asdict(stats))


@app.get("/api/v1/enem/{year}/states", response_model=list[StateRanking], responses=ERROR_RESPONSES)
def get_enem_states_ranking(
    year: YearParam,
    repo: RepositoryDep,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=MAX_UF_LIMIT, description="Número de estados a retornar")] = 10,
):
    """Retorna o ranking de médias gerais por estado (UF)."""
    ranking = repo.get_state_ranking(year, limit)
    response.headers["Cache-Control"] = CACHE_CONTROL_DATA
    return [StateRanking(**asdict(entry)) for entry in ranking]


if __name__ == "__main__":
    import uvicorn
    # Para rodar manualmente: python -m src.api.main
    # Bind local por segurança; em containers o host é definido no CMD do Dockerfile.
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
