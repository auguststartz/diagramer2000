import json

from app.backend.layout import compute_layout
from app.backend.models import DiagramRequest
from app.backend.render_excalidraw import render_to_excalidraw


def _make_request(**kwargs) -> DiagramRequest:
    defaults = {
        "customer_name": "Acme",
        "region": "us-east-1",
        "production_server_count": 2,
        "non_production_server_count": 0,
    }
    defaults.update(kwargs)
    return DiagramRequest(**defaults)


def test_valid_json() -> None:
    ir = compute_layout(_make_request())
    raw = render_to_excalidraw(ir)
    data = json.loads(raw)
    assert data["type"] == "excalidraw"
    assert data["version"] == 2


def test_has_elements() -> None:
    ir = compute_layout(_make_request())
    data = json.loads(render_to_excalidraw(ir))
    assert len(data["elements"]) > 0


def test_contains_rectangles_and_text() -> None:
    ir = compute_layout(_make_request(include_rds=True))
    data = json.loads(render_to_excalidraw(ir))
    types = {e["type"] for e in data["elements"]}
    assert "rectangle" in types
    assert "text" in types


def test_contains_lines_for_connections() -> None:
    ir = compute_layout(_make_request(include_rds=True))
    data = json.loads(render_to_excalidraw(ir))
    types = {e["type"] for e in data["elements"]}
    assert "line" in types


def test_customer_network_with_services() -> None:
    ir = compute_layout(_make_request(
        show_customer_network=True,
        customer_network_epic=True,
        include_rds=True,
        include_fsx=True,
    ))
    data = json.loads(render_to_excalidraw(ir))
    assert len(data["elements"]) > 15


def test_source_field() -> None:
    ir = compute_layout(_make_request())
    data = json.loads(render_to_excalidraw(ir))
    assert data["source"] == "diagramer2000"


def test_app_state() -> None:
    ir = compute_layout(_make_request())
    data = json.loads(render_to_excalidraw(ir))
    assert data["appState"]["viewBackgroundColor"] == "#ffffff"
