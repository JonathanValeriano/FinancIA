# 🤖 FinancIA-Bot

Um bot inteligente para Telegram que analisa extratos bancários, categoriza transações usando IA (BERT) e integra dados com o Open Finance. Desenvolvido para ajudar usuários a terem uma vida financeira mais saudável.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-Em%20Desenvolvimento-yellow)

---

## 📦 Tecnologias Principais

| Biblioteca                | Versão      | Uso                                       |
|--------------------------|-------------|-------------------------------------------|
| `python-telegram-bot`    | ≥ 20.0      | Framework para o bot do Telegram          |
| `pandas`                 | ≥ 2.0.0     | Processamento de extratos (CSV/Excel)     |
| `sqlalchemy`             | ≥ 2.0.0     | ORM com SQLite                            |
| `transformers[torch]`    | ≥ 4.30.0    | Categorização com BERT em português       |
| `sentence-transformers`  | ≥ 2.2.2     | Similaridade semântica (fallback)         |
| `python-dotenv`          | ≥ 1.0.0     | Carregamento de variáveis de ambiente     |
| `scikit-learn`           | ≥ 1.0.0     | Cálculo de similaridade                   |
| `torch`                  | ≥ 2.0.0     | Backend para o modelo BERT                |

---

## 📂 Estrutura de Arquivos

```
financIA-bot/
├── src/
│   └── financIA/
│       ├── bot/                    # Comandos e mensagens do bot
│       ├── core/                   # IA e banco de dados
│       ├── file_parsers/           # Parsers para bancos (CSV/XLSX)
│       ├── integrations/           # Integração com Open Finance
│       ├── services/               # Lógica de negócios
│       └── utils/                  # Validações e funções auxiliares
├── data/
│   └── processed/                  # SQLite e dados tratados
├── user_uploads/                   # Extratos enviados por usuários
├── main.py                         # Ponto de entrada
├── config.py                       # Configurações (.env)
├── pyproject.toml                  # Configuração de build
└── requirements.txt                # Lista de dependências
```

---

## ✨ Funcionalidades

### 📤 Upload de Extratos
- Suporte a `.csv` e `.xlsx`
- Detecção automática do banco (Itaú, Bradesco, Santander)
- Validação de formato e tamanho (≤ 5MB)

### 🤖 Categorização Automática
- Regras manuais (ex: `"PIX"` → `"Transferência"`)
- Modelo BERT em português: `neuralmind/bert-base-portuguese-cased`
- Fallback com similaridade semântica (Sentence Transformers)

### 🔗 Integração Open Finance
- Autenticação via OAuth2
- Sincronização de transações da conta bancária

### 🗃️ Armazenamento
- Banco de dados SQLite
- Diretórios separados por usuário

---

## ⚙️ Como Executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar o `.env`
Crie um arquivo `.env` com o seguinte conteúdo:

```ini
TELEGRAM_BOT_TOKEN=seu_token
OPEN_FINANCE_CLIENT_ID=seu_id
OPEN_FINANCE_CLIENT_SECRET=seu_secret
```

### 3. Executar o bot
```bash
python -m src.financIA.main
```

---

## 🛠️ Correções e Boas Práticas

- Importações absolutas (`src.financIA.*`)
- Todos os diretórios com `__init__.py`
- Tratamento de `Path`, encoding (`ISO-8859-1`) e logs informativos

---

## 🧩 Possibilidades Futuras

- Dashboard interativo com Streamlit ou Gradio
- Integração com bancos via Open Finance em tempo real
- Exportação de relatórios financeiros em PDF
- API REST para consulta de dados
- Testes automatizados com `pytest` e CI/CD no GitHub Actions

---

## 📜 Licença

Projeto licenciado sob a [MIT License](LICENSE).

---

## 👨‍💻 Autor

Desenvolvido por Jonathan William Valeriano — [LinkedIn](#) | [Portfólio](https://jwvaleriano.netlify.app)
