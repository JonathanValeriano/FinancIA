# 🤖 FinancIA-Bot

> Um bot de Telegram inteligente que analisa extratos bancários com auxílio de **IA**, promovendo uma vida financeira mais saudável.

---

## 📌 Sobre o Projeto

O **FinancIA-Bot** permite que usuários enviem extratos bancários (CSV/Excel) diretamente pelo Telegram, onde o bot processa, categoriza e armazena as transações de forma inteligente. Utilizando **modelos de linguagem** como o BERT e integrando com **Open Finance**, o bot oferece uma análise automatizada e precisa das suas finanças pessoais.

---

## ⚙️ Funcionalidades

### 📤 Upload de Extratos
- Suporte a arquivos `.csv` e `.xlsx`
- Tamanho máximo: **5MB**
- Detecção automática de banco: **Itaú**, **Bradesco** e **Santander**
- Validação de formato e encoding

### 🤖 Categorização Inteligente
- Regras manuais simples (ex: "PIX" → Transferência)
- Modelo de IA: [`neuralmind/bert-base-portuguese-cased`](https://huggingface.co/neuralmind/bert-base-portuguese-cased)
- Fallback por **similaridade semântica** (`sentence-transformers`)

### 🔄 Integração com Open Finance
- Autenticação via OAuth2
- Sincronização de transações diretamente da instituição financeira

### 💾 Armazenamento
- Base local em **SQLite**
- Uploads organizados por usuário
- Histórico e categorias persistentes

---

## 🧠 Tecnologias e Bibliotecas

| Biblioteca                | Versão    | Uso                                      |
|--------------------------|-----------|------------------------------------------|
| `python-telegram-bot`    | ≥ 20.0    | Framework para o bot do Telegram         |
| `pandas`                 | ≥ 2.0.0   | Processamento de dados bancários         |
| `sqlalchemy`             | ≥ 2.0.0   | ORM para banco SQLite                    |
| `transformers[torch]`    | ≥ 4.30.0  | Modelo BERT para categorização           |
| `sentence-transformers`  | ≥ 2.2.2   | Similaridade semântica (backup)          |
| `torch`                  | ≥ 2.0.0   | Backend para BERT                        |
| `scikit-learn`           | ≥ 1.0.0   | Similaridade e pré-processamento         |
| `python-dotenv`          | ≥ 1.0.0   | Variáveis de ambiente (.env)             |

---

## 📁 Estrutura de Arquivos

```bash
financIA-bot/
├── src/
│   └── financIA/
│       ├── bot/                   # Comandos e mensagens do Telegram
│       │   └── handlers.py
│       ├── core/
│       │   ├── categorizer.py     # Categorização com IA
│       │   └── database.py        # Conexão com SQLite
│       ├── file_parsers/
│       │   └── bank_parser.py     # Parsers por banco
│       ├── integrations/
│       │   └── open_finance.py    # Integração OAuth2
│       ├── services/
│       │   └── analysis_service.py # Processamento central
│       ├── utils/
│       │   └── file_validation.py # Validação de arquivos
├── data/
│   └── processed/                 # Banco de dados SQLite
├── user_uploads/                 # Arquivos de usuários
├── main.py                        # Ponto de entrada
├── config.py                      # Configurações globais
├── .env                           # Credenciais e variáveis
├── requirements.txt               # Dependências do projeto
├── pyproject.toml                 # Build e metadata
└── README.md                      # Este arquivo
