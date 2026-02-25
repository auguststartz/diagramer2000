from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from .diagram import generate_png
from .models import DiagramRequest
from .regions import AWS_REGIONS, VALID_REGION_CODES

app = FastAPI(title="AWS Diagram Generator", version="0.1.0")
app.mount("/static", StaticFiles(directory="app/frontend"), name="static")


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    with open("app/frontend/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/v1/regions")
def list_regions() -> dict[str, list[dict[str, str]]]:
    return {"regions": [{"code": code, "name": name} for code, name in AWS_REGIONS]}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/diagram.png")
def render_diagram(payload: DiagramRequest) -> Response:
    if payload.region not in VALID_REGION_CODES:
        raise HTTPException(status_code=400, detail="Unsupported AWS region code")

    png_bytes = generate_png(payload)
    return Response(content=png_bytes, media_type="image/png")
