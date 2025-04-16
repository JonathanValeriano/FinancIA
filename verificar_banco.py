import sys
from pathlib import Path
import sqlite3

# Adiciona a raiz do projeto ao sys.path
BASE_DIR = Path(__file__).resolve().parent / "financIA-bot"
sys.path.append(str(BASE_DIR / "src"))

from financIA.config import Config

print("📂 Verificando banco de dados em:", Config.DB_PATH)

try:
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()

    print("📋 Tabelas encontradas no banco:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = cursor.fetchall()
    for tabela in tabelas:
        print(" -", tabela[0])

    if any("assets" in t for t in tabelas):
        print("✅ A tabela 'assets' existe!")
    else:
        print("❌ A tabela 'assets' NÃO foi encontrada.")

except Exception as e:
    print("💥 Erro ao acessar o banco:", e)
finally:
    conn.close()
