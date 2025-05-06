from fastapi import APIRouter
import requests
from src.financIA.config import Config

router = APIRouter()

@router.get("/api/quote")
def get_quote(symbol: str):
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbol}.SA&apikey={Config.TWELVE_DATA_API_KEY}"
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}
