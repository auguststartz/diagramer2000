from __future__ import annotations

import base64
import hashlib
import json
import textwrap
from pathlib import Path

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
    "okta": ICON_ROOT_CLOUD / "okta.png",
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
    "okta": ("okta",),
}


def _resolve_icon_path(icon_key: str) -> Path | None:
    mapped = ICON_MAP.get(icon_key)
    if mapped and mapped.exists():
        return mapped
    keywords = ICON_KEYWORDS.get(icon_key, ())
    candidates = sorted(
        p
        for root in ALL_ICON_ROOTS
        for p in (root.rglob("*") if root.exists() else [])
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}
    )
    for c in candidates:
        if any(kw in c.name.lower() for kw in keywords):
            return c
    return None


def _load_icon_b64(icon_key: str) -> tuple[str, str] | None:
    """Return (fileId, dataURL) or None."""
    path = _resolve_icon_path(icon_key)
    if path is None:
        return None
    data = path.read_bytes()
    file_id = hashlib.sha256(data).hexdigest()[:20]
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    data_url = f"data:{mime};base64,{base64.b64encode(data).decode()}"
    return file_id, data_url


# Map parent_id -> group ID for grouping children together
_CONTAINER_ROLES = {"region", "az", "customer_network", "non_production", "service_column", "cloud_services"}


def render_to_excalidraw(ir: DiagramIR) -> bytes:
    elements: list[dict] = []
    files: dict[str, dict] = {}
    # Cache loaded icon file IDs
    icon_cache: dict[str, tuple[str, str] | None] = {}

    # Build group mapping: parent_id -> groupId
    group_map: dict[str, str] = {}
    for elem in ir.elements:
        if isinstance(elem, IRRect) and elem.semantic_role in _CONTAINER_ROLES:
            group_map[elem.id] = f"group_{elem.id}"

    def _group_ids_for(parent_id: str | None) -> list[str]:
        ids: list[str] = []
        pid = parent_id
        while pid and pid in group_map:
            ids.append(group_map[pid])
            # Walk up: find the parent's parent
            for e in ir.elements:
                if isinstance(e, IRRect) and e.id == pid:
                    pid = e.parent_id
                    break
            else:
                break
        return ids

    elem_counter = [0]

    def _next_id() -> str:
        elem_counter[0] += 1
        return f"ex_{elem_counter[0]}"

    for elem in ir.elements:
        if isinstance(elem, IRRect):
            group_ids = _group_ids_for(elem.parent_id)
            if elem.id in group_map:
                group_ids.insert(0, group_map[elem.id])

            rect_id = _next_id()
            rect_elem: dict = {
                "id": rect_id,
                "type": "rectangle",
                "x": elem.x,
                "y": elem.y,
                "width": elem.width,
                "height": elem.height,
                "angle": 0,
                "strokeColor": elem.stroke_color,
                "backgroundColor": elem.fill_color,
                "fillStyle": "solid",
                "strokeWidth": elem.stroke_width,
                "roughness": 0,
                "opacity": 100,
                "groupIds": group_ids,
                "roundness": {"type": 3, "value": elem.radius},
                "boundElements": [],
                "locked": False,
                "isDeleted": False,
                "version": 1,
                "versionNonce": 0,
            }

            if elem.label and elem.semantic_role != "ec2_node":
                text_id = _next_id()
                rect_elem["boundElements"] = [{"id": text_id, "type": "text"}]
                elements.append(rect_elem)

                # Bound text element
                if elem.semantic_role in ("cn_node", "cs_node"):
                    tx = elem.x + elem.width // 2
                    ty = elem.y + elem.label_y_offset if elem.label_y_offset >= 0 else elem.y + elem.height // 2
                elif elem.semantic_role == "service_node":
                    tx = elem.x + elem.label_x_offset
                    ty = elem.y + elem.label_y_offset
                else:
                    tx = elem.x + elem.label_x_offset
                    ty = elem.y + elem.label_y_offset

                text_width = max(len(elem.label) * elem.label_font_size * 6 // 10, 30)
                text_height = elem.label_font_size + 8

                elements.append({
                    "id": text_id,
                    "type": "text",
                    "x": tx,
                    "y": ty,
                    "width": text_width,
                    "height": text_height,
                    "angle": 0,
                    "strokeColor": elem.label_color,
                    "backgroundColor": "transparent",
                    "fillStyle": "solid",
                    "strokeWidth": 1,
                    "roughness": 0,
                    "opacity": 100,
                    "groupIds": group_ids,
                    "text": elem.label,
                    "fontSize": elem.label_font_size,
                    "fontFamily": 1,
                    "textAlign": "center" if elem.semantic_role in ("cn_node", "cs_node") else "left",
                    "verticalAlign": "middle" if elem.semantic_role in ("cn_node", "cs_node") else "top",
                    "containerId": rect_id,
                    "boundElements": [],
                    "locked": False,
                    "isDeleted": False,
                    "version": 1,
                    "versionNonce": 0,
                })
            else:
                elements.append(rect_elem)

        elif isinstance(elem, IRText):
            group_ids = []
            if elem.max_width > 0:
                char_width = elem.font_size * 0.6
                chars_per_line = max(1, int(elem.max_width / char_width))
                wrapped_lines = textwrap.wrap(elem.text, width=chars_per_line)
                display_text = "\n".join(wrapped_lines) if wrapped_lines else elem.text
                line_height = int(elem.font_size * 1.4)
                text_width = elem.max_width
                text_height = max(line_height, len(wrapped_lines) * line_height)
            else:
                display_text = elem.text
                text_width = max(len(elem.text) * elem.font_size * 6 // 10, 30)
                text_height = elem.font_size + 8
            elements.append({
                "id": _next_id(),
                "type": "text",
                "x": elem.x,
                "y": elem.y,
                "width": text_width,
                "height": text_height,
                "angle": 0,
                "strokeColor": elem.color,
                "backgroundColor": "transparent",
                "fillStyle": "solid",
                "strokeWidth": 1,
                "roughness": 0,
                "opacity": 100,
                "groupIds": group_ids,
                "text": display_text,
                "fontSize": elem.font_size,
                "fontFamily": 1,
                "textAlign": "left",
                "verticalAlign": "top",
                "boundElements": [],
                "locked": False,
                "isDeleted": False,
                "version": 1,
                "versionNonce": 0,
            })

        elif isinstance(elem, IRLine):
            elements.append({
                "id": _next_id(),
                "type": "line",
                "x": elem.x1,
                "y": elem.y1,
                "width": abs(elem.x2 - elem.x1),
                "height": abs(elem.y2 - elem.y1),
                "angle": 0,
                "strokeColor": elem.color,
                "backgroundColor": "transparent",
                "fillStyle": "solid",
                "strokeWidth": elem.width,
                "roughness": 0,
                "opacity": 100,
                "groupIds": [],
                "points": [
                    [0, 0],
                    [elem.x2 - elem.x1, elem.y2 - elem.y1],
                ],
                "boundElements": [],
                "locked": False,
                "isDeleted": False,
                "version": 1,
                "versionNonce": 0,
            })

        elif isinstance(elem, IRDot):
            elements.append({
                "id": _next_id(),
                "type": "ellipse",
                "x": elem.cx - elem.radius,
                "y": elem.cy - elem.radius,
                "width": elem.radius * 2,
                "height": elem.radius * 2,
                "angle": 0,
                "strokeColor": elem.color,
                "backgroundColor": elem.color,
                "fillStyle": "solid",
                "strokeWidth": 0,
                "roughness": 0,
                "opacity": 100,
                "groupIds": [],
                "boundElements": [],
                "locked": False,
                "isDeleted": False,
                "version": 1,
                "versionNonce": 0,
            })

        elif isinstance(elem, IRIcon):
            group_ids = []

            # Try to embed icon as image
            if elem.icon_key not in icon_cache:
                icon_cache[elem.icon_key] = _load_icon_b64(elem.icon_key)

            icon_data = icon_cache[elem.icon_key]
            if icon_data:
                file_id, data_url = icon_data
                if file_id not in files:
                    files[file_id] = {
                        "mimeType": "image/png",
                        "id": file_id,
                        "dataURL": data_url,
                        "created": 0,
                        "lastRetrieved": 0,
                    }
                elements.append({
                    "id": _next_id(),
                    "type": "image",
                    "x": elem.x,
                    "y": elem.y,
                    "width": elem.width,
                    "height": elem.height,
                    "angle": 0,
                    "strokeColor": "transparent",
                    "backgroundColor": "transparent",
                    "fillStyle": "solid",
                    "strokeWidth": 0,
                    "roughness": 0,
                    "opacity": 100,
                    "groupIds": group_ids,
                    "fileId": file_id,
                    "scale": [1, 1],
                    "boundElements": [],
                    "locked": False,
                    "isDeleted": False,
                    "version": 1,
                    "versionNonce": 0,
                })
            else:
                # Fallback: colored rect with text label
                fallback_id = _next_id()
                text_id = _next_id()
                elements.append({
                    "id": fallback_id,
                    "type": "rectangle",
                    "x": elem.x,
                    "y": elem.y,
                    "width": elem.width,
                    "height": elem.height,
                    "angle": 0,
                    "strokeColor": "#9A6700" if elem.icon_key == "ec2" else "#1D4ED8",
                    "backgroundColor": "#FFE6B3" if elem.icon_key == "ec2" else "#DBEAFE",
                    "fillStyle": "solid",
                    "strokeWidth": 2,
                    "roughness": 0,
                    "opacity": 100,
                    "groupIds": group_ids,
                    "roundness": {"type": 3, "value": 8},
                    "boundElements": [{"id": text_id, "type": "text"}],
                    "locked": False,
                    "isDeleted": False,
                    "version": 1,
                    "versionNonce": 0,
                })
                elements.append({
                    "id": text_id,
                    "type": "text",
                    "x": elem.x + elem.width // 4,
                    "y": elem.y + elem.height // 4,
                    "width": elem.width // 2,
                    "height": elem.height // 2,
                    "angle": 0,
                    "strokeColor": "#111827",
                    "backgroundColor": "transparent",
                    "fillStyle": "solid",
                    "strokeWidth": 1,
                    "roughness": 0,
                    "opacity": 100,
                    "groupIds": group_ids,
                    "text": elem.icon_key.upper()[:3],
                    "fontSize": max(elem.width // 4, 8),
                    "fontFamily": 1,
                    "textAlign": "center",
                    "verticalAlign": "middle",
                    "containerId": fallback_id,
                    "boundElements": [],
                    "locked": False,
                    "isDeleted": False,
                    "version": 1,
                    "versionNonce": 0,
                })

    output = {
        "type": "excalidraw",
        "version": 2,
        "source": "diagramer2000",
        "elements": elements,
        "appState": {
            "viewBackgroundColor": "#ffffff",
            "gridSize": None,
        },
        "files": files,
    }

    return json.dumps(output, indent=2).encode("utf-8")
