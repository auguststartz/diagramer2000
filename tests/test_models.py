import pytest
from pydantic import ValidationError

from app.backend.models import DiagramRequest


def test_valid_payload() -> None:
    payload = DiagramRequest(
        customer_name="Acme",
        region="us-east-1",
        production_server_count=2,
        non_production_server_count=1,
    )

    assert payload.customer_name == "Acme"
    assert payload.region == "us-east-1"
    assert payload.availability_zone_count == 2


def test_footer_text_default() -> None:
    payload = DiagramRequest(
        customer_name="Acme",
        region="us-east-1",
        production_server_count=2,
    )
    assert payload.footer_text.startswith("OpenText Fax Private Claude")

    custom = DiagramRequest(
        customer_name="Acme",
        region="us-east-1",
        production_server_count=2,
        footer_text="Custom footer",
    )
    assert custom.footer_text == "Custom footer"


@pytest.mark.parametrize(
    "field,value",
    [
        ("production_server_count", 0),
        ("production_server_count", 21),
        ("availability_zone_count", 0),
        ("availability_zone_count", 4),
        ("non_production_server_count", -1),
    ],
)
def test_invalid_numeric_ranges(field: str, value: int) -> None:
    kwargs = {
        "customer_name": "Acme",
        "region": "us-east-1",
        "production_server_count": 2,
        "availability_zone_count": 2,
        "non_production_server_count": 1,
    }
    kwargs[field] = value

    with pytest.raises(ValidationError):
        DiagramRequest(**kwargs)


def test_customer_network_defaults() -> None:
    payload = DiagramRequest(
        customer_name="Acme",
        region="us-east-1",
        production_server_count=2,
    )
    assert payload.show_customer_network is False
    assert payload.customer_network_epic is False
    assert payload.customer_network_mfp is False
    assert payload.customer_network_smtp is False
    assert payload.customer_network_exchange is False
    assert payload.customer_network_directory is False
    assert payload.customer_network_autoprint is False
    assert payload.customer_network_otfaim is False

    payload_on = DiagramRequest(
        customer_name="Acme",
        region="us-east-1",
        production_server_count=2,
        show_customer_network=True,
        customer_network_epic=True,
    )
    assert payload_on.show_customer_network is True
    assert payload_on.customer_network_epic is True


def test_include_vpn_default() -> None:
    payload = DiagramRequest(
        customer_name="Acme",
        region="us-east-1",
        production_server_count=2,
    )
    assert payload.include_vpn is False


def test_cloud_services_defaults_and_okta_toggle() -> None:
    payload = DiagramRequest(
        customer_name="Acme",
        region="us-east-1",
        production_server_count=2,
    )
    assert payload.show_cloud_services is False
    assert payload.cloud_services_office365 is False
    assert payload.cloud_services_hosted_epic is False
    assert payload.cloud_services_entra is False
    assert payload.cloud_services_okta is False

    payload_on = DiagramRequest(
        customer_name="Acme",
        region="us-east-1",
        production_server_count=2,
        show_cloud_services=True,
        cloud_services_okta=True,
    )
    assert payload_on.show_cloud_services is True
    assert payload_on.cloud_services_okta is True
