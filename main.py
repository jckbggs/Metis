import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone
from threading import Lock

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from chatbot.mitigating_circumstances import MitigatingCircumstancesBot
from chatbot.website_info_bot import WebsiteInfoBot
from chatbot.assignment_brief_bot import AssignmentBriefBot

from database.auth_queries import get_user_by_username
from database.password_utils import verify_password
from database.auth_create import create_user
from database.brief_create import create_demo_brief_for_user
from database.brief_queries import get_brief_for_user, get_marking_criteria_for_brief


app = FastAPI()

load_dotenv(Path(__file__).resolve().parent / "chatbot" / ".env", override=True)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "change_me")
)

BASE_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = BASE_DIR / "website"

EVALUATION_LOG_PATH = BASE_DIR / "data" / "evaluation_logs" / "chatbot_evaluation.jsonl"
evaluation_log_lock = Lock()

mitigating_bot = MitigatingCircumstancesBot()
website_info_bot = WebsiteInfoBot()
assignment_brief_bot = AssignmentBriefBot()

GUEST_CHAT_LIMIT = 15
ADMIN_USERNAME = "admin"


class ChatRequest(BaseModel):
    message: str


def get_anonymous_participant_id(request: Request) -> str:
    """
    Creates one anonymous participant ID per browser session.
    This avoids storing the real username in evaluation logs.
    """
    if "anonymous_participant_id" not in request.session:
        request.session["anonymous_participant_id"] = "P-" + str(uuid.uuid4())[:8]

    return request.session["anonymous_participant_id"]


def save_evaluation_log(
    request: Request,
    bot_name: str,
    user_input: str,
    bot_output: str,
    response_time_ms: int,
    logged_in: bool = False,
    success: bool = True,
    error: str | None = None,
):
    """
    Saves anonymised chatbot evaluation data to a JSONL file.
    It does not save the real username.
    """
    try:
        EVALUATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "participant_id": get_anonymous_participant_id(request),
            "bot_name": bot_name,
            "account_type": "logged_in" if logged_in else "guest",
            "user_input": user_input,
            "bot_output": bot_output,
            "response_time_ms": response_time_ms,
            "success": success,
            "error": str(error) if error else None,
        }

        with evaluation_log_lock:
            with EVALUATION_LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    except Exception as log_error:
        print("Evaluation logging failed:", log_error)


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

    try:
        create_demo_brief_for_user(username, demo_brief)
    except Exception as e:
        print("Signup brief creation error:", e)
        return RedirectResponse(url="/signup?error=db_error", status_code=303)

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
        "username": username if username else None,
        "is_admin": username == ADMIN_USERNAME
    }


@app.get("/api/evaluation/logs")
def evaluation_logs(request: Request):
    username = request.session.get("username")

    if username != ADMIN_USERNAME:
        return {
            "error": "Admin access required."
        }

    empty_summary = {
        "total_interactions": 0,
        "average_response_time_ms": 0,
        "success_rate": 0,
        "unique_participants": 0,
        "most_used_bot": None
    }

    if not EVALUATION_LOG_PATH.exists():
        return {
            "logs": [],
            "summary": empty_summary,
            "bot_counts": {}
        }

    logs = []

    with EVALUATION_LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    total = len(logs)

    if total == 0:
        return {
            "logs": [],
            "summary": empty_summary,
            "bot_counts": {}
        }

    response_times = [
        item.get("response_time_ms", 0)
        for item in logs
        if isinstance(item.get("response_time_ms"), int)
    ]

    average_response_time = (
        round(sum(response_times) / len(response_times), 2)
        if response_times else 0
    )

    successful = sum(1 for item in logs if item.get("success") is True)
    success_rate = round((successful / total) * 100, 2)

    participants = {
        item.get("participant_id")
        for item in logs
        if item.get("participant_id")
    }

    bot_counts = {}
    for item in logs:
        bot_name = item.get("bot_name", "unknown")
        bot_counts[bot_name] = bot_counts.get(bot_name, 0) + 1

    most_used_bot = max(bot_counts, key=bot_counts.get) if bot_counts else None

    return {
        "logs": logs,
        "summary": {
            "total_interactions": total,
            "average_response_time_ms": average_response_time,
            "success_rate": success_rate,
            "unique_participants": len(participants),
            "most_used_bot": most_used_bot
        },
        "bot_counts": bot_counts
    }


@app.post("/chat")
def chat(req: ChatRequest, request: Request):
    start_time = time.perf_counter()

    username = request.session.get("username")
    logged_in = bool(username)

    reply = ""
    success = True
    error = None

    try:
        brief = get_brief_for_user(username) if username else None

        reply = mitigating_bot.reply(
            user_input=req.message,
            username=username,
            brief=brief,
        )

        return {"reply": reply}

    except Exception as e:
        success = False
        error = str(e)
        reply = "Sorry, something went wrong."
        print("Mitigating bot error:", e)
        return {"reply": reply}

    finally:
        response_time_ms = int((time.perf_counter() - start_time) * 1000)

        save_evaluation_log(
            request=request,
            bot_name="mitigating_circumstances",
            user_input=req.message,
            bot_output=reply,
            response_time_ms=response_time_ms,
            logged_in=logged_in,
            success=success,
            error=error,
        )


@app.post("/chat/website-info")
def website_info_chat(req: ChatRequest, request: Request):
    start_time = time.perf_counter()

    username = request.session.get("username")
    logged_in = bool(username)

    reply = ""
    success = True
    error = None

    try:
        if not logged_in:
            current_count = request.session.get("guest_chat_count", 0)

            if current_count >= GUEST_CHAT_LIMIT:
                reply = "You have reached the guest chat limit. Please log in to continue using the chatbot."

                return {
                    "reply": reply,
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

    except Exception as e:
        success = False
        error = str(e)
        reply = "Sorry, something went wrong."
        print("Website info bot error:", e)

        return {
            "reply": reply,
            "remaining": None,
            "logged_in": logged_in,
            "username": username
        }

    finally:
        response_time_ms = int((time.perf_counter() - start_time) * 1000)

        save_evaluation_log(
            request=request,
            bot_name="website_information",
            user_input=req.message,
            bot_output=reply,
            response_time_ms=response_time_ms,
            logged_in=logged_in,
            success=success,
            error=error,
        )


@app.post("/chat/assignment-brief")
def assignment_brief_chat(req: ChatRequest, request: Request):
    start_time = time.perf_counter()

    username = request.session.get("username")
    logged_in = bool(username)

    reply = ""
    success = True
    error = None

    try:
        if not username:
            reply = "Please log in to use the assignment brief chatbot."
            return {"reply": reply}

        brief = get_brief_for_user(username)

        if not brief:
            reply = f"Hi {username}. I could not find a brief linked to your account."
            return {"reply": reply}

        criteria_rows = get_marking_criteria_for_brief(brief["brief_id"])

        reply = assignment_brief_bot.reply(
            user_input=req.message,
            username=username,
            brief=brief,
            criteria_rows=criteria_rows,
        )

        return {"reply": reply}

    except Exception as e:
        success = False
        error = str(e)
        reply = "Sorry, something went wrong."
        print("Assignment brief bot error:", e)
        return {"reply": reply}

    finally:
        response_time_ms = int((time.perf_counter() - start_time) * 1000)

        save_evaluation_log(
            request=request,
            bot_name="assignment_brief",
            user_input=req.message,
            bot_output=reply,
            response_time_ms=response_time_ms,
            logged_in=logged_in,
            success=success,
            error=error,
        )


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


@app.get("/evaluation-dashboard")
def evaluation_dashboard_page(request: Request):
    username = request.session.get("username")

    if username != ADMIN_USERNAME:
        return RedirectResponse(url="/login", status_code=303)

    return FileResponse(WEBSITE_DIR / "evaluation-dashboard.html")


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