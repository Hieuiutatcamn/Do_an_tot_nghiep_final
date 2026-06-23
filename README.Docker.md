# Chạy Sunlens Camera bằng Docker

Hệ thống thuê thiết bị máy ảnh gồm 3 dịch vụ chạy chung bằng `docker compose`:

| Dịch vụ    | Công nghệ            | Cổng (host) | Mô tả                                  |
|------------|----------------------|-------------|----------------------------------------|
| `db`       | MySQL 8.4            | `3307`      | Database `do_an_tot_nghiep` (utf8mb4)  |
| `backend`  | FastAPI + Uvicorn    | `8000`      | API tại `/api/v1`, Swagger tại `/docs` |
| `frontend` | nginx (web tĩnh)     | `5500`      | Giao diện user + admin                 |

> Repo đã được gộp: `DoAnTotNghiep_BackEnd/` (backend) và `DOANTOTNGHIEP_FrontEnd/` (frontend) nằm chung 1 git repo.

---

## 1. Yêu cầu

- Docker Desktop (đã có Docker Engine + `docker compose` v2).
- Cổng `5500`, `8000`, `3307` trên máy đang trống.

## 2. Chuẩn bị file `.env` (chứa secrets)

Backend đọc cấu hình từ `DoAnTotNghiep_BackEnd/Backend/.env`. File này **không nằm trong git** (chứa secrets) nên cần có sẵn trên đĩa:

```bash
# Nếu chưa có .env, tạo từ mẫu rồi điền các khóa
cp DoAnTotNghiep_BackEnd/Backend/.env.example DoAnTotNghiep_BackEnd/Backend/.env
```

Các biến quan trọng (đã có sẵn giá trị mặc định/ghi đè trong `docker-compose.yml`):

- `DB_HOST=db`, `DB_PASSWORD=123456`, `DB_NAME=do_an_tot_nghiep` — **đừng sửa**, đã khớp container MySQL.
- `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY` — đổi sang chuỗi bí mật thật (≥ 16 ký tự) trong `docker-compose.yml` khi chạy production.
- Tùy chọn (để app chạy đủ tính năng): `GOOGLE_*`, `FACEBOOK_*` (đăng nhập MXH), `VNPAY_*` (thanh toán), `RESEND_API_KEY` (gửi email). Thiếu cái nào thì tính năng đó tạm tắt, phần còn lại vẫn chạy.

## 3. Khởi động

```bash
docker compose up -d --build
```

Lần đầu chạy:
1. `db` nạp sẵn schema + dữ liệu mẫu từ `DoAnTotNghiep_BackEnd/do_an_tot_nghiep_query.sql`.
2. `backend` đợi DB sẵn sàng → chạy `alembic upgrade head` (áp dụng migration `0019 → 0021`, các trường VNPay) → bật Uvicorn.
3. `frontend` (nginx) phục vụ web tĩnh.

Theo dõi log:

```bash
docker compose logs -f backend
```

## 4. Truy cập

- Giao diện người dùng: <http://127.0.0.1:5500> (tự chuyển tới trang chủ)
  - Đăng nhập: `http://127.0.0.1:5500/DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/user/Sunlens_Camera/dang_nhap.html`
  - Trang admin: `http://127.0.0.1:5500/DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/admin/Sunlens_Camera/tong_quan.html`
- API docs (Swagger): <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

### Tài khoản mẫu (từ dữ liệu seed)

| Vai trò    | Đăng nhập | Mật khẩu |
|------------|-----------|----------|
| Admin      | `admin2`  | `123456` |
| Nhân viên  | `nv01`    | `123456` |
| Khách hàng | `kh02`    | `123456` |

> Lưu ý: trong dữ liệu mẫu, `admin1` và `kh01` đã được đổi mật khẩu khác (không phải `123456`). Các tài khoản `admin2`, `nv01`–`nv03`, `kh02`–`kh10` dùng `123456`.

## 5. Lệnh thường dùng

```bash
docker compose ps                 # trạng thái các container
docker compose logs -f backend    # xem log backend
docker compose restart backend    # khởi động lại backend sau khi sửa code (cần build lại)
docker compose up -d --build      # build lại image sau khi đổi code/dependencies
docker compose down               # dừng (giữ nguyên dữ liệu DB)
docker compose down -v            # dừng + XÓA dữ liệu DB (lần sau seed lại từ đầu)
```

Chạy test trong container:

```bash
docker compose exec backend python -m pytest
```

Vào MySQL:

```bash
docker compose exec db mysql -uroot -p123456 do_an_tot_nghiep
```

## 6. Cách hoạt động (điểm cần biết)

- **Backend ghi ảnh vào cây frontend.** 3 API (thiết bị, CCCD khách hàng, avatar) lưu ảnh ra
  `DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/user/Sunlens_Camera/assets/images/...`.
  Vì vậy thư mục `DOANTOTNGHIEP_FrontEnd` được **mount chung** vào cả `backend` (ghi) lẫn `frontend` (đọc).
  Bố cục thư mục trong container được giữ giống repo (`/workspace/...`) để đường dẫn này khớp.
- **Một worker duy nhất.** Backend có vòng lặp nền quét đơn VNPay hết hạn; chạy nhiều worker sẽ lặp thừa nên cố định `--workers 1`.
- **Ảnh upload `/uploads`** được giữ qua volume `DoAnTotNghiep_BackEnd/Backend/uploads`.
- **Dữ liệu DB** nằm trong volume `db_data`. Seed chỉ nạp **một lần** khi volume rỗng — muốn nạp lại phải `docker compose down -v`.

## 7. Lưu ý môi trường thật (production)

- Frontend đang **hardcode** gọi API tới `http://127.0.0.1:8000` (trong JS). Khi deploy domain thật phải đổi địa chỉ này trong các file JS (hoặc đặt biến `window.SUNLENS_API_ORIGIN` / dùng reverse proxy `/api`).
- OAuth Google/Facebook và VNPay return/IPN cần URL công khai (HTTPS). Sửa `BACKEND_PUBLIC_URL`, `*_REDIRECT_URI`, `VNPAY_RETURN_URL`, `VNPAY_IPN_URL` trong `.env`.
- Đổi `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY`, mật khẩu MySQL trước khi public.

## 8. Sự cố thường gặp

- **Backend khởi động lại liên tục lúc đầu:** đang đợi MySQL nạp seed (lần đầu ~30–60s). Xem `docker compose logs -f backend`.
- **Lỗi cổng đã dùng:** đổi cổng host trong `docker-compose.yml` (vế trái `host:container`).
- **Ảnh upload bị 404:** kiểm tra container `backend` và `frontend` cùng mount `./DOANTOTNGHIEP_FrontEnd`.
- **Tiếng Việt bị lỗi font:** MySQL đã cấu hình `utf8mb4`; nếu nạp lại dữ liệu thủ công nhớ dùng `utf8mb4`.
