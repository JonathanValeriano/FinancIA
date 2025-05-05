import os

# Estrutura de diretórios
folders = [
    "bot-landing-page",
    "bot-landing-page/assets",
    "bot-landing-page/styles"
]

# Conteúdo do index.html
index_html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinancIA Bot - Telegram</title>
    <link rel="stylesheet" href="styles/style.css">
</head>
<body>
    <main class="container">
        <section class="content">
            <h1>🤖 FinancIA Bot</h1>
            <p>Seu assistente financeiro no Telegram. Envie extratos, acompanhe investimentos e receba insights automáticos sobre seus ativos.</p>
            <ul>
                <li>📊 Análise de transações bancárias</li>
                <li>🧠 Classificação automática de despesas</li>
                <li>💼 Acompanhamento de ações e FIIs</li>
                <li>📰 Notícias atualizadas sobre seus investimentos</li>
            </ul>
            <div class="qr-section">
                <p>📲 Escaneie o QR Code e comece agora:</p>
                <img src="assets/qr-code.png" alt="QR Code do Bot" class="qr-code">
            </div>
        </section>
    </main>
</body>
</html>
"""

# Conteúdo do style.css
style_css = """
body {
    margin: 0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #0e1117;
    color: #ffffff;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
}

.content {
    background-color: #1a1f2b;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 0 10px rgba(0,0,0,0.4);
}

h1 {
    font-size: 2.5rem;
    color: #00ffae;
}

ul {
    margin-top: 1rem;
    line-height: 1.6;
}

.qr-section {
    margin-top: 2rem;
    text-align: center;
}

.qr-code {
    margin-top: 1rem;
    width: 180px;
    height: auto;
    border: 2px solid #00ffae;
    border-radius: 10px;
}
"""

# Criação das pastas
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Arquivos
with open("bot-landing-page/index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

with open("bot-landing-page/styles/style.css", "w", encoding="utf-8") as f:
    f.write(style_css)

# Placeholder para o QR Code
qr_placeholder_path = "bot-landing-page/assets/qr-code.png"
with open(qr_placeholder_path, "wb") as f:
    pass  # você deve adicionar manualmente o QR code depois

print("✅ Estrutura da landing page criada com sucesso!")
