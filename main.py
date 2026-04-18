from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from chatbot.mitigating_circumstances import MitigatingAgent

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = BASE_DIR / "website"

mitigating_bot = MitigatingAgent()


class ChatRequest(BaseModel):
    message: str


app.mount("/static", StaticFiles(directory=str(WEBSITE_DIR)), name="static")


@app.get("/api/me")
def api_me():
    return {"logged_in": False}


@app.post("/chat")
def chat(req: ChatRequest):
    reply = mitigating_bot.handle(req.message)
    return {"reply": reply}


@app.get("/")
def home():
    return FileResponse(WEBSITE_DIR / "index.html")


@app.get("/mitigating-circumstances")
def mitigating_page():
    return FileResponse(WEBSITE_DIR / "mitigating-circumstances.html")


@app.get("/contact")
def contact_page():
    return FileResponse(WEBSITE_DIR / "contact_us.html")


@app.get("/about")
def about_page():
    return FileResponse(WEBSITE_DIR / "about.html")


@app.get("/faqs")
def faqs_page():
    return FileResponse(WEBSITE_DIR / "faqs.html")


@app.get("/login")
def login_page():
    return FileResponse(WEBSITE_DIR / "login.html")


@app.get("/your-calendar")
def your_calendar_page():
    return FileResponse(WEBSITE_DIR / "your_calendar.html")


@app.get("/assignment-brief")
def assignment_brief_page():
    return FileResponse(WEBSITE_DIR / "assignment-brief.html")


@app.get("/assignment-calendar")
def assignment_calendar_page():
    return FileResponse(WEBSITE_DIR / "assignment-calendar.html")