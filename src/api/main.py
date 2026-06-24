from fastapi import FastAPI, HTTPException, Query
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

def get_db_connection():
    # Cria uma conexão duckdb para consultas
    return duckdb.connect(database=':memory:', read_only=False)

def get_parquet_path(year: int):
    # Sanitização: Garantir que year seja um ano válido para evitar manipulações absurdas de path
    if year < 1998 or year > 2100:
        logger.warning(f"Tentativa de acesso com ano inválido: {year}")
        return None

    path = os.path.join(
        os.path.abspath(settings.processed_data_dir), 
        f'enem_{year}', 'enem_processed.parquet'
    )
    
    # Path Traversal Prevention (já mitigado pelo type hint 'int', mas explicitado aqui)
    if not os.path.abspath(path).startswith(os.path.abspath(settings.processed_data_dir)):
        logger.error(f"Path Traversal detectado: {path}")
        return None

    if not os.path.exists(path):
        return None
    return path

class StatsResponse(BaseModel):
    total_inscritos: int
    media_geral: float
    media_redacao: float
    media_matematica: float

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à PrismaEnem API! Acesse /docs para ver a documentação."}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/v1/enem/{year}/stats", response_model=StatsResponse)
def get_enem_stats(year: int):
    """Retorna estatísticas gerais do ENEM para um ano específico."""
    parquet_path = get_parquet_path(year)
    if not parquet_path:
        raise HTTPException(status_code=404, detail=f"Dados processados do ano {year} não encontrados.")

    try:
        con = get_db_connection()
        query = f"""
            SELECT 
                COUNT(*) as total_inscritos,
                AVG(CAST(MEDIA_GERAL AS FLOAT)) as media_geral,
                AVG(CAST(NU_NOTA_REDACAO AS FLOAT)) as media_redacao,
                AVG(CAST(NU_NOTA_MT AS FLOAT)) as media_matematica
            FROM read_parquet('{parquet_path}')
            WHERE MEDIA_GERAL > 0
        """
        result = con.execute(query).fetchone()
        
        return StatsResponse(
            total_inscritos=result[0],
            media_geral=round(result[1], 2) if result[1] else 0.0,
            media_redacao=round(result[2], 2) if result[2] else 0.0,
            media_matematica=round(result[3], 2) if result[3] else 0.0
        )
    except Exception as e:
        logger.error(f"Erro interno ao consultar stats do ano {year}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor ao processar os dados.")

@app.get("/api/v1/enem/{year}/states")
def get_enem_states_ranking(year: int, limit: int = Query(10, description="Número de estados a retornar")):
    """Retorna o ranking de médias gerais por estado (UF)."""
    parquet_path = get_parquet_path(year)
    if not parquet_path:
        raise HTTPException(status_code=404, detail=f"Dados processados do ano {year} não encontrados.")

    try:
        con = get_db_connection()
        query = f"""
            SELECT 
                SG_UF_ESC as uf,
                AVG(CAST(MEDIA_GERAL AS FLOAT)) as media,
                COUNT(*) as total_alunos
            FROM read_parquet('{parquet_path}')
            WHERE SG_UF_ESC IS NOT NULL AND MEDIA_GERAL > 0
            GROUP BY SG_UF_ESC
            ORDER BY media DESC
            LIMIT ?
        """
        # Usando bind parameters (?) para injetar o LIMIT de forma segura
        df = con.execute(query, [limit]).df()
        
        # Converte o DataFrame do pandas para uma lista de dicionários
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Erro interno ao consultar states do ano {year} com limit {limit}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor ao buscar ranking.")

if __name__ == "__main__":
    import uvicorn
    # Para rodar manualmente: python -m src.api.main
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
