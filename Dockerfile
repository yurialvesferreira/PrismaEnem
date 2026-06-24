FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema necessárias para compilar alguns pacotes se preciso
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# O código-fonte será montado via volume no docker-compose para fins de desenvolvimento.
# Para produção, você deve descomentar a linha abaixo.
# COPY . .

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
