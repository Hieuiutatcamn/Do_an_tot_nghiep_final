from pydantic import BaseModel, Field

from app.schemas.chung import MoHinhORM


class DanhMucCoBan(BaseModel):
    ten_danh_muc: str | None = Field(default=None, max_length=100)
    mo_ta: str | None = Field(default=None, max_length=255)


class DanhMucTao(DanhMucCoBan):
    ten_danh_muc: str = Field(max_length=100, examples=["May quay phim"])


class DanhMucCapNhat(DanhMucCoBan):
    pass


class DanhMucPhanHoi(MoHinhORM):
    id_danh_muc: int
    ten_danh_muc: str | None = None
    mo_ta: str | None = None
