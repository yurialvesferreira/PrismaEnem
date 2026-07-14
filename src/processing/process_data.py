import os
import argparse
import duckdb
import time
import sys

# Adiciona o diretório raiz ao PYTHONPATH para importar configurações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from config.settings import settings

def process_enem_data(year: int) -> bool:
    """
    Lê os dados brutos (CSV), realiza transformações básicas e
    salva em formato Parquet no diretório processed.
    Retorna True em caso de sucesso.
    """
    raw_csv_path = os.path.join(
        os.path.abspath(settings.raw_data_dir),
        f'enem_{year}', 'DADOS', f'MICRODADOS_ENEM_{year}.csv'
    )

    processed_dir = os.path.join(os.path.abspath(settings.processed_data_dir), f'enem_{year}')
    os.makedirs(processed_dir, exist_ok=True)
    parquet_output_path = os.path.join(processed_dir, 'enem_processed.parquet')

    if not os.path.exists(raw_csv_path):
        print(f"Erro: Arquivo bruto não encontrado em {raw_csv_path}")
        print("Dica: Execute o script de ingestão (ou de mock) primeiro.")
        return False

    # Os caminhos vêm das configurações + ano (int), mas o COPY do DuckDB não aceita
    # bind params — rejeitamos aspas para impedir qualquer quebra do literal SQL.
    for path in (raw_csv_path, parquet_output_path):
        if "'" in path:
            print(f"Erro: caminho com caractere inválido (aspas simples): {path}")
            return False

    print(f"Iniciando processamento dos dados do ENEM {year} com DuckDB...")
    start_time = time.time()

    # Consulta ETL básica com DuckDB
    # - Lê o CSV delimitado por ';'
    # - Filtra notas válidas ou substitui nulos por 0
    # - Grava no formato parquet comprimido (snappy)

    query = f"""
    COPY (
        SELECT
            NU_INSCRICAO,
            NU_ANO,
            TP_FAIXA_ETARIA,
            TP_SEXO,
            TP_ESTADO_CIVIL,
            TP_COR_RACA,
            TP_ESCOLA,
            SG_UF_ESC,
            TP_DEPENDENCIA_ADM_ESC,
            TP_LOCALIZACAO_ESC,
            -- O CSV é lido com all_varchar=1: TRY_CAST converte as notas para
            -- DOUBLE (valores inválidos viram NULL) e o COALESCE zera os nulos.
            COALESCE(TRY_CAST(NU_NOTA_CN AS DOUBLE), 0) as NU_NOTA_CN,
            COALESCE(TRY_CAST(NU_NOTA_CH AS DOUBLE), 0) as NU_NOTA_CH,
            COALESCE(TRY_CAST(NU_NOTA_LC AS DOUBLE), 0) as NU_NOTA_LC,
            COALESCE(TRY_CAST(NU_NOTA_MT AS DOUBLE), 0) as NU_NOTA_MT,
            COALESCE(TRY_CAST(NU_NOTA_REDACAO AS DOUBLE), 0) as NU_NOTA_REDACAO,
            -- Cria uma nota média geral
            (COALESCE(TRY_CAST(NU_NOTA_CN AS DOUBLE), 0) + COALESCE(TRY_CAST(NU_NOTA_CH AS DOUBLE), 0) +
             COALESCE(TRY_CAST(NU_NOTA_LC AS DOUBLE), 0) + COALESCE(TRY_CAST(NU_NOTA_MT AS DOUBLE), 0) +
             COALESCE(TRY_CAST(NU_NOTA_REDACAO AS DOUBLE), 0)) / 5.0 as MEDIA_GERAL
        FROM read_csv_auto('{raw_csv_path}', sep=';', all_varchar=1)
        WHERE NU_INSCRICAO IS NOT NULL
    ) TO '{parquet_output_path}' (FORMAT PARQUET, COMPRESSION 'SNAPPY');
    """

    con = duckdb.connect(database=':memory:')
    try:
        con.execute(query)
    finally:
        con.close()

    end_time = time.time()
    print(f"Processamento concluído em {end_time - start_time:.2f} segundos.")
    print(f"Dados salvos em: {parquet_output_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Processa os microdados brutos do ENEM e converte para Parquet.")
    parser.add_argument("--year", type=int, default=2023, help="Ano do ENEM a ser processado (ex: 2023)")
    args = parser.parse_args()

    if not process_enem_data(args.year):
        sys.exit(1)

if __name__ == "__main__":
    main()
