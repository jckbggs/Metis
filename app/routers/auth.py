from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.database import create_user, get_user, verify_password

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/signup")
async def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    dob: str = Form(...),
):
    username = username.strip()

    if not username or not password or not dob:
        return RedirectResponse("/signup?error=missing_fields", status_code=303)

    if len(username) > 50:
        return RedirectResponse("/signup?error=username_too_long", status_code=303)

    if password != confirm_password:
        return RedirectResponse("/signup?error=password_mismatch", status_code=303)

    if len(password) < 6:
        return RedirectResponse("/signup?error=password_too_short", status_code=303)

    ok, reason = create_user(username, password, dob)
    if not ok:
        error = "username_taken" if reason == "username_taken" else "db_error"
        return RedirectResponse(f"/signup?error={error}", status_code=303)

    request.session["username"] = username
    return RedirectResponse("/", status_code=303)


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    username = username.strip()
    user = get_user(username)

    if not user or not verify_password(password, user["password_hash"]):
        return RedirectResponse("/login?error=invalid_credentials", status_code=303)

    request.session["username"] = username
    return RedirectResponse("/", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/me")
async def me(request: Request):
    username = request.session.get("username")
    if not username:
        return {"logged_in": False}
    return {"logged_in": True, "username": username}
