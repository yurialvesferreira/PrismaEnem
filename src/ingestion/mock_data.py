import os
import argparse
import csv
import random

def create_mock_csv(year: int, num_rows: int, output_dir: str):
    """Cria um CSV com dados simulados do ENEM para testes locais do boilerplate."""
    print(f"Gerando {num_rows} linhas de mock data para o ENEM {year}...")
    
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f'MICRODADOS_ENEM_{year}.csv')

    headers = [
        'NU_INSCRICAO', 'NU_ANO', 'TP_FAIXA_ETARIA', 'TP_SEXO', 
        'TP_ESTADO_CIVIL', 'TP_COR_RACA', 'TP_NACIONALIDADE', 
        'TP_ST_CONCLUSAO', 'TP_ANO_CONCLUIU', 'TP_ESCOLA', 
        'SG_UF_ESC', 'TP_DEPENDENCIA_ADM_ESC', 'TP_LOCALIZACAO_ESC',
        'NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT', 'NU_NOTA_REDACAO'
    ]

    ufs = ['SP', 'MG', 'RJ', 'BA', 'RS', 'PR', 'PE', 'CE', 'PA', 'SC', 'GO', 'MA', 'PB', 'ES', 'AM', 'RN', 'AL', 'PI', 'MT', 'MS', 'SE', 'RO', 'TO', 'AC', 'AP', 'RR']

    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(headers)

        for i in range(num_rows):
            row = [
                f"{year}{str(i).zfill(8)}",  # NU_INSCRICAO
                year,                         # NU_ANO
                random.randint(1, 20),        # TP_FAIXA_ETARIA
                random.choice(['M', 'F']),    # TP_SEXO
                random.randint(0, 4),         # TP_ESTADO_CIVIL
                random.randint(0, 5),         # TP_COR_RACA
                random.randint(0, 4),         # TP_NACIONALIDADE
                random.randint(1, 4),         # TP_ST_CONCLUSAO
                random.randint(0, 16),        # TP_ANO_CONCLUIU
                random.randint(1, 3),         # TP_ESCOLA
                random.choice(ufs),           # SG_UF_ESC
                random.randint(1, 4),         # TP_DEPENDENCIA_ADM_ESC
                random.randint(1, 2),         # TP_LOCALIZACAO_ESC
                round(random.uniform(300, 800), 1), # NU_NOTA_CN
                round(random.uniform(300, 850), 1), # NU_NOTA_CH
                round(random.uniform(300, 800), 1), # NU_NOTA_LC
                round(random.uniform(300, 950), 1), # NU_NOTA_MT
                random.choice([0, 300, 500, 600, 700, 800, 900, 920, 940, 960, 980, 1000]) # NU_NOTA_REDACAO
            ]
            writer.writerow(row)

    print(f"Mock data criado com sucesso em: {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Gera dados simulados do ENEM (Mock) para ambiente de desenvolvimento.")
    parser.add_argument("--year", type=int, default=2023, help="Ano do ENEM (ex: 2023)")
    parser.add_argument("--rows", type=int, default=10000, help="Número de linhas a gerar")
    args = parser.parse_args()

    # Salva na pasta data/raw dentro de uma pasta enem_{year}/DADOS (simulando a estrutura do zip do inep)
    raw_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', f'enem_{args.year}', 'DADOS')
    
    create_mock_csv(args.year, args.rows, raw_dir)

if __name__ == "__main__":
    main()
