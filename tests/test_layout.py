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


# --- Notes section tests ---


def test_notes_section_appears_when_services_selected() -> None:
    ir = compute_layout(_make_request(
        show_customer_network=True,
        customer_network_smtp=True,
        customer_network_exchange=True,
    ))
    texts = [e for e in ir.elements if isinstance(e, IRText)]
    headings = [t for t in texts if t.semantic_role == "notes_heading"]
    descriptions = [t for t in texts if t.semantic_role == "notes_description"]
    service_names = [t for t in texts if t.semantic_role == "notes_service_name"]
    assert len(headings) == 1
    assert headings[0].text == "Notes"
    assert len(descriptions) == 2
    assert len(service_names) == 2


def test_canvas_height_exceeds_default_with_many_services() -> None:
    ir = compute_layout(_make_request(
        show_customer_network=True,
        customer_network_epic=True,
        customer_network_mfp=True,
        customer_network_smtp=True,
        customer_network_exchange=True,
        customer_network_directory=True,
        customer_network_autoprint=True,
        customer_network_otfaim=True,
    ))
    assert ir.canvas_height > 1080


def test_footer_positioned_below_notes() -> None:
    ir = compute_layout(_make_request(
        show_customer_network=True,
        customer_network_smtp=True,
    ))
    texts = [e for e in ir.elements if isinstance(e, IRText)]
    footer = [t for t in texts if t.semantic_role == "footer"][0]
    descriptions = [t for t in texts if t.semantic_role == "notes_description"]
    assert len(descriptions) == 1
    assert footer.y > descriptions[0].y


def test_no_notes_when_no_services_selected() -> None:
    ir = compute_layout(_make_request(show_customer_network=True))
    texts = [e for e in ir.elements if isinstance(e, IRText)]
    headings = [t for t in texts if t.semantic_role == "notes_heading"]
    descriptions = [t for t in texts if t.semantic_role == "notes_description"]
    assert len(headings) == 0
    assert len(descriptions) == 0


def test_no_notes_when_customer_network_disabled() -> None:
    ir = compute_layout(_make_request(
        show_customer_network=False,
        customer_network_smtp=True,
        customer_network_exchange=True,
    ))
    texts = [e for e in ir.elements if isinstance(e, IRText)]
    headings = [t for t in texts if t.semantic_role == "notes_heading"]
    descriptions = [t for t in texts if t.semantic_role == "notes_description"]
    assert len(headings) == 0
    assert len(descriptions) == 0


# --- Cloud services section tests ---


def test_cloud_services_box_and_nodes() -> None:
    ir = compute_layout(_make_request(
        show_cloud_services=True,
        cloud_services_office365=True,
        cloud_services_entra=True,
    ))
    rects = [e for e in ir.elements if isinstance(e, IRRect)]
    cs_box = [r for r in rects if r.semantic_role == "cloud_services"]
    cs_nodes = [r for r in rects if r.semantic_role == "cs_node"]
    assert len(cs_box) == 1
    assert cs_box[0].fill_color == "#EFF6FF"
    assert cs_box[0].stroke_color == "#2563EB"
    assert len(cs_nodes) == 2


def test_cloud_services_connecting_line() -> None:
    ir = compute_layout(_make_request(show_cloud_services=True))
    rects = [e for e in ir.elements if isinstance(e, IRRect)]
    region = [r for r in rects if r.semantic_role == "region"][0]
    cs_box = [r for r in rects if r.semantic_role == "cloud_services"][0]
    lines = [e for e in ir.elements if isinstance(e, IRLine)]
    # Find the vertical line between region bottom and CS box top
    connecting = [
        ln for ln in lines
        if ln.y1 == region.y + region.height and ln.y2 == cs_box.y
    ]
    assert len(connecting) == 1


def test_no_cloud_services_when_disabled() -> None:
    ir = compute_layout(_make_request(show_cloud_services=False))
    rects = [e for e in ir.elements if isinstance(e, IRRect)]
    cs_box = [r for r in rects if r.semantic_role == "cloud_services"]
    assert len(cs_box) == 0


def test_cloud_services_notes_appear() -> None:
    ir = compute_layout(_make_request(
        show_cloud_services=True,
        cloud_services_office365=True,
        cloud_services_hosted_epic=True,
    ))
    texts = [e for e in ir.elements if isinstance(e, IRText)]
    headings = [t for t in texts if t.semantic_role == "notes_heading"]
    descriptions = [t for t in texts if t.semantic_role == "notes_description"]
    service_names = [t for t in texts if t.semantic_role == "notes_service_name"]
    assert len(headings) == 1
    assert len(descriptions) == 2
    assert len(service_names) == 2
    names = {t.text for t in service_names}
    assert "Office365" in names
    assert "Hosted EPIC" in names


# --- CN/CS node icon tests ---


def test_cn_nodes_have_icons() -> None:
    ir = compute_layout(_make_request(
        show_customer_network=True,
        customer_network_epic=True,
        customer_network_smtp=True,
        customer_network_exchange=True,
    ))
    icons = [e for e in ir.elements if isinstance(e, IRIcon)]
    cn_icon_keys = {i.icon_key for i in icons if i.icon_key in ("epic", "smtp", "exchange")}
    assert cn_icon_keys == {"epic", "smtp", "exchange"}


def test_cs_nodes_have_icons() -> None:
    ir = compute_layout(_make_request(
        show_cloud_services=True,
        cloud_services_office365=True,
        cloud_services_entra=True,
    ))
    icons = [e for e in ir.elements if isinstance(e, IRIcon)]
    cs_icon_keys = {i.icon_key for i in icons if i.icon_key in ("office365", "entra")}
    assert cs_icon_keys == {"office365", "entra"}
