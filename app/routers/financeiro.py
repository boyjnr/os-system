from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/os",
    tags=["OS"]
)

@router.get("/nova", response_class=HTMLResponse)
def os_nova(request: Request):
    return templates.TemplateResponse(
        "os_nova.html",
        {
            "request": request
        }
    )
