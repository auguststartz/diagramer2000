from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from .diagram import generate_drawio, generate_excalidraw, generate_jpeg, generate_pdf, generate_png
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


@app.post("/api/v1/diagram.jpg")
def render_diagram_jpeg(payload: DiagramRequest) -> Response:
    if payload.region not in VALID_REGION_CODES:
        raise HTTPException(status_code=400, detail="Unsupported AWS region code")

    jpeg_bytes = generate_jpeg(payload)
    return Response(content=jpeg_bytes, media_type="image/jpeg")


@app.post("/api/v1/diagram.pdf")
def render_diagram_pdf(payload: DiagramRequest) -> Response:
    if payload.region not in VALID_REGION_CODES:
        raise HTTPException(status_code=400, detail="Unsupported AWS region code")

    pdf_bytes = generate_pdf(payload)
    return Response(content=pdf_bytes, media_type="application/pdf")


@app.post("/api/v1/diagram.drawio")
def render_diagram_drawio(payload: DiagramRequest) -> Response:
    if payload.region not in VALID_REGION_CODES:
        raise HTTPException(status_code=400, detail="Unsupported AWS region code")

    drawio_bytes = generate_drawio(payload)
    return Response(
        content=drawio_bytes,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=diagram.drawio"},
    )


@app.post("/api/v1/diagram.excalidraw")
def render_diagram_excalidraw(payload: DiagramRequest) -> Response:
    if payload.region not in VALID_REGION_CODES:
        raise HTTPException(status_code=400, detail="Unsupported AWS region code")

    excalidraw_bytes = generate_excalidraw(payload)
    return Response(
        content=excalidraw_bytes,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=diagram.excalidraw"},
    )
