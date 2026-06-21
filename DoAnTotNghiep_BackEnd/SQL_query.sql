
drop database  do_an_tot_nghiep
CREATE DATABASE IF NOT EXISTS do_an_tot_nghiep;
USE do_an_tot_nghiep;

-- =========================
-- TABLE: TAI_KHOAN
-- =========================
CREATE TABLE TAI_KHOAN (
    id_tai_khoan INT AUTO_INCREMENT PRIMARY KEY,
    Dang_nhap VARCHAR(50) NOT NULL,
    Mat_khau VARCHAR(100) NOT NULL,
    Vai_tro VARCHAR(20),
    Trang_thai VARCHAR(20),
    `Key` BIT
);

INSERT INTO TAI_KHOAN (Dang_nhap, Mat_khau, Vai_tro, Trang_thai, `Key`) VALUES
('admin1','123456','Admin','Hoat dong',1),
('admin2','123456','Admin','Hoat dong',1),
('nv01','123456','Nhan vien','Hoat dong',1),
('nv02','123456','Nhan vien','Hoat dong',1),
('nv03','123456','Nhan vien','Hoat dong',1),
('kh01','123456','Khach hang','Hoat dong',1),
('kh02','123456','Khach hang','Hoat dong',1),
('kh03','123456','Khach hang','Hoat dong',1),
('kh04','123456','Khach hang','Hoat dong',1),
('kh05','123456','Khach hang','Hoat dong',1),
('kh06','123456','Khach hang','Hoat dong',1),
('kh07','123456','Khach hang','Hoat dong',1),
('kh08','123456','Khach hang','Hoat dong',1),
('kh09','123456','Khach hang','Hoat dong',1),
('kh10','123456','Khach hang','Hoat dong',1),
('kh11','123456','Khach hang','Hoat dong',1),
('kh12','123456','Khach hang','Hoat dong',1),
('kh13','123456','Khach hang','Hoat dong',1),
('kh14','123456','Khach hang','Hoat dong',1),
('kh15','123456','Khach hang','Hoat dong',1);

-- =========================
-- TABLE: NHAN_VIEN
-- =========================
CREATE TABLE NHAN_VIEN (
    Id_nhan_vien INT AUTO_INCREMENT PRIMARY KEY,
    Id_tai_khoan INT UNIQUE,
    ho_ten NVARCHAR(100),
    sdt NVARCHAR(20),
    FOREIGN KEY (Id_tai_khoan) REFERENCES TAI_KHOAN(id_tai_khoan)
);

INSERT INTO NHAN_VIEN (Id_tai_khoan, ho_ten, sdt) VALUES
(1,'Nguyen Van Admin','0901000001'),
(2,'Tran Thi Admin','0901000002'),
(3,'Le Van Nam','0901000003'),
(4,'Pham Gia Bao','0901000004'),
(5,'Vo Minh Quan','0901000005');

-- =========================
-- TABLE: KHACH_HANG
-- =========================
CREATE TABLE KHACH_HANG (
    Id_khach_hang INT AUTO_INCREMENT PRIMARY KEY,
    Id_tai_khoan INT UNIQUE,
    ho_ten NVARCHAR(100),
    sdt VARCHAR(20),
    gioi_tinh NVARCHAR(20),
    ngay_sinh DATE,
    dia_chi NVARCHAR(255),
    So_CCCD VARCHAR(20),
    Anh_CCCD_mat_truoc VARCHAR(255),
    Anh_CCCD_mat_sau VARCHAR(255),
    email VARCHAR(100),
    Anh_CCCD VARCHAR(255),
    FOREIGN KEY (Id_tai_khoan) REFERENCES TAI_KHOAN(id_tai_khoan)
);

INSERT INTO KHACH_HANG
(Id_tai_khoan, ho_ten, sdt, So_CCCD, Anh_CCCD_mat_truoc, Anh_CCCD_mat_sau, email, Anh_CCCD)
VALUES
(6,'Nguyen Van A','0911111111','001001000001','cccd_truoc1.jpg','cccd_sau1.jpg','a@gmail.com','anh_dai_dien1.jpg'),
(7,'Tran Thi B','0911111112','001001000002','cccd_truoc2.jpg','cccd_sau2.jpg','b@gmail.com','anh_dai_dien2.jpg'),
(8,'Le Van C','0911111113','001001000003','cccd_truoc3.jpg','cccd_sau3.jpg','c@gmail.com','anh_dai_dien3.jpg'),
(9,'Pham Thi D','0911111114','001001000004','cccd_truoc4.jpg','cccd_sau4.jpg','d@gmail.com','anh_dai_dien4.jpg'),
(10,'Vo Minh E','0911111115','001001000005','cccd_truoc5.jpg','cccd_sau5.jpg','e@gmail.com','anh_dai_dien5.jpg'),
(11,'Hoang Gia F','0911111116','001001000006','cccd_truoc6.jpg','cccd_sau6.jpg','f@gmail.com','anh_dai_dien6.jpg'),
(12,'Do Thi G','0911111117','001001000007','cccd_truoc7.jpg','cccd_sau7.jpg','g@gmail.com','anh_dai_dien7.jpg'),
(13,'Bui Van H','0911111118','001001000008','cccd_truoc8.jpg','cccd_sau8.jpg','h@gmail.com','anh_dai_dien8.jpg'),
(14,'Nguyen Thi I','0911111119','001001000009','cccd_truoc9.jpg','cccd_sau9.jpg','i@gmail.com','anh_dai_dien9.jpg'),
(15,'Tran Van K','0911111120','001001000010','cccd_truoc10.jpg','cccd_sau10.jpg','k@gmail.com','anh_dai_dien10.jpg'),
(16,'Pham Gia L','0911111121','001001000011','cccd_truoc11.jpg','cccd_sau11.jpg','l@gmail.com','anh_dai_dien11.jpg'),
(17,'Le Minh M','0911111122','001001000012','cccd_truoc12.jpg','cccd_sau12.jpg','m@gmail.com','anh_dai_dien12.jpg'),
(18,'Vo Thi N','0911111123','001001000013','cccd_truoc13.jpg','cccd_sau13.jpg','n@gmail.com','anh_dai_dien13.jpg'),
(19,'Huynh Van O','0911111124','001001000014','cccd_truoc14.jpg','cccd_sau14.jpg','o@gmail.com','anh_dai_dien14.jpg'),
(20,'Dang Thi P','0911111125','001001000015','cccd_truoc15.jpg','cccd_sau15.jpg','p@gmail.com','anh_dai_dien15.jpg');

-- =========================
-- TABLE: DANH_MUC
-- =========================
CREATE TABLE DANH_MUC (
    Id_danh_muc INT AUTO_INCREMENT PRIMARY KEY,
    ten_danh_muc NVARCHAR(100),
    mo_ta NVARCHAR(255)
);

INSERT INTO DANH_MUC (ten_danh_muc, mo_ta) VALUES
('May anh DSLR','May anh chup hinh chuyen nghiep'),
('May anh Mirrorless','May anh khong guong lat'),
('Ong kinh','Cac loai lens'),
('Flycam','Thiet bi bay quay phim'),
('Phu kien','Tripod, den, pin');

-- =========================




CREATE TABLE THIET_BI (
    Id_thiet_bi INT AUTO_INCREMENT PRIMARY KEY,

    ten_thiet_bi NVARCHAR(100) NOT NULL,

    danh_muc_id INT,

    so_luong INT DEFAULT 0,

    gia_thue DECIMAL(12,2),

    tinh_trang NVARCHAR(50),

    mo_ta NVARCHAR(255),

    FOREIGN KEY (danh_muc_id)
    REFERENCES DANH_MUC(Id_danh_muc)
);



-- =========================
-- INSERT DATA THIET_BI
-- =========================




INSERT INTO THIET_BI
(
    ten_thiet_bi,
    danh_muc_id,
    so_luong,
    gia_thue,
    tinh_trang,
    mo_ta
)
VALUES

('Canon EOS 5D',1,3,500000,'San sang','DSLR FullFrame'),
('Canon 90D',1,2,350000,'San sang','DSLR Canon'),
('Nikon D750',1,0,450000,'Dang thue','DSLR Nikon'),

('Sony A7III',2,5,700000,'San sang','Mirrorless Sony'),
('Sony A6400',2,1,500000,'San sang','Sony vlog'),
('Canon R6',2,0,800000,'Dang thue','Canon mirrorless'),

('Lens 50mm f1.8',3,4,150000,'San sang','Lens portrait'),
('Lens 24-70mm',3,2,300000,'San sang','Lens zoom'),
('Lens 70-200mm',3,0,450000,'Dang thue','Lens tele'),

('DJI Mini 3',4,3,600000,'San sang','Flycam du lich'),
('DJI Air 3',4,1,900000,'San sang','Flycam cao cap'),

('Tripod Beike',5,10,100000,'San sang','Tripod'),
('Den LED Yongnuo',5,6,120000,'San sang','Den quay phim'),
('Pin Sony NP-FZ100',5,8,80000,'San sang','Pin du phong'),

('GoPro Hero 12',5,0,550000,'Dang thue','Action camera'),

('Canon RF 24-105',3,2,400000,'San sang','Lens RF'),
('Sony 85mm GM',3,1,550000,'San sang','Lens chan dung'),

('Macbook Edit Video',5,1,1000000,'San sang','Laptop edit'),

('DJI RS3',5,0,450000,'Dang thue','Gimbal'),

('Mic Rode Wireless',5,4,250000,'San sang','Micro');

-- =========================
-- TABLE: DON_THUE
-- =========================



CREATE TABLE DON_THUE (

    Id_don_thue INT AUTO_INCREMENT PRIMARY KEY,

    Id_khach_hang INT,

    ngay_dat DATETIME DEFAULT CURRENT_TIMESTAMP,

    trang_thai ENUM(
        'Cho xac nhan',
        'Da xac nhan',
        'Dang thue',
        'Da thue',
        'Da qua han'
    ) DEFAULT 'Cho xac nhan',

    tong_tien DECIMAL(12,2),

    Anh_chuyen_khoan VARCHAR(255),

    ghi_chu NVARCHAR(255),

    FOREIGN KEY (Id_khach_hang)
    REFERENCES KHACH_HANG(Id_khach_hang)
);



-- =========================
-- INSERT DATA DON_THUE
-- =========================

INSERT INTO DON_THUE
(
    Id_khach_hang,
    ngay_dat,
    trang_thai,
    tong_tien,
    Anh_chuyen_khoan,
    ghi_chu
)
VALUES

(1,'2025-05-01 10:00:00',
'Cho xac nhan',
1200000,
'ck1.jpg',
'Khach dat online'),

(2,'2025-05-02 09:00:00',
'Da xac nhan',
1500000,
'ck2.jpg',
'Cho giao may'),

(3,'2025-05-03 08:30:00',
'Dang thue',
700000,
'ck3.jpg',
'Khach dang su dung'),

(4,'2025-05-04 11:00:00',
'Da thue',
2000000,
'ck4.jpg',
'Da tra may'),

(5,'2025-05-05 13:20:00',
'Da qua han',
2500000,
'ck5.jpg',
'Khach tra tre'),

(6,'2025-05-06 14:10:00',
'Cho xac nhan',
900000,
'ck6.jpg',
'Can xac minh CCCD'),

(7,'2025-05-07 15:30:00',
'Da xac nhan',
450000,
'ck7.jpg',
'Da thanh toan'),

(8,'2025-05-08 16:40:00',
'Dang thue',
1300000,
'ck8.jpg',
'Thue 2 ngay'),

(9,'2025-05-09 09:45:00',
'Da thue',
1100000,
'ck9.jpg',
'Khach VIP'),

(10,'2025-05-10 12:15:00',
'Da qua han',
600000,
'ck10.jpg',
'Qua han 1 ngay');

-- =========================
-- TABLE: CHI_TIET_DON_THUE
-- =========================
CREATE TABLE CHI_TIET_DON_THUE (
    Id_chi_tiet_don_thue INT AUTO_INCREMENT PRIMARY KEY,
    id_don_thue INT,
    id_thiet_bi INT,
    ngay_nhan DATETIME,
    ngay_tra DATETIME,
    so_luong INT,
    gia_thue DECIMAL(10,2),
    FOREIGN KEY (id_don_thue) REFERENCES DON_THUE(Id_don_thue),
    FOREIGN KEY (id_thiet_bi) REFERENCES THIET_BI(Id_thiet_bi)
);

INSERT INTO CHI_TIET_DON_THUE
(id_don_thue, id_thiet_bi, ngay_nhan, ngay_tra, so_luong, gia_thue)
VALUES
(1,1,'2025-05-01','2025-05-03',1,500000),
(1,7,'2025-05-01','2025-05-03',1,150000),
(2,4,'2025-05-02','2025-05-04',1,700000),
(2,8,'2025-05-02','2025-05-04',1,300000),
(3,10,'2025-05-03','2025-05-04',1,600000),
(4,5,'2025-05-04','2025-05-05',1,500000),
(5,6,'2025-05-05','2025-05-07',1,800000),
(5,9,'2025-05-05','2025-05-07',1,450000),
(6,11,'2025-05-06','2025-05-08',1,900000),
(7,12,'2025-05-07','2025-05-07',2,100000),
(8,15,'2025-05-08','2025-05-09',1,550000),
(8,13,'2025-05-08','2025-05-09',1,120000),
(9,16,'2025-05-09','2025-05-11',1,400000),
(9,20,'2025-05-09','2025-05-11',1,250000),
(10,18,'2025-05-10','2025-05-12',1,1000000);

-- =========================
-- TABLE: KHIEU_NAI
-- =========================
CREATE TABLE KHIEU_NAI (
    Id_khieu_nai INT AUTO_INCREMENT PRIMARY KEY,
    id_don_thue INT,
    id_khach_hang INT,
    noi_dung NVARCHAR(255),
    trang_thai NVARCHAR(50),
    FOREIGN KEY (id_don_thue) REFERENCES DON_THUE(Id_don_thue),
    FOREIGN KEY (id_khach_hang) REFERENCES KHACH_HANG(Id_khach_hang)
);

CREATE TABLE KHIEU_NAI (
    Id_khieu_nai INT AUTO_INCREMENT PRIMARY KEY,
    id_don_thue INT,
    id_khach_hang INT,
    noi_dung NVARCHAR(255),
    trang_thai NVARCHAR(50),
    ngay_khieu_nai DATETIME,
    FOREIGN KEY (id_don_thue) REFERENCES DON_THUE(Id_don_thue),
    FOREIGN KEY (id_khach_hang) REFERENCES KHACH_HANG(Id_khach_hang)
);

INSERT INTO KHIEU_NAI
(id_don_thue, id_khach_hang, noi_dung, trang_thai, ngay_khieu_nai)
VALUES
(2,2,'May bi loi pin','Dang xu ly','2026-05-10 09:15:00'),
(5,5,'Thiet bi giao tre','Da tiep nhan','2026-05-11 14:30:00'),
(8,8,'Lens co vet xuoc','Dang kiem tra','2026-05-12 11:00:00'),
(9,9,'Khong dung du phu kien','Da xu ly','2026-05-13 16:20:00'),
(10,10,'Hoan tien cham','Cho phan hoi','2026-05-14 10:45:00');


DELIMITER $$

CREATE PROCEDURE sp_tao_don_thue (
    IN p_id_khach_hang INT,
    IN p_anh_ck VARCHAR(255),
    IN p_ghi_chu NVARCHAR(255)
)
BEGIN

    INSERT INTO DON_THUE
    (
        Id_khach_hang,
        ngay_dat,
        trang_thai,
        tong_tien,
        Anh_chuyen_khoan,
        ghi_chu
    )
    VALUES
    (
        p_id_khach_hang,
        NOW(),
        'Cho xac nhan',
        0,
        p_anh_ck,
        p_ghi_chu
    );

END $$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE sp_them_chi_tiet_thue (
    IN p_id_don_thue INT,
    IN p_id_thiet_bi INT,
    IN p_ngay_nhan DATETIME,
    IN p_ngay_tra DATETIME,
    IN p_so_luong INT
)
BEGIN

    DECLARE v_gia_thue DECIMAL(12,2);

    SELECT gia_thue
    INTO v_gia_thue
    FROM THIET_BI
    WHERE Id_thiet_bi = p_id_thiet_bi;

    INSERT INTO CHI_TIET_DON_THUE
    (
        id_don_thue,
        id_thiet_bi,
        ngay_nhan,
        ngay_tra,
        so_luong,
        gia_thue
    )
    VALUES
    (
        p_id_don_thue,
        p_id_thiet_bi,
        p_ngay_nhan,
        p_ngay_tra,
        p_so_luong,
        v_gia_thue
    );

    UPDATE THIET_BI
    SET so_luong = so_luong - p_so_luong
    WHERE Id_thiet_bi = p_id_thiet_bi;

END $$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE sp_tim_thiet_bi (
    IN p_tu_khoa VARCHAR(100)
)
BEGIN

    SELECT *
    FROM THIET_BI
    WHERE ten_thiet_bi LIKE CONCAT('%', p_tu_khoa, '%')
       OR mo_ta LIKE CONCAT('%', p_tu_khoa, '%');

END $$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER trg_update_tinh_trang
BEFORE UPDATE ON THIET_BI
FOR EACH ROW
BEGIN

    IF NEW.so_luong <= 0 THEN
        SET NEW.tinh_trang = 'Dang thue';
    ELSE
        SET NEW.tinh_trang = 'San sang';
    END IF;

END $$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER trg_update_tong_tien
AFTER INSERT ON CHI_TIET_DON_THUE
FOR EACH ROW
BEGIN

    UPDATE DON_THUE
    SET tong_tien =
    (
        SELECT SUM(gia_thue * so_luong)
        FROM CHI_TIET_DON_THUE
        WHERE id_don_thue = NEW.id_don_thue
    )
    WHERE Id_don_thue = NEW.id_don_thue;

END $$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER trg_update_trang_thai_don
BEFORE UPDATE ON DON_THUE
FOR EACH ROW
BEGIN

    IF NEW.trang_thai = 'Dang thue'
       AND OLD.trang_thai = 'Cho xac nhan'
    THEN
        SET NEW.trang_thai = 'Da xac nhan';
    END IF;

END $$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER trg_kiem_tra_qua_han
BEFORE UPDATE ON CHI_TIET_DON_THUE
FOR EACH ROW
BEGIN

    IF NEW.ngay_tra < NOW() THEN

        UPDATE DON_THUE
        SET trang_thai = 'Da qua han'
        WHERE Id_don_thue = NEW.id_don_thue;

    END IF;

END $$

DELIMITER ;

CREATE VIEW vw_lich_su_thue AS

SELECT
    dt.Id_don_thue,
    kh.ho_ten,
    tb.ten_thiet_bi,
    ctdt.ngay_nhan,
    ctdt.ngay_tra,
    ctdt.so_luong,
    ctdt.gia_thue
FROM DON_THUE dt

JOIN KHACH_HANG kh
ON dt.Id_khach_hang = kh.Id_khach_hang

JOIN CHI_TIET_DON_THUE ctdt
ON dt.Id_don_thue = ctdt.id_don_thue

JOIN THIET_BI tb
ON ctdt.id_thiet_bi = tb.Id_thiet_bi;

-- =========================================
-- FUNCTION: kiểm tra thiết bị còn hàng
-- =========================================

DELIMITER $$

CREATE FUNCTION fn_con_hang (
    p_id_thiet_bi INT
)
RETURNS VARCHAR(50)

DETERMINISTIC

BEGIN

    DECLARE v_so_luong INT;

    SELECT so_luong
    INTO v_so_luong
    FROM THIET_BI
    WHERE Id_thiet_bi = p_id_thiet_bi;

    IF v_so_luong > 0 THEN
        RETURN 'Con hang';
    ELSE
        RETURN 'Het hang';
    END IF;

END $$

DELIMITER ;



-- =========================================
-- FUNCTION: đếm số lần thuê của khách
-- =========================================

DELIMITER $$

CREATE FUNCTION fn_so_lan_thue (
    p_id_khach_hang INT
)
RETURNS INT

DETERMINISTIC

BEGIN

    DECLARE v_so_lan INT;

    SELECT COUNT(*)
    INTO v_so_lan
    FROM DON_THUE
    WHERE Id_khach_hang = p_id_khach_hang;

    RETURN v_so_lan;

END $$

DELIMITER ;



-- =========================================
-- FUNCTION: tính số ngày thuê
-- =========================================

DELIMITER $$

CREATE FUNCTION fn_so_ngay_thue (
    p_ngay_nhan DATETIME,
    p_ngay_tra DATETIME
)
RETURNS INT

DETERMINISTIC

BEGIN

    RETURN DATEDIFF(p_ngay_tra, p_ngay_nhan);

END $$

DELIMITER ;



-- =========================================
-- FUNCTION: format tiền VNĐ
-- =========================================

DELIMITER $$

CREATE FUNCTION fn_format_tien (
    p_tien DECIMAL(12,2)
)
RETURNS VARCHAR(50)

DETERMINISTIC

BEGIN

    RETURN CONCAT(FORMAT(p_tien,0), ' VNĐ');

END $$

DELIMITER ;



-- =========================================
-- FUNCTION: đếm số thiết bị đang thuê
-- =========================================

DELIMITER $$

CREATE FUNCTION fn_so_tb_dang_thue ()
RETURNS INT

DETERMINISTIC

BEGIN

    DECLARE v_count INT;

    SELECT COUNT(*)
    INTO v_count
    FROM THIET_BI
    WHERE tinh_trang = 'Dang thue';

    RETURN v_count;

END $$

DELIMITER ;



-- =========================================
-- FUNCTION: lấy tên danh mục
-- =========================================

DELIMITER $$

CREATE FUNCTION fn_ten_danh_muc (
    p_id_danh_muc INT
)
RETURNS VARCHAR(100)

DETERMINISTIC

BEGIN

    DECLARE v_ten VARCHAR(100);

    SELECT ten_danh_muc
    INTO v_ten
    FROM DANH_MUC
    WHERE Id_danh_muc = p_id_danh_muc;

    RETURN v_ten;

END $$

DELIMITER ;



-- =========================================
-- FUNCTION: tổng doanh thu
-- =========================================

DELIMITER $$

CREATE FUNCTION fn_tong_doanh_thu ()
RETURNS DECIMAL(12,2)

DETERMINISTIC

BEGIN

    DECLARE v_doanh_thu DECIMAL(12,2);

    SELECT SUM(tong_tien)
    INTO v_doanh_thu
    FROM DON_THUE;

    RETURN IFNULL(v_doanh_thu,0);

END $$

DELIMITER ;



-- =========================================
-- FUNCTION: kiểm tra đơn quá hạn
-- =========================================

DELIMITER $$

CREATE FUNCTION fn_kiem_tra_qua_han (
    p_id_don_thue INT
)
RETURNS VARCHAR(50)

DETERMINISTIC

BEGIN

    DECLARE v_ngay_tra DATETIME;

    SELECT MAX(ngay_tra)
    INTO v_ngay_tra
    FROM CHI_TIET_DON_THUE
    WHERE id_don_thue = p_id_don_thue;

    IF v_ngay_tra < NOW() THEN
        RETURN 'Da qua han';
    ELSE
        RETURN 'Con han';
    END IF;

END $$

DELIMITER ;

-- =========================================
-- FUNCTION: tính tổng tiền đơn thuê
-- =========================================

DELIMITER $$

CREATE FUNCTION fn_tinh_tong_tien (
    p_id_don_thue INT
)
RETURNS DECIMAL(12,2)

DETERMINISTIC

BEGIN

    DECLARE v_tong_tien DECIMAL(12,2);

    SELECT 
        SUM(gia_thue * so_luong)
    INTO v_tong_tien
    FROM CHI_TIET_DON_THUE
    WHERE id_don_thue = p_id_don_thue;

    RETURN IFNULL(v_tong_tien, 0);

END $$

DELIMITER ;vw_lich_su_thue
