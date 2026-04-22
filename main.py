import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from chatbot.mitigating_circumstances import MitigatingAgent
from chatbot.website_info_bot import WebsiteInfoBot
from chatbot.assignment_brief_bot import AssignmentBriefBot

from database.auth_queries import get_user_by_username
from database.password_utils import verify_password
from database.auth_create import create_user
from database.brief_create import create_demo_brief_for_user
from database.brief_queries import get_brief_for_user, get_marking_criteria_for_brief

app = FastAPI()

load_dotenv(Path(__file__).resolve().parent / "chatbot" / ".env")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "change_me")
)

BASE_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = BASE_DIR / "website"

mitigating_bot = MitigatingAgent()
website_info_bot = WebsiteInfoBot()
assignment_brief_bot = AssignmentBriefBot()

GUEST_CHAT_LIMIT = 15


class ChatRequest(BaseModel):
    message: str


app.mount("/static", StaticFiles(directory=str(WEBSITE_DIR)), name="static")


@app.post("/api/signup")
def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    dob: str = Form(...),
    demo_brief: str = Form(...)
):
    username = username.strip()

    if not username or not password or not confirm_password or not dob or not demo_brief:
        return RedirectResponse(url="/signup?error=missing_fields", status_code=303)

    if len(username) > 50:
        return RedirectResponse(url="/signup?error=username_too_long", status_code=303)

    if len(password) < 6:
        return RedirectResponse(url="/signup?error=password_too_short", status_code=303)

    if password != confirm_password:
        return RedirectResponse(url="/signup?error=password_mismatch", status_code=303)

    ok, err = create_user(username, password, dob)

    if not ok:
        if err == "username_taken":
            return RedirectResponse(url="/signup?error=username_taken", status_code=303)
        return RedirectResponse(url="/signup?error=db_error", status_code=303)

    create_demo_brief_for_user(username, demo_brief)

    request.session["username"] = username
    request.session.pop("guest_chat_count", None)

    return RedirectResponse(url="/", status_code=303)


@app.post("/api/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    username = username.strip()
    user = get_user_by_username(username)

    if not user:
        return RedirectResponse(url="/login?error=invalid_credentials", status_code=303)

    if not verify_password(password, user["password_hash"]):
        return RedirectResponse(url="/login?error=invalid_credentials", status_code=303)

    request.session["username"] = user["username"]
    request.session.pop("guest_chat_count", None)

    return RedirectResponse(url="/", status_code=303)


@app.get("/api/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.get("/api/me")
def api_me(request: Request):
    username = request.session.get("username")
    return {
        "logged_in": bool(username),
        "username": username if username else None
    }


@app.post("/chat")
def chat(req: ChatRequest):
    reply = mitigating_bot.handle(req.message)
    return {"reply": reply}


@app.post("/chat/website-info")
def website_info_chat(req: ChatRequest, request: Request):
    username = request.session.get("username")
    logged_in = bool(username)

    if not logged_in:
        current_count = request.session.get("guest_chat_count", 0)

        if current_count >= GUEST_CHAT_LIMIT:
            return {
                "reply": "You have reached the guest chat limit. Please log in to continue using the chatbot.",
                "remaining": 0,
                "logged_in": False,
                "username": None
            }

        request.session["guest_chat_count"] = current_count + 1
        remaining = GUEST_CHAT_LIMIT - request.session["guest_chat_count"]

        reply = website_info_bot.reply(
            req.message,
            username=None,
            logged_in=False
        )

        return {
            "reply": reply,
            "remaining": remaining,
            "logged_in": False,
            "username": None
        }

    reply = website_info_bot.reply(
        req.message,
        username=username,
        logged_in=True
    )

    return {
        "reply": reply,
        "remaining": None,
        "logged_in": True,
        "username": username
    }


@app.post("/chat/assignment-brief")
def assignment_brief_chat(req: ChatRequest, request: Request):
    username = request.session.get("username")

    if not username:
        return {"reply": "Please log in to use the assignment brief chatbot."}

    brief = get_brief_for_user(username)

    if not brief:
        return {"reply": f"Hi {username}. I could not find a brief linked to your account."}

    criteria_rows = get_marking_criteria_for_brief(brief["brief_id"])

    reply = assignment_brief_bot.reply(
        user_input=req.message,
        username=username,
        brief=brief,
        criteria_rows=criteria_rows,
    )

    return {"reply": reply}


@app.get("/")
def home():
    return FileResponse(WEBSITE_DIR / "index.html")


@app.get("/mitigating-circumstances")
def mitigating_page():
    return FileResponse(WEBSITE_DIR / "mitigating-circumstances.html")


@app.get("/website-information")
def website_information_page():
    return FileResponse(WEBSITE_DIR / "website-information.html")


@app.get("/assignment-brief")
def assignment_brief_page():
    return FileResponse(WEBSITE_DIR / "assignment-brief.html")


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


@app.get("/signup")
def signup_page():
    return FileResponse(WEBSITE_DIR / "signup.html")


@app.get("/your-calendar")
def your_calendar_page():
    return FileResponse(WEBSITE_DIR / "your_calendar.html")


@app.get("/assignment-calendar")
def assignment_calendar_page():
    return FileResponse(WEBSITE_DIR / "assignment-calendar.html")