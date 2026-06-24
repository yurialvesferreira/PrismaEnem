import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Configurações gerais do projeto carregadas do .env
    """
    inep_data_url_base: str = "https://download.inep.gov.br/microdados/"
    
    # Cloud Config (Opcionais para MVP local)
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"
    bigquery_project_id: str | None = None

    # Local Paths
    data_dir: str = "./data"
    raw_data_dir: str = "./data/raw"
    processed_data_dir: str = "./data/processed"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
