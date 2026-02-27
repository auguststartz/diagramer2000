from pydantic import BaseModel, Field, field_validator


class DiagramRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=80)
    region: str = Field(min_length=1)
    production_server_count: int = Field(ge=1, le=20)
    availability_zone_count: int = Field(default=2, ge=1, le=3)
    non_production_server_count: int = Field(ge=0, le=20, default=0)
    include_rds: bool = False
    include_fsx: bool = False
    include_vpn: bool = False
    show_customer_network: bool = False
    customer_network_epic: bool = False
    customer_network_mfp: bool = False
    customer_network_smtp: bool = False
    customer_network_exchange: bool = False
    customer_network_directory: bool = False
    customer_network_autoprint: bool = False
    customer_network_otfaim: bool = False
    show_cloud_services: bool = False
    cloud_services_office365: bool = False
    cloud_services_hosted_epic: bool = False
    cloud_services_entra: bool = False
    footer_text: str = Field(
        default="OpenText Fax Private Claude Production Environments are a pair of RightFax servers. Edit this text later with something more useful.",
        max_length=300,
    )

    @field_validator("customer_name")
    @classmethod
    def strip_customer_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("region")
    @classmethod
    def strip_region(cls, value: str) -> str:
        return value.strip()
