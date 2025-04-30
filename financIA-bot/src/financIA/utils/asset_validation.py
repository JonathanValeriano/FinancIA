import requests
import logging
import time
import re

logger = logging.getLogger(__name__)
VALIDATED_CACHE = {}

# Regex para validar tickers comuns da B3 (ex: PETR4, MXRF11)
TICKER_REGEX = re.compile(r'^[A-Z]{4}[0-9]{1,2}\.SA$')

def validate_asset_symbol(symbol: str) -> bool:
    symbol = symbol.strip().upper()

    if not symbol.endswith(".SA"):
        symbol += ".SA"

    if symbol in VALIDATED_CACHE:
        logger.info(f"[VALIDAÇÃO] Cache usado para {symbol}: {VALIDATED_CACHE[symbol]}")
        return VALIDATED_CACHE[symbol]

    try:
        time.sleep(0.5)
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        logger.info(f"[VALIDAÇÃO] Requisição para: {url}")
        response = requests.get(url, timeout=5)

        if response.status_code == 429:
            logger.warning(f"[VALIDAÇÃO] Limite atingido (429) para {symbol}")
            # Fallback: valida pelo padrão regex
            if TICKER_REGEX.match(symbol):
                logger.info(f"[VALIDAÇÃO] Aceitando {symbol} via fallback por padrão B3")
                VALIDATED_CACHE[symbol] = True
                return True
            VALIDATED_CACHE[symbol] = False
            return False

        response.raise_for_status()
        data = response.json()
        results = data.get("quoteResponse", {}).get("result", [])
        is_valid = len(results) > 0 and "symbol" in results[0]

        VALIDATED_CACHE[symbol] = is_valid
        logger.info(f"[VALIDAÇÃO] Resultado para {symbol}: {is_valid} | Nome retornado: {results[0].get('longName', 'N/A') if results else 'N/A'}")
        return is_valid

    except Exception as e:
        logger.error(f"[VALIDAÇÃO] Erro ao validar {symbol}: {e}")
        VALIDATED_CACHE[symbol] = False
        return False
