import os
import argparse
import duckdb
import time

def process_enem_data(year: int):
    """
    Lê os dados brutos (CSV), realiza transformações básicas e 
    salva em formato Parquet no diretório processed.
    """
    raw_csv_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'data', 'raw', 
        f'enem_{year}', 'DADOS', f'MICRODADOS_ENEM_{year}.csv'
    )
    
    processed_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed', f'enem_{year}')
    os.makedirs(processed_dir, exist_ok=True)
    parquet_output_path = os.path.join(processed_dir, 'enem_processed.parquet')

    if not os.path.exists(raw_csv_path):
        print(f"Erro: Arquivo bruto não encontrado em {raw_csv_path}")
        print("Dica: Execute o script de ingestão (ou de mock) primeiro.")
        return

    print(f"Iniciando processamento dos dados do ENEM {year} com DuckDB...")
    start_time = time.time()

    # Conectar ao DuckDB em memória
    con = duckdb.connect(database=':memory:')

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
            COALESCE(NU_NOTA_CN, 0) as NU_NOTA_CN,
            COALESCE(NU_NOTA_CH, 0) as NU_NOTA_CH,
            COALESCE(NU_NOTA_LC, 0) as NU_NOTA_LC,
            COALESCE(NU_NOTA_MT, 0) as NU_NOTA_MT,
            COALESCE(NU_NOTA_REDACAO, 0) as NU_NOTA_REDACAO,
            -- Cria uma nota média geral
            (COALESCE(NU_NOTA_CN, 0) + COALESCE(NU_NOTA_CH, 0) + 
             COALESCE(NU_NOTA_LC, 0) + COALESCE(NU_NOTA_MT, 0) + 
             COALESCE(NU_NOTA_REDACAO, 0)) / 5.0 as MEDIA_GERAL
        FROM read_csv_auto('{raw_csv_path}', sep=';', all_varchar=1)
        WHERE NU_INSCRICAO IS NOT NULL
    ) TO '{parquet_output_path}' (FORMAT PARQUET, COMPRESSION 'SNAPPY');
    """

    con.execute(query)
    
    end_time = time.time()
    print(f"Processamento concluído em {end_time - start_time:.2f} segundos.")
    print(f"Dados salvos em: {parquet_output_path}")

def main():
    parser = argparse.ArgumentParser(description="Processa os microdados brutos do ENEM e converte para Parquet.")
    parser.add_argument("--year", type=int, default=2023, help="Ano do ENEM a ser processado (ex: 2023)")
    args = parser.parse_args()

    process_enem_data(args.year)

if __name__ == "__main__":
    main()
