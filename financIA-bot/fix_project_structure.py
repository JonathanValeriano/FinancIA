import os
import shutil
import stat
from pathlib import Path
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ProjectFixer:
    def __init__(self, project_root):
        self.root = Path(project_root)
        self.required_structure = {
            'src': {
                'financIA': {
                    '__init__.py': None,
                    'bot': {
                        '__init__.py': None,
                        'handlers.py': None
                    },
                    'core': {
                        '__init__.py': None,
                        'categorizer.py': None,
                        'database.py': None
                    },
                    'file_parsers': {
                        '__init__.py': None,
                        'bank_parser.py': None
                    },
                    'integrations': {
                        '__init__.py': None,
                        'open_finance.py': None
                    },
                    'services': {
                        '__init__.py': None,
                        'analysis_service.py': None
                    },
                    'utils': {
                        '__init__.py': None,
                        'file_validation.py': None
                    }
                }
            },
            'data': {
                'processed': {
                    'transactions.db': None
                }
            },
            'user_uploads': {},
            'main.py': None,
            'config.py': None,
            'pyproject.toml': None,
            'README.md': None,
            '.env': None,
            '.env.example': None,
            '.gitignore': None
        }

    def fix_structure(self):
        """Corrige a estrutura completa do projeto"""
        try:
            self._clean_unnecessary_files()
            self._create_missing_structure()
            self._move_existing_files()
            self._clean_pycache()
            logger.info("✅ Estrutura do projeto corrigida com sucesso!")
            self.print_current_structure()
        except Exception as e:
            logger.error(f"❌ Erro ao corrigir estrutura: {e}")

    def _remove_readonly(self, func, path, _):
        """Remove atributo de somente-leitura e tenta novamente"""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def _clean_unnecessary_files(self):
        """Remove arquivos e pastas desnecessários com tratamento de permissão"""
        unnecessary = [
            self.root / 'financIA_bot.egg-info',
            self.root / 'src' / 'financIA_bot.egg-info',
            self.root / 'src' / 'data',
            self.root / 'src' / 'core',
            self.root / 'src' / 'integrations',
            self.root / 'src' / 'services'
        ]
        
        for path in unnecessary:
            if path.exists():
                try:
                    if path.is_dir():
                        shutil.rmtree(path, onerror=self._remove_readonly)
                    else:
                        path.unlink()
                    logger.info(f"Removido: {path}")
                except PermissionError:
                    logger.warning(f"⚠️ Não foi possível remover {path} - Acesso negado. Tente fechar o VS Code/outros editores.")

    def _create_missing_structure(self):
        """Cria a estrutura de diretórios e arquivos faltantes"""
        for path, content in self._walk_structure(self.root, self.required_structure):
            if content is None:  # É um arquivo
                if not path.exists():
                    try:
                        path.touch()
                        logger.info(f"Criado arquivo: {path}")
                    except PermissionError:
                        logger.warning(f"⚠️ Não foi possível criar {path} - Permissão negada")
            else:  # É um diretório
                if not path.exists():
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Criado diretório: {path}")
                    except PermissionError:
                        logger.warning(f"⚠️ Não foi possível criar {path} - Permissão negada")

    def _move_existing_files(self):
        """Move arquivos para os locais corretos com tratamento de permissão"""
        move_map = {
            # Arquivos do core
            self.root / 'src' / 'core' / 'categorizer.py': self.root / 'src' / 'financIA' / 'core' / 'categorizer.py',
            self.root / 'src' / 'core' / 'database.py': self.root / 'src' / 'financIA' / 'core' / 'database.py',
            
            # Arquivos de serviços
            self.root / 'src' / 'services' / 'analysis_service.py': self.root / 'src' / 'financIA' / 'services' / 'analysis_service.py',
            
            # Arquivos de integração
            self.root / 'src' / 'integrations' / 'open_finance.py': self.root / 'src' / 'financIA' / 'integrations' / 'open_finance.py'
        }

        for src, dst in move_map.items():
            if src.exists() and not dst.exists():
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    logger.info(f"Movido: {src} -> {dst}")
                except PermissionError:
                    logger.warning(f"⚠️ Não foi possível mover {src} - Permissão negada")

    def _clean_pycache(self):
        """Remove todas as pastas __pycache__ com tratamento de permissão"""
        for pycache in self.root.glob('**/__pycache__'):
            try:
                shutil.rmtree(pycache, onerror=self._remove_readonly)
                logger.info(f"Removido __pycache__: {pycache}")
            except PermissionError:
                logger.warning(f"⚠️ Não foi possível remover {pycache} - Acesso negado")

    def _walk_structure(self, base_path, structure):
        """Gerador para percorrer a estrutura"""
        for name, content in structure.items():
            path = base_path / name
            yield path, content
            if isinstance(content, dict):
                yield from self._walk_structure(path, content)

    def print_current_structure(self):
        """Exibe a estrutura atual do projeto"""
        from collections import defaultdict
        structure = defaultdict(list)

        def build_tree(path, level=0):
            indent = "    " * level
            name = path.name
            if path.is_file():
                structure['files'].append(f"{indent}├── {name}")
            else:
                structure['dirs'].append(f"{indent}└── {name}/")
                for item in sorted(path.iterdir()):
                    if item.name != '__pycache__':
                        build_tree(item, level + 1)

        build_tree(self.root)
        
        print("\nEstrutura Atual do Projeto:")
        for item in structure['dirs'] + structure['files']:
            print(item)

if __name__ == "__main__":
    print("🛠️  Corrigindo estrutura do projeto...")
    fixer = ProjectFixer(os.getcwd())
    fixer.fix_structure()