from io import BytesIO
from pathlib import Path
from math import ceil

from PIL import Image, ImageDraw, ImageFont

from .models import DiagramRequest

CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
ICON_ROOT = Path("app/icons/aws")
ICON_MAP = {
    "ec2": ICON_ROOT / "ec2.png",
    "rds": ICON_ROOT / "rds.png",
    "fsx": ICON_ROOT / "fsx.png",
}


def _safe_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def _distribute_servers(total_servers: int, az_count: int) -> list[int]:
    base = total_servers // az_count
    remainder = total_servers % az_count
    return [base + (1 if i < remainder else 0) for i in range(az_count)]


def _draw_box(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], text: str, *, outline: str = "#1F2937", width: int = 3) -> None:
    draw.rounded_rectangle(xy, radius=14, outline=outline, width=width, fill="#F9FAFB")
    draw.text((xy[0] + 16, xy[1] + 12), text, fill="#111827", font=_safe_font(26))


def _load_icon(icon_key: str) -> Image.Image | None:
    icon_path = ICON_MAP[icon_key]
    if not icon_path.exists():
        return None
    with Image.open(icon_path) as icon:
        return icon.convert("RGBA")


def _paste_icon(canvas: Image.Image, icon_key: str, x: int, y: int, size: tuple[int, int]) -> bool:
    icon = _load_icon(icon_key)
    if icon is None:
        return False
    resized = icon.resize(size, Image.Resampling.LANCZOS)
    canvas.paste(resized, (x, y), resized)
    return True


def _draw_ec2_node(canvas: Image.Image, draw: ImageDraw.ImageDraw, x: int, y: int, label: str) -> None:
    node_w = 170
    node_h = 140
    draw.rounded_rectangle((x, y, x + node_w, y + node_h), radius=10, fill="#F8FAFC", outline="#9CA3AF", width=2)
    has_icon = _paste_icon(canvas, "ec2", x + 53, y + 10, (64, 64))
    if not has_icon:
        draw.rounded_rectangle((x + 53, y + 10, x + 117, y + 74), radius=8, fill="#FFE6B3", outline="#9A6700", width=2)
        draw.text((x + 68, y + 32), "EC2", fill="#111827", font=_safe_font(16))

    draw.text((x + 8, y + 80), "EC2 Instance", fill="#111827", font=_safe_font(17))
    if label.startswith("OpenText Fax Server "):
        server_number = label.replace("OpenText Fax Server ", "", 1)
        draw.text((x + 8, y + 102), f"OpenText Fax Server {server_number}", fill="#374151", font=_safe_font(14))
    else:
        draw.text((x + 8, y + 102), label, fill="#374151", font=_safe_font(14))


def _draw_service_node(canvas: Image.Image, draw: ImageDraw.ImageDraw, x: int, y: int, label: str, icon_key: str) -> None:
    node_w = 220
    node_h = 110
    draw.rounded_rectangle((x, y, x + node_w, y + node_h), radius=10, fill="#EFF6FF", outline="#1D4ED8", width=2)
    has_icon = _paste_icon(canvas, icon_key, x + 14, y + 18, (56, 56))
    if not has_icon:
        draw.rounded_rectangle((x + 14, y + 18, x + 70, y + 74), radius=8, fill="#DBEAFE", outline="#1D4ED8", width=2)
        draw.text((x + 26, y + 40), label[:3], fill="#1E3A8A", font=_safe_font(14))
    draw.text((x + 84, y + 44), label, fill="#1E3A8A", font=_safe_font(24))


def generate_png(payload: DiagramRequest) -> bytes:
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color="#FFFFFF")
    draw = ImageDraw.Draw(image)

    title = f"{payload.customer_name} - AWS Architecture"
    draw.text((50, 26), title, fill="#111827", font=_safe_font(44))

    region_box = (60, 120, 1600, 900)
    _draw_box(draw, region_box, f"AWS Region: {payload.region}")

    az_count = payload.availability_zone_count
    inner_left = region_box[0] + 30
    inner_top = region_box[1] + 70
    inner_right = region_box[2] - 30
    inner_bottom = region_box[3] - 40
    gap = 24
    az_width = (inner_right - inner_left - (gap * (az_count - 1))) // az_count

    dist = _distribute_servers(payload.production_server_count, az_count)

    for idx in range(az_count):
        x0 = inner_left + idx * (az_width + gap)
        x1 = x0 + az_width
        y0 = inner_top
        y1 = inner_bottom
        _draw_box(draw, (x0, y0, x1, y1), f"AZ-{idx + 1}", outline="#4B5563", width=2)

        node_count = dist[idx]
        if node_count == 0:
            continue

        cols = min(3, node_count)
        rows = ceil(node_count / cols)
        node_gap_x = 20
        node_gap_y = 20
        node_w = 170
        node_h = 140
        grid_w = cols * node_w + (cols - 1) * node_gap_x
        grid_h = rows * node_h + (rows - 1) * node_gap_y

        start_x = x0 + (az_width - grid_w) // 2
        start_y = y0 + 80 + max(0, (y1 - y0 - 120 - grid_h) // 2)

        server_num = sum(dist[:idx]) + 1
        for n in range(node_count):
            r = n // cols
            c = n % cols
            nx = start_x + c * (node_w + node_gap_x)
            ny = start_y + r * (node_h + node_gap_y)
            _draw_ec2_node(image, draw, nx, ny, f"OpenText Fax Server {server_num}")
            server_num += 1

    if payload.non_production_server_count > 0:
        non_prod_box = (1640, 180, 1880, 900)
        _draw_box(draw, non_prod_box, "Non-Production", outline="#7C3AED")

        max_nodes = payload.non_production_server_count
        for i in range(max_nodes):
            ny = 250 + (i * 150)
            if ny + 140 > non_prod_box[3] - 10:
                break
            _draw_ec2_node(image, draw, 1676, ny, f"OpenText Fax Server {i + 1}")

    services: list[tuple[str, str]] = []
    if payload.include_rds:
        services.append(("Amazon RDS", "rds"))
    if payload.include_fsx:
        services.append(("Amazon FSx", "fsx"))

    if services:
        service_box = (60, 920, 1600, 1070)
        _draw_box(draw, service_box, "Data Tier Services", outline="#1D4ED8", width=2)
        x = service_box[0] + 220
        y = service_box[1] + 26
        spacing = 260
        arrow_start = (830, 900)
        for i, (service, icon_key) in enumerate(services):
            sx = x + i * spacing
            _draw_service_node(image, draw, sx, y, service, icon_key)
            arrow_end = (sx + 110, y)
            draw.line((arrow_start, arrow_end), fill="#1D4ED8", width=3)

    footer = f"Production servers: {payload.production_server_count} | AZs: {payload.availability_zone_count}"
    footer_y = 1040 if services else 1020
    draw.text((50, footer_y), footer, fill="#4B5563", font=_safe_font(24))

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
