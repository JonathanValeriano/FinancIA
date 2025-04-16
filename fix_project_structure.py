import os
from pathlib import Path
import shutil
import re

# Caminhos principais
BASE_DIR = Path(__file__).resolve().parent
ROOT_DATA_DB = BASE_DIR / "financIA-bot" / "data" / "processed" / "transactions.db"
SRC_DATA_DB = BASE_DIR / "financIA-bot" / "src" / "data" / "processed" / "transactions.db"
CONFIG_FILE = BASE_DIR / "financIA-bot" / "src" / "financIA" / "config.py"

def ensure_data_dir():
    """Garante que a pasta correta do banco exista"""
    ROOT_DATA_DB.parent.mkdir(parents=True, exist_ok=True)

def move_db_file():
    """Move o banco da pasta src/data para data/, se necessário"""
    if SRC_DATA_DB.exists():
        print("📦 Movendo banco de dados de 'src/data' para 'data/'...")
        ensure_data_dir()
        shutil.move(str(SRC_DATA_DB), str(ROOT_DATA_DB))
    else:
        print("✅ Nenhum banco duplicado encontrado em 'src/data'.")

def clean_up_src_data():
    """Remove pasta src/data/processed se estiver vazia"""
    try:
        processed = SRC_DATA_DB.parent
        data = processed.parent
        if processed.exists() and not any(processed.iterdir()):
            processed.rmdir()
            print("🧹 Removido: src/data/processed/")
        if data.exists() and not any(data.iterdir()):
            data.rmdir()
            print("🧹 Removido: src/data/")
    except Exception as e:
        print(f"⚠️ Erro ao limpar pastas: {e}")

def fix_config_path():
    """Corrige o caminho do banco em config.py"""
    if not CONFIG_FILE.exists():
        print("❌ Arquivo de config não encontrado.")
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    new_path = "Path(__file__).resolve().parent.parent.parent / 'data' / 'processed' / 'transactions.db'"
    fixed_content = re.sub(
        r"(DB_PATH\s*=\s*)[^\n]+",
        rf"\1{new_path}",
        content
    )

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(fixed_content)

    print("🔧 Caminho corrigido no config.py!")

def main():
    print("🔍 Corrigindo estrutura de pastas e banco de dados...\n")
    move_db_file()
    clean_up_src_data()
    fix_config_path()
    print("\n✅ Estrutura ajustada com sucesso!")

if __name__ == "__main__":
    main()
