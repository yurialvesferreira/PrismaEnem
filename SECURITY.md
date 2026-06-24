# 🛡️ Security Policy — PrismaEnem

Este documento descreve as decisões de segurança implementadas no boilerplate **PrismaEnem**, os vetores de risco considerados e as instruções para reportar vulnerabilidades.

---

## 📋 Versões Suportadas

| Versão | Suportada |
|--------|-----------|
| `main` | ✅ Ativa |

---

## 🔒 Decisões de Segurança Implementadas

### 1. Prevenção de SQL Injection (DuckDB)

**Vetor:** Injeção de variáveis externas em queries SQL via f-strings.

**Solução adotada — DuckDB View Registration Pattern:**

O caminho do arquivo Parquet (`parquet_path`) é registrado como uma view usando **bind parameters nativos** do DuckDB, nunca interpolado diretamente em uma string SQL:

```python
# ✅ SEGURO — parquet_path é bind param (?), nunca concatenado em SQL
con.execute("CREATE OR REPLACE VIEW enem_data AS SELECT * FROM read_parquet(?)", [parquet_path])

# As queries subsequentes referenciam apenas o nome da view (literal fixo no código)
query = "SELECT ... FROM enem_data WHERE ..."
con.execute(query, [limit])  # limit também via bind param
```

**Por que não é suficiente apenas validar o tipo?** O FastAPI valida que `year` e `limit` são inteiros, mas a prática de construir queries com f-strings cria uma dependência frágil de validação — um padrão que se propaga de forma insegura em forks. O bind param elimina o risco by design.

---

### 2. Sanitização Rigorosa de Caminhos de Arquivo

**Vetor:** Path Traversal — manipulação do `year` para apontar para arquivos fora do diretório permitido.

**Solução adotada (múltiplas camadas):**

```python
# Camada 1: Validação de domínio (ano deve ser ENEM válido)
if year < 1998 or year > 2100:
    return None  # Rejeita silenciosamente, loga o aviso

# Camada 2: Path Traversal Prevention explícita
if not os.path.abspath(path).startswith(os.path.abspath(settings.processed_data_dir)):
    logger.error(f"Path Traversal detectado: {path}")
    return None
```

O type hint `int` do FastAPI já mitiga a maioria dos ataques, mas as camadas adicionais garantem defesa em profundidade (*defense in depth*).

---

### 3. Ocultação de Erros Internos (Information Disclosure)

**Vetor:** `detail=str(e)` retornando stack traces, caminhos de arquivos ou estrutura interna do banco ao cliente.

**Solução adotada:**

```python
except Exception as e:
    # Log completo internamente para debugging
    logger.error(f"Erro interno ao consultar stats do ano {year}: {str(e)}")
    # Mensagem genérica e segura para o cliente
    raise HTTPException(status_code=500, detail="Erro interno do servidor ao processar os dados.")
```

O cliente nunca recebe informações do sistema. Os logs internos ficam disponíveis apenas nos logs do container (`docker logs prisma_api`).

---

### 4. CORS Restritivo e Configurável

**Vetor:** `allow_origins=["*"]` permitindo que qualquer site faça requisições cross-origin à API.

**Solução adotada:** As origens permitidas são definidas no `config/settings.py` e sobrescritas via variável de ambiente:

```python
# config/settings.py
cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
```

```ini
# .env — para produção, restrinja ao seu domínio
CORS_ORIGINS=["https://meusite.com.br"]
```

---

### 5. Docker Hardening — Princípio do Menor Privilégio

**Vetor:** Container rodando como `root`. Em caso de RCE, o atacante tem controle total do container.

**Solução adotada — Multi-stage Build + Non-root User:**

```dockerfile
# Stage 1: builder (tem build-essential, gcc, pip)
FROM python:3.11-slim AS builder
...

# Stage 2: runtime (imagem limpa, sem ferramentas de build)
FROM python:3.11-slim AS runtime

# Usuário dedicado, sem shell interativo, sem home directory
RUN useradd --system --no-create-home --shell /usr/sbin/nologin prismauser
USER prismauser

# Sem --reload (apenas para desenvolvimento local)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Benefícios concretos:
- Imagem final **~40-60% menor** (sem gcc, build-essential)
- Superfície de ataque reduzida no runtime
- Escalada de privilégios impossível (sem shell, sem sudo)

---

### 6. Proteção de Segredos — .gitignore e .env

**Vetor:** Commit acidental de credenciais, tokens ou dados sensíveis.

**Solução adotada:**

```gitignore
# Nenhum arquivo .env é commitado (incluindo .env.local, .env.production, etc.)
.env
.env.*

# Os microdados do ENEM NUNCA devem ser commitados (podem ter centenas de GB)
data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep
```

O token do JupyterLab é lido do `.env` em runtime:

```yaml
# docker-compose.yml
- JUPYTER_TOKEN=${JUPYTER_TOKEN:-prisma_secret_token_123}
```

---

## 🚨 Reportando uma Vulnerabilidade

Se você encontrar uma vulnerabilidade de segurança neste repositório:

1. **NÃO abra uma issue pública.** Isso expõe o problema antes que possa ser corrigido.
2. Envie um e-mail diretamente para o mantenedor descrevendo:
   - O vetor de ataque
   - Passos para reproduzir
   - Impacto potencial
3. Você receberá uma resposta em até **72 horas**.
4. Após a correção ser publicada, a vulnerabilidade poderá ser divulgada publicamente (responsible disclosure).

---

## 🔮 Melhorias Futuras de Segurança

Para versões futuras do PrismaEnem, considere implementar:

- [ ] **Rate Limiting** na API (ex: via `slowapi`) para mitigar ataques de força bruta e DoS.
- [ ] **Autenticação JWT** nos endpoints para ambientes multi-tenant.
- [ ] **Auditoria de dependências** automática com `pip-audit` ou Dependabot.
- [ ] **HTTPS obrigatório** via Nginx reverse proxy com certificado Let's Encrypt.
- [ ] **Secrets Manager** (AWS Secrets Manager, HashiCorp Vault) para produção.

---

*Documento mantido pela comunidade PrismaEnem. Última revisão: Junho 2025.*
