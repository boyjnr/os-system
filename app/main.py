from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"

@app.get("/")
def root():
    return {"status": "OS System online"}
