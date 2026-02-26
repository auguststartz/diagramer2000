import xml.etree.ElementTree as ET

from app.backend.layout import compute_layout
from app.backend.models import DiagramRequest
from app.backend.render_drawio import render_to_drawio


def _make_request(**kwargs) -> DiagramRequest:
    defaults = {
        "customer_name": "Acme",
        "region": "us-east-1",
        "production_server_count": 2,
        "non_production_server_count": 0,
    }
    defaults.update(kwargs)
    return DiagramRequest(**defaults)


def test_valid_xml() -> None:
    ir = compute_layout(_make_request())
    xml_bytes = render_to_drawio(ir)
    root = ET.fromstring(xml_bytes)
    assert root.tag == "mxfile"


def test_has_mxgraph_model() -> None:
    ir = compute_layout(_make_request())
    xml_bytes = render_to_drawio(ir)
    root = ET.fromstring(xml_bytes)
    diagram = root.find("diagram")
    assert diagram is not None
    model = diagram.find("mxGraphModel")
    assert model is not None


def test_contains_cells() -> None:
    ir = compute_layout(_make_request(include_rds=True))
    xml_bytes = render_to_drawio(ir)
    root = ET.fromstring(xml_bytes)
    cells = root.findall(".//mxCell")
    # At least: 2 default + region + 2 AZs + some EC2 + service nodes + texts
    assert len(cells) > 10


def test_region_uses_aws4_stencil() -> None:
    ir = compute_layout(_make_request())
    xml_bytes = render_to_drawio(ir)
    root = ET.fromstring(xml_bytes)
    cells = root.findall(".//mxCell")
    region_cells = [c for c in cells if "group_region" in (c.get("style") or "")]
    assert len(region_cells) == 1


def test_az_uses_aws4_stencil() -> None:
    ir = compute_layout(_make_request())
    xml_bytes = render_to_drawio(ir)
    root = ET.fromstring(xml_bytes)
    cells = root.findall(".//mxCell")
    az_cells = [c for c in cells if "availability_zone" in (c.get("style") or "")]
    assert len(az_cells) == 2


def test_page_dimensions() -> None:
    ir = compute_layout(_make_request())
    xml_bytes = render_to_drawio(ir)
    root = ET.fromstring(xml_bytes)
    model = root.find(".//mxGraphModel")
    assert model is not None
    assert model.get("pageWidth") == "1920"
    assert model.get("pageHeight") == "1080"


def test_customer_network_with_services() -> None:
    ir = compute_layout(_make_request(
        show_customer_network=True,
        customer_network_epic=True,
        include_rds=True,
        include_fsx=True,
    ))
    xml_bytes = render_to_drawio(ir)
    root = ET.fromstring(xml_bytes)
    # Should be valid XML with many cells
    cells = root.findall(".//mxCell")
    assert len(cells) > 15
