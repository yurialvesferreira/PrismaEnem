#!/bin/bash
set -u

# Define cores para o output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}           Iniciando Quick Start do PrismaEnem        ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Detecta o interpretador Python disponível (python3 é o padrão na maioria das distros)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Erro: Python não encontrado. Instale o Python 3.10+ para continuar.${NC}"
    exit 1
fi

# Verifica se o docker-compose está instalado
if command -v docker-compose &> /dev/null; then
    DOCKER_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_CMD="docker compose"
else
    echo -e "${RED}Erro: Docker Compose não encontrado. Instale o Docker para continuar.${NC}"
    exit 1
fi

echo -e "\n${GREEN}[1/4] Configurando Variáveis de Ambiente...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    # Gera um token aleatório para o JupyterLab em vez do placeholder do .env.example
    JUPYTER_TOKEN_GENERATED=$($PYTHON_CMD -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i.bak "s|^JUPYTER_TOKEN=.*|JUPYTER_TOKEN=${JUPYTER_TOKEN_GENERATED}|" .env && rm -f .env.bak
    echo "✅ Arquivo .env criado a partir do .env.example (token do Jupyter gerado automaticamente)."
else
    echo "✅ Arquivo .env já existe. Pulando cópia."
fi

echo -e "\n${GREEN}[2/4] Gerando Dados de Mock (Simulação)...${NC}"
# Garante que as pastas existam
mkdir -p data/raw data/processed
if ! $PYTHON_CMD src/ingestion/mock_data.py --year 2023 --rows 5000; then
    echo -e "${YELLOW}Atenção: Falha ao rodar script Python localmente. Verifique se o venv está ativo e 'requirements.txt' instalado.${NC}"
    echo "Execute: pip install -r requirements.txt"
    exit 1
fi
echo "✅ Dados mockados gerados."

echo -e "\n${GREEN}[3/4] Processando Dados (ETL com DuckDB)...${NC}"
if ! $PYTHON_CMD src/processing/process_data.py --year 2023; then
    echo -e "${YELLOW}Atenção: Falha ao processar os dados.${NC}"
    exit 1
fi
echo "✅ Dados processados e salvos em formato Parquet."

echo -e "\n${GREEN}[4/4] Subindo Infraestrutura via Docker...${NC}"
echo "Iniciando API, Frontend e JupyterLab..."
if ! $DOCKER_CMD up --build -d; then
    echo -e "${RED}Erro: Falha ao subir os containers. Verifique se o Docker está em execução.${NC}"
    exit 1
fi

# Lê o token atual do .env para exibir a URL correta do JupyterLab
JUPYTER_TOKEN_CURRENT=$(grep -E '^JUPYTER_TOKEN=' .env | cut -d '=' -f2-)

echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN} PrismaEnem rodando com sucesso! ${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "Acesse os seguintes endereços no seu navegador:\n"
echo -e "📊 Frontend (Dashboard):   http://localhost:3000"
echo -e "🔌 API Docs (Swagger):     http://localhost:8000/docs"
echo -e "🔬 JupyterLab:             http://localhost:8888/lab?token=${JUPYTER_TOKEN_CURRENT}\n"
echo -e "Para visualizar os logs, use: ${YELLOW}$DOCKER_CMD logs -f${NC}"
echo -e "Para parar os serviços, use:  ${YELLOW}$DOCKER_CMD down${NC}"
