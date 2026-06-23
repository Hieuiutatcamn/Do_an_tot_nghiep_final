from __future__ import annotations

import json
from pathlib import Path

import pymysql
from passlib.context import CryptContext


ROOT = Path(__file__).resolve().parent
REPORT_BEFORE = ROOT / "cleanup_report_before.json"
REPORT_AFTER = ROOT / "cleanup_report_after.json"
ORPHAN_UPLOADS = ROOT / "orphan_uploads.txt"

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "root",
    "password": "123456",
    "database": "do_an_tot_nghiep_clean_work",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": False,
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


KEEP_CUSTOMER_IDS = {1, 2, 3, 4, 5}
KEEP_ACCOUNT_IDS = {1, 3, 6, 7, 8, 9, 10}
KEEP_EMPLOYEE_IDS = {1, 3}
KEEP_ORDER_IDS = {1, 2, 3, 4, 5, 39, 42, 64, 65, 67}
KEEP_CART_IDS = {6, 7, 60, 61}
KEEP_COMPLAINT_IDS = {1, 2, 8}
KEEP_CONVERSATION_ID = 5
KEEP_TICKET_ID = 3


BASE_DIRS = [
    Path(r"D:\HocTap\hocki2nam4\Final_DATN\DOANTOTNGHIEP_FrontEnd\Webthuemayanh_FE\user\Sunlens_Camera"),
    Path(r"D:\HocTap\hocki2nam4\Final_DATN\DoAnTotNghiep_BackEnd\Backend"),
]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def resolve_path(raw: str | None) -> Path | None:
    if not raw:
        return None
    value = raw.strip()
    if not value:
        return None
    if value.startswith("http://") or value.startswith("https://"):
        return None
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list) and parsed:
                return resolve_path(parsed[0])
        except json.JSONDecodeError:
            return None
    normalized = value.lstrip("/").replace("/", "\\")
    for base in BASE_DIRS:
        candidate = base / normalized
        if candidate.exists():
            return candidate
    if normalized.startswith("uploads\\"):
        direct = Path(r"D:\HocTap\hocki2nam4\Final_DATN\DoAnTotNghiep_BackEnd\Backend") / normalized
        if direct.exists():
            return direct
    return None


def fetch_scalar(cur, sql: str, params: tuple | None = None):
    cur.execute(sql, params or ())
    row = cur.fetchone()
    return next(iter(row.values())) if row else None


def collect_before_report(cur) -> dict:
    report: dict[str, object] = {}
    counts = {}
    for table in [
        "tai_khoan",
        "khach_hang",
        "nhan_vien",
        "don_thue",
        "chi_tiet_don_thue",
        "gio_hang",
        "khieu_nai",
        "thong_bao",
        "chat_ticket",
        "cuoc_tro_chuyen",
        "tin_nhan_chat",
        "tin_nhan_ai",
        "thiet_bi",
        "ma_giam_gia",
    ]:
        counts[table] = fetch_scalar(cur, f"SELECT COUNT(*) AS total FROM {table}")
    report["counts"] = counts

    cur.execute(
        """
        SELECT tk.id_tai_khoan, tk.Dang_nhap, tk.Vai_tro, kh.Id_khach_hang, kh.ho_ten,
               kh.thu_dien_tu, kh.sdt, kh.So_CCCD
        FROM tai_khoan tk
        LEFT JOIN khach_hang kh ON kh.Id_tai_khoan = tk.id_tai_khoan
        WHERE tk.Dang_nhap IN ('admin1', 'user1', 'admin2', 'nv04')
           OR COALESCE(kh.thu_dien_tu, '') REGEXP '^[a-z]@gmail\\.com$'
           OR COALESCE(kh.sdt, '') LIKE '09111111%'
           OR COALESCE(kh.So_CCCD, '') LIKE '0010010000%'
        ORDER BY tk.id_tai_khoan
        """
    )
    report["suspicious_accounts_customers"] = cur.fetchall()

    cur.execute(
        """
        SELECT d.Id_don_thue, d.Id_khach_hang, d.trang_thai, d.Anh_chuyen_khoan
        FROM don_thue d
        WHERE d.Anh_chuyen_khoan IS NULL
           OR d.Anh_chuyen_khoan IN ('ck2.jpg', 'ck3.jpg', 'ck4.jpg', 'ck5.jpg', 'ck6.jpg', 'ck7.jpg', 'ck8.jpg', 'ck9.jpg', 'ck10.jpg')
        ORDER BY d.Id_don_thue
        """
    )
    report["orders_with_bad_or_missing_payment_image"] = cur.fetchall()

    cur.execute(
        """
        SELECT nv.Id_nhan_vien, tk.Dang_nhap, nv.ho_ten, nv.sdt
        FROM nhan_vien nv
        JOIN tai_khoan tk ON tk.id_tai_khoan = nv.Id_tai_khoan
        ORDER BY nv.Id_nhan_vien
        """
    )
    report["employees"] = cur.fetchall()

    cur.execute(
        """
        SELECT id_cuoc_tro_chuyen, id_khach_hang, id_nhan_vien, che_do_chat, trang_thai, chu_de
        FROM cuoc_tro_chuyen
        ORDER BY id_cuoc_tro_chuyen
        """
    )
    report["conversations"] = cur.fetchall()
    return report


def standardize_accounts(cur) -> None:
    hashed = hash_password("123456")
    updates = [
        ("admin", hashed, "Admin", "Hoat dong", 1),
        ("nv01", hashed, "Nhan vien", "Hoat dong", 3),
        ("kh01", hashed, "Khach hang", "Hoat dong", 6),
        ("kh02", hashed, "Khach hang", "Hoat dong", 7),
        ("kh03", hashed, "Khach hang", "Hoat dong", 8),
        ("kh04", hashed, "Khach hang", "Hoat dong", 9),
        ("kh05", hashed, "Khach hang", "Hoat dong", 10),
    ]
    for login, password, role, status, account_id in updates:
        cur.execute(
            """
            UPDATE tai_khoan
            SET Dang_nhap = %s,
                Mat_khau = %s,
                Vai_tro = %s,
                Trang_thai = %s,
                kich_hoat = b'1'
            WHERE id_tai_khoan = %s
            """,
            (login, password, role, status, account_id),
        )

    avatar_updates = {
        6: "assets/images/user/cccd_anh_dai_dien_1.png",
        7: "assets/images/user/cccd_avatar_1.png",
        8: "assets/images/user/user1_1.png",
        9: "assets/images/user/user1.2.png",
        10: "assets/images/user/cccd_avatar_1.png",
    }
    for account_id, avatar in avatar_updates.items():
        cur.execute(
            "UPDATE tai_khoan SET anh_dai_dien = %s WHERE id_tai_khoan = %s",
            (avatar, account_id),
        )

    cur.execute(
        "UPDATE nhan_vien SET ho_ten = %s, sdt = %s WHERE Id_nhan_vien = 1",
        ("Trần Công Hiếu", "0901000001"),
    )
    cur.execute(
        "UPDATE nhan_vien SET ho_ten = %s, sdt = %s WHERE Id_nhan_vien = 3",
        ("Lê Văn Nam", "0901000002"),
    )


def standardize_customers(cur) -> None:
    customer_updates = [
        (
            "Công Hiếu Trần",
            "+84906586982",
            "sunlenscamera@gmail.com",
            "001001000123",
            "assets/images/user/cccd_front_1.jpg",
            "assets/images/user/cccd_back_1.jpg",
            "Nam",
            "2004-05-11",
            "382/37/9 Hùng Vương, Thanh Khê, Đà Nẵng",
            1,
        ),
        (
            "Nguyễn Thị Lan",
            "0909000002",
            "lan.nguyen@sunlens.demo",
            "046204009602",
            "assets/images/user/cccd_front_2.jpg",
            "assets/images/user/cccd_back_2.jpg",
            "Nữ",
            "2000-08-14",
            "42 Nguyễn Văn Linh, Hải Châu, Đà Nẵng",
            2,
        ),
        (
            "Trần Minh Khoa",
            "0909000003",
            "khoa.tran@sunlens.demo",
            "046204009603",
            "assets/images/user/cccd_front_3.jpg",
            "assets/images/user/cccd_back_3.jpg",
            "Nam",
            "1999-11-22",
            "19 Lê Duẩn, Thanh Khê, Đà Nẵng",
            3,
        ),
        (
            "Lê Hoàng An",
            "0909000004",
            "an.le@sunlens.demo",
            "046204009604",
            "assets/images/user/cccd_front_2.jpg",
            "assets/images/user/cccd_back_2.jpg",
            "Nam",
            "2001-03-09",
            "88 Phan Châu Trinh, Hải Châu, Đà Nẵng",
            4,
        ),
        (
            "Phạm Ngọc Mai",
            "0909000005",
            "mai.pham@sunlens.demo",
            "046204009605",
            "assets/images/user/cccd_front_3.jpg",
            "assets/images/user/cccd_back_3.jpg",
            "Nữ",
            "2002-07-17",
            "135 Điện Biên Phủ, Thanh Khê, Đà Nẵng",
            5,
        ),
    ]
    for row in customer_updates:
        cur.execute(
            """
            UPDATE khach_hang
            SET ho_ten = %s,
                sdt = %s,
                thu_dien_tu = %s,
                So_CCCD = %s,
                Anh_CCCD_mat_truoc = %s,
                Anh_CCCD_mat_sau = %s,
                gioi_tinh = %s,
                ngay_sinh = %s,
                dia_chi = %s
            WHERE Id_khach_hang = %s
            """,
            row,
        )


def prune_accounts_and_customers(cur) -> None:
    cur.execute(
        f"DELETE FROM nhan_vien_online WHERE id_nhan_vien NOT IN ({','.join(map(str, sorted(KEEP_EMPLOYEE_IDS)))})"
    )
    cur.execute(
        f"DELETE FROM nhan_vien WHERE Id_nhan_vien NOT IN ({','.join(map(str, sorted(KEEP_EMPLOYEE_IDS)))})"
    )
    cur.execute(
        f"DELETE FROM tin_nhan_ai WHERE id_khach_hang NOT IN ({','.join(map(str, sorted(KEEP_CUSTOMER_IDS)))})"
    )
    cur.execute(
        f"DELETE FROM gio_hang WHERE Id_gio_hang NOT IN ({','.join(map(str, sorted(KEEP_CART_IDS)))})"
    )
    cur.execute(
        f"DELETE FROM khieu_nai WHERE Id_khieu_nai NOT IN ({','.join(map(str, sorted(KEEP_COMPLAINT_IDS)))})"
    )
    cur.execute(
        f"DELETE FROM chi_tiet_don_thue WHERE id_don_thue NOT IN ({','.join(map(str, sorted(KEEP_ORDER_IDS)))})"
    )
    cur.execute(
        f"DELETE FROM don_thue WHERE Id_don_thue NOT IN ({','.join(map(str, sorted(KEEP_ORDER_IDS)))})"
    )
    cur.execute(
        f"DELETE FROM khach_hang WHERE Id_khach_hang NOT IN ({','.join(map(str, sorted(KEEP_CUSTOMER_IDS)))})"
    )
    cur.execute(
        f"DELETE FROM tai_khoan WHERE id_tai_khoan NOT IN ({','.join(map(str, sorted(KEEP_ACCOUNT_IDS)))})"
    )


def clean_orders_and_details(cur) -> None:
    payment_images = {
        1: "/uploads/payment/ce730ee986af4456b7ffb98119fe259c.jpg",
        2: "/uploads/payment/eb8a9eb1301c45d491b02659b7c98321.jpg",
        3: "/uploads/payment/24b05a9131e54e1b940047b7b69ec76a.jpg",
        4: "/uploads/payment/65e7cbe8ab9e4187982746674b46d404.jpg",
        5: "/uploads/payment/b68a3f5a62374ea986fbeae94f6993da.jpg",
        39: "/uploads/payment/24b05a9131e54e1b940047b7b69ec76a.jpg",
        42: "/uploads/payment/eb8a9eb1301c45d491b02659b7c98321.jpg",
        64: "/uploads/payment/1b93244412a64b5b855a2f1675427d58.jpg",
        65: "/uploads/payment/8d4ed01511f84a33be0cdc6b24b7b525.jpg",
        67: "/uploads/payment/daaea642f20b459197bd52283da45863.jpg",
    }
    for order_id, image in payment_images.items():
        cur.execute(
            "UPDATE don_thue SET Anh_chuyen_khoan = %s WHERE Id_don_thue = %s",
            (image, order_id),
        )

    detail_statuses = {
        1: "Da qua han",
        2: "Da qua han",
        3: "Da qua han",
        4: "Da qua han",
        5: "Da thue",
        39: "Da dat",
        42: "Da xac nhan",
        64: "Da huy",
        65: "Da thue",
        67: "Dang thue",
    }
    for order_id, status in detail_statuses.items():
        cur.execute(
            "UPDATE chi_tiet_don_thue SET trang_thai = %s WHERE id_don_thue = %s",
            (status, order_id),
        )

    order_statuses = {
        1: "Da qua han",
        2: "Da qua han",
        3: "Da qua han",
        4: "Da qua han",
        5: "Da thue",
        39: "Da dat",
        42: "Da xac nhan",
        64: "Da huy",
        65: "Da thue",
        67: "Dang thue",
    }
    for order_id, status in order_statuses.items():
        cur.execute(
            "UPDATE don_thue SET trang_thai = %s WHERE Id_don_thue = %s",
            (status, order_id),
        )


def clean_complaints(cur) -> None:
    cur.execute(
        """
        UPDATE khieu_nai
        SET id_khach_hang = 2,
            id_don_thue = 2,
            tieu_de = 'Thiết bị giao chậm',
            noi_dung = 'Khách hàng phản ánh đơn thuê giao chậm hơn lịch dự kiến và cần được hỗ trợ.',
            trang_thai = 'Đang xử lý',
            ngay_khieu_nai = '2026-06-10 09:15:00'
        WHERE Id_khieu_nai = 1
        """
    )
    cur.execute(
        """
        UPDATE khieu_nai
        SET id_khach_hang = 5,
            id_don_thue = 5,
            tieu_de = 'Thiết bị thiếu phụ kiện',
            noi_dung = 'Khách hàng phản ánh bộ thiết bị giao thiếu một pin dự phòng và cần bổ sung.',
            trang_thai = 'Chờ xử lý',
            ngay_khieu_nai = '2026-06-11 14:30:00'
        WHERE Id_khieu_nai = 2
        """
    )
    cur.execute(
        """
        UPDATE khieu_nai
        SET id_khach_hang = 1,
            id_don_thue = 67,
            tieu_de = 'Máy ảnh lấy nét chậm',
            noi_dung = 'Khách hàng đang thuê phản ánh máy lấy nét chậm trong điều kiện thiếu sáng và cần được tư vấn.',
            trang_thai = 'Đang xử lý',
            ngay_khieu_nai = '2026-06-22 10:05:00'
        WHERE Id_khieu_nai = 8
        """
    )


def clean_carts(cur) -> None:
    cur.execute(
        "UPDATE gio_hang SET ngay_nhan = '2026-06-28', ngay_tra = '2026-06-30' WHERE Id_gio_hang IN (6, 7)"
    )
    cur.execute(
        "UPDATE gio_hang SET ngay_nhan = '2026-06-27', ngay_tra = '2026-06-29' WHERE Id_gio_hang IN (60, 61)"
    )


def clean_chat(cur) -> None:
    cur.execute("DELETE FROM tin_nhan_chat WHERE id_cuoc_tro_chuyen <> %s", (KEEP_CONVERSATION_ID,))
    cur.execute("DELETE FROM chat_ticket WHERE id_yeu_cau_chat <> %s", (KEEP_TICKET_ID,))
    cur.execute("DELETE FROM cuoc_tro_chuyen WHERE id_cuoc_tro_chuyen <> %s", (KEEP_CONVERSATION_ID,))
    cur.execute("DELETE FROM tin_nhan_chat WHERE id_cuoc_tro_chuyen = %s", (KEEP_CONVERSATION_ID,))

    cur.execute(
        """
        UPDATE cuoc_tro_chuyen
        SET id_khach_hang = 1,
            id_nhan_vien = 1,
            che_do_chat = 'STAFF',
            trang_thai = 'NHAN_VIEN_DANG_XU_LY',
            chu_de = 'Tư vấn thuê máy quay vlog',
            can_nhan_vien = 1,
            ngay_tao = '2026-06-23 19:46:48',
            ngay_cap_nhat = '2026-06-23 19:49:53'
        WHERE id_cuoc_tro_chuyen = %s
        """,
        (KEEP_CONVERSATION_ID,),
    )
    cur.execute(
        """
        UPDATE chat_ticket
        SET id_cuoc_tro_chuyen = %s,
            id_khach_hang = 1,
            loai_yeu_cau = 'CAN_XAC_NHAN',
            noi_dung = 'Khách hàng cần nhân viên tư vấn thêm về thuê máy quay vlog và chính sách đặt cọc.',
            trang_thai = 'MOI',
            ngay_tao = '2026-06-23 19:46:48'
        WHERE id_yeu_cau_chat = %s
        """,
        (KEEP_CONVERSATION_ID, KEEP_TICKET_ID),
    )

    messages = [
        (KEEP_CONVERSATION_ID, "CUSTOMER", 1, "Tôi muốn tư vấn máy ảnh hoặc máy quay phù hợp để quay vlog trong 3 ngày.", "TEXT", 1, "2026-06-23 19:46:48"),
        (KEEP_CONVERSATION_ID, "STAFF", 1, "Chào anh/chị, SunLens Camera xin hỗ trợ. Mình ưu tiên quay vlog trong nhà hay ngoài trời để bên em tư vấn thiết bị phù hợp hơn ạ?", "TEXT", 1, "2026-06-23 19:47:10"),
        (KEEP_CONVERSATION_ID, "CUSTOMER", 1, "Mình quay ngoài trời, ngân sách khoảng 1 triệu và muốn hỏi thêm chính sách đặt cọc.", "TEXT", 1, "2026-06-23 19:48:12"),
        (KEEP_CONVERSATION_ID, "STAFF", 1, "Bên em gợi ý Sony A6400 hoặc Canon M50. Chính sách đặt cọc sẽ tùy giá trị thiết bị, nhân viên sẽ gửi chi tiết ngay trong cuộc trò chuyện này.", "TEXT", 1, "2026-06-23 19:49:53"),
    ]
    cur.executemany(
        """
        INSERT INTO tin_nhan_chat
            (id_cuoc_tro_chuyen, loai_nguoi_gui, id_nguoi_gui, noi_dung, loai_tin_nhan, da_doc, ngay_tao)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        messages,
    )


def clean_ai_messages(cur) -> None:
    cur.execute("DELETE FROM tin_nhan_ai")
    rows = [
        (1, "USER", "Xin chào, tôi muốn được tư vấn máy ảnh để quay vlog.", "2026-06-23 19:45:24"),
        (1, "AI", "Chào bạn, SunLens Camera rất vui được hỗ trợ. Bạn dự định thuê máy trong bao nhiêu ngày và ngân sách khoảng bao nhiêu ạ?", "2026-06-23 19:45:27"),
        (1, "USER", "Ngân sách của tôi khoảng 1 triệu cho 3 ngày.", "2026-06-23 19:45:41"),
        (1, "AI", "Với nhu cầu quay vlog trong 3 ngày, mình có thể tham khảo Sony A6400 hoặc Canon M50. Cả hai đều phù hợp cho nhu cầu quay ngoài trời.", "2026-06-23 19:45:44"),
        (1, "USER", "Tôi muốn hỏi thêm về chính sách đặt cọc.", "2026-06-23 19:46:18"),
        (1, "AI", "Bên em thường yêu cầu đặt cọc từ 200.000 VND và có thể thanh toán qua VNPAY hoặc chuyển khoản. Nếu bạn muốn, em sẽ kết nối nhân viên để hỗ trợ chi tiết hơn.", "2026-06-23 19:46:21"),
    ]
    cur.executemany(
        """
        INSERT INTO tin_nhan_ai (id_khach_hang, vai_tro, noi_dung, ngay_tao)
        VALUES (%s, %s, %s, %s)
        """,
        rows,
    )


def clean_notifications(cur) -> None:
    cur.execute("DELETE FROM thong_bao")
    rows = [
        (6, 39, "Đặt hàng thành công", "Đơn thuê #39 đã được tạo thành công.", "Dat hang thanh cong", "User", "Chua doc", "2026-06-13 23:45:22"),
        (1, 39, "Có đơn hàng mới", "Đơn thuê #39 vừa được tạo.", "Co don hang moi", "Admin", "Chua doc", "2026-06-13 23:45:22"),
        (3, 39, "Có đơn hàng mới", "Đơn thuê #39 vừa được tạo.", "Co don hang moi", "Nhan vien", "Chua doc", "2026-06-13 23:45:22"),
        (7, 42, "Xác nhận đơn thuê", "Đơn thuê #42 đã được xác nhận.", "Cap nhat don hang", "User", "Chua doc", "2026-06-18 14:58:30"),
        (6, 64, "Hủy đơn hàng thành công", "Bạn đã hủy đơn hàng #64 thành công.", "Cap nhat don hang", "User", "Da doc", "2026-06-21 19:08:10"),
        (1, 64, "Khách hàng hủy đơn hàng", "Khách hàng đã hủy đơn hàng #64.", "Cap nhat don hang", "Admin", "Da doc", "2026-06-21 19:08:10"),
        (3, 64, "Khách hàng hủy đơn hàng", "Khách hàng đã hủy đơn hàng #64.", "Cap nhat don hang", "Nhan vien", "Da doc", "2026-06-21 19:08:10"),
        (6, 65, "Đơn thuê hoàn tất", "Đơn thuê #65 đã hoàn tất.", "Cap nhat don hang", "User", "Chua doc", "2026-06-21 22:16:46"),
        (6, 67, "Đơn thuê đang được xử lý", "Đơn thuê #67 đang trong trạng thái đang thuê.", "Cap nhat don hang", "User", "Chua doc", "2026-06-21 23:31:07"),
        (1, 67, "Có đơn hàng mới", "Đơn thuê #67 đang được theo dõi để hỗ trợ khách hàng.", "Co don hang moi", "Admin", "Chua doc", "2026-06-21 23:31:07"),
        (3, 67, "Có đơn hàng mới", "Đơn thuê #67 đang được theo dõi để hỗ trợ khách hàng.", "Co don hang moi", "Nhan vien", "Chua doc", "2026-06-21 23:31:07"),
        (1, 67, "Khiếu nại mới cần xử lý", "Khách hàng vừa gửi một khiếu nại liên quan đến đơn thuê #67.", "Khieu nai", "Admin", "Chua doc", "2026-06-22 10:05:00"),
    ]
    cur.executemany(
        """
        INSERT INTO thong_bao
            (Id_tai_khoan, Id_don_thue, tieu_de, noi_dung, loai_thong_bao, doi_tuong_nhan, trang_thai, ngay_tao)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        rows,
    )


def collect_orphan_uploads(cur) -> list[str]:
    referenced = set()
    for table, column in [
        ("tai_khoan", "anh_dai_dien"),
        ("khach_hang", "Anh_CCCD_mat_truoc"),
        ("khach_hang", "Anh_CCCD_mat_sau"),
        ("don_thue", "Anh_chuyen_khoan"),
    ]:
        cur.execute(f"SELECT {column} AS path_value FROM {table} WHERE {column} IS NOT NULL AND TRIM({column}) <> ''")
        for row in cur.fetchall():
            value = row["path_value"]
            resolved = resolve_path(value)
            if resolved:
                referenced.add(str(resolved.resolve()).lower())

    all_files = []
    for folder in [
        Path(r"D:\HocTap\hocki2nam4\Final_DATN\DOANTOTNGHIEP_FrontEnd\Webthuemayanh_FE\user\Sunlens_Camera\assets\images\user"),
        Path(r"D:\HocTap\hocki2nam4\Final_DATN\DoAnTotNghiep_BackEnd\Backend\uploads\cccd"),
        Path(r"D:\HocTap\hocki2nam4\Final_DATN\DoAnTotNghiep_BackEnd\Backend\uploads\payment"),
    ]:
        if folder.exists():
            all_files.extend(folder.glob("*"))
    orphan = sorted(
        str(path.resolve())
        for path in all_files
        if str(path.resolve()).lower() not in referenced
    )
    return orphan


def validate(cur) -> dict:
    checks = {}
    checks["orphan_orders_customer"] = fetch_scalar(
        cur,
        """
        SELECT COUNT(*) AS total
        FROM don_thue d
        LEFT JOIN khach_hang k ON k.Id_khach_hang = d.Id_khach_hang
        WHERE k.Id_khach_hang IS NULL
        """,
    )
    checks["orphan_order_details_order"] = fetch_scalar(
        cur,
        """
        SELECT COUNT(*) AS total
        FROM chi_tiet_don_thue c
        LEFT JOIN don_thue d ON d.Id_don_thue = c.id_don_thue
        WHERE d.Id_don_thue IS NULL
        """,
    )
    checks["orphan_order_details_device"] = fetch_scalar(
        cur,
        """
        SELECT COUNT(*) AS total
        FROM chi_tiet_don_thue c
        LEFT JOIN thiet_bi t ON t.Id_thiet_bi = c.id_thiet_bi
        WHERE t.Id_thiet_bi IS NULL
        """,
    )
    checks["orphan_complaints"] = fetch_scalar(
        cur,
        """
        SELECT COUNT(*) AS total
        FROM khieu_nai k
        LEFT JOIN don_thue d ON d.Id_don_thue = k.id_don_thue
        LEFT JOIN khach_hang kh ON kh.Id_khach_hang = k.id_khach_hang
        WHERE d.Id_don_thue IS NULL OR kh.Id_khach_hang IS NULL
        """,
    )
    checks["orphan_notifications"] = fetch_scalar(
        cur,
        """
        SELECT COUNT(*) AS total
        FROM thong_bao t
        LEFT JOIN tai_khoan tk ON tk.id_tai_khoan = t.Id_tai_khoan
        LEFT JOIN don_thue d ON d.Id_don_thue = t.Id_don_thue
        WHERE tk.id_tai_khoan IS NULL OR d.Id_don_thue IS NULL
        """,
    )
    checks["orphan_carts"] = fetch_scalar(
        cur,
        """
        SELECT COUNT(*) AS total
        FROM gio_hang g
        LEFT JOIN khach_hang kh ON kh.Id_khach_hang = g.Id_khach_hang
        LEFT JOIN thiet_bi tb ON tb.Id_thiet_bi = g.Id_thiet_bi
        WHERE kh.Id_khach_hang IS NULL OR tb.Id_thiet_bi IS NULL
        """,
    )
    checks["orphan_chat_ticket"] = fetch_scalar(
        cur,
        """
        SELECT COUNT(*) AS total
        FROM chat_ticket ct
        LEFT JOIN cuoc_tro_chuyen c ON c.id_cuoc_tro_chuyen = ct.id_cuoc_tro_chuyen
        LEFT JOIN khach_hang kh ON kh.Id_khach_hang = ct.id_khach_hang
        WHERE c.id_cuoc_tro_chuyen IS NULL OR kh.Id_khach_hang IS NULL
        """,
    )
    checks["orphan_chat_message"] = fetch_scalar(
        cur,
        """
        SELECT COUNT(*) AS total
        FROM tin_nhan_chat tn
        LEFT JOIN cuoc_tro_chuyen c ON c.id_cuoc_tro_chuyen = tn.id_cuoc_tro_chuyen
        WHERE c.id_cuoc_tro_chuyen IS NULL
        """,
    )

    image_checks = []
    for table, column, label in [
        ("tai_khoan", "anh_dai_dien", "avatar"),
        ("khach_hang", "Anh_CCCD_mat_truoc", "cccd_front"),
        ("khach_hang", "Anh_CCCD_mat_sau", "cccd_back"),
        ("don_thue", "Anh_chuyen_khoan", "payment"),
    ]:
        cur.execute(f"SELECT {column} AS path_value FROM {table} WHERE {column} IS NOT NULL AND TRIM({column}) <> ''")
        for row in cur.fetchall():
            path_value = row["path_value"]
            image_checks.append(
                {
                    "group": label,
                    "path": path_value,
                    "exists": bool(resolve_path(path_value) or path_value.startswith("http")),
                }
            )
    checks["image_checks"] = image_checks
    return checks


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def main() -> None:
    with pymysql.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            before = collect_before_report(cur)
            write_json(REPORT_BEFORE, before)

            clean_notifications(cur)
            clean_ai_messages(cur)
            clean_chat(cur)
            standardize_accounts(cur)
            standardize_customers(cur)
            clean_orders_and_details(cur)
            clean_complaints(cur)
            clean_carts(cur)
            prune_accounts_and_customers(cur)

            checks = validate(cur)
            orphan = collect_orphan_uploads(cur)
            ORPHAN_UPLOADS.write_text("\n".join(orphan), encoding="utf-8")

            after_counts = {}
            for table in [
                "tai_khoan",
                "khach_hang",
                "nhan_vien",
                "don_thue",
                "chi_tiet_don_thue",
                "gio_hang",
                "khieu_nai",
                "thong_bao",
                "chat_ticket",
                "cuoc_tro_chuyen",
                "tin_nhan_chat",
                "tin_nhan_ai",
                "thiet_bi",
                "ma_giam_gia",
            ]:
                after_counts[table] = fetch_scalar(cur, f"SELECT COUNT(*) AS total FROM {table}")

            cur.execute(
                """
                SELECT tk.id_tai_khoan, tk.Dang_nhap, tk.Vai_tro, kh.Id_khach_hang, kh.ho_ten, kh.thu_dien_tu
                FROM tai_khoan tk
                LEFT JOIN khach_hang kh ON kh.Id_tai_khoan = tk.id_tai_khoan
                ORDER BY tk.id_tai_khoan
                """
            )
            final_accounts = cur.fetchall()

            cur.execute(
                """
                SELECT Id_don_thue, Id_khach_hang, trang_thai, Anh_chuyen_khoan
                FROM don_thue
                ORDER BY Id_don_thue
                """
            )
            final_orders = cur.fetchall()

            report_after = {
                "counts": after_counts,
                "final_accounts": final_accounts,
                "final_orders": final_orders,
                "checks": checks,
                "orphan_upload_count": len(orphan),
            }
            write_json(REPORT_AFTER, report_after)
        conn.commit()


if __name__ == "__main__":
    main()
