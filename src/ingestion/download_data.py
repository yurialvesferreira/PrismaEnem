import os
import argparse
import requests
import zipfile
from urllib.parse import urlparse
from tqdm import tqdm
import sys

# Adiciona o diretório raiz ao PYTHONPATH para importar configurações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from config.settings import settings

# Timeout (conexão, leitura) — evita que o processo trave indefinidamente
REQUEST_TIMEOUT = (10, 60)


def validate_url(url: str) -> None:
    """Aceita apenas URLs http(s) — bloqueia esquemas como file:// ou ftp://."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"URL inválida ou esquema não suportado: {url}")
    if parsed.scheme == "http":
        print("Aviso: a URL usa http (sem TLS). Prefira https para garantir a integridade do download.")


def download_file(url: str, output_path: str):
    """Downloads a file with a progress bar (atomically, via arquivo temporário)."""
    print(f"Baixando dados de: {url}")
    # Baixa para um .part e renomeia no final: um download interrompido
    # nunca é confundido com um arquivo completo.
    partial_path = f"{output_path}.part"
    with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte

        with open(partial_path, 'wb') as file, tqdm(
                desc=output_path,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
            for data in response.iter_content(block_size):
                size = file.write(data)
                bar.update(size)

    os.replace(partial_path, output_path)


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
    default_url = f"{settings.inep_data_url_base.rstrip('/')}/microdados_enem_{year}.zip"
    url = args.url if args.url else default_url

    raw_dir = os.path.abspath(settings.raw_data_dir)
    os.makedirs(raw_dir, exist_ok=True)

    zip_filename = f"microdados_enem_{year}.zip"
    zip_path = os.path.join(raw_dir, zip_filename)
    extract_path = os.path.join(raw_dir, f"enem_{year}")

    try:
        validate_url(url)
        if not os.path.exists(zip_path):
            download_file(url, zip_path)
        else:
            print(f"Arquivo {zip_filename} já existe em {raw_dir}. Pulando download.")

        extract_zip(zip_path, extract_path)
        print(f"Processo finalizado com sucesso. Dados disponíveis em: {extract_path}")

    except Exception as e:
        print(f"Erro durante a ingestão: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
