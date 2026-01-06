from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.routers.financeiro import router as financeiro_router

app = FastAPI()

@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"

@app.get("/")
def root():
    return {"status": "OS System online"}

# Ativa /os/nova
app.include_router(financeiro_router)
