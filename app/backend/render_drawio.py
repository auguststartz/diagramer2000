from __future__ import annotations

import xml.etree.ElementTree as ET

from .ir import DiagramIR, IRDot, IRIcon, IRLine, IRRect, IRText

# draw.io AWS4 stencil style fragments keyed by semantic_role
_ROLE_STYLES: dict[str, str] = {
    "region": (
        "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;"
        "grStroke=1;verticalAlign=top;align=left;spacingLeft=30;"
        "dashed=0;"
    ),
    "az": (
        "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_availability_zone;"
        "grStroke=1;verticalAlign=top;align=left;spacingLeft=30;"
        "dashed=1;"
    ),
    "customer_network": (
        "rounded=1;arcSize=6;verticalAlign=top;align=left;spacingLeft=10;"
        "dashed=0;"
    ),
    "non_production": (
        "rounded=1;arcSize=6;verticalAlign=top;align=left;spacingLeft=10;"
        "dashed=0;"
    ),
    "service_column": (
        "rounded=1;arcSize=6;verticalAlign=top;align=left;spacingLeft=10;"
        "dashed=0;"
    ),
}

_SERVICE_ICON_STYLES: dict[str, str] = {
    "ec2": "shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;",
    "rds": "shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds;",
    "fsx": "shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.fsx;",
    "vpn": "shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.transit_gateway;",
}


def _color_style(fill: str, stroke: str, stroke_w: int, font_color: str, font_size: int) -> str:
    return (
        f"fillColor={fill};strokeColor={stroke};strokeWidth={stroke_w};"
        f"fontColor={font_color};fontSize={font_size};"
    )


def _find_parent_cell(elem_id: str, parent_id: str | None, id_map: dict[str, str]) -> str:
    if parent_id and parent_id in id_map:
        return id_map[parent_id]
    return "1"


def render_to_drawio(ir: DiagramIR) -> bytes:
    root = ET.Element("mxfile", host="app.diagrams.net", type="device")
    diagram = ET.SubElement(root, "diagram", name="AWS Architecture", id="d0")
    model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": "0", "dy": "0", "grid": "1", "gridSize": "10",
        "guides": "1", "tooltips": "1", "connect": "1",
        "arrows": "1", "fold": "1", "page": "1",
        "pageScale": "1",
        "pageWidth": str(ir.canvas_width),
        "pageHeight": str(ir.canvas_height),
    })
    mxroot = ET.SubElement(model, "root")

    # Default parent cells required by draw.io
    ET.SubElement(mxroot, "mxCell", id="0")
    ET.SubElement(mxroot, "mxCell", id="1", parent="0")

    # Map IR element id -> draw.io cell id
    id_map: dict[str, str] = {}
    cell_counter = [2]

    def next_cell_id() -> str:
        cid = str(cell_counter[0])
        cell_counter[0] += 1
        return cid

    # Collect parent rects (containers) so we can compute relative coords for children
    parent_origins: dict[str, tuple[int, int]] = {}

    # First pass: register all rect elements that act as containers
    for elem in ir.elements:
        if isinstance(elem, IRRect):
            parent_origins[elem.id] = (elem.x, elem.y)

    for elem in ir.elements:
        if isinstance(elem, IRRect):
            cid = next_cell_id()
            id_map[elem.id] = cid

            parent_cell = _find_parent_cell(elem.id, elem.parent_id, id_map)
            is_container = elem.semantic_role in (
                "region", "az", "customer_network", "non_production", "service_column",
            )

            # Compute position relative to parent container
            x, y = elem.x, elem.y
            if elem.parent_id and elem.parent_id in parent_origins:
                px, py = parent_origins[elem.parent_id]
                x -= px
                y -= py

            role_style = _ROLE_STYLES.get(elem.semantic_role, "rounded=1;arcSize=6;")
            color_part = _color_style(
                elem.fill_color, elem.stroke_color, elem.stroke_width,
                elem.label_color, elem.label_font_size,
            )
            container_part = "container=1;" if is_container else ""
            style = f"{role_style}{color_part}{container_part}"

            label = elem.label if elem.semantic_role != "ec2_node" else ""

            cell = ET.SubElement(mxroot, "mxCell", {
                "id": cid,
                "value": label,
                "style": style,
                "vertex": "1",
                "parent": parent_cell,
            })
            if is_container:
                cell.set("connectable", "0")

            ET.SubElement(cell, "mxGeometry", {
                "x": str(x), "y": str(y),
                "width": str(elem.width), "height": str(elem.height),
                "as": "geometry",
            })

        elif isinstance(elem, IRText):
            cid = next_cell_id()
            id_map[elem.id] = cid

            style = (
                f"text;html=1;resizable=0;autosize=1;align=left;verticalAlign=middle;"
                f"fontSize={elem.font_size};fontColor={elem.color};"
                f"fillColor=none;strokeColor=none;"
            )

            cell = ET.SubElement(mxroot, "mxCell", {
                "id": cid,
                "value": elem.text,
                "style": style,
                "vertex": "1",
                "parent": "1",
            })
            ET.SubElement(cell, "mxGeometry", {
                "x": str(elem.x), "y": str(elem.y),
                "width": str(max(len(elem.text) * elem.font_size // 2, 40)),
                "height": str(elem.font_size + 10),
                "as": "geometry",
            })

        elif isinstance(elem, IRLine):
            cid = next_cell_id()
            id_map[elem.id] = cid

            style = (
                f"endArrow=none;startArrow=none;"
                f"strokeColor={elem.color};strokeWidth={elem.width};"
            )

            cell = ET.SubElement(mxroot, "mxCell", {
                "id": cid,
                "value": "",
                "style": style,
                "edge": "1",
                "parent": "1",
            })
            geom = ET.SubElement(cell, "mxGeometry", {
                "relative": "1",
                "as": "geometry",
            })
            ET.SubElement(geom, "mxPoint", {
                "x": str(elem.x1), "y": str(elem.y1),
                "as": "sourcePoint",
            })
            ET.SubElement(geom, "mxPoint", {
                "x": str(elem.x2), "y": str(elem.y2),
                "as": "targetPoint",
            })

        elif isinstance(elem, IRDot):
            cid = next_cell_id()
            id_map[elem.id] = cid
            r = elem.radius
            style = (
                f"ellipse;fillColor={elem.color};strokeColor={elem.color};"
                f"strokeWidth=0;"
            )
            cell = ET.SubElement(mxroot, "mxCell", {
                "id": cid,
                "value": "",
                "style": style,
                "vertex": "1",
                "parent": "1",
            })
            ET.SubElement(cell, "mxGeometry", {
                "x": str(elem.cx - r), "y": str(elem.cy - r),
                "width": str(r * 2), "height": str(r * 2),
                "as": "geometry",
            })

        elif isinstance(elem, IRIcon):
            cid = next_cell_id()
            id_map[elem.id] = cid

            icon_style = _SERVICE_ICON_STYLES.get(
                elem.icon_key,
                f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{elem.icon_key};",
            )
            style = (
                f"{icon_style}"
                f"fillColor=none;strokeColor=none;"
            )
            cell = ET.SubElement(mxroot, "mxCell", {
                "id": cid,
                "value": "",
                "style": style,
                "vertex": "1",
                "parent": "1",
            })
            ET.SubElement(cell, "mxGeometry", {
                "x": str(elem.x), "y": str(elem.y),
                "width": str(elem.width), "height": str(elem.height),
                "as": "geometry",
            })

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
