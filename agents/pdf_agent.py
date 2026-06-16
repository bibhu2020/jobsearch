import os
from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader
import markdown as md
from playwright.async_api import async_playwright

router = APIRouter()

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

TEMPLATE_MAP = {
    "cover_letter": "cover_letter.html",
    "resume": "resume.html",
    "interview_questions": "interview_questions.html",
    "company_brief": "company_brief.html",
}


class ExportRequest(BaseModel):
    content: str
    type: str
    title: str = ""
    company: str = ""


@router.post("/export")
async def export_pdf(req: ExportRequest):
    template_name = TEMPLATE_MAP.get(req.type, "cover_letter.html")
    template = jinja_env.get_template(template_name)

    html_content = md.markdown(
        req.content,
        extensions=["extra", "nl2br"],
    )
    html = template.render(
        content=html_content,
        title=req.title,
        company=req.company,
        kit_type=req.type.replace("_", " ").title(),
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        pdf_bytes = await page.pdf(
            format="A4",
            margin={"top": "2cm", "right": "2cm", "bottom": "2cm", "left": "2cm"},
            print_background=True,
        )
        await browser.close()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{req.type}.pdf"'},
    )
