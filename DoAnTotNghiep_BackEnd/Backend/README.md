# Camera Rental Backend

Backend FastAPI + MySQL cho hệ thống thuê thiết bị máy ảnh. API có Swagger tại `/docs`, JWT authentication, CRUD thiết bị/danh mục, tạo đơn thuê, lịch sử thuê, upload ảnh và trò chuyện trực tiếp giữa khách hàng với nhân viên/Admin.

## Cấu trúc thư mục

```text
Backend/
├── app/
│   ├── database/      # Base, session, custom DB types
│   ├── models/        # SQLAlchemy models bám schema MySQL
│   ├── routers/       # FastAPI routers
│   ├── schemas/       # Pydantic request/response schemas
│   ├── services/      # Business logic
│   ├── utils/         # Config, JWT, pagination, upload
│   └── main.py
├── alembic/           # Database migrations
├── tests/             # Pytest tests
├── uploads/           # Ảnh upload runtime
├── .env.example
├── .env
├── requirements.txt
└── README.md
```

## Bảng database được cover

Backend hiện có API/model cho các nhóm dữ liệu chính:

- `TAI_KHOAN`: `/api/v1/accounts`
- `NHAN_VIEN`: `/api/v1/employees`
- `KHACH_HANG`: `/api/v1/customers`
- `DANH_MUC`: `/api/v1/categories`
- `THIET_BI`: `/api/v1/devices`
- `DON_THUE`, `CHI_TIET_DON_THUE`: `/api/v1/rentals`
- `cuoc_tro_chuyen`, `tin_nhan_chat`, `chat_ticket`, `nhan_vien_online`: `/api/v1/tro-chuyen` và `/api/v1/admin/chat`
- `KHIEU_NAI`: `/api/v1/complaints`

## Cài đặt

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Tạo database MySQL:

```sql
CREATE DATABASE IF NOT EXISTS do_an_tot_nghiep CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Cập nhật `.env` theo MySQL của bạn:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=do_an_tot_nghiep
APP_DEBUG=true
JWT_SECRET_KEY=change-this-access-secret
JWT_REFRESH_SECRET_KEY=change-this-refresh-secret
RESET_PASSWORD_TOKEN_EXPIRE_MINUTES=30
RESET_PASSWORD_FRONTEND_URL=http://127.0.0.1:5500/DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/user/Sunlens_Camera/dat_lai_mat_khau.html
```

Chạy migration:

```bash
alembic upgrade head
```

Chạy server:

```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Nếu đang đứng ở thư mục gốc repo, có thể chạy:

```bash
.\Backend\.venv\Scripts\python.exe -m uvicorn --app-dir Backend app.main:app --reload
```

Mở Swagger:

```text
http://127.0.0.1:8000/docs
```

## API chính

- Auth: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `GET /api/v1/auth/me`
- Password reset: `POST /api/v1/auth/forgot-password`, `POST /api/v1/auth/reset-password`
- OAuth: `GET /api/v1/auth/google/login`, `GET /api/v1/auth/google/callback`, `GET /api/v1/auth/facebook/login`, `GET /api/v1/auth/facebook/callback`
- Tài khoản: CRUD quản trị tại `/api/v1/accounts`
- Khách hàng: CRUD quản trị tại `/api/v1/customers`
- Nhân viên: CRUD quản trị tại `/api/v1/employees`
- Danh mục: CRUD tại `/api/v1/categories`
- Thiết bị: CRUD, search, filter, kiểm tra còn hàng, upload ảnh tại `/api/v1/devices`
- Đơn thuê: tạo đơn, xem lịch sử, cập nhật trạng thái tại `/api/v1/rentals`
- Khiếu nại: tạo/xem/xử lý tại `/api/v1/complaints`
- Trò chuyện nhân viên: tạo/gửi tin nhắn, lấy lịch sử và quản lý trạng thái tại `/api/v1/tro-chuyen`

Các API `accounts`, `customers`, `employees` yêu cầu vai trò `Admin`. API tạo/sửa/xóa danh mục, thiết bị và cập nhật trạng thái đơn thuê yêu cầu `Admin` hoặc `Nhan vien`. Khách hàng được tạo/xem khiếu nại của mình; `Admin`/`Nhan vien` được xem và cập nhật trạng thái khiếu nại.

## Cấu hình OAuth

Thêm Client ID/Secret vào `.env` và đăng ký callback URL tương ứng tại Google/Facebook:

```env
BACKEND_PUBLIC_URL=http://127.0.0.1:8000
OAUTH_FRONTEND_LOGIN_URL=http://127.0.0.1:5500/DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/user/Sunlens_Camera/dang_nhap.html
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
FACEBOOK_CLIENT_ID=
FACEBOOK_CLIENT_SECRET=
FACEBOOK_API_VERSION=v22.0
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/v1/auth/facebook/callback
FACEBOOK_FRONTEND_SUCCESS_URL=http://127.0.0.1:5500/DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/user/Sunlens_Camera/trang_chu.html
```

Callback URL:

```text
http://127.0.0.1:8000/api/v1/auth/google/callback
http://localhost:8000/api/v1/auth/facebook/callback
```

Trong **Meta Developers → Facebook Login → Settings → URI chuyển hướng OAuth hợp lệ**, thêm chính xác:

```text
http://localhost:8000/api/v1/auth/facebook/callback
```

Không đăng ký callback Facebook bằng `http://127.0.0.1:8000/...`.

Nếu Facebook vẫn chặn HTTP local, chạy backend qua ngrok rồi thay `.env` và URI chuyển hướng OAuth hợp lệ trên Meta Developers bằng cùng một URL HTTPS:

```env
FACEBOOK_REDIRECT_URI=https://your-ngrok-domain.ngrok-free.app/api/v1/auth/facebook/callback
```

## Test API trong Swagger

1. Chạy server trong thư mục `Backend` bằng `uvicorn app.main:app --reload`.
2. Mở `http://127.0.0.1:8000/docs`.
3. Gọi `POST /api/v1/auth/login` với tài khoản có vai trò phù hợp.
4. Copy `access_token`, bấm `Authorize`, nhập `Bearer <access_token>`.
5. Test các nhóm API `Accounts`, `Customers`, `Employees`, `Complaints`.

## Ví dụ response

Đăng nhập:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

Danh sách thiết bị:

```json
{
  "items": [
    {
      "id_thiet_bi": 1,
      "ten_thiet_bi": "Sony A7III",
      "danh_muc_id": 2,
      "so_luong": 5,
      "gia_thue": "700000.00",
      "tinh_trang": "San sang",
      "mo_ta": "Mirrorless Sony",
      "hinh_anh": "/uploads/devices/1/image.jpg",
      "category": {
        "id_danh_muc": 2,
        "ten_danh_muc": "May anh Mirrorless",
        "mo_ta": "May anh khong guong lat"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

Tạo đơn thuê:

```json
{
  "id_khach_hang": 1,
  "ghi_chu": "Khach dat online",
  "items": [
    {
      "id_thiet_bi": 1,
      "ngay_nhan": "2026-05-20T08:00:00",
      "ngay_tra": "2026-05-22T08:00:00",
      "so_luong": 1
    }
  ]
}
```

Response:

```json
{
  "id_don_thue": 11,
  "id_khach_hang": 1,
  "ngay_dat": "2026-05-13T10:00:00",
  "trang_thai": "Cho xac nhan",
  "tong_tien": "1400000.00",
  "anh_chuyen_khoan": null,
  "ghi_chu": "Khach dat online",
  "details": [
    {
      "id_chi_tiet_don_thue": 16,
      "id_don_thue": 11,
      "id_thiet_bi": 1,
      "ngay_nhan": "2026-05-20T08:00:00",
      "ngay_tra": "2026-05-22T08:00:00",
      "so_luong": 1,
      "gia_thue": "700000.00"
    }
  ]
}
```

Tạo nhân viên:

```json
{
  "id_tai_khoan": 3,
  "ho_ten": "Le Van Nam",
  "sdt": "0901000003"
}
```

Tạo khiếu nại:

```json
{
  "id_don_thue": 2,
  "noi_dung": "May bi loi pin"
}
```

## Test

```bash
python -m pytest
```

Nếu đang đứng ở thư mục gốc repo, cũng có thể chạy `python -m pytest`.

Test suite dùng SQLite in-memory để kiểm tra auth, thiết bị, đơn thuê, trò chuyện nhân viên, tài khoản, khách hàng, nhân viên và khiếu nại mà không cần MySQL thật.
