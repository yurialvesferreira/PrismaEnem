# =============================================================================
# STAGE 1: builder — instala dependências em ambiente isolado
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Instala apenas o necessário para compilar wheels nativas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Instala em uma pasta local para copiar ao stage final
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# =============================================================================
# STAGE 2: runtime — imagem final mínima, sem ferramentas de build
# =============================================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copia somente os pacotes instalados do stage anterior
COPY --from=builder /install /usr/local

# Cria um usuário não-root dedicado — sem shell, sem home, privilégios mínimos
RUN useradd --system --no-create-home --shell /usr/sbin/nologin prismauser \
    && chown -R prismauser:prismauser /app

USER prismauser

# O código é montado via volume no docker-compose (desenvolvimento).
# Em produção, descomente a linha abaixo para copiar o código na imagem:
# COPY --chown=prismauser:prismauser . .

# Sem --reload: esse flag é apenas para desenvolvimento local
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
