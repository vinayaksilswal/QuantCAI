from fastapi import APIRouter, Request, Form, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from config import settings
from auth import create_access_token
import secrets

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="templates")

@router.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@router.post("/admin/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...)):
    correct_username = secrets.compare_digest(
        username.encode("utf8"), settings.admin_username.encode("utf8")
    )
    correct_password = secrets.compare_digest(
        password.encode("utf8"), settings.admin_password.encode("utf8")
    )
    
    if not (correct_username and correct_password):
        # Redirect back to login with error
        return RedirectResponse(url="/admin/login?error=1", status_code=303)
        
    token = create_access_token(data={"sub": username})
    
    redirect = RedirectResponse(url="/admin", status_code=303)
    redirect.set_cookie(
        key="admin_session",
        value=token,
        httponly=True,
        max_age=86400, # 1 day
        samesite="lax",
        secure=(settings.environment == "production")
    )
    return redirect

@router.get("/admin/logout")
async def logout():
    redirect = RedirectResponse(url="/admin/login", status_code=303)
    redirect.delete_cookie("admin_session")
    return redirect
