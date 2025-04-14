import os
from pathlib import Path
import shutil

PROJECT_NAME = "financIA-web"

STRUCTURE = {
    "backend": {
        "app": {
            "auth": ["authentication.py", "security.py"],
            "models": ["user.py"],
            "schemas": ["user.py"],
            "api": {
                "endpoints": ["auth.py"]
            },
            "db": ["session.py"]
        },
        "migrations": [],
        "main.py": None,
        "requirements.txt": None
    },
    "frontend": {
        "public": ["index.html"],
        "src": {
            "components": ["LoginForm.vue"],
            "stores": ["auth.js"],
            "router": ["index.js"],
            "assets": ["main.css"],
            "App.vue": None,
            "main.js": None
        },
        "vite.config.js": None,
        "package.json": None
    },
    ".env": None,
    "docker-compose.yml": None,
    "README.md": None
}

BACKEND_MAIN_CONTENT = """\
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "FinancIA Web API"}
"""

BACKEND_SECURITY_CONTENT = """\
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

# Configurações (em produção, use variáveis de ambiente)
SECRET_KEY = os.getenv("SECRET_KEY", "default-insecure-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({**data, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)
"""

FRONTEND_LOGIN_VUE = """\
<template>
  <div class="login-container">
    <form @submit.prevent="handleSubmit" class="login-form">
      <h2>Login</h2>
      
      <div class="form-group">
        <label for="email">E-mail</label>
        <input
          v-model="email"
          type="email"
          required
          placeholder="seu@email.com"
          autocomplete="username"
        />
      </div>

      <div class="form-group">
        <label for="password">Senha</label>
        <input
          v-model="password"
          type="password"
          required
          placeholder="••••••••"
          autocomplete="current-password"
          minlength="8"
        />
      </div>

      <button type="submit" :disabled="loading" class="login-button">
        {{ loading ? 'Carregando...' : 'Entrar' }}
      </button>

      <div v-if="error" class="error-message">{{ error }}</div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const handleSubmit = async () => {
  try {
    loading.value = true
    error.value = ''
    // Implementar chamada à API
  } catch (err) {
    error.value = 'Credenciais inválidas'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.login-form {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.login-button {
  width: 100%;
  padding: 0.75rem;
  background-color: #4f46e5;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.login-button:hover {
  background-color: #4338ca;
}

.login-button:disabled {
  background-color: #a5b4fc;
  cursor: not-allowed;
}

.error-message {
  color: #ef4444;
  margin-top: 1rem;
  text-align: center;
}
</style>
"""

DOCKER_COMPOSE_CONTENT = """\
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/financia
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules

  db:
    image: postgres:13
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: financia
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""

def create_project_structure(base_path: Path, structure: dict, parent: Path = None):
    """Cria recursivamente a estrutura de diretórios e arquivos"""
    if parent is None:
        parent = base_path
    
    for name, content in structure.items():
        path = parent / name
        
        if content is None:  # É um arquivo
            path.touch()
            print(f"Arquivo criado: {path}")
            
            # Adiciona conteúdo específico a arquivos importantes
            if name == "main.py":
                path.write_text(BACKEND_MAIN_CONTENT)
            elif name == "security.py":
                path.write_text(BACKEND_SECURITY_CONTENT)
            elif name == "LoginForm.vue":
                path.write_text(FRONTEND_LOGIN_VUE)
            elif name == "docker-compose.yml":
                path.write_text(DOCKER_COMPOSE_CONTENT)
                
        elif isinstance(content, dict):  # É um diretório
            path.mkdir(parents=True, exist_ok=True)
            print(f"Diretório criado: {path}")
            create_project_structure(base_path, content, path)
        elif isinstance(content, list):  # Arquivos dentro de diretório
            path.mkdir(parents=True, exist_ok=True)
            for file in content:
                file_path = path / file
                file_path.touch()
                print(f"Arquivo criado: {file_path}")

def create_requirements_file(project_path: Path):
    """Cria arquivo requirements.txt para o backend"""
    content = """\
fastapi==0.95.2
uvicorn==0.22.0
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.0.1
sqlalchemy==2.0.15
psycopg2-binary==2.9.6
python-multipart==0.0.6
python-dotenv==1.0.0
alembic==1.11.1
"""
    (project_path / "backend" / "requirements.txt").write_text(content)

def create_package_json(project_path: Path):
    """Cria package.json para o frontend"""
    content = """\
{
  "name": "financIA-web",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.2.47",
    "pinia": "^2.0.36",
    "vue-router": "^4.1.6",
    "axios": "^1.3.5"
  },
  "devDependencies": {
    "vite": "^4.2.0",
    "@vitejs/plugin-vue": "^4.1.0"
  }
}
"""
    (project_path / "frontend" / "package.json").write_text(content)

def create_vite_config(project_path: Path):
    """Cria vite.config.js"""
    content = """\
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
"""
    (project_path / "frontend" / "vite.config.js").write_text(content)

def main():
    project_path = Path.cwd() / PROJECT_NAME
    
    if project_path.exists():
        print(f"Erro: O diretório {PROJECT_NAME} já existe!")
        return
    
    print(f"Criando projeto {PROJECT_NAME}...")
    project_path.mkdir()
    
    # Cria estrutura de diretórios e arquivos
    create_project_structure(project_path, STRUCTURE)
    
    # Cria arquivos de configuração
    create_requirements_file(project_path)
    create_package_json(project_path)
    create_vite_config(project_path)
    
    # Cria .env com configurações básicas
    env_content = """\
# Backend
SECRET_KEY=insira-uma-chave-secreta-forte-aqui
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/financia

# Frontend
VITE_API_BASE_URL=http://localhost:8000
"""
    (project_path / ".env").write_text(env_content)
    
    print(f"\n✅ Projeto criado com sucesso em {project_path}")
    print("\nPróximos passos:")
    print("1. cd financIA-web")
    print("2. Configurar o PostgreSQL ou ajustar DATABASE_URL no .env")
    print("3. Para o backend:")
    print("   cd backend && pip install -r requirements.txt")
    print("4. Para o frontend:")
    print("   cd frontend && npm install")
    print("\nExecute com docker-compose:")
    print("   docker-compose up --build")

if __name__ == "__main__":
    main()