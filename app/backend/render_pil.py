from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .ir import DiagramIR, IRDot, IRIcon, IRLine, IRRect, IRText

ICON_ROOT = Path("app/icons/aws")
ICON_ROOT_ONPREM = Path("app/icons/onprem")
ICON_ROOT_CLOUD = Path("app/icons/cloud")
ALL_ICON_ROOTS = [ICON_ROOT, ICON_ROOT_ONPREM, ICON_ROOT_CLOUD]

ICON_MAP = {
    "ec2": ICON_ROOT / "ec2.png",
    "rds": ICON_ROOT / "rds.png",
    "fsx": ICON_ROOT / "fsx.png",
    "vpn": ICON_ROOT / "vpn.png",
    "epic": ICON_ROOT_ONPREM / "epic.png",
    "mfp": ICON_ROOT_ONPREM / "mfp.png",
    "smtp": ICON_ROOT_ONPREM / "smtp.png",
    "exchange": ICON_ROOT_ONPREM / "exchange.png",
    "directory": ICON_ROOT_ONPREM / "directory.png",
    "autoprint": ICON_ROOT_ONPREM / "autoprint.png",
    "otfaim": ICON_ROOT_ONPREM / "otfaim.png",
    "office365": ICON_ROOT_CLOUD / "office365.png",
    "hosted_epic": ICON_ROOT_CLOUD / "hosted_epic.png",
    "entra": ICON_ROOT_CLOUD / "entra.png",
}
ICON_KEYWORDS = {
    "ec2": ("ec2", "elastic-compute-cloud"),
    "rds": ("rds", "relational-database"),
    "fsx": ("fsx", "file-system"),
    "vpn": ("vpn", "transit-gateway", "virtual-private-network"),
    "epic": ("epic",),
    "mfp": ("mfp", "multifunction"),
    "smtp": ("smtp", "email"),
    "exchange": ("exchange",),
    "directory": ("directory", "ldap", "active-directory"),
    "autoprint": ("autoprint", "print"),
    "otfaim": ("otfaim",),
    "office365": ("office365", "o365"),
    "hosted_epic": ("hosted_epic", "hosted-epic"),
    "entra": ("entra", "azure-ad"),
}
_RESOLVED_ICON_PATHS: dict[str, Path | None] = {}


def _safe_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def _resolve_icon_path(icon_key: str) -> Path | None:
    if icon_key in _RESOLVED_ICON_PATHS:
        return _RESOLVED_ICON_PATHS[icon_key]

    mapped = ICON_MAP.get(icon_key)
    if mapped and mapped.exists():
        _RESOLVED_ICON_PATHS[icon_key] = mapped
        return mapped

    keywords = ICON_KEYWORDS.get(icon_key, ())
    candidates = sorted(
        p
        for root in ALL_ICON_ROOTS
        for p in (root.rglob("*") if root.exists() else [])
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}
    )
    for candidate in candidates:
        name = candidate.name.lower()
        if any(keyword in name for keyword in keywords):
            _RESOLVED_ICON_PATHS[icon_key] = candidate
            return candidate

    _RESOLVED_ICON_PATHS[icon_key] = None
    return None


def _load_icon(icon_key: str) -> Image.Image | None:
    icon_path = _resolve_icon_path(icon_key)
    if icon_path is None:
        return None
    with Image.open(icon_path) as icon:
        return icon.convert("RGBA")


def _wrap_text_pil(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, max_width: int) -> str:
    """Word-wrap text to fit within max_width pixels using actual font metrics."""
    words = text.split()
    lines: list[str] = []
    current_line = ""
    for word in words:
        test = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)


def _paste_icon(canvas: Image.Image, icon_key: str, x: int, y: int, size: tuple[int, int]) -> bool:
    icon = _load_icon(icon_key)
    if icon is None:
        return False
    resized = icon.resize(size, Image.Resampling.LANCZOS)
    canvas.paste(resized, (x, y), resized)
    return True


def render_to_pil(ir: DiagramIR) -> Image.Image:
    image = Image.new("RGB", (ir.canvas_width, ir.canvas_height), color="#FFFFFF")
    draw = ImageDraw.Draw(image)

    for elem in ir.elements:
        if isinstance(elem, IRRect):
            x0 = elem.x
            y0 = elem.y
            x1 = elem.x + elem.width
            y1 = elem.y + elem.height
            draw.rounded_rectangle(
                (x0, y0, x1, y1),
                radius=elem.radius,
                outline=elem.stroke_color,
                width=elem.stroke_width,
                fill=elem.fill_color,
            )
            if elem.label:
                if elem.semantic_role in ("cn_node", "cs_node") and elem.label_x_offset == -1:
                    # Center label horizontally; use label_y_offset for vertical
                    font = _safe_font(elem.label_font_size)
                    bbox = draw.textbbox((0, 0), elem.label, font=font)
                    tw = bbox[2] - bbox[0]
                    ly = y0 + elem.label_y_offset if elem.label_y_offset >= 0 else y0 + (elem.height - (bbox[3] - bbox[1])) // 2
                    draw.text(
                        (x0 + (elem.width - tw) // 2, ly),
                        elem.label, fill=elem.label_color, font=font,
                    )
                elif elem.semantic_role == "service_node":
                    # Service node: icon-based fallback handled by IRIcon
                    draw.text(
                        (x0 + elem.label_x_offset, y0 + elem.label_y_offset),
                        elem.label, fill=elem.label_color,
                        font=_safe_font(elem.label_font_size),
                    )
                elif elem.semantic_role == "ec2_node":
                    # EC2 nodes: label/sublabel handled by separate IRText elements
                    pass
                else:
                    draw.text(
                        (x0 + elem.label_x_offset, y0 + elem.label_y_offset),
                        elem.label, fill=elem.label_color,
                        font=_safe_font(elem.label_font_size),
                    )

        elif isinstance(elem, IRText):
            font = _safe_font(elem.font_size)
            if elem.max_width > 0:
                wrapped = _wrap_text_pil(draw, elem.text, font, elem.max_width)
                draw.multiline_text(
                    (elem.x, elem.y), wrapped,
                    fill=elem.color, font=font,
                )
            else:
                draw.text(
                    (elem.x, elem.y), elem.text,
                    fill=elem.color, font=font,
                )

        elif isinstance(elem, IRLine):
            draw.line(
                (elem.x1, elem.y1, elem.x2, elem.y2),
                fill=elem.color, width=elem.width,
            )

        elif isinstance(elem, IRDot):
            r = elem.radius
            draw.ellipse(
                (elem.cx - r, elem.cy - r, elem.cx + r, elem.cy + r),
                fill=elem.color,
            )

        elif isinstance(elem, IRIcon):
            has_icon = _paste_icon(
                image, elem.icon_key, elem.x, elem.y,
                (elem.width, elem.height),
            )
            if not has_icon:
                # Fallback rectangle for missing icons
                draw.rounded_rectangle(
                    (elem.x, elem.y, elem.x + elem.width, elem.y + elem.height),
                    radius=8, fill="#FFE6B3" if elem.icon_key == "ec2" else "#DBEAFE",
                    outline="#9A6700" if elem.icon_key == "ec2" else "#1D4ED8",
                    width=2,
                )
                font = _safe_font(max(elem.width // 4, 8))
                draw.text(
                    (elem.x + elem.width // 4, elem.y + elem.height // 4),
                    elem.icon_key.upper()[:3],
                    fill="#111827" if elem.icon_key == "ec2" else "#1E3A8A",
                    font=font,
                )

    return image
