import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.routers import auth

app = FastAPI()

SESSION_SECRET = os.getenv("SESSION_SECRET", "change-this-secret-in-production")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
website_dir = os.path.join(PROJECT_ROOT, "website")

app.mount("/static", StaticFiles(directory=website_dir), name="static")

app.include_router(auth.router)


def page(filename: str) -> FileResponse:
    return FileResponse(os.path.join(website_dir, filename))


@app.get("/")
def home():
    return page("index.html")

@app.get("/about")
def about():
    return page("about.html")

@app.get("/faqs")
def faqs():
    return page("faqs.html")

@app.get("/contact")
def contact():
    return page("contact_us.html")

@app.get("/login")
def login_page():
    return page("login.html")

@app.get("/signup")
def signup_page():
    return page("signup.html")

@app.get("/assignment-brief")
def assignment_brief():
    return page("assignment-brief.html")

@app.get("/mitigating-circumstances")
def mitigating():
    return page("mitigating-circumstances.html")

@app.get("/assignment-reviewer")
def reviewer():
    return page("assignement_reviewer.html")

@app.get("/your-calendar")
def calendar():
    return page("your_calendar.html")
