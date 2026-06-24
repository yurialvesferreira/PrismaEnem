import os
import argparse
import requests
import zipfile
from tqdm import tqdm
import sys

# Adiciona o diretório raiz ao PYTHONPATH para importar configurações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from config.settings import settings

def download_file(url: str, output_path: str):
    """Downloads a file with a progress bar."""
    print(f"Baixando dados de: {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 # 1 Kibibyte

    with open(output_path, 'wb') as file, tqdm(
            desc=output_path,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
        for data in response.iter_content(block_size):
            size = file.write(data)
            bar.update(size)

def extract_zip(zip_path: str, extract_to: str):
    """Extracts a ZIP file."""
    print(f"Extraindo {zip_path} para {extract_to}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print("Extração concluída.")

def main():
    parser = argparse.ArgumentParser(description="Baixa e extrai microdados do ENEM do portal do INEP.")
    parser.add_argument("--year", type=int, required=True, help="Ano do ENEM (ex: 2023)")
    parser.add_argument("--url", type=str, help="URL customizada do ZIP. Se não fornecida, usa um padrão hipotético.")
    args = parser.parse_args()

    year = args.year
    
    # Exemplo hipotético de URL (o portal do INEP frequentemente muda a estrutura de URLs e muitas vezes requer navegação. 
    # Esta é uma simulação de URL baseada em como os dados são disponibilizados.)
    default_url = f"https://download.inep.gov.br/microdados/microdados_enem_{year}.zip"
    url = args.url if args.url else default_url

    raw_dir = os.path.abspath(settings.raw_data_dir)
    os.makedirs(raw_dir, exist_ok=True)

    zip_filename = f"microdados_enem_{year}.zip"
    zip_path = os.path.join(raw_dir, zip_filename)
    extract_path = os.path.join(raw_dir, f"enem_{year}")

    try:
        if not os.path.exists(zip_path):
            download_file(url, zip_path)
        else:
            print(f"Arquivo {zip_filename} já existe em {raw_dir}. Pulando download.")
        
        extract_zip(zip_path, extract_path)
        print(f"Processo finalizado com sucesso. Dados disponíveis em: {extract_path}")

    except Exception as e:
        print(f"Erro durante a ingestão: {e}")

if __name__ == "__main__":
    main()
