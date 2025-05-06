import os
from pathlib import Path

def listar_estrutura_diretorios(diretorio_base, nivel=0, ignorar=[], mostrar_ocultos=False):
    """
    Lista a estrutura de diretórios e arquivos de um projeto.
    
    Args:
        diretorio_base (str): Caminho do diretório raiz do projeto
        nivel (int): Nível de indentação (usado internamente para recursão)
        ignorar (list): Lista de diretórios/arquivos para ignorar
        mostrar_ocultos (bool): Se True, mostra arquivos/diretórios ocultos
    """
    # Converte para Path object se não for
    diretorio_base = Path(diretorio_base)
    
    # Verifica se o diretório existe
    if not diretorio_base.exists():
        print(f"Diretório não encontrado: {diretorio_base}")
        return
    
    # Ignora diretórios/arquivos na lista de ignorar
    if diretorio_base.name in ignorar:
        return
    
    # Ignora arquivos/diretórios ocultos se mostrar_ocultos for False
    if not mostrar_ocultos and diretorio_base.name.startswith('.'):
        return
    
    # Indentação baseada no nível
    indent = '    ' * nivel
    
    # Se for diretório, imprime e chama recursivamente para seus conteúdos
    if diretorio_base.is_dir():
        print(f"{indent}📁 {diretorio_base.name}/")
        
        # Ordena os itens: diretórios primeiro, depois arquivos, ambos em ordem alfabética
        itens = sorted(os.listdir(diretorio_base))
        itens = [diretorio_base / item for item in itens]
        itens = sorted(itens, key=lambda x: (not x.is_dir(), x.name.lower()))
        
        for item in itens:
            listar_estrutura_diretorios(item, nivel + 1, ignorar, mostrar_ocultos)
    else:
        print(f"{indent}📄 {diretorio_base.name}")

if __name__ == "__main__":
    # Configurações
    DIRETORIO_PROJETO = '.'  # Usa o diretório atual como padrão
    IGNORAR = ['.git', '__pycache__', '.idea', 'venv', 'env', 'node_modules']  # Diretórios para ignorar
    MOSTRAR_OCULTOS = False  # Se True, mostra arquivos/diretórios que começam com '.'
    
    print("\nESTRUTURA DO PROJETO:")
    print("====================")
    listar_estrutura_diretorios(DIRETORIO_PROJETO, ignorar=IGNORAR, mostrar_ocultos=MOSTRAR_OCULTOS)