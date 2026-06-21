-- Raw MySQL migration for revision 20260617_0016.
-- Use this only on a database that still has the old English column names.
-- The Alembic Python migration is idempotent and safer for normal deployment.

ALTER TABLE TAI_KHOAN
CHANGE `Key` kich_hoat BIT(1) NULL;

ALTER TABLE TAI_KHOAN
CHANGE nha_cung_cap nha_cung_cap VARCHAR(20) NULL DEFAULT 'local';

ALTER TABLE TAI_KHOAN
CHANGE nha_cung_cap_id id_nha_cung_cap VARCHAR(255) NULL;

ALTER TABLE TAI_KHOAN
CHANGE anh_dai_dien anh_dai_dien VARCHAR(500) NULL;

ALTER TABLE TAI_KHOAN
DROP INDEX uq_tai_khoan_nha_cung_cap_identity;

ALTER TABLE TAI_KHOAN
ADD UNIQUE KEY uq_tai_khoan_nha_cung_cap_dinh_danh (nha_cung_cap, id_nha_cung_cap);

ALTER TABLE KHACH_HANG
CHANGE email thu_dien_tu VARCHAR(100) NULL;

ALTER TABLE THIET_BI
CHANGE danh_muc_id id_danh_muc INT NULL;

ALTER TABLE MA_GIAM_GIA
CHANGE ma_code ma_giam_gia VARCHAR(50) NOT NULL;

ALTER TABLE MA_GIAM_GIA
CHANGE created_at ngay_tao DATETIME NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE MA_GIAM_GIA
CHANGE updated_at ngay_cap_nhat DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

ALTER TABLE cuoc_tro_chuyen
CHANGE chat_mode che_do_chat ENUM('STAFF') NOT NULL DEFAULT 'STAFF';

ALTER TABLE cuoc_tro_chuyen
CHANGE need_staff can_nhan_vien TINYINT(1) NULL DEFAULT 0;

ALTER TABLE cuoc_tro_chuyen
CHANGE created_at ngay_tao DATETIME NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE cuoc_tro_chuyen
CHANGE updated_at ngay_cap_nhat DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

ALTER TABLE tin_nhan_chat
CHANGE sender_type loai_nguoi_gui ENUM('CUSTOMER','STAFF') NOT NULL;

ALTER TABLE tin_nhan_chat
CHANGE sender_id id_nguoi_gui INT NULL;

ALTER TABLE tin_nhan_chat
CHANGE created_at ngay_tao DATETIME NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE nhan_vien_online
CHANGE id id_nhan_vien_online INT NOT NULL AUTO_INCREMENT;

ALTER TABLE nhan_vien_online
CHANGE is_online dang_truc_tuyen TINYINT(1) NULL DEFAULT 0;

ALTER TABLE nhan_vien_online
CHANGE last_seen lan_cuoi_hoat_dong DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

ALTER TABLE chat_ticket
CHANGE id_ticket id_yeu_cau_chat INT NOT NULL AUTO_INCREMENT;

ALTER TABLE chat_ticket
CHANGE loai_ticket loai_yeu_cau ENUM('KHIEU_NAI','HUY_DON','HOAN_TIEN','CAN_XAC_NHAN','KHAC') NULL DEFAULT 'KHAC';

ALTER TABLE chat_ticket
CHANGE created_at ngay_tao DATETIME NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE backup_file_chat_before_drop_20260616_231740
CHANGE file_url duong_dan_tap_tin VARCHAR(500) NOT NULL;

ALTER TABLE backup_file_chat_before_drop_20260616_231740
CHANGE file_type loai_tap_tin VARCHAR(100) NULL;

ALTER TABLE backup_file_chat_before_drop_20260616_231740
CHANGE created_at ngay_tao DATETIME NULL DEFAULT CURRENT_TIMESTAMP;
