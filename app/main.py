from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

website_dir = os.path.join(PROJECT_ROOT, "website")

print("BASE_DIR:", BASE_DIR)
print("PROJECT_ROOT:", PROJECT_ROOT)
print("WEBSITE_DIR:", website_dir)
print("WEBSITE EXISTS:", os.path.exists(website_dir))

app.mount("/static", StaticFiles(directory=website_dir), name="static")


@app.get("/")
def home():
    return FileResponse(os.path.join(website_dir, "index.html"))

@app.get("/about")
def about():
    return FileResponse(os.path.join(website_dir, "about.html"))

@app.get("/faqs")
def faqs():
    return FileResponse(os.path.join(website_dir, "faqs.html"))

@app.get("/contact")
def contact():
    return FileResponse(os.path.join(website_dir, "contact_us.html"))

@app.get("/login")
def login():
    return FileResponse(os.path.join(website_dir, "login.html"))

@app.get("/assignment-brief")
def assignment_brief():
    return FileResponse(os.path.join(website_dir, "assignment-brief.html"))

@app.get("/mitigating-circumstances")
def mitigating():
    return FileResponse(os.path.join(website_dir, "mitigating-circumstances.html"))

@app.get("/assignment-reviewer")
def reviewer():
    return FileResponse(os.path.join(website_dir, "assignement_reviewer.html"))

@app.get("/your-calendar")
def calendar():
    return FileResponse(os.path.join(website_dir, "your_calendar.html"))