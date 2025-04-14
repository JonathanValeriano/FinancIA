import os
from pathlib import Path
import logging
from typing import Dict, List

def validate_project_structure(root_path: str) -> Dict:
    """Valida a estrutura do projeto FinancIA-bot"""
    expected_structure = {
        'src': {
            'financIA': {
                '__init__.py': 'file',
                'bot': {'__init__.py': 'file', 'handlers.py': 'file'},
                'core': {'__init__.py': 'file', 'categorizer.py': 'file', 'database.py': 'file'},
                'file_parsers': {'__init__.py': 'file', 'bank_parser.py': 'file'},
                'integrations': {'__init__.py': 'file', 'open_finance.py': 'file'},
                'services': {'__init__.py': 'file', 'analysis_service.py': 'file'},
                'utils': {'__init__.py': 'file', 'file_validation.py': 'file'}
            }
        },
        'main.py': 'file',
        'config.py': 'file',
        'pyproject.toml': 'file',
        'requirements.txt': 'file'
    }

    missing = []
    present = []

    def check_structure(base: Path, expected: Dict, path: str = ""):
        for item, content in expected.items():
            current_path = base / item
            full_path = f"{path}/{item}" if path else item
            
            if isinstance(content, dict):
                if not current_path.exists():
                    missing.append(f"Directory missing: {full_path}")
                else:
                    present.append(f"Directory found: {full_path}")
                    check_structure(current_path, content, full_path)
            else:
                if not current_path.exists():
                    missing.append(f"File missing: {full_path}")
                else:
                    present.append(f"File found: {full_path}")

    check_structure(Path(root_path), expected_structure)
    
    return {
        'missing': missing,
        'present': present,
        'is_valid': len(missing) == 0
    }

def generate_structure_diagram(root_path: str) -> str:
    """Gera um diagrama ASCII da estrutura do projeto"""
    from collections import defaultdict

    structure = defaultdict(list)
    prefix = []

    def build_tree(path: Path, level: int = 0):
        indent = "    " * level
        name = path.name
        
        if path.is_file():
            prefix.append(f"{indent}├── {name}")
        else:
            prefix.append(f"{indent}└── {name}/")
            for item in sorted(path.iterdir()):
                build_tree(item, level + 1)

    build_tree(Path(root_path))
    
    diagram = "\n".join(prefix)
    return f"\nProject Structure Diagram:\n{diagram}"

def main():
    root_path = os.path.dirname(os.path.abspath(__file__))
    print(f"Validating project structure at: {root_path}")
    
    # Validação
    result = validate_project_structure(root_path)
    
    print("\nValidation Results:")
    if result['is_valid']:
        print("✅ Project structure is valid!")
    else:
        print("❌ Issues found in project structure:")
        for issue in result['missing']:
            print(f"  - {issue}")
    
    # Diagrama
    print(generate_structure_diagram(root_path))

if __name__ == "__main__":
    main()