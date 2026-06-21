from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ThongDiepApi(BaseModel):
    message: str


class MoHinhORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MoHinhTienTe(MoHinhORM):
    @field_serializer("*", when_used="json")
    def serialize_decimal(self, value):
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, datetime):
            return value.isoformat()
        return value


class TaiLenPhanHoi(BaseModel):
    file_name: str
    file_url: str = Field(examples=["/uploads/devices/1/example.jpg"])
