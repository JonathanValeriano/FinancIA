import os
import re
from pathlib import Path

def validate_project_structure(root_path):
    """Valida a estrutura do projeto financIA-bot"""
    print("🔍 Validando estrutura do projeto...")
    
    # Estrutura esperada
    expected_structure = {
        'main.py': 'file',
        'pyproject.toml': 'file',
        'src': {
            'financIA': {
                '__init__.py': 'file',
                'bot': {
                    '__init__.py': 'file',
                    'handlers.py': 'file'
                },
                'core': {
                    '__init__.py': 'file',
                    'categorizer.py': 'file'
                },
                'integrations': {
                    '__init__.py': 'file',
                    'open_finance.py': 'file'
                },
                'services': {
                    '__init__.py': 'file',
                    'analysis_service.py': 'file'
                }
            }
        }
    }

    # Verificar estrutura
    missing_items = []
    for item, content in expected_structure.items():
        path = Path(root_path) / item
        if isinstance(content, dict):
            if not path.exists() or not path.is_dir():
                missing_items.append(f"Diretório faltando: {path}")
            else:
                missing_items.extend(validate_structure_recursive(path, content))
        else:
            if not path.exists():
                missing_items.append(f"Arquivo faltando: {path}")

    return missing_items

def validate_structure_recursive(base_path, expected_structure):
    missing = []
    for item, content in expected_structure.items():
        path = base_path / item
        if isinstance(content, dict):
            if not path.exists() or not path.is_dir():
                missing.append(f"Diretório faltando: {path}")
            else:
                missing.extend(validate_structure_recursive(path, content))
        else:
            if not path.exists():
                missing.append(f"Arquivo faltando: {path}")
    return missing

def fix_imports_in_file(file_path):
    """Corrige imports em um arquivo Python"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Padrão para encontrar imports absolutos incorretos
    pattern = r'from\s+src\.financIA\.([a-zA-Z_]+)\.([a-zA-Z_]+)\s+import\s+([a-zA-Z_]+)'
    matches = re.findall(pattern, content)
    
    if not matches:
        return False
    
    # Substituir por imports relativos
    for module, submodule, import_name in matches:
        relative_import = f"from ..{module}.{submodule} import {import_name}"
        content = re.sub(
            f'from\s+src\.financIA\.{module}\.{submodule}\s+import\s+{import_name}',
            relative_import,
            content
        )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def validate_and_fix_project():
    root_path = os.getcwd()
    print(f"📂 Diretório raiz: {root_path}")
    
    # 1. Validar estrutura
    issues = validate_project_structure(root_path)
    
    if issues:
        print("\n⚠️ Problemas encontrados:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("\n✅ Estrutura de pastas está correta!")
    
    # 2. Verificar e corrigir imports
    print("\n🔧 Verificando imports nos arquivos Python...")
    files_to_check = [
        'src/financIA/services/analysis_service.py',
        'src/financIA/bot/handlers.py',
        'src/financIA/core/categorizer.py',
        'src/financIA/integrations/open_finance.py'
    ]
    
    for file in files_to_check:
        file_path = Path(root_path) / file
        if file_path.exists():
            if fix_imports_in_file(file_path):
                print(f"🛠️  Corrigidos imports em: {file}")
            else:
                print(f"✅ Imports OK em: {file}")
        else:
            print(f"⚠️ Arquivo não encontrado: {file}")
    
    # 3. Criar __init__.py faltantes
    print("\n📂 Verificando arquivos __init__.py...")
    init_files_to_create = []
    
    for root, dirs, files in os.walk(Path(root_path) / 'src' / 'financIA'):
        if '__init__.py' not in files:
            init_path = Path(root) / '__init__.py'
            init_files_to_create.append(init_path)
    
    for init_file in init_files_to_create:
        init_file.touch()
        print(f"📄 Criado: {init_file}")
    
    print("\n🎉 Validação concluída! Execute o projeto com:")
    print("python -m src.financIA.main")

if __name__ == "__main__":
    validate_and_fix_project()