from io import BytesIO

from .layout import compute_layout
from .models import DiagramRequest
from .render_pil import render_to_pil


def generate_png(payload: DiagramRequest) -> bytes:
    ir = compute_layout(payload)
    image = render_to_pil(ir)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def generate_jpeg(payload: DiagramRequest) -> bytes:
    ir = compute_layout(payload)
    image = render_to_pil(ir)
    rgb_image = image.convert("RGB")
    output = BytesIO()
    rgb_image.save(output, format="JPEG", quality=95)
    return output.getvalue()


def generate_pdf(payload: DiagramRequest) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    ir = compute_layout(payload)
    image = render_to_pil(ir)

    page_w, page_h = letter
    img_w, img_h = image.size

    margin = 36
    max_w = page_w - 2 * margin
    max_h = page_h - 2 * margin
    scale = min(max_w / img_w, max_h / img_h)
    draw_w = img_w * scale
    draw_h = img_h * scale

    x = (page_w - draw_w) / 2
    y = (page_h - draw_h) / 2

    output = BytesIO()
    c = canvas.Canvas(output, pagesize=letter)
    c.drawImage(ImageReader(image), x, y, width=draw_w, height=draw_h)
    c.showPage()
    c.save()
    return output.getvalue()


def generate_drawio(payload: DiagramRequest) -> bytes:
    from .render_drawio import render_to_drawio

    ir = compute_layout(payload)
    return render_to_drawio(ir)


def generate_excalidraw(payload: DiagramRequest) -> bytes:
    from .render_excalidraw import render_to_excalidraw

    ir = compute_layout(payload)
    return render_to_excalidraw(ir)
