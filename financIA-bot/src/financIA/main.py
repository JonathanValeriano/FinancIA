from fastapi import FastAPI
from src.financIA.api import twelvedata_api

app = FastAPI()
app.include_router(twelvedata_api.router)
