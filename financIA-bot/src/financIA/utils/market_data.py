# src/financIA/utils/market_data.py
import time
import requests
import logging
import yfinance as yf
from src.financIA.config import Config

ticker = yf.Ticker("PETR4.SA")
print(ticker.info.get("currentPrice"))  # ou
print(ticker.info.get("regularMarketPrice"))

logger = logging.getLogger(__name__)

# --- Cache simples em memória ---
_cache = {}

def _cache_get(key: str, ttl: int = 600):
    entry = _cache.get(key)
    if not entry:
        return None
    value, expires_at = entry
    if time.time() > expires_at:
        _cache.pop(key, None)
        return None
    return value

def _cache_set(key: str, value, ttl: int = 600):
    _cache[key] = (value, time.time() + ttl)

# --- Ações na B3 usam sufixo .SA ---
def _format_symbol(ticker: str) -> str:
    return f"{ticker.upper()}.SA"

# --- Indicadores e preço com yfinance + cache ---
def get_stock_indicators(ticker: str) -> dict:
    """
    Busca indicadores financeiros básicos (P/L, DY, ROE) via Yahoo Finance.
    Retorna dicionário com valores ou 'N/A' em caso de falha.
    """
    try:
        ticker_yf = yf.Ticker(f"{ticker}.SA")
        info = ticker_yf.info

        # Verifica e arredonda apenas se for numérico
        pe_raw = info.get("trailingPE")
        pl = round(float(pe_raw), 2) if isinstance(pe_raw, (int, float)) else "N/A"

        dy_raw = info.get("dividendYield")
        dy = f"{round(float(dy_raw) * 100, 2)}%" if isinstance(dy_raw, (int, float)) else "N/A"

        roe_raw = info.get("returnOnEquity")
        roe = f"{round(float(roe_raw) * 100, 2)}%" if isinstance(roe_raw, (int, float)) else "N/A"

        return {
            "P/L": pl,
            "DY": dy,
            "ROE": roe
        }
    except Exception as e:
        logger.warning(f"[Indicadores] Erro ao buscar indicadores de {ticker}: {e}")
        return {"P/L": "N/A", "DY": "N/A", "ROE": "N/A"}

def get_stock_price(ticker: str) -> str:
    key = f"price:{ticker}"
    cached = _cache_get(key)
    if cached:
        return cached

    try:
        symbol = _format_symbol(ticker)
        ticker_yf = yf.Ticker(symbol)
        info = ticker_yf.info

        if not info:
            logger.warning(f"[Preço] Info vazio para {ticker}")
            return "N/A"

        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")

        if isinstance(price, (int, float)):
            price_str = f"R$ {price:.2f}"
            _cache_set(key, price_str)
            return price_str
        else:
            logger.warning(f"[Preço] Valor inválido para {ticker}: {price}")
            return "N/A"

    except Exception as e:
        logger.warning(f"[Preço] Erro ao buscar preço de {ticker}: {e}")
        return "N/A"

# --- Notícias com cache ---
def get_latest_news(ticker: str) -> str:
    key = f"news:{ticker}"
    cached = _cache_get(key)
    if cached:
        return cached

    api_key = Config.GNEWS_API_KEY
    if not api_key or api_key == "INSIRA_SUA_CHAVE_AQUI":
        logger.warning("[Notícias] API KEY da GNews não configurada.")
        return "⚠️ Nenhuma notícia disponível no momento."

    url = (
        f"https://gnews.io/api/v4/search"
        f"?q={ticker}"
        f"&lang=pt"
        f"&max=3"
        f"&apikey={api_key}"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        if not articles:
            return "🔎 Nenhuma notícia encontrada."

        summary = ""
        for art in articles:
            title = art.get("title", "Sem título")
            date = art.get("publishedAt", "")[:10]
            summary += f"• {title} ({date})\n"

        _cache_set(key, summary.strip())
        return summary.strip()
    except Exception as e:
        logger.warning(f"[Notícias] Erro ao buscar notícias de {ticker}: {e}")
        return "⚠️ Não foi possível obter notícias."

# --- Regras de recomendação simples ---
def gerar_recomendacao(ticker: str, indicadores: dict) -> str:
    try:
        pl = float(indicadores.get("P/L", 0))
        roe = float(indicadores.get("ROE", "0").replace("%", ""))
    except:
        return "⚠️ Observação"
    if roe > 10 and pl < 20:
        return "✅ Manter"
    if roe < 0 or pl > 100:
        return "🛑 Vender"
    return "⚠️ Observar"

# --- Resumo geral da carteira ---
def resumo_dos_ativos(ativos: list[dict]) -> str:
    manter = observar = vender = 0
    for a in ativos:
        inds = get_stock_indicators(a['name'])
        rec = gerar_recomendacao(a['name'], inds)
        if "Manter" in rec:
            manter += 1
        elif "Vender" in rec:
            vender += 1
        else:
            observar += 1
    total = len(ativos)
    return (
        f"Sua carteira possui {total} ativos.\n"
        f"✅ Manter: {manter} | ⚠️ Observar: {observar} | 🛑 Vender: {vender}"
    )
