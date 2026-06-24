# PrismaEnem — Microdados do ENEM, do Raw ao Dashboard

> **Boilerplate open-source de engenharia de dados educacionais:** ingestão, ETL com DuckDB, API FastAPI, Dashboard Next.js e análise exploratória com JupyterLab — tudo em um único `./quick_start.sh`.

---

## ✨ Visão Geral

O **PrismaEnem** transforma a complexidade dos microdados do ENEM em insights claros e acionáveis. Assim como um prisma decompõe a luz branca em suas cores constituintes, este projeto permite que desenvolvedores, cientistas de dados, gestores escolares e pesquisadores desvendem o vasto universo de informações educacionais do Brasil.

Este boilerplate foi construído com foco em **portabilidade**, **segurança by design** e **experiência "fork-and-run"**: qualquer pessoa deve conseguir clonar, executar um script e ter todo o ambiente funcional em minutos.

---

## 🚀 Quick Start (Fork & Run)

```bash
git clone https://github.com/yurialvesferreira/PrismaEnem.git
cd PrismaEnem
chmod +x quick_start.sh
./quick_start.sh
```

O script cuida de tudo: gera dados mock do ENEM, processa via DuckDB, e sobe toda a infraestrutura com Docker.

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Dashboard** | http://localhost:3000 | Interface visual Dark Mode (Next.js + Chart.js) |
| **API Docs** | http://localhost:8000/docs | Documentação interativa gerada pelo FastAPI |
| **JupyterLab** | http://localhost:8888 | Análise exploratória dos dados processados |

> **Token do JupyterLab:** definido pela variável `JUPYTER_TOKEN` no seu `.env` (padrão: `prisma_secret_token_123`).

---

## 💡 Funcionalidades Principais

| Camada | O que faz |
|--------|-----------|
| **Ingestão** | Download automatizado dos ZIPs do INEP **ou** geração de dados mock para testes sem baixar ~4GB |
| **ETL (DuckDB)** | Pipeline de transformação que lê os CSVs brutos e gera arquivos `.parquet` otimizados para consultas analíticas |
| **API (FastAPI)** | Endpoints REST para estatísticas nacionais e ranking por estado, com documentação automática em `/docs` |
| **Dashboard (Next.js)** | Interface Dark Mode com comparativo da sua escola vs. média nacional e ranking de UFs via Chart.js |
| **JupyterLab** | Container pronto para análise exploratória nos Parquets gerados, sem configuração adicional |

---

## 🏗️ Arquitetura

O PrismaEnem adota o modelo **Data Lakehouse local**:

```
INEP (ZIP/CSV)
     │
     ▼
[data/raw/]           ← Dados brutos (ignorados pelo Git)
     │
     ▼
DuckDB ETL            ← process_data.py transforma e agrega
     │
     ▼
[data/processed/]     ← Arquivos .parquet (ignorados pelo Git)
     │
     ▼
FastAPI               ← Lê os Parquets, expõe via REST
     │
     ▼
Next.js Dashboard     ← Consome a API, renderiza visualizações
```

**Por que DuckDB + Parquet?**
- DuckDB executa queries analíticas in-process, sem servidor — ideal para ambientes single-node.
- Parquet reduz o tamanho dos dados em até 10x comparado ao CSV e acelera queries em colunas específicas.

---

## 🛠️ Stack Tecnológico

| Camada | Tecnologia implementada | Possíveis substituições |
|--------|------------------------|-------------------------|
| **Ingestão** | Python (`requests`, `zipfile`) | Airflow, Prefect, Dagster |
| **Armazenamento Bruto** | Disco local (`data/raw/`) | AWS S3, Google Cloud Storage |
| **Processamento (ETL)** | DuckDB + Polars | Dask, Apache Spark |
| **Armazenamento Processado** | Parquet local (`data/processed/`) | BigQuery, Redshift, Snowflake |
| **API** | FastAPI + Uvicorn | Flask, Django REST, Go Gin |
| **Frontend** | Next.js + Tailwind CSS + Chart.js | React (CRA), Vue.js |
| **Notebooks** | JupyterLab | VS Code Notebooks |
| **Orquestração** | Docker Compose | Kubernetes, AWS ECS |
| **Config Management** | Pydantic Settings + `.env` | — |

---

## 📂 Estrutura do Projeto

```text
PrismaEnem/
├── data/
│   ├── raw/                  # Microdados originais ou mocks CSV (não versionados)
│   └── processed/            # Arquivos .parquet gerados pelo DuckDB (não versionados)
│
├── src/
│   ├── ingestion/
│   │   ├── download_data.py  # Download dos ZIPs do INEP com barra de progresso
│   │   └── mock_data.py      # Gerador de dados simulados para testes offline
│   ├── processing/
│   │   └── process_data.py   # Pipeline ETL: CSV → DuckDB → Parquet
│   ├── api/
│   │   └── main.py           # API FastAPI com endpoints /stats e /states
│   └── frontend/
│       ├── .env.local.example # Template de variáveis para o Next.js
│       └── src/
│           ├── app/           # Rotas Next.js App Router (page.tsx — Dashboard)
│           └── components/    # Componentes UI reutilizáveis (Chart.tsx)
│
├── config/
│   └── settings.py           # Central de configurações via Pydantic + .env
│
├── docs/                      # Assets de documentação
├── quick_start.sh             # Script end-to-end: mock → ETL → Docker up
├── docker-compose.yml         # Orquestra API + Frontend + JupyterLab
├── Dockerfile                 # Multi-stage build para a API (non-root)
├── requirements.txt           # Dependências Python
├── .env.example               # Template de variáveis de ambiente
├── .gitignore                 # Protege .env e dados brutos de serem commitados
├── SECURITY.md                # Política de segurança e decisões arquiteturais
└── README.md                  # Este arquivo
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

Copie o `.env.example` e ajuste conforme necessário:

```bash
cp .env.example .env
```

As variáveis mais relevantes:

```ini
# Caminhos dos dados (relativos à raiz do projeto)
DATA_DIR=./data
RAW_DATA_DIR=./data/raw
PROCESSED_DATA_DIR=./data/processed

# URL base dos microdados do INEP
INEP_DATA_URL_BASE=https://download.inep.gov.br/microdados/

# CORS — em produção, restrinja ao seu domínio
# CORS_ORIGINS=["https://meusite.com.br"]

# JupyterLab — altere para um token seguro em produção
JUPYTER_TOKEN=prisma_secret_token_123

# Next.js — URL da API consumida pelo Dashboard
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Frontend local (sem Docker)

```bash
cd src/frontend
cp .env.local.example .env.local
npm install
npm run dev
```

---

## 🔧 Uso Manual (Alternativa ao quick_start.sh)

**1. Gerar dados mock (sem baixar do INEP):**
```bash
python src/ingestion/mock_data.py --year 2023 --rows 5000
```

**2. Baixar dados reais do INEP (~4 GB):**
```bash
python src/ingestion/download_data.py --year 2023
```

**3. Processar os dados (CSV → Parquet via DuckDB):**
```bash
python src/processing/process_data.py --year 2023
```

**4. Subir toda a infraestrutura:**
```bash
docker-compose up --build
```

---

## 🔒 Segurança

O PrismaEnem foi construído com **segurança by design**. Entre as medidas implementadas:

- ✅ **Sem SQL Injection:** queries DuckDB usam o padrão View Registration + bind parameters (`?`) — nenhuma variável externa é interpolada em SQL.
- ✅ **Sem Information Disclosure:** erros internos são logados no servidor, o cliente recebe apenas mensagens genéricas.
- ✅ **CORS restritivo:** origens permitidas configuráveis via `.env`, sem `"*"` hardcoded.
- ✅ **Docker non-root:** container roda como `prismauser` (sem shell, sem home) em imagem multi-stage.
- ✅ **Secrets protegidos:** `.env` e dados brutos nunca são commitados (`.gitignore` rigoroso).

Para o relatório completo, consulte o [`SECURITY.md`](./SECURITY.md).

---

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do repositório.
2. Crie uma branch para sua feature: `git checkout -b feature/minha-feature`
3. Implemente e documente suas mudanças.
4. Faça commit seguindo o padrão Conventional Commits: `git commit -m 'feat: adiciona suporte ao ano X'`
5. Abra um Pull Request descrevendo o problema resolvido e o impacto da mudança.

> Encontrou uma vulnerabilidade de segurança? **Não abra uma issue pública.** Consulte as instruções de responsible disclosure no [`SECURITY.md`](./SECURITY.md).

---

## 🔗 Referências

- [Microdados ENEM — Portal Gov.br](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

---

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
