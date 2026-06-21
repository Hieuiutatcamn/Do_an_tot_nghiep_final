import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from types import SimpleNamespace

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.tai_khoan import TaiKhoan
from app.models.danh_muc import DanhMuc
from app.models.khach_hang import KhachHang
from app.models.nhan_vien import NhanVien
from app.models.thiet_bi import ThietBi
from app.services import gui_email_service
from app.utils.security import hash_password


@pytest.fixture(autouse=True)
def gia_lap_resend(monkeypatch):
    resend_gia_lap = SimpleNamespace(
        api_key=None,
        Emails=SimpleNamespace(
            send=lambda params: {"id": "email_kiem_thu"},
        ),
    )
    monkeypatch.setattr(
        gui_email_service,
        "nap_thu_vien_resend",
        lambda: resend_gia_lap,
    )
    return resend_gia_lap


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        admin = TaiKhoan(
            dang_nhap="admin",
            mat_khau=hash_password("secret123"),
            vai_tro="Admin",
            trang_thai="Hoat dong",
            key=True,
        )
        employee_account = TaiKhoan(
            dang_nhap="nhanvien",
            mat_khau=hash_password("secret123"),
            vai_tro="Nhan vien",
            trang_thai="Hoat dong",
            key=True,
        )
        customer_account = TaiKhoan(
            dang_nhap="kh01",
            mat_khau="123456",
            vai_tro="Khach hang",
            trang_thai="Hoat dong",
            key=True,
        )
        db.add_all([admin, employee_account, customer_account])
        db.flush()

        customer = KhachHang(
            id_tai_khoan=customer_account.id_tai_khoan,
            ho_ten="Nguyen Van A",
            sdt="0911111111",
            email="a@example.com",
        )
        employee = NhanVien(
            id_tai_khoan=employee_account.id_tai_khoan,
            ho_ten="Nhan vien SunLens",
            sdt="0900000001",
        )
        category = DanhMuc(ten_danh_muc="May anh Mirrorless", mo_ta="May anh khong guong lat")
        db.add_all([customer, employee, category])
        db.flush()

        db.add_all(
            [
                ThietBi(
                    ten_thiet_bi="Sony A7III",
                    danh_muc_id=category.id_danh_muc,
                    so_luong=2,
                    gia_thue=700000,
                    tinh_trang="San sang",
                    mo_ta="Mirrorless Sony",
                ),
                ThietBi(
                    ten_thiet_bi="Canon R6",
                    danh_muc_id=category.id_danh_muc,
                    so_luong=0,
                    gia_thue=800000,
                    tinh_trang="Dang thue",
                    mo_ta="Canon mirrorless",
                ),
            ]
        )
        db.commit()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def auth_headers(client: TestClient, username: str = "kh01", password: str = "123456") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
