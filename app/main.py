from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import requests

app = FastAPI()

MODEL_BACKEND = os.getenv("MODEL_BACKEND", "mock")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")

app.mount("/static", StaticFiles(directory="/workspace/website"), name="static")


@app.get("/")
def home():
    return FileResponse("/workspace/website/index.html")


@app.get("/chat")
def chat(q: str):
    if MODEL_BACKEND == "ollama":
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": "llama3.1", "prompt": q, "stream": False},
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            return {"reply": data.get("response", "")}
        except Exception as e:
            return {"error": str(e)}

    return {"reply": f"Metis mock reply: {q}"}