from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Configurações gerais do projeto carregadas do .env
    """
    # extra="ignore": o .env contém variáveis de outros serviços (JUPYTER_TOKEN,
    # NEXT_PUBLIC_API_URL) que não pertencem à API e não devem derrubá-la no startup.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

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

    # Security
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

settings = Settings()
