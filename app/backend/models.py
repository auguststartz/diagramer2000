from pydantic import BaseModel, Field, field_validator


class DiagramRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=80)
    region: str = Field(min_length=1)
    production_server_count: int = Field(ge=1, le=20)
    availability_zone_count: int = Field(ge=1, le=3)
    non_production_server_count: int = Field(ge=0, le=20, default=0)
    include_rds: bool = False
    include_fsx: bool = False

    @field_validator("customer_name")
    @classmethod
    def strip_customer_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("region")
    @classmethod
    def strip_region(cls, value: str) -> str:
        return value.strip()
