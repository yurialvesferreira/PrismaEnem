#!/bin/bash

# Define cores para o output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}           Iniciando Quick Start do PrismaEnem        ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Verifica se o docker-compose está instalado
if ! command -v docker-compose &> /dev/null
then
    echo -e "${YELLOW}Aviso: 'docker-compose' não foi encontrado. Tentando usar 'docker compose'...${NC}"
    DOCKER_CMD="docker compose"
else
    DOCKER_CMD="docker-compose"
fi

echo -e "\n${GREEN}[1/4] Configurando Variáveis de Ambiente...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Arquivo .env criado a partir do .env.example."
else
    echo "✅ Arquivo .env já existe. Pulando cópia."
fi

echo -e "\n${GREEN}[2/4] Gerando Dados de Mock (Simulação)...${NC}"
# Garante que as pastas existam
mkdir -p data/raw data/processed
# Instala requirements mínimos locais para rodar o script se necessário, 
# mas vamos assumir que o ambiente local já tenha as deps base do python ou roda via docker.
# Como é um quick start, vamos rodar os scripts python assumindo ambiente local.
python src/ingestion/mock_data.py --year 2023 --rows 5000
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Atenção: Falha ao rodar script Python localmente. Verifique se o venv está ativo e 'requirements.txt' instalado.${NC}"
    echo "Execute: pip install -r requirements.txt"
    exit 1
fi
echo "✅ Dados mockados gerados."

echo -e "\n${GREEN}[3/4] Processando Dados (ETL com DuckDB)...${NC}"
python src/processing/process_data.py --year 2023
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Atenção: Falha ao processar os dados.${NC}"
    exit 1
fi
echo "✅ Dados processados e salvos em formato Parquet."

echo -e "\n${GREEN}[4/4] Subindo Infraestrutura via Docker...${NC}"
echo "Iniciando API, Frontend e JupyterLab..."
$DOCKER_CMD up --build -d

echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN} PrismaEnem rodando com sucesso! ${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "Acesse os seguintes endereços no seu navegador:\n"
echo -e "📊 Frontend (Dashboard):   http://localhost:3000"
echo -e "🔌 API Docs (Swagger):     http://localhost:8000/docs"
echo -e "🔬 JupyterLab:             http://localhost:8888/lab?token=prisma\n"
echo -e "Para visualizar os logs, use: ${YELLOW}$DOCKER_CMD logs -f${NC}"
echo -e "Para parar os serviços, use:  ${YELLOW}$DOCKER_CMD down${NC}"
