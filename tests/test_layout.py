from app.backend.ir import DiagramIR, IRDot, IRIcon, IRLine, IRRect, IRText
from app.backend.layout import compute_layout
from app.backend.models import DiagramRequest


def _make_request(**kwargs) -> DiagramRequest:
    defaults = {
        "customer_name": "Acme",
        "region": "us-east-1",
        "production_server_count": 2,
        "non_production_server_count": 0,
    }
    defaults.update(kwargs)
    return DiagramRequest(**defaults)


def test_returns_diagram_ir() -> None:
    ir = compute_layout(_make_request())
    assert isinstance(ir, DiagramIR)
    assert ir.canvas_width == 1920
    assert ir.canvas_height == 1080


def test_has_title_and_footer() -> None:
    ir = compute_layout(_make_request(footer_text="My footer"))
    texts = [e for e in ir.elements if isinstance(e, IRText)]
    title = [t for t in texts if t.semantic_role == "title"]
    footer = [t for t in texts if t.semantic_role == "footer"]
    assert len(title) == 1
    assert "Acme" in title[0].text
    assert len(footer) == 1
    assert footer[0].text == "My footer"


def test_has_region_and_az_rects() -> None:
    ir = compute_layout(_make_request())
    rects = [e for e in ir.elements if isinstance(e, IRRect)]
    region = [r for r in rects if r.semantic_role == "region"]
    azs = [r for r in rects if r.semantic_role == "az"]
    assert len(region) == 1
    assert len(azs) == 2  # default az_count is 2


def test_ec2_nodes_created() -> None:
    ir = compute_layout(_make_request(production_server_count=4))
    ec2 = [e for e in ir.elements if isinstance(e, IRRect) and e.semantic_role == "ec2_node"]
    assert len(ec2) == 4


def test_non_production_nodes() -> None:
    ir = compute_layout(_make_request(non_production_server_count=3))
    rects = [e for e in ir.elements if isinstance(e, IRRect)]
    np_box = [r for r in rects if r.semantic_role == "non_production"]
    assert len(np_box) == 1
    np_ec2 = [r for r in rects if r.semantic_role == "ec2_node" and r.parent_id == np_box[0].id]
    assert len(np_ec2) == 3


def test_services_center_column() -> None:
    ir = compute_layout(_make_request(include_rds=True, include_fsx=True))
    rects = [e for e in ir.elements if isinstance(e, IRRect)]
    svc_col = [r for r in rects if r.semantic_role == "service_column"]
    svc_nodes = [r for r in rects if r.semantic_role == "service_node"]
    assert len(svc_col) == 1
    assert len(svc_nodes) == 2


def test_customer_network_nodes() -> None:
    ir = compute_layout(_make_request(
        show_customer_network=True,
        customer_network_epic=True,
        customer_network_smtp=True,
    ))
    rects = [e for e in ir.elements if isinstance(e, IRRect)]
    cn = [r for r in rects if r.semantic_role == "customer_network"]
    cn_nodes = [r for r in rects if r.semantic_role == "cn_node"]
    assert len(cn) == 1
    assert len(cn_nodes) == 2


def test_connection_lines_for_services() -> None:
    ir = compute_layout(_make_request(include_rds=True))
    lines = [e for e in ir.elements if isinstance(e, IRLine)]
    dots = [e for e in ir.elements if isinstance(e, IRDot)]
    # 1 service x 2 lines (left + right) = 2 lines
    assert len(lines) >= 2
    # 1 service x 4 dots (2 per line) = 4 dots
    assert len(dots) >= 4


def test_unique_element_ids() -> None:
    ir = compute_layout(_make_request(
        include_rds=True, include_fsx=True,
        show_customer_network=True, customer_network_epic=True,
        non_production_server_count=2,
    ))
    ids = [e.id for e in ir.elements]
    assert len(ids) == len(set(ids)), "Element IDs must be unique"


def test_single_az_services_no_center_column() -> None:
    ir = compute_layout(_make_request(
        availability_zone_count=1, include_rds=True,
    ))
    rects = [e for e in ir.elements if isinstance(e, IRRect)]
    svc_col = [r for r in rects if r.semantic_role == "service_column"]
    svc_nodes = [r for r in rects if r.semantic_role == "service_node"]
    assert len(svc_col) == 0  # no center column with 1 AZ
    assert len(svc_nodes) == 1


def test_icons_created_for_ec2_and_services() -> None:
    ir = compute_layout(_make_request(include_rds=True))
    icons = [e for e in ir.elements if isinstance(e, IRIcon)]
    icon_keys = {i.icon_key for i in icons}
    assert "ec2" in icon_keys
    assert "rds" in icon_keys
