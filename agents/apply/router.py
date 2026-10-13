from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.apply.manager import ALLOWED_ACTIONS, TERMINAL, manager

router = APIRouter()


class StartRequest(BaseModel):
    run_id: str
    kind: str = "apply"
    site: str | None = None       # kind == "login": which site to connect
    job: dict = {}
    applicant: dict = {}
    files: dict = {}
    settings: dict = {}
    easy_apply: dict = {}
    gmail: dict | None = None
    sessions: dict = {}
    known_accounts: list[str] = []


class VerificationRequest(BaseModel):
    value: str


class InputRequest(BaseModel):
    kind: str
    x: float | None = None
    y: float | None = None
    text: str | None = None
    key: str | None = None
    dy: float | None = None


ALLOWED_KEYS = {"Enter", "Tab", "Backspace", "Escape", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space", "Shift+Tab"}


def _get(run_id: str):
    run = manager.get(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@router.post("/runs")
async def start_run(req: StartRequest):
    run = manager.start(req.model_dump())
    return {"run_id": run.id, "status": run.status}


@router.get("/runs/{run_id}")
async def get_run(run_id: str, screenshot: int = 1):
    return _get(run_id).snapshot(include_screenshot=bool(screenshot))


@router.post("/runs/{run_id}/input")
async def send_input(run_id: str, req: InputRequest):
    run = _get(run_id)
    page = run.view_page()
    if run.status in TERMINAL or page is None or page.is_closed():
        raise HTTPException(409, "The browser is not available")
    if req.kind == "click" and req.x is not None and req.y is not None:
        await page.mouse.click(req.x, req.y)
    elif req.kind == "type" and req.text:
        await page.keyboard.type(req.text[:2000], delay=15)
    elif req.kind == "key" and req.key in ALLOWED_KEYS:
        await page.keyboard.press(req.key)
    elif req.kind == "scroll" and req.dy is not None:
        await page.mouse.wheel(0, max(-3000, min(3000, req.dy)))
    else:
        raise HTTPException(400, "Invalid input")
    return {"ok": True}


@router.post("/runs/{run_id}/verification")
async def provide_verification(run_id: str, req: VerificationRequest):
    run = _get(run_id)
    if run.status != "needs_input" or not run.needs or run.needs.get("kind") != "verification":
        raise HTTPException(409, "The run isn't waiting for a verification code")
    value = req.value.strip()
    if not value or len(value) > 2000:
        raise HTTPException(400, "Enter the code or link")
    run.provided = value
    run.actions.put_nowait("resume")
    return {"ok": True}


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    manager.cancel(_get(run_id))
    return {"ok": True}


@router.post("/runs/{run_id}/{action}")
async def control_run(run_id: str, action: str):
    run = _get(run_id)
    allowed = ALLOWED_ACTIONS.get(action)
    if allowed is None:
        raise HTTPException(400, "Unknown action")
    if run.status not in allowed:
        raise HTTPException(409, f"'{action}' is not available while the run is {run.status.replace('_', ' ')}")
    run.actions.put_nowait(action)
    return {"ok": True}
