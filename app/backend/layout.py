from __future__ import annotations

import textwrap
from math import ceil

from .ir import DiagramIR, IRDot, IRIcon, IRLine, IRRect, IRText
from .models import DiagramRequest

CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

SERVICE_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    "customer_network_epic": (
        "EPIC",
        "Integration with the EPIC electronic health record system for automated fax delivery of patient documents, referrals, and lab results directly from clinical workflows.",
    ),
    "customer_network_mfp": (
        "MFP",
        "Multifunction printer integration enabling scan-to-fax workflows. Physical MFP devices on the customer network route scanned documents through RightFax for outbound delivery.",
    ),
    "customer_network_smtp": (
        "SMTP",
        "Email-to-fax gateway allowing users to send faxes by composing an email with attachments. The SMTP connector converts inbound emails into outbound fax transmissions.",
    ),
    "customer_network_exchange": (
        "Exchange",
        "Microsoft Exchange integration providing native fax functionality within Outlook. Users can send and receive faxes as email messages with full tracking and delivery receipts.",
    ),
    "customer_network_directory": (
        "Network Directory",
        "LDAP/Active Directory integration for centralized user provisioning and authentication. Fax routing rules and permissions are synchronized from the corporate directory.",
    ),
    "customer_network_autoprint": (
        "AutoPrint",
        "Automated print-to-fax routing that captures documents from designated print queues and submits them as fax jobs without manual intervention.",
    ),
    "customer_network_otfaim": (
        "OTFAIM",
        "OpenText Fax Appliance for Intelligent Mail provides intelligent document capture and routing, converting inbound faxes into structured data for downstream business processes.",
    ),
    "cloud_services_office365": (
        "Office365",
        "Microsoft Office 365 cloud integration enabling fax delivery and receipt through Exchange Online, SharePoint, and Teams connectors for seamless enterprise communication.",
    ),
    "cloud_services_hosted_epic": (
        "Hosted EPIC",
        "Cloud-hosted EPIC electronic health record integration providing automated fax workflows for patient documents, referrals, and clinical results via the hosted EPIC environment.",
    ),
    "cloud_services_entra": (
        "Entra",
        "Microsoft Entra ID (formerly Azure AD) integration for cloud-based identity and access management, providing single sign-on and conditional access policies for fax services.",
    ),
    "cloud_services_okta": (
        "OKTA",
        "Okta cloud identity integration for centralized authentication, single sign-on, and adaptive multi-factor access control across fax-related applications and services.",
    ),
}

NOTES_LEFT_MARGIN = 80
NOTES_RIGHT_MARGIN = 80
NOTES_TEXT_WIDTH = CANVAS_WIDTH - NOTES_LEFT_MARGIN - NOTES_RIGHT_MARGIN

CENTER_COL_WIDTH = 240
CENTER_COL_GAP = 16
SERVICE_NODE_WIDTH = 190
SERVICE_NODE_HEIGHT = 86
SERVICE_STACK_SPACING = 24


def _estimate_wrapped_text_height(text: str, max_width: int, font_size: int) -> int:
    """Estimate pixel height of wrapped text using a character-width heuristic."""
    char_width = font_size * 0.6
    chars_per_line = max(1, int(max_width / char_width))
    lines = textwrap.wrap(text, width=chars_per_line)
    line_height = int(font_size * 1.4)
    return max(line_height, len(lines) * line_height)


def _distribute_servers(total_servers: int, az_count: int) -> list[int]:
    base = total_servers // az_count
    remainder = total_servers % az_count
    return [base + (1 if i < remainder else 0) for i in range(az_count)]


def _next_id(counter: list[int]) -> str:
    counter[0] += 1
    return str(counter[0])


def compute_layout(payload: DiagramRequest) -> DiagramIR:
    ir = DiagramIR(canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT)
    ctr = [0]  # mutable counter for unique IDs

    # Title
    ir.elements.append(IRText(
        id=_next_id(ctr), x=50, y=26,
        text=f"{payload.customer_name} - AWS Architecture",
        color="#111827", font_size=44, semantic_role="title",
    ))

    if payload.show_customer_network:
        cn_box = (60, 110, 1600, 260)
        region_box = (60, 290, 1600, 900)

        cn_id = _next_id(ctr)
        ir.elements.append(IRRect(
            id=cn_id, x=cn_box[0], y=cn_box[1],
            width=cn_box[2] - cn_box[0], height=cn_box[3] - cn_box[1],
            radius=14, stroke_width=3, fill_color="#F0FDF4",
            stroke_color="#16A34A", label="Customer Network",
            label_color="#111827", label_font_size=26,
            label_x_offset=16, label_y_offset=12,
            parent_id=None, semantic_role="customer_network",
        ))

        cn_nodes: list[tuple[str, str, str]] = []
        if payload.customer_network_epic:
            cn_nodes.append(("EPIC", "#16A34A", "epic"))
        if payload.customer_network_mfp:
            cn_nodes.append(("MFP", "#16A34A", "mfp"))
        if payload.customer_network_smtp:
            cn_nodes.append(("SMTP", "#16A34A", "smtp"))
        if payload.customer_network_exchange:
            cn_nodes.append(("Exchange", "#16A34A", "exchange"))
        if payload.customer_network_directory:
            cn_nodes.append(("Network Directory", "#16A34A", "directory"))
        if payload.customer_network_autoprint:
            cn_nodes.append(("AutoPrint", "#16A34A", "autoprint"))
        if payload.customer_network_otfaim:
            cn_nodes.append(("OTFAIM", "#111827", "otfaim"))

        if cn_nodes:
            node_w, node_h = 150, 100
            node_gap = 20
            total_w = len(cn_nodes) * node_w + (len(cn_nodes) - 1) * node_gap
            start_x = cn_box[0] + (cn_box[2] - cn_box[0] - total_w) // 2
            node_y = cn_box[1] + (cn_box[3] - cn_box[1] - node_h) // 2

            for i, (label, color, icon_key) in enumerate(cn_nodes):
                nx = start_x + i * (node_w + node_gap)
                ir.elements.append(IRRect(
                    id=_next_id(ctr), x=nx, y=node_y,
                    width=node_w, height=node_h, radius=10,
                    stroke_width=2, fill_color="#F0FDF4",
                    stroke_color=color, label=label,
                    label_color=color, label_font_size=22,
                    label_x_offset=-1, label_y_offset=52,
                    parent_id=cn_id, semantic_role="cn_node",
                ))

                icon_sz = 36
                icon_x = nx + (node_w - icon_sz) // 2
                icon_y = node_y + 8
                ir.elements.append(IRIcon(
                    id=_next_id(ctr), x=icon_x, y=icon_y,
                    width=icon_sz, height=icon_sz, icon_key=icon_key,
                ))

        line_x = (cn_box[0] + cn_box[2]) // 2
        line_y_top = cn_box[3]
        line_y_bottom = region_box[1]
        dot_r = 4
        ir.elements.append(IRLine(
            id=_next_id(ctr), x1=line_x, y1=line_y_top,
            x2=line_x, y2=line_y_bottom,
            color="#1F2937", width=2,
        ))
        ir.elements.append(IRDot(
            id=_next_id(ctr), cx=line_x, cy=line_y_top, radius=dot_r, color="#1F2937",
        ))
        ir.elements.append(IRDot(
            id=_next_id(ctr), cx=line_x, cy=line_y_bottom, radius=dot_r, color="#1F2937",
        ))
    else:
        region_box = (60, 120, 1600, 900)

    region_id = _next_id(ctr)
    ir.elements.append(IRRect(
        id=region_id,
        x=region_box[0], y=region_box[1],
        width=region_box[2] - region_box[0],
        height=region_box[3] - region_box[1],
        radius=14, stroke_width=3, fill_color="#F9FAFB",
        stroke_color="#1F2937",
        label=f"AWS Region: {payload.region}",
        label_color="#111827", label_font_size=26,
        label_x_offset=16, label_y_offset=12,
        parent_id=None, semantic_role="region",
    ))

    az_count = payload.availability_zone_count
    include_rds = payload.include_rds
    include_fsx = payload.include_fsx
    inner_left = region_box[0] + 30
    inner_top = region_box[1] + 70
    inner_right = region_box[2] - 30
    inner_bottom = region_box[3] - 40
    gap = 24
    use_center_column = (include_rds or include_fsx or payload.include_vpn) and az_count >= 2

    if use_center_column:
        az_width = (inner_right - inner_left - CENTER_COL_GAP - CENTER_COL_WIDTH - CENTER_COL_GAP) // 2
    else:
        az_width = (inner_right - inner_left - (gap * (az_count - 1))) // az_count

    dist = _distribute_servers(payload.production_server_count, az_count)

    az_ids: list[str] = []
    for idx in range(az_count):
        if use_center_column:
            if idx == 0:
                x0 = inner_left
            else:
                x0 = inner_left + az_width + CENTER_COL_GAP + CENTER_COL_WIDTH + CENTER_COL_GAP
        else:
            x0 = inner_left + idx * (az_width + gap)
        x1 = x0 + az_width
        y0 = inner_top
        y1 = inner_bottom

        az_id = _next_id(ctr)
        az_ids.append(az_id)
        ir.elements.append(IRRect(
            id=az_id, x=x0, y=y0,
            width=x1 - x0, height=y1 - y0,
            radius=14, stroke_width=2, fill_color="#F9FAFB",
            stroke_color="#4B5563", label=f"AZ-{idx + 1}",
            label_color="#111827", label_font_size=26,
            label_x_offset=16, label_y_offset=12,
            parent_id=region_id, semantic_role="az",
        ))

        node_count = dist[idx]
        if node_count == 0:
            continue

        cols = min(3, ceil(node_count / 3))
        rows = ceil(node_count / cols)
        node_gap_x = 20
        node_gap_y = 20
        node_w = 170
        node_h = 140
        grid_w = cols * node_w + (cols - 1) * node_gap_x
        grid_h = rows * node_h + (rows - 1) * node_gap_y

        available_h = y1 - y0 - 120
        if grid_h > available_h and grid_h > 0:
            scale = available_h / grid_h
            node_w = int(node_w * scale)
            node_h = int(node_h * scale)
            node_gap_x = int(node_gap_x * scale)
            node_gap_y = int(node_gap_y * scale)
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

            ec2_id = _next_id(ctr)
            label = f"OpenText Fax Server {server_num}"
            ir.elements.append(IRRect(
                id=ec2_id, x=nx, y=ny,
                width=node_w, height=node_h,
                radius=10, stroke_width=2,
                fill_color="#F8FAFC", stroke_color="#9CA3AF",
                label=label, label_color="#374151",
                label_font_size=14, label_x_offset=8,
                label_y_offset=102,
                parent_id=az_id, semantic_role="ec2_node",
            ))

            sx = node_w / 170
            sy = node_h / 140
            s = min(sx, sy)
            icon_sz = max(int(64 * s), 16)
            icon_x = nx + (node_w - icon_sz) // 2
            icon_y = ny + max(int(10 * sy), 4)
            ir.elements.append(IRIcon(
                id=_next_id(ctr), x=icon_x, y=icon_y,
                width=icon_sz, height=icon_sz, icon_key="ec2",
            ))

            ir.elements.append(IRText(
                id=_next_id(ctr),
                x=nx + int(8 * sx), y=ny + int(80 * sy),
                text="EC2 Instance", color="#111827",
                font_size=max(int(17 * s), 10),
                semantic_role="node_label",
            ))

            sub_font_size = max(int(14 * s), 8)
            ir.elements.append(IRText(
                id=_next_id(ctr),
                x=nx + int(8 * sx), y=ny + int(102 * sy),
                text=label, color="#374151",
                font_size=sub_font_size,
                semantic_role="node_sublabel",
            ))

            server_num += 1

    # Non-production servers
    if payload.non_production_server_count > 0:
        non_prod_box = (1640, region_box[1] + 60, 1880, 900)
        np_id = _next_id(ctr)
        ir.elements.append(IRRect(
            id=np_id,
            x=non_prod_box[0], y=non_prod_box[1],
            width=non_prod_box[2] - non_prod_box[0],
            height=non_prod_box[3] - non_prod_box[1],
            radius=14, stroke_width=3,
            fill_color="#F9FAFB", stroke_color="#7C3AED",
            label="Non-Production", label_color="#111827",
            label_font_size=26, label_x_offset=16,
            label_y_offset=12, parent_id=None,
            semantic_role="non_production",
        ))

        max_nodes = payload.non_production_server_count
        np_node_w = 170
        np_node_h = 140
        np_gap = 10
        np_start_y = non_prod_box[1] + 70
        np_available_h = non_prod_box[3] - 10 - np_start_y
        np_total_h = max_nodes * np_node_h + (max_nodes - 1) * np_gap

        if np_total_h > np_available_h and np_total_h > 0:
            scale = np_available_h / np_total_h
            np_node_w = int(np_node_w * scale)
            np_node_h = int(np_node_h * scale)
            np_gap = int(np_gap * scale)

        np_x = non_prod_box[0] + (non_prod_box[2] - non_prod_box[0] - np_node_w) // 2
        for i in range(max_nodes):
            ny = np_start_y + i * (np_node_h + np_gap)
            if ny + np_node_h > non_prod_box[3] - 10:
                break

            np_ec2_id = _next_id(ctr)
            label = f"OpenText Fax Server {i + 1}"
            ir.elements.append(IRRect(
                id=np_ec2_id, x=np_x, y=ny,
                width=np_node_w, height=np_node_h,
                radius=10, stroke_width=2,
                fill_color="#F8FAFC", stroke_color="#9CA3AF",
                label=label, label_color="#374151",
                label_font_size=14, label_x_offset=8,
                label_y_offset=102,
                parent_id=np_id, semantic_role="ec2_node",
            ))

            sx = np_node_w / 170
            sy = np_node_h / 140
            s = min(sx, sy)
            icon_sz = max(int(64 * s), 16)
            icon_x = np_x + (np_node_w - icon_sz) // 2
            icon_y = ny + max(int(10 * sy), 4)
            ir.elements.append(IRIcon(
                id=_next_id(ctr), x=icon_x, y=icon_y,
                width=icon_sz, height=icon_sz, icon_key="ec2",
            ))

            ir.elements.append(IRText(
                id=_next_id(ctr),
                x=np_x + int(8 * sx), y=ny + int(80 * sy),
                text="EC2 Instance", color="#111827",
                font_size=max(int(17 * s), 10),
                semantic_role="node_label",
            ))

            sub_font_size = max(int(14 * s), 8)
            ir.elements.append(IRText(
                id=_next_id(ctr),
                x=np_x + int(8 * sx), y=ny + int(102 * sy),
                text=label, color="#374151",
                font_size=sub_font_size,
                semantic_role="node_sublabel",
            ))

    # Shared services
    services: list[tuple[str, str]] = []
    if payload.include_vpn:
        services.append(("AWS Transit VPN", "vpn"))
    if payload.include_rds:
        services.append(("Amazon RDS", "rds"))
    if payload.include_fsx:
        services.append(("Amazon FSx", "fsx"))

    if services and use_center_column:
        col_x0 = inner_left + az_width + CENTER_COL_GAP
        col_x1 = col_x0 + CENTER_COL_WIDTH
        col_y0 = inner_top
        col_y1 = inner_bottom

        svc_col_id = _next_id(ctr)
        ir.elements.append(IRRect(
            id=svc_col_id, x=col_x0, y=col_y0,
            width=col_x1 - col_x0, height=col_y1 - col_y0,
            radius=14, stroke_width=1,
            fill_color="#EFF6FF", stroke_color="#93C5FD",
            label="", label_color="#1E3A8A",
            label_font_size=18, label_x_offset=10,
            label_y_offset=0, parent_id=region_id,
            semantic_role="service_column",
        ))

        total_stack_h = (len(services) * SERVICE_NODE_HEIGHT) + ((len(services) - 1) * SERVICE_STACK_SPACING)
        stack_start_y = col_y0 + ((col_y1 - col_y0 - total_stack_h) // 2)
        stack_x = col_x0 + (CENTER_COL_WIDTH - SERVICE_NODE_WIDTH) // 2

        ir.elements.append(IRText(
            id=_next_id(ctr), x=col_x0 + 10, y=stack_start_y - 30,
            text="Shared Data Tier Services", color="#1E3A8A",
            font_size=18, semantic_role="section_label",
        ))

        az1_right = inner_left + az_width
        az2_left = col_x1 + CENTER_COL_GAP
        dot_r = 4
        line_color = "#3B82F6"

        for i, (service, icon_key) in enumerate(services):
            sy = stack_start_y + i * (SERVICE_NODE_HEIGHT + SERVICE_STACK_SPACING)
            svc_id = _next_id(ctr)
            ir.elements.append(IRRect(
                id=svc_id, x=stack_x, y=sy,
                width=SERVICE_NODE_WIDTH, height=SERVICE_NODE_HEIGHT,
                radius=10, stroke_width=2,
                fill_color="#EFF6FF", stroke_color="#1D4ED8",
                label=service, label_color="#1E3A8A",
                label_font_size=18, label_x_offset=72,
                label_y_offset=34, parent_id=svc_col_id,
                semantic_role="service_node",
            ))

            ir.elements.append(IRIcon(
                id=_next_id(ctr), x=stack_x + 10, y=sy + 15,
                width=52, height=52, icon_key=icon_key,
            ))

            cy = sy + SERVICE_NODE_HEIGHT // 2
            node_left = stack_x
            node_right = stack_x + SERVICE_NODE_WIDTH

            # AZ1 -> service
            ir.elements.append(IRLine(
                id=_next_id(ctr), x1=az1_right, y1=cy,
                x2=node_left, y2=cy, color=line_color, width=2,
            ))
            ir.elements.append(IRDot(
                id=_next_id(ctr), cx=az1_right, cy=cy, radius=dot_r, color=line_color,
            ))
            ir.elements.append(IRDot(
                id=_next_id(ctr), cx=node_left, cy=cy, radius=dot_r, color=line_color,
            ))

            # service -> AZ2
            ir.elements.append(IRLine(
                id=_next_id(ctr), x1=node_right, y1=cy,
                x2=az2_left, y2=cy, color=line_color, width=2,
            ))
            ir.elements.append(IRDot(
                id=_next_id(ctr), cx=node_right, cy=cy, radius=dot_r, color=line_color,
            ))
            ir.elements.append(IRDot(
                id=_next_id(ctr), cx=az2_left, cy=cy, radius=dot_r, color=line_color,
            ))

    elif services:
        shared_center_x = inner_left + (az_width // 2)
        total_stack_h = (len(services) * SERVICE_NODE_HEIGHT) + ((len(services) - 1) * SERVICE_STACK_SPACING)
        stack_start_y = inner_top + ((inner_bottom - inner_top - total_stack_h) // 2)
        stack_x = shared_center_x - (SERVICE_NODE_WIDTH // 2)

        ir.elements.append(IRText(
            id=_next_id(ctr), x=stack_x - 8, y=stack_start_y - 34,
            text="Shared Data Tier Services", color="#1E3A8A",
            font_size=22, semantic_role="section_label",
        ))
        for i, (service, icon_key) in enumerate(services):
            sy = stack_start_y + i * (SERVICE_NODE_HEIGHT + SERVICE_STACK_SPACING)
            svc_id = _next_id(ctr)
            ir.elements.append(IRRect(
                id=svc_id, x=stack_x, y=sy,
                width=SERVICE_NODE_WIDTH, height=SERVICE_NODE_HEIGHT,
                radius=10, stroke_width=2,
                fill_color="#EFF6FF", stroke_color="#1D4ED8",
                label=service, label_color="#1E3A8A",
                label_font_size=18, label_x_offset=72,
                label_y_offset=34, parent_id=None,
                semantic_role="service_node",
            ))
            ir.elements.append(IRIcon(
                id=_next_id(ctr), x=stack_x + 10, y=sy + 15,
                width=52, height=52, icon_key=icon_key,
            ))

    # Cloud services section
    cs_box_bottom = region_box[3]
    if payload.show_cloud_services:
        cs_gap = 30
        cs_height = 150
        cs_x0 = region_box[0]
        cs_x1 = region_box[2]
        cs_y0 = region_box[3] + cs_gap
        cs_y1 = cs_y0 + cs_height

        cs_id = _next_id(ctr)
        ir.elements.append(IRRect(
            id=cs_id, x=cs_x0, y=cs_y0,
            width=cs_x1 - cs_x0, height=cs_y1 - cs_y0,
            radius=14, stroke_width=3, fill_color="#EFF6FF",
            stroke_color="#2563EB", label="Cloud Services",
            label_color="#111827", label_font_size=26,
            label_x_offset=16, label_y_offset=12,
            parent_id=None, semantic_role="cloud_services",
        ))

        cs_nodes: list[tuple[str, str, str]] = []
        if payload.cloud_services_office365:
            cs_nodes.append(("Office365", "#2563EB", "office365"))
        if payload.cloud_services_hosted_epic:
            cs_nodes.append(("Hosted EPIC", "#2563EB", "hosted_epic"))
        if payload.cloud_services_entra:
            cs_nodes.append(("Entra", "#2563EB", "entra"))
        if payload.cloud_services_okta:
            cs_nodes.append(("OKTA", "#2563EB", "okta"))

        if cs_nodes:
            node_w, node_h = 150, 100
            node_gap = 20
            total_w = len(cs_nodes) * node_w + (len(cs_nodes) - 1) * node_gap
            start_x = cs_x0 + (cs_x1 - cs_x0 - total_w) // 2
            node_y = cs_y0 + (cs_y1 - cs_y0 - node_h) // 2

            for i, (label, color, icon_key) in enumerate(cs_nodes):
                nx = start_x + i * (node_w + node_gap)
                ir.elements.append(IRRect(
                    id=_next_id(ctr), x=nx, y=node_y,
                    width=node_w, height=node_h, radius=10,
                    stroke_width=2, fill_color="#EFF6FF",
                    stroke_color=color, label=label,
                    label_color=color, label_font_size=22,
                    label_x_offset=-1, label_y_offset=52,
                    parent_id=cs_id, semantic_role="cs_node",
                ))

                icon_sz = 36
                icon_x = nx + (node_w - icon_sz) // 2
                icon_y = node_y + 8
                ir.elements.append(IRIcon(
                    id=_next_id(ctr), x=icon_x, y=icon_y,
                    width=icon_sz, height=icon_sz, icon_key=icon_key,
                ))

        # Connecting line from region box bottom to cloud services box top
        line_x = (region_box[0] + region_box[2]) // 2
        line_y_top = region_box[3]
        line_y_bottom = cs_y0
        dot_r = 4
        ir.elements.append(IRLine(
            id=_next_id(ctr), x1=line_x, y1=line_y_top,
            x2=line_x, y2=line_y_bottom,
            color="#1F2937", width=2,
        ))
        ir.elements.append(IRDot(
            id=_next_id(ctr), cx=line_x, cy=line_y_top, radius=dot_r, color="#1F2937",
        ))
        ir.elements.append(IRDot(
            id=_next_id(ctr), cx=line_x, cy=line_y_bottom, radius=dot_r, color="#1F2937",
        ))

        cs_box_bottom = cs_y1

    # Notes section
    notes_y = cs_box_bottom + 30  # start below the cloud services box (or region box)

    if payload.show_customer_network or payload.show_cloud_services:
        selected_services: list[tuple[str, str]] = []
        for key, (display_name, description) in SERVICE_DESCRIPTIONS.items():
            if getattr(payload, key, False):
                selected_services.append((display_name, description))

        if selected_services:
            # "Notes" heading
            ir.elements.append(IRText(
                id=_next_id(ctr), x=NOTES_LEFT_MARGIN, y=notes_y,
                text="Notes", color="#111827", font_size=30,
                semantic_role="notes_heading",
            ))
            notes_y += 40

            # Horizontal rule
            ir.elements.append(IRLine(
                id=_next_id(ctr),
                x1=NOTES_LEFT_MARGIN, y1=notes_y,
                x2=CANVAS_WIDTH - NOTES_RIGHT_MARGIN, y2=notes_y,
                color="#D1D5DB", width=2,
            ))
            notes_y += 20

            desc_font_size = 16
            name_font_size = 18

            for display_name, description in selected_services:
                # Bold service name
                ir.elements.append(IRText(
                    id=_next_id(ctr), x=NOTES_LEFT_MARGIN, y=notes_y,
                    text=display_name, color="#111827",
                    font_size=name_font_size, semantic_role="notes_service_name",
                ))
                notes_y += int(name_font_size * 1.6)

                # Wrapped description paragraph
                desc_height = _estimate_wrapped_text_height(
                    description, NOTES_TEXT_WIDTH, desc_font_size,
                )
                ir.elements.append(IRText(
                    id=_next_id(ctr), x=NOTES_LEFT_MARGIN, y=notes_y,
                    text=description, color="#4B5563",
                    font_size=desc_font_size, semantic_role="notes_description",
                    max_width=NOTES_TEXT_WIDTH,
                ))
                notes_y += desc_height + 16  # gap between service entries

    # Footer
    footer_y = max(1020, notes_y + 20)
    ir.elements.append(IRText(
        id=_next_id(ctr), x=50, y=footer_y,
        text=payload.footer_text, color="#4B5563",
        font_size=24, semantic_role="footer",
    ))

    ir.canvas_height = max(CANVAS_HEIGHT, footer_y + 60)

    return ir
