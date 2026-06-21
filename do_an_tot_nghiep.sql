CREATE DATABASE  IF NOT EXISTS `do_an_tot_nghiep` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `do_an_tot_nghiep`;
-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: do_an_tot_nghiep
-- ------------------------------------------------------
-- Server version	9.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('20260619_0021');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chat_ticket`
--

DROP TABLE IF EXISTS `chat_ticket`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chat_ticket` (
  `id_yeu_cau_chat` int NOT NULL AUTO_INCREMENT,
  `id_cuoc_tro_chuyen` int NOT NULL,
  `id_khach_hang` int NOT NULL,
  `loai_yeu_cau` enum('KHIEU_NAI','HUY_DON','HOAN_TIEN','CAN_XAC_NHAN','KHAC') DEFAULT 'KHAC',
  `noi_dung` text,
  `trang_thai` enum('MOI','DANG_XU_LY','DA_XU_LY') DEFAULT 'MOI',
  `ngay_tao` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_yeu_cau_chat`),
  KEY `ix_chat_ticket_cuoc_tro_chuyen` (`id_cuoc_tro_chuyen`),
  KEY `ix_chat_ticket_khach_hang` (`id_khach_hang`),
  KEY `ix_chat_ticket_trang_thai` (`trang_thai`),
  CONSTRAINT `chat_ticket_ibfk_1` FOREIGN KEY (`id_cuoc_tro_chuyen`) REFERENCES `cuoc_tro_chuyen` (`id_cuoc_tro_chuyen`),
  CONSTRAINT `chat_ticket_ibfk_2` FOREIGN KEY (`id_khach_hang`) REFERENCES `khach_hang` (`Id_khach_hang`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chat_ticket`
--

LOCK TABLES `chat_ticket` WRITE;
/*!40000 ALTER TABLE `chat_ticket` DISABLE KEYS */;
INSERT INTO `chat_ticket` VALUES (1,1,1,'KHAC','Khách hàng yêu cầu chat với nhân viên.','MOI','2026-06-04 17:29:47'),(2,3,16,'KHAC','Khách hàng yêu cầu chat với nhân viên.','MOI','2026-06-07 18:09:48');
/*!40000 ALTER TABLE `chat_ticket` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chi_tiet_don_thue`
--

DROP TABLE IF EXISTS `chi_tiet_don_thue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chi_tiet_don_thue` (
  `Id_chi_tiet_don_thue` int NOT NULL AUTO_INCREMENT,
  `id_don_thue` int DEFAULT NULL,
  `id_thiet_bi` int DEFAULT NULL,
  `ngay_nhan` datetime DEFAULT NULL,
  `ngay_tra` datetime DEFAULT NULL,
  `so_luong` int DEFAULT NULL,
  `gia_thue` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`Id_chi_tiet_don_thue`),
  KEY `id_don_thue` (`id_don_thue`),
  KEY `id_thiet_bi` (`id_thiet_bi`),
  CONSTRAINT `chi_tiet_don_thue_ibfk_1` FOREIGN KEY (`id_don_thue`) REFERENCES `don_thue` (`Id_don_thue`),
  CONSTRAINT `chi_tiet_don_thue_ibfk_2` FOREIGN KEY (`id_thiet_bi`) REFERENCES `thiet_bi` (`Id_thiet_bi`)
) ENGINE=InnoDB AUTO_INCREMENT=105 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chi_tiet_don_thue`
--

LOCK TABLES `chi_tiet_don_thue` WRITE;
/*!40000 ALTER TABLE `chi_tiet_don_thue` DISABLE KEYS */;
INSERT INTO `chi_tiet_don_thue` VALUES (1,1,1,'2025-05-01 00:00:00','2025-05-03 00:00:00',1,500000.00),(2,1,7,'2025-05-01 00:00:00','2025-05-03 00:00:00',1,150000.00),(3,2,4,'2025-05-02 00:00:00','2025-05-04 00:00:00',1,700000.00),(4,2,8,'2025-05-02 00:00:00','2025-05-04 00:00:00',1,300000.00),(5,3,10,'2025-05-03 00:00:00','2025-05-04 00:00:00',1,600000.00),(6,4,5,'2025-05-04 00:00:00','2025-05-05 00:00:00',1,500000.00),(7,5,6,'2025-05-05 00:00:00','2025-05-07 00:00:00',1,800000.00),(8,5,9,'2025-05-05 00:00:00','2025-05-07 00:00:00',1,450000.00),(9,6,11,'2025-05-06 00:00:00','2025-05-08 00:00:00',1,900000.00),(10,7,12,'2025-05-07 00:00:00','2025-05-07 00:00:00',2,100000.00),(11,8,15,'2025-05-08 00:00:00','2025-05-09 00:00:00',1,550000.00),(12,8,13,'2025-05-08 00:00:00','2025-05-09 00:00:00',1,120000.00),(13,9,16,'2025-05-09 00:00:00','2025-05-11 00:00:00',1,400000.00),(14,9,20,'2025-05-09 00:00:00','2025-05-11 00:00:00',1,250000.00),(15,10,18,'2025-05-10 00:00:00','2025-05-12 00:00:00',1,1000000.00),(16,13,7,'2026-06-02 00:00:00','2026-06-05 00:00:00',1,150000.00),(17,13,10,'2026-06-02 00:00:00','2026-06-05 00:00:00',1,600000.00),(18,13,1,'2026-05-30 00:00:00','2026-06-04 00:00:00',1,500000.00),(19,14,1,'2026-06-05 00:00:00','2026-06-08 00:00:00',1,500000.00),(20,15,5,'2026-06-06 00:00:00','2026-06-07 00:00:00',1,500000.00),(84,39,2,'2026-06-14 00:00:00','2026-06-17 00:00:00',1,350000.00),(85,40,2,'2026-06-18 00:00:00','2026-06-21 00:00:00',1,350000.00),(87,42,1,'2026-06-18 00:00:00','2026-06-20 00:00:00',1,500000.00),(88,43,1,'2026-06-20 00:00:00','2026-06-23 00:00:00',1,500000.00),(89,44,1,'2026-06-20 00:00:00','2026-06-22 00:00:00',1,500000.00),(90,45,1,'2026-06-20 00:00:00','2026-06-23 00:00:00',1,500000.00),(91,46,4,'2026-06-20 00:00:00','2026-06-21 00:00:00',1,700000.00),(92,47,7,'2026-06-20 00:00:00','2026-06-21 00:00:00',1,150000.00),(93,48,2,'2026-06-20 00:00:00','2026-06-23 00:00:00',1,350000.00),(94,49,7,'2026-06-21 00:00:00','2026-06-22 00:00:00',1,150000.00),(95,50,14,'2026-06-21 00:00:00','2026-06-24 00:00:00',1,80000.00),(96,51,14,'2026-06-21 00:00:00','2026-06-24 00:00:00',1,80000.00),(97,52,11,'2026-06-21 00:00:00','2026-06-24 00:00:00',1,900000.00),(98,55,14,'2026-06-21 00:00:00','2026-06-24 00:00:00',1,80000.00),(99,56,14,'2026-06-21 00:00:00','2026-06-24 00:00:00',1,80000.00),(100,57,20,'2026-06-21 00:00:00','2026-06-24 00:00:00',1,250000.00),(101,58,20,'2026-06-21 00:00:00','2026-06-24 00:00:00',1,250000.00),(102,59,2,'2026-06-21 00:00:00','2026-06-24 00:00:00',1,350000.00),(103,60,1,'2026-06-21 00:00:00','2026-06-24 00:00:00',1,500000.00),(104,61,2,'2026-06-21 00:00:00','2026-06-24 00:00:00',1,350000.00);
/*!40000 ALTER TABLE `chi_tiet_don_thue` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_update_tong_tien` AFTER INSERT ON `chi_tiet_don_thue` FOR EACH ROW BEGIN

    UPDATE DON_THUE
    SET tong_tien =
    (
        SELECT SUM(gia_thue * so_luong)
        FROM CHI_TIET_DON_THUE
        WHERE id_don_thue = NEW.id_don_thue
    )
    WHERE Id_don_thue = NEW.id_don_thue;

END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_kiem_tra_qua_han` BEFORE UPDATE ON `chi_tiet_don_thue` FOR EACH ROW BEGIN

    IF NEW.ngay_tra < NOW() THEN

        UPDATE DON_THUE
        SET trang_thai = 'Da qua han'
        WHERE Id_don_thue = NEW.id_don_thue;

    END IF;

END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `cuoc_tro_chuyen`
--

DROP TABLE IF EXISTS `cuoc_tro_chuyen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cuoc_tro_chuyen` (
  `id_cuoc_tro_chuyen` int NOT NULL AUTO_INCREMENT,
  `id_khach_hang` int NOT NULL,
  `id_nhan_vien` int DEFAULT NULL,
  `che_do_chat` enum('STAFF') NOT NULL DEFAULT 'STAFF',
  `trang_thai` enum('CHO_NHAN_VIEN','NHAN_VIEN_DANG_XU_LY','DA_DONG') NOT NULL DEFAULT 'CHO_NHAN_VIEN',
  `chu_de` varchar(255) DEFAULT NULL,
  `can_nhan_vien` tinyint(1) DEFAULT '0',
  `ngay_tao` datetime DEFAULT CURRENT_TIMESTAMP,
  `ngay_cap_nhat` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_cuoc_tro_chuyen`),
  KEY `ix_cuoc_tro_chuyen_khach_hang` (`id_khach_hang`),
  KEY `ix_cuoc_tro_chuyen_nhan_vien` (`id_nhan_vien`),
  KEY `ix_cuoc_tro_chuyen_trang_thai` (`trang_thai`),
  KEY `ix_cuoc_tro_chuyen_created_at` (`ngay_tao`),
  CONSTRAINT `cuoc_tro_chuyen_ibfk_1` FOREIGN KEY (`id_khach_hang`) REFERENCES `khach_hang` (`Id_khach_hang`),
  CONSTRAINT `cuoc_tro_chuyen_ibfk_2` FOREIGN KEY (`id_nhan_vien`) REFERENCES `nhan_vien` (`Id_nhan_vien`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cuoc_tro_chuyen`
--

LOCK TABLES `cuoc_tro_chuyen` WRITE;
/*!40000 ALTER TABLE `cuoc_tro_chuyen` DISABLE KEYS */;
INSERT INTO `cuoc_tro_chuyen` VALUES (1,1,1,'STAFF','NHAN_VIEN_DANG_XU_LY',NULL,0,'2026-06-04 17:29:47','2026-06-18 06:32:22'),(2,1,1,'STAFF','NHAN_VIEN_DANG_XU_LY',NULL,0,'2026-06-04 17:39:35','2026-06-18 08:00:50'),(3,16,1,'STAFF','NHAN_VIEN_DANG_XU_LY',NULL,0,'2026-06-07 18:09:48','2026-06-18 02:13:20'),(4,2,1,'STAFF','NHAN_VIEN_DANG_XU_LY',NULL,0,'2026-06-13 21:53:01','2026-06-18 02:13:18'),(5,1,1,'STAFF','NHAN_VIEN_DANG_XU_LY',NULL,0,'2026-06-18 13:33:33','2026-06-21 13:02:14'),(6,3,1,'STAFF','NHAN_VIEN_DANG_XU_LY',NULL,0,'2026-06-18 20:35:01','2026-06-18 20:36:41');
/*!40000 ALTER TABLE `cuoc_tro_chuyen` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `danh_muc`
--

DROP TABLE IF EXISTS `danh_muc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `danh_muc` (
  `Id_danh_muc` int NOT NULL AUTO_INCREMENT,
  `ten_danh_muc` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `mo_ta` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  PRIMARY KEY (`Id_danh_muc`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `danh_muc`
--

LOCK TABLES `danh_muc` WRITE;
/*!40000 ALTER TABLE `danh_muc` DISABLE KEYS */;
INSERT INTO `danh_muc` VALUES (1,'Máy ảnh DSLR','Máy ảnh chụp hình chuyên nghiệp'),(2,'Máy ảnh Mirrorless','Máy ảnh không gương lật'),(3,'Ống kính','Các loại Lens'),(4,'Flycam','Thiết bị bay quay phim'),(5,'Phụ kiện','Tripod, đèn , pin');
/*!40000 ALTER TABLE `danh_muc` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `don_thue`
--

DROP TABLE IF EXISTS `don_thue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `don_thue` (
  `Id_don_thue` int NOT NULL AUTO_INCREMENT,
  `Id_khach_hang` int DEFAULT NULL,
  `ngay_dat` datetime DEFAULT CURRENT_TIMESTAMP,
  `trang_thai` enum('Cho thanh toan','Da dat','Da xac nhan','Dang thue','Da thue','Da huy','Da qua han') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Da dat',
  `tong_tien` decimal(12,2) DEFAULT NULL,
  `Anh_chuyen_khoan` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ghi_chu` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id_ma_giam_gia` int DEFAULT NULL,
  `so_tien_giam` decimal(12,2) DEFAULT '0.00',
  `phuong_thuc_thanh_toan` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ma_giao_dich_vnpay` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `so_tien_da_thanh_toan` decimal(12,2) DEFAULT '0.00',
  `han_thanh_toan_vnpay` datetime DEFAULT NULL,
  `ngay_thanh_toan` datetime DEFAULT NULL,
  PRIMARY KEY (`Id_don_thue`),
  KEY `Id_khach_hang` (`Id_khach_hang`),
  KEY `fk_don_thue_ma_giam_gia` (`id_ma_giam_gia`),
  CONSTRAINT `don_thue_ibfk_1` FOREIGN KEY (`Id_khach_hang`) REFERENCES `khach_hang` (`Id_khach_hang`),
  CONSTRAINT `fk_don_thue_ma_giam_gia` FOREIGN KEY (`id_ma_giam_gia`) REFERENCES `ma_giam_gia` (`id_ma_giam_gia`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=62 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `don_thue`
--

LOCK TABLES `don_thue` WRITE;
/*!40000 ALTER TABLE `don_thue` DISABLE KEYS */;
INSERT INTO `don_thue` VALUES (1,1,'2025-05-01 10:00:00','Da qua han',1200000.00,'/uploads/payment/ce730ee986af4456b7ffb98119fe259c.jpg','Khach dat online',NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(2,2,'2025-05-02 09:00:00','Da qua han',1500000.00,'ck2.jpg','Cho giao may',NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(3,3,'2025-05-03 08:30:00','Da qua han',700000.00,'ck3.jpg','Khach dang su dung',NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(4,4,'2025-05-04 11:00:00','Da qua han',2000000.00,'ck4.jpg','Da tra may',NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(5,5,'2025-05-05 13:20:00','Da thue',2500000.00,'ck5.jpg','Khach tra tre',NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(6,6,'2025-05-06 14:10:00','Da thue',900000.00,'ck6.jpg','Can xac minh CCCD',NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(7,7,'2025-05-07 15:30:00','Da thue',450000.00,'ck7.jpg','Da thanh toan',NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(8,8,'2025-05-08 16:40:00','Da thue',1300000.00,'ck8.jpg','Thue 2 ngay',NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(9,9,'2025-05-09 09:45:00','Da thue',1100000.00,'ck9.jpg','Khach VIP',NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(10,10,'2025-05-10 12:15:00','Da thue',600000.00,'ck10.jpg','Qua han 1 ngay',NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(13,1,'2026-06-03 22:04:26','Da huy',4750000.00,NULL,'Ly do huy: Khách hàng tự hủy đơn',NULL,0.00,'Chuyen khoan thu cong',NULL,0.00,NULL,NULL),(14,1,'2026-06-04 12:01:39','Dang thue',1500000.00,NULL,'Ly do huy: Khách hàng tự hủy đơn',NULL,0.00,'Chuyen khoan thu cong',NULL,0.00,NULL,NULL),(15,1,'2026-06-05 17:52:57','Dang thue',500000.00,NULL,NULL,NULL,0.00,'Chuyen khoan thu cong',NULL,0.00,NULL,NULL),(39,1,'2026-06-13 23:45:22','Da dat',1050000.00,'/uploads/payment/24b05a9131e54e1b940047b7b69ec76a.jpg',NULL,NULL,0.00,'Chuyen khoan thu cong',NULL,0.00,NULL,NULL),(40,1,'2026-06-17 14:00:10','Dang thue',1050000.00,'/uploads/payment/500efb6f716d44ce9eed72ef357ec24d.jpg',NULL,NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(42,2,'2026-06-18 14:55:25','Da dat',900000.00,'/uploads/payment/eb8a9eb1301c45d491b02659b7c98321.jpg',NULL,3,100000.00,'Chuyen khoan thu cong',NULL,0.00,NULL,NULL),(43,1,'2026-06-19 12:15:57','Da huy',1500000.00,NULL,'Ly do huy: Khách hàng tự hủy đơn',NULL,0.00,'VNPAY',NULL,0.00,NULL,NULL),(44,1,'2026-06-19 12:32:40','Da huy',1000000.00,NULL,'Hệ thống tự động hủy do quá thời gian thanh toán VNPAY.',NULL,0.00,'VNPAY',NULL,0.00,'2026-06-19 12:47:40',NULL),(45,1,'2026-06-19 12:36:25','Da thue',1500000.00,'/uploads/payment/b68a3f5a62374ea986fbeae94f6993da.jpg',NULL,NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(46,1,'2026-06-19 13:18:39','Da xac nhan',700000.00,NULL,NULL,NULL,0.00,'VNPAY','15589753',200000.00,'2026-06-19 13:33:39','2026-06-19 13:19:02'),(47,1,'2026-06-19 13:21:56','Da xac nhan',150000.00,'/uploads/payment/7855855b96ac433bad09e695dbc70217.jpg',NULL,NULL,0.00,'Chuyen khoan thu cong',NULL,200000.00,NULL,NULL),(48,1,'2026-06-19 14:59:14','Da thue',1050000.00,NULL,NULL,NULL,0.00,'VNPAY','15589909',200000.00,'2026-06-19 15:14:14','2026-06-19 15:00:35'),(49,1,'2026-06-20 01:34:59','Da huy',150000.00,NULL,'Ly do huy: Khách hàng tự hủy đơn',NULL,0.00,'VNPAY','15590761',200000.00,'2026-06-20 01:50:00','2026-06-20 01:36:21'),(50,1,'2026-06-20 01:37:51','Da huy',240000.00,'/uploads/payment/65e7cbe8ab9e4187982746674b46d404.jpg','Ly do huy: Khách hàng tự hủy đơn',NULL,0.00,'Chuyen khoan thu cong',NULL,0.00,NULL,NULL),(51,1,'2026-06-20 01:39:09','Da huy',240000.00,'/uploads/payment/74fd1ecfc73a4468a75c4010be8e058d.jpg','Ly do huy: Khách hàng tự hủy đơn',NULL,0.00,'Chuyen khoan thu cong',NULL,0.00,NULL,NULL),(52,2,'2026-06-20 01:41:39','Da dat',2700000.00,NULL,NULL,NULL,0.00,'Chuyen khoan thu cong',NULL,0.00,NULL,NULL),(55,1,'2026-06-20 02:29:02','Da huy',240000.00,'/uploads/payment/b7ce599a6e1f49399afe84c11b41747b.jpg','Ly do huy: Khách hàng tự hủy đơn',NULL,0.00,'Chuyen khoan thu cong',NULL,0.00,NULL,NULL),(56,1,'2026-06-20 02:31:01','Da huy',240000.00,'/uploads/payment/04a0865f33aa4444a428e68b95880ccf.jpg','Ly do huy: Khách hàng tự hủy đơn',NULL,0.00,'Chuyen khoan thu cong',NULL,0.00,NULL,NULL),(57,1,'2026-06-20 02:41:07','Da huy',750000.00,'/uploads/payment/9eff26c4bfd34bff987205f7e3a7f0c7.jpg','Ly do huy: Khách hàng tự hủy đơn',NULL,0.00,'Chuyen khoan thu cong',NULL,0.00,NULL,NULL),(58,1,'2026-06-20 02:48:30','Da xac nhan',750000.00,NULL,NULL,NULL,0.00,'VNPAY','15590799',200000.00,'2026-06-20 03:03:30','2026-06-20 02:48:50'),(59,1,'2026-06-20 09:57:18','Dang thue',1050000.00,NULL,NULL,NULL,0.00,'VNPAY','15590972',200000.00,'2026-06-20 10:12:19','2026-06-20 09:57:53'),(60,1,'2026-06-20 10:22:29','Da huy',1500000.00,NULL,'Hệ thống tự động hủy do quá thời gian thanh toán VNPAY.',NULL,0.00,'VNPAY',NULL,0.00,'2026-06-20 10:37:30',NULL),(61,1,'2026-06-20 19:28:14','Da thue',1050000.00,NULL,NULL,NULL,0.00,'VNPAY','15591425',200000.00,'2026-06-20 19:43:14','2026-06-20 19:29:11');
/*!40000 ALTER TABLE `don_thue` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_update_trang_thai_don` BEFORE UPDATE ON `don_thue` FOR EACH ROW BEGIN

    IF NEW.trang_thai = 'Dang thue'
       AND OLD.trang_thai = 'Cho xac nhan'
    THEN
        SET NEW.trang_thai = 'Da xac nhan';
    END IF;

END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `gio_hang`
--

DROP TABLE IF EXISTS `gio_hang`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gio_hang` (
  `Id_gio_hang` int NOT NULL AUTO_INCREMENT,
  `Id_khach_hang` int NOT NULL,
  `Id_thiet_bi` int NOT NULL,
  `so_luong` int DEFAULT '1',
  `ngay_nhan` date DEFAULT NULL,
  `ngay_tra` date DEFAULT NULL,
  `ngay_them` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Id_gio_hang`),
  KEY `Id_khach_hang` (`Id_khach_hang`),
  KEY `Id_thiet_bi` (`Id_thiet_bi`),
  CONSTRAINT `gio_hang_ibfk_1` FOREIGN KEY (`Id_khach_hang`) REFERENCES `khach_hang` (`Id_khach_hang`),
  CONSTRAINT `gio_hang_ibfk_2` FOREIGN KEY (`Id_thiet_bi`) REFERENCES `thiet_bi` (`Id_thiet_bi`)
) ENGINE=InnoDB AUTO_INCREMENT=52 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gio_hang`
--

LOCK TABLES `gio_hang` WRITE;
/*!40000 ALTER TABLE `gio_hang` DISABLE KEYS */;
INSERT INTO `gio_hang` VALUES (6,4,6,1,'2026-06-04','2026-06-06','2026-06-01 17:51:35'),(7,4,7,1,'2026-06-04','2026-06-06','2026-06-01 17:51:35'),(8,5,8,1,'2026-06-05','2026-06-08','2026-06-01 17:51:35'),(9,6,9,1,'2026-06-06','2026-06-10','2026-06-01 17:51:35'),(10,7,10,1,'2026-06-07','2026-06-12','2026-06-01 17:51:35'),(11,8,11,2,'2026-06-08','2026-06-10','2026-06-01 17:51:35'),(12,9,12,1,'2026-06-09','2026-06-13','2026-06-01 17:51:35'),(13,10,13,1,'2026-06-10','2026-06-15','2026-06-01 17:51:35');
/*!40000 ALTER TABLE `gio_hang` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `khach_hang`
--

DROP TABLE IF EXISTS `khach_hang`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `khach_hang` (
  `Id_khach_hang` int NOT NULL AUTO_INCREMENT,
  `Id_tai_khoan` int DEFAULT NULL,
  `ho_ten` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `sdt` varchar(20) DEFAULT NULL,
  `So_CCCD` varchar(20) DEFAULT NULL,
  `Anh_CCCD_mat_truoc` varchar(255) DEFAULT NULL,
  `Anh_CCCD_mat_sau` varchar(255) DEFAULT NULL,
  `thu_dien_tu` varchar(100) DEFAULT NULL,
  `Anh_CCCD` varchar(255) DEFAULT NULL,
  `gioi_tinh` varchar(20) DEFAULT NULL,
  `ngay_sinh` date DEFAULT NULL,
  `dia_chi` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Id_khach_hang`),
  UNIQUE KEY `Id_tai_khoan` (`Id_tai_khoan`),
  UNIQUE KEY `uq_khach_hang_sdt` (`sdt`),
  UNIQUE KEY `uq_khach_hang_so_cccd` (`So_CCCD`),
  UNIQUE KEY `uq_khach_hang_email` (`thu_dien_tu`),
  CONSTRAINT `khach_hang_ibfk_1` FOREIGN KEY (`Id_tai_khoan`) REFERENCES `tai_khoan` (`id_tai_khoan`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `khach_hang`
--

LOCK TABLES `khach_hang` WRITE;
/*!40000 ALTER TABLE `khach_hang` DISABLE KEYS */;
INSERT INTO `khach_hang` VALUES (1,6,'Công Hiếu Trầnnnn','+84906586982','001001000123','assets/images/user/cccd_front_1.jpg','assets/images/user/cccd_back_1.jpg','sunlenscamera@gmail.com','assets/images/user/cccd_anh_dai_dien_1.png','Nam','2026-06-11','382/37/9 hùng vương , thanh khê , Đà Nẵngg'),(2,7,'Tran Thi B','0911111112','001001000002','assets/images/user/cccd_front_2.jpg','assets/images/user/cccd_back_2.jpg','b@gmail.com','avatar2.jpg',NULL,NULL,NULL),(3,8,'Trần Công Hiếu','0906586981','046204009663','assets/images/user/cccd_front_3.jpg','assets/images/user/cccd_back_3.jpg','c@gmail.com','https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=2189004655196082&height=50&width=50&ext=1783914613&hash=AftuegFySRhPyz9FxUsibAhP',NULL,'2004-06-13','382 Hùng Vương'),(4,9,'Pham Thi D','0911111114','001001000004','cccd_truoc4.jpg','cccd_sau4.jpg','d@gmail.com','avatar4.jpg',NULL,NULL,NULL),(5,10,'Vo Minh E','0911111115','001001000005','cccd_truoc5.jpg','cccd_sau5.jpg','e@gmail.com','avatar5.jpg',NULL,NULL,NULL),(6,11,'Hoang Gia F','0911111116','001001000006','cccd_truoc6.jpg','cccd_sau6.jpg','f@gmail.com','avatar6.jpg',NULL,NULL,NULL),(7,12,'Do Thi G','0911111117','001001000007','cccd_truoc7.jpg','cccd_sau7.jpg','g@gmail.com','avatar7.jpg',NULL,NULL,NULL),(8,13,'Bui Van H','0911111118','001001000008','cccd_truoc8.jpg','cccd_sau8.jpg','h@gmail.com','avatar8.jpg',NULL,NULL,NULL),(9,14,'Nguyen Thi I','0911111119','001001000009','cccd_truoc9.jpg','cccd_sau9.jpg','i@gmail.com','avatar9.jpg',NULL,NULL,NULL),(10,15,'Tran Van K','0911111120','001001000010','cccd_truoc10.jpg','cccd_sau10.jpg','k@gmail.com','avatar10.jpg',NULL,NULL,NULL),(11,16,'Pham Gia L','0911111121','001001000011','cccd_truoc11.jpg','cccd_sau11.jpg','l@gmail.com','avatar11.jpg',NULL,NULL,NULL),(12,17,'Le Minh M','0911111122','001001000012','cccd_truoc12.jpg','cccd_sau12.jpg','m@gmail.com','avatar12.jpg',NULL,NULL,NULL),(13,18,'Vo Thi N','0911111123','001001000013','cccd_truoc13.jpg','cccd_sau13.jpg','n@gmail.com','avatar13.jpg',NULL,NULL,NULL),(14,19,'Huynh Van O','0911111124','001001000014','cccd_truoc14.jpg','cccd_sau14.jpg','o@gmail.com','avatar14.jpg',NULL,NULL,NULL),(15,20,'Dang Thi P','0911111125','001001000015','cccd_truoc15.jpg','cccd_sau15.jpg','p@gmail.com','avatar15.jpg',NULL,NULL,NULL),(16,22,'Công Hiếu Trần',NULL,'046204009665','assets/images/user/cccd_front_16.jpg','assets/images/user/cccd_back_16.png','conghieu2k4@gmail.com','assets/images/user/cccd_avatar_16.png',NULL,NULL,NULL),(17,23,'Công Hiếu Trần',NULL,'04602301233','assets/images/user/cccd_front_17.png',NULL,NULL,NULL,NULL,NULL,NULL),(18,24,'nha nho Tiem',NULL,NULL,NULL,NULL,'shoppetiemnhanho123@gmail.com',NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `khach_hang` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `khieu_nai`
--

DROP TABLE IF EXISTS `khieu_nai`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `khieu_nai` (
  `Id_khieu_nai` int NOT NULL AUTO_INCREMENT,
  `id_don_thue` int DEFAULT NULL,
  `id_khach_hang` int DEFAULT NULL,
  `noi_dung` text,
  `trang_thai` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `ngay_khieu_nai` datetime DEFAULT NULL,
  `tieu_de` varchar(255) DEFAULT NULL,
  `san_pham_khieu_nai` text,
  PRIMARY KEY (`Id_khieu_nai`),
  KEY `id_don_thue` (`id_don_thue`),
  KEY `id_khach_hang` (`id_khach_hang`),
  CONSTRAINT `khieu_nai_ibfk_1` FOREIGN KEY (`id_don_thue`) REFERENCES `don_thue` (`Id_don_thue`),
  CONSTRAINT `khieu_nai_ibfk_2` FOREIGN KEY (`id_khach_hang`) REFERENCES `khach_hang` (`Id_khach_hang`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `khieu_nai`
--

LOCK TABLES `khieu_nai` WRITE;
/*!40000 ALTER TABLE `khieu_nai` DISABLE KEYS */;
INSERT INTO `khieu_nai` VALUES (1,2,2,'May bi loi pin','Đang xử lý','2026-05-10 09:15:00','máy bay hỏng','[\"DJI Mini 3\"]'),(2,5,5,'Thiet bi giao tre','Đã tiếp nhận','2026-05-11 14:30:00','Không quay được khi bay','[\"DJI Mini 3\"]'),(3,8,8,'Lens co vet xuoc','Đã xử lý','2026-05-12 11:00:00','Không khởi dộng nguồn được','[\"Lens SONY 50mm f1.8\"]'),(4,9,9,'Khong dung du phu kien','Đã xử lý','2026-05-13 16:20:00','Màn hình nhạt','[\"Lens SONY 50mm f1.8\"]'),(5,10,10,'Hoan tien cham','Da xu ly','2026-05-14 10:45:00','Lỗi pin','[\"Canon EOS 5D\"]'),(6,13,1,'Camera khi nhận bị tình trạng hơi xương mong shop hỗ trợ','Đã xử lý','2026-06-04 19:21:38','Camera bị hơi sương','[\"Canon EOS 5D\"]'),(7,13,1,'Flycam bị lỗi điều khiển không được','Đang xử lý','2026-06-05 18:47:39','Flycam bị lỗi','[\"Lens SONY 50mm f1.8\", \"DJI Mini 3\"]'),(8,40,1,'camera bị mờ','Chờ xử lý','2026-06-18 14:59:14','Camera bị hơi sương','[\"Canon M50\"]'),(9,40,1,'camera bị bụi','Cho phan hoi','2026-06-18 15:02:25','Camera bị hơi sương','[\"Canon M50\"]'),(10,47,1,'cam bị mờ','Cho phan hoi','2026-06-20 01:24:32','cam mờ','[\"Lens SONY 50mm f1.8\"]');
/*!40000 ALTER TABLE `khieu_nai` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ma_giam_gia`
--

DROP TABLE IF EXISTS `ma_giam_gia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ma_giam_gia` (
  `id_ma_giam_gia` int NOT NULL AUTO_INCREMENT,
  `ma_giam_gia` varchar(50) NOT NULL,
  `ten_ma` varchar(255) DEFAULT NULL,
  `mo_ta` varchar(255) DEFAULT NULL,
  `loai_giam_gia` enum('phan_tram','tien_mat') NOT NULL,
  `gia_tri_giam` decimal(12,2) NOT NULL,
  `dieu_kien_loai` enum('so_ngay_thue','tong_tien_don','khong_dieu_kien') DEFAULT 'khong_dieu_kien',
  `so_ngay_thue_toi_thieu` int DEFAULT '0',
  `gia_tri_don_toi_thieu` decimal(12,2) DEFAULT '0.00',
  `ngay_bat_dau` date DEFAULT NULL,
  `ngay_ket_thuc` date DEFAULT NULL,
  `so_luong` int DEFAULT '0',
  `da_su_dung` int DEFAULT '0',
  `trang_thai` enum('dang_hoat_dong','tam_ngung','het_han') DEFAULT 'dang_hoat_dong',
  `ngay_tao` datetime DEFAULT CURRENT_TIMESTAMP,
  `ngay_cap_nhat` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_ma_giam_gia`),
  UNIQUE KEY `ma_code` (`ma_giam_gia`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ma_giam_gia`
--

LOCK TABLES `ma_giam_gia` WRITE;
/*!40000 ALTER TABLE `ma_giam_gia` DISABLE KEYS */;
INSERT INTO `ma_giam_gia` VALUES (1,'THUE3NGAY10','Thuê 3 ngày giảm 10%','Giảm 10% khi thuê từ 3 ngày trở lên','phan_tram',10.00,'so_ngay_thue',3,0.00,'2026-01-01','2030-12-31',0,0,'dang_hoat_dong','2026-06-05 23:59:25','2026-06-05 23:59:25'),(2,'THUE7NGAY20','Thuê 7 ngày giảm 20%','Giảm 20% khi thuê từ 7 ngày trở lên','phan_tram',20.00,'so_ngay_thue',7,0.00,'2026-01-01','2030-12-31',0,0,'dang_hoat_dong','2026-06-05 23:59:25','2026-06-05 23:59:25'),(3,'GIAM100K','Giảm 100.000đ','Giảm 100.000đ cho đơn từ 1.000.000đ','tien_mat',100000.00,'tong_tien_don',0,1000000.00,'2026-01-01','2030-12-31',0,1,'dang_hoat_dong','2026-06-05 23:59:25','2026-06-18 14:55:25'),(4,'GIAM200K','giam200k',NULL,'tien_mat',200000.00,'tong_tien_don',0,1000000.00,'2026-06-17','2026-06-20',5,0,'dang_hoat_dong','2026-06-17 14:05:42','2026-06-19 00:59:13');
/*!40000 ALTER TABLE `ma_giam_gia` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `nhan_vien`
--

DROP TABLE IF EXISTS `nhan_vien`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nhan_vien` (
  `Id_nhan_vien` int NOT NULL AUTO_INCREMENT,
  `Id_tai_khoan` int DEFAULT NULL,
  `ho_ten` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `sdt` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  PRIMARY KEY (`Id_nhan_vien`),
  UNIQUE KEY `Id_tai_khoan` (`Id_tai_khoan`),
  CONSTRAINT `nhan_vien_ibfk_1` FOREIGN KEY (`Id_tai_khoan`) REFERENCES `tai_khoan` (`id_tai_khoan`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `nhan_vien`
--

LOCK TABLES `nhan_vien` WRITE;
/*!40000 ALTER TABLE `nhan_vien` DISABLE KEYS */;
INSERT INTO `nhan_vien` VALUES (1,1,'Tran Cong Hieu','0901000001'),(2,2,'Tran Thi Minh','0901000003'),(3,3,'Le Van Nam','0901000003'),(4,4,'Pham Gia Bao','0901000004'),(5,5,'Vo Minh Quan','0901000005');
/*!40000 ALTER TABLE `nhan_vien` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `nhan_vien_online`
--

DROP TABLE IF EXISTS `nhan_vien_online`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nhan_vien_online` (
  `id_nhan_vien_online` int NOT NULL AUTO_INCREMENT,
  `id_nhan_vien` int NOT NULL,
  `dang_truc_tuyen` tinyint(1) DEFAULT '0',
  `lan_cuoi_hoat_dong` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_nhan_vien_online`),
  UNIQUE KEY `ix_nhan_vien_online_nhan_vien` (`id_nhan_vien`),
  KEY `ix_nhan_vien_online_online` (`dang_truc_tuyen`,`lan_cuoi_hoat_dong`),
  CONSTRAINT `nhan_vien_online_ibfk_1` FOREIGN KEY (`id_nhan_vien`) REFERENCES `nhan_vien` (`Id_nhan_vien`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `nhan_vien_online`
--

LOCK TABLES `nhan_vien_online` WRITE;
/*!40000 ALTER TABLE `nhan_vien_online` DISABLE KEYS */;
INSERT INTO `nhan_vien_online` VALUES (1,1,0,'2026-06-21 06:34:32'),(2,3,0,'2026-06-20 12:36:09');
/*!40000 ALTER TABLE `nhan_vien_online` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tai_khoan`
--

DROP TABLE IF EXISTS `tai_khoan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tai_khoan` (
  `id_tai_khoan` int NOT NULL AUTO_INCREMENT,
  `Dang_nhap` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Mat_khau` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Vai_tro` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `Trang_thai` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `kich_hoat` bit(1) DEFAULT NULL,
  `nha_cung_cap` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'local',
  `id_nha_cung_cap` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `anh_dai_dien` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id_tai_khoan`),
  UNIQUE KEY `uq_tai_khoan_dang_nhap` (`Dang_nhap`),
  UNIQUE KEY `uq_tai_khoan_nha_cung_cap_dinh_danh` (`nha_cung_cap`,`id_nha_cung_cap`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tai_khoan`
--

LOCK TABLES `tai_khoan` WRITE;
/*!40000 ALTER TABLE `tai_khoan` DISABLE KEYS */;
INSERT INTO `tai_khoan` VALUES (1,'admin1','$2b$12$D6q.p5wbTO7RqO4kX0qg3.TPXAVBa8oUmg8hWp4mFNAipP0cVq8x.','Admin','Hoat dong',_binary '','local',NULL,NULL),(2,'admin2','$2b$12$I.qpbeqTjqjd3LxmvCKVAuDigYTudpM23f6p3uk2KXN4HAX66bmxq','Admin','Hoat dong',_binary '','local',NULL,NULL),(3,'nv01','$2b$12$snxJKVcQvo1.RQUU9dj/HOGfAgU5eFJYd/Zd0c89CRWIKktl2vTn6','Nhan vien','Hoat dong',_binary '','local',NULL,NULL),(4,'nv02','$2b$12$I/qmMxwhsDegOQni8KR9Hu9OVERviWdpxlsfUbCcBfW/R/Tw67tbG','Nhan vien','Hoat dong',_binary '','local',NULL,NULL),(5,'nv03','123456','Nhan vien','Hoat dong',_binary '','local',NULL,NULL),(6,'kh01','$2b$12$.Ps7sgj0svk8qRacQMrE/O2VM12W6G6WBbyxmli8MxvxgWMYPLECO','Khach hang','Hoat dong',_binary '','facebook','2189004655196082','https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=2189004655196082&height=50&width=50&ext=1784400019&hash=Afs1CsJ4XVA1Sli9y4dIH0f7'),(7,'kh02','$2b$12$vp7TfdWokLRNOUBxyOlNWOUSZraUBPlIhKukGGH.OqhXqTsfT1BoO','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(8,'kh03','$2b$12$MAKeyqnHbVK1k2fhPjn55e5pH/C39jS7fEk1lmslsMZoTIoZYXs4C','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(9,'kh04','123456','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(10,'kh05','123456','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(11,'kh06','123456','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(12,'kh07','123456','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(13,'kh08','123456','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(14,'kh09','123456','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(15,'kh10','123456','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(16,'kh11','$2b$12$qDusYFbBr82rrbcVWaxACOg3maEz.xDAhOebwhTCpd7YOZNFY2zFK','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(17,'kh12','123456','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(18,'kh13','123456','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(19,'kh14','123456','Khach hang','Ngung hoat dong',_binary '\0','local',NULL,NULL),(20,'kh15','123456','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(21,'nv04','$2b$12$5VII/waM2WHJ173drrADSujjcXAXIAVyKsZx5STU.dDgpbj6cYAfS','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(22,'conghieu06','$2b$12$2nRcBUXllAJek1TMdLSOCOki6rZvvDrFCZOaZedG9jqGokIm6hKXm','Khach hang','Hoat dong',_binary '','google','107490726199448842098','https://lh3.googleusercontent.com/a/ACg8ocIgEWuNd4EBdfgYql2kMWrj_P5RAcZoscnW_ZSSdAgSigjgNb7h=s96-c'),(23,'eqeq','$2b$12$wQEOVWN8mnyM2UzrERgi9eDvoI5rHs3lnPATO8cllt3mxb.IYyIjC','Khach hang','Hoat dong',_binary '','local',NULL,NULL),(24,'google_92jSOj9TcGM','$2b$12$JbADMXRAA9r1JejNwQ/JGOR8gsxg0Xov8BhU1onYJhkqCf1OwrgWi','Khach hang','Hoat dong',_binary '','google','102107869757960883692','https://lh3.googleusercontent.com/a/ACg8ocJpaRU42IfiR6aleDWnLzDCBvFNrO88zVprljQrHD81Pv94Gw=s96-c');
/*!40000 ALTER TABLE `tai_khoan` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `thiet_bi`
--

DROP TABLE IF EXISTS `thiet_bi`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `thiet_bi` (
  `Id_thiet_bi` int NOT NULL AUTO_INCREMENT,
  `ten_thiet_bi` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `id_danh_muc` int DEFAULT NULL,
  `so_luong` int DEFAULT '0',
  `gia_thue` decimal(12,2) DEFAULT NULL,
  `tinh_trang` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `mo_ta` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `hinh_anh` varchar(2000) DEFAULT NULL,
  PRIMARY KEY (`Id_thiet_bi`),
  KEY `danh_muc_id` (`id_danh_muc`),
  CONSTRAINT `thiet_bi_ibfk_1` FOREIGN KEY (`id_danh_muc`) REFERENCES `danh_muc` (`Id_danh_muc`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `thiet_bi`
--

LOCK TABLES `thiet_bi` WRITE;
/*!40000 ALTER TABLE `thiet_bi` DISABLE KEYS */;
INSERT INTO `thiet_bi` VALUES (1,'Canon EOS 5D',1,2,500000.00,'San sang','DSLR FullFrame','[\"assets/images/product/device_1_1.png\", \"assets/images/product/device_1_2.png\", \"assets/images/product/device_1_3.png\", \"assets/images/product/device_1_4.png\", \"assets/images/product/device_1_5.png\"]'),(2,'Canon M50',1,2,350000.00,'San sang','DSLR Canon','[\"assets/images/product/device_2_1.png\", \"assets/images/product/device_2_2.png\", \"assets/images/product/device_2_3.png\", \"assets/images/product/device_2_4.png\", \"assets/images/product/device_2_5.png\"]'),(3,'Nikon D750',1,0,450000.00,'Dang thue','DSLR Nikon','[\"assets/images/product/device_3_1.png\"]'),(4,'Sony A7III',2,5,700000.00,'San sang','Mirrorless Sony','[\"assets/images/product/device_4_1.png\"]'),(5,'Sony A6400',2,1,500000.00,'San sang','Sony vlog','[\"assets/images/product/device_5_1.png\"]'),(6,'Canon R6',2,0,800000.00,'Dang thue','Canon mirrorless','[\"assets/images/product/device_6_1.png\"]'),(7,'Lens SONY 50mm f1.8',3,3,150000.00,'San sang','Lens portrait','[\"assets/images/product/device_7_1.png\"]'),(8,'Lens Canon 24-70mm',3,2,300000.00,'San sang','Lens zoom','[\"assets/images/product/device_8_1.png\"]'),(9,'Lens Canon 70-200mm',3,0,450000.00,'Dang thue','Lens tele','[\"assets/images/product/device_9_1.png\"]'),(10,'DJI Mini 3',4,2,600000.00,'San sang','Flycam du lich','[\"assets/images/product/device_10_1.png\"]'),(11,'DJI Air 3',4,1,900000.00,'San sang','Flycam cao cap','[\"assets/images/product/device_11_1.png\"]'),(12,'Tripod Beike',5,10,100000.00,'San sang','Tripod','[\"assets/images/product/device_12_1.png\"]'),(13,'Đèn LED Yongnuo',5,6,120000.00,'San sang','Den quay phim','[\"assets/images/product/device_13_1.png\"]'),(14,'Pin Sony NP-FZ100',5,8,80000.00,'San sang','Pin du phong','[\"assets/images/product/device_14_1.png\"]'),(15,'GoPro Hero 12',5,0,550000.00,'Dang thue','Action camera','[\"assets/images/product/device_15_1.png\"]'),(16,'Canon RF 24-105',3,2,400000.00,'San sang','Lens RF','[\"assets/images/product/device_16_1.png\"]'),(17,'Sony 85mm GM',3,1,550000.00,'San sang','Lens chan dung','[\"assets/images/product/device_17_1.png\"]'),(18,'Phông vải cotton cao cấp phông nền chụp hình quay phim',5,1,70000.00,'San sang','Chất liệu: Vải cotton cao cấp; dày dặn; ít nhăn, bề mặt mịn giúp ánh sáng phản chiếu đều, mang lại hình ảnh tự nhiên và sắc nét','[\"assets/images/product/device_18_1.png\"]'),(19,'DJI RS3',5,0,450000.00,'Dang thue','Gimbal','[\"assets/images/product/device_19_1.png\"]'),(20,'Tấm hất sáng 60cm',5,4,250000.00,'San sang','Tấm hất sáng','[\"assets/images/product/device_20_1.png\"]');
/*!40000 ALTER TABLE `thiet_bi` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_update_tinh_trang` BEFORE UPDATE ON `thiet_bi` FOR EACH ROW BEGIN

    IF NEW.so_luong <= 0 THEN
        SET NEW.tinh_trang = 'Dang thue';
    ELSE
        SET NEW.tinh_trang = 'San sang';
    END IF;

END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `thong_bao`
--

DROP TABLE IF EXISTS `thong_bao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `thong_bao` (
  `Id_thong_bao` int NOT NULL AUTO_INCREMENT,
  `Id_tai_khoan` int DEFAULT NULL,
  `Id_don_thue` int DEFAULT NULL,
  `tieu_de` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `noi_dung` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `loai_thong_bao` enum('Dat hang thanh cong','Co don hang moi','Cap nhat don hang','Khieu nai','He thong') COLLATE utf8mb4_unicode_ci DEFAULT 'He thong',
  `doi_tuong_nhan` enum('User','Admin','Nhan vien') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `trang_thai` enum('Chua doc','Da doc') COLLATE utf8mb4_unicode_ci DEFAULT 'Chua doc',
  `ngay_tao` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Id_thong_bao`),
  KEY `Id_tai_khoan` (`Id_tai_khoan`),
  KEY `Id_don_thue` (`Id_don_thue`),
  CONSTRAINT `thong_bao_ibfk_1` FOREIGN KEY (`Id_tai_khoan`) REFERENCES `tai_khoan` (`id_tai_khoan`),
  CONSTRAINT `thong_bao_ibfk_2` FOREIGN KEY (`Id_don_thue`) REFERENCES `don_thue` (`Id_don_thue`)
) ENGINE=InnoDB AUTO_INCREMENT=238 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `thong_bao`
--

LOCK TABLES `thong_bao` WRITE;
/*!40000 ALTER TABLE `thong_bao` DISABLE KEYS */;
INSERT INTO `thong_bao` VALUES (1,1,1,'Đặt hàng thành công','Đơn thuê #1 đã được tạo thành công.','Dat hang thanh cong','User','Da doc','2026-06-01 17:51:49'),(2,1,1,'Có đơn hàng mới','Khách hàng vừa tạo đơn thuê #1.','Co don hang moi','Admin','Da doc','2026-06-01 17:51:49'),(3,2,2,'Đơn hàng đã xác nhận','Đơn thuê #2 đã được xác nhận.','Cap nhat don hang','User','Chua doc','2026-06-01 17:51:49'),(4,3,3,'Đơn hàng đang thuê','Thiết bị của đơn #3 đã được bàn giao.','Cap nhat don hang','User','Da doc','2026-06-01 17:51:49'),(5,4,4,'Nhắc lịch trả thiết bị','Đơn thuê #4 sẽ đến hạn trả trong 24 giờ tới.','Cap nhat don hang','User','Chua doc','2026-06-01 17:51:49'),(6,5,5,'Khiếu nại mới','Có khiếu nại mới từ khách hàng.','Khieu nai','Admin','Chua doc','2026-06-01 17:51:49'),(7,6,6,'Đơn hàng hoàn tất','Đơn thuê #6 đã hoàn tất.','Cap nhat don hang','User','Da doc','2026-06-01 17:51:49'),(8,7,7,'Có đơn hàng mới','Có đơn thuê mới cần xử lý.','Co don hang moi','Nhan vien','Da doc','2026-06-01 17:51:49'),(9,8,8,'Thanh toán thành công','Đơn thuê #8 đã được thanh toán.','Cap nhat don hang','User','Da doc','2026-06-01 17:51:49'),(10,9,9,'Đơn hàng quá hạn','Đơn thuê #9 đã quá hạn trả thiết bị.','Cap nhat don hang','User','Chua doc','2026-06-01 17:51:49'),(11,10,10,'Thông báo hệ thống','Chào mừng bạn đến với hệ thống thuê thiết bị.','He thong','User','Da doc','2026-06-01 17:51:49'),(12,2,2,'Có đơn hàng mới','Khách hàng vừa đặt đơn thuê #2.','Co don hang moi','Admin','Chua doc','2026-06-01 17:51:49'),(13,3,3,'Có đơn hàng mới','Khách hàng vừa đặt đơn thuê #3.','Co don hang moi','Admin','Chua doc','2026-06-01 17:51:49'),(14,4,4,'Có đơn hàng mới','Đơn thuê mới cần xác nhận.','Co don hang moi','Nhan vien','Chua doc','2026-06-01 17:51:49'),(15,5,5,'Bảo trì hệ thống','Máy chủ sẽ bảo trì lúc 22:00.','He thong','Admin','Chua doc','2026-06-01 17:51:49'),(16,6,13,'Đặt hàng thành công','Đơn thuê #13 đã được tạo thành công.','Dat hang thanh cong','User','Da doc','2026-06-03 22:04:26'),(17,1,13,'Có đơn hàng mới','Đơn thuê #13 vừa được tạo.','Co don hang moi','Admin','Da doc','2026-06-03 22:04:26'),(18,2,13,'Có đơn hàng mới','Đơn thuê #13 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-03 22:04:26'),(19,3,13,'Có đơn hàng mới','Đơn thuê #13 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-03 22:04:26'),(20,4,13,'Có đơn hàng mới','Đơn thuê #13 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-03 22:04:26'),(21,5,13,'Có đơn hàng mới','Đơn thuê #13 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-03 22:04:26'),(22,6,14,'Đặt hàng thành công','Đơn thuê #14 đã được tạo thành công.','Dat hang thanh cong','User','Da doc','2026-06-04 12:01:39'),(23,1,14,'Có đơn hàng mới','Đơn thuê #14 vừa được tạo.','Co don hang moi','Admin','Da doc','2026-06-04 12:01:39'),(24,2,14,'Có đơn hàng mới','Đơn thuê #14 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-04 12:01:39'),(25,3,14,'Có đơn hàng mới','Đơn thuê #14 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-04 12:01:39'),(26,4,14,'Có đơn hàng mới','Đơn thuê #14 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-04 12:01:39'),(27,5,14,'Có đơn hàng mới','Đơn thuê #14 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-04 12:01:39'),(28,6,14,'Hủy đơn hàng thành công','Bạn đã hủy đơn hàng #14 thành công.','Cap nhat don hang','User','Da doc','2026-06-04 12:29:07'),(29,1,14,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #14.','Cap nhat don hang','Admin','Da doc','2026-06-04 12:29:07'),(30,2,14,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #14.','Cap nhat don hang','Admin','Chua doc','2026-06-04 12:29:07'),(31,3,14,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #14.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-04 12:29:07'),(32,4,14,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #14.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-04 12:29:07'),(33,5,14,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #14.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-04 12:29:07'),(34,6,15,'Đặt hàng thành công','Đơn thuê #15 đã được tạo thành công.','Dat hang thanh cong','User','Da doc','2026-06-05 17:52:57'),(35,1,15,'Có đơn hàng mới','Đơn thuê #15 vừa được tạo.','Co don hang moi','Admin','Da doc','2026-06-05 17:52:57'),(36,2,15,'Có đơn hàng mới','Đơn thuê #15 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-05 17:52:57'),(37,3,15,'Có đơn hàng mới','Đơn thuê #15 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-05 17:52:57'),(38,4,15,'Có đơn hàng mới','Đơn thuê #15 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-05 17:52:57'),(39,5,15,'Có đơn hàng mới','Đơn thuê #15 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-05 17:52:57'),(46,6,39,'Đặt hàng thành công','Đơn thuê #39 đã được tạo thành công.','Dat hang thanh cong','User','Da doc','2026-06-13 23:45:22'),(47,1,39,'Có đơn hàng mới','Đơn thuê #39 vừa được tạo.','Co don hang moi','Admin','Da doc','2026-06-13 23:45:22'),(48,2,39,'Có đơn hàng mới','Đơn thuê #39 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-13 23:45:22'),(49,3,39,'Có đơn hàng mới','Đơn thuê #39 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-13 23:45:22'),(50,4,39,'Có đơn hàng mới','Đơn thuê #39 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-13 23:45:22'),(51,5,39,'Có đơn hàng mới','Đơn thuê #39 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-13 23:45:22'),(52,6,40,'Đặt hàng thành công','Đơn thuê #40 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-17 14:00:10'),(53,1,40,'Có đơn hàng mới','Đơn thuê #40 vừa được tạo.','Co don hang moi','Admin','Da doc','2026-06-17 14:00:10'),(54,2,40,'Có đơn hàng mới','Đơn thuê #40 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-17 14:00:10'),(55,3,40,'Có đơn hàng mới','Đơn thuê #40 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-17 14:00:10'),(56,4,40,'Có đơn hàng mới','Đơn thuê #40 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-17 14:00:10'),(57,5,40,'Có đơn hàng mới','Đơn thuê #40 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-17 14:00:10'),(58,6,40,'Xác nhận đơn thuê','Đơn thuê #40 đã được xác nhận.','Cap nhat don hang','User','Chua doc','2026-06-17 14:03:41'),(65,7,42,'Đặt hàng thành công','Đơn thuê #42 đã được tạo thành công.','Dat hang thanh cong','User','Da doc','2026-06-18 14:55:25'),(66,1,42,'Có đơn hàng mới','Đơn thuê #42 vừa được tạo.','Co don hang moi','Admin','Da doc','2026-06-18 14:55:25'),(67,2,42,'Có đơn hàng mới','Đơn thuê #42 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-18 14:55:25'),(68,3,42,'Có đơn hàng mới','Đơn thuê #42 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-18 14:55:25'),(69,4,42,'Có đơn hàng mới','Đơn thuê #42 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-18 14:55:25'),(70,5,42,'Có đơn hàng mới','Đơn thuê #42 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-18 14:55:25'),(71,6,13,'Hủy đơn hàng thành công','Bạn đã hủy đơn hàng #13 thành công.','Cap nhat don hang','User','Chua doc','2026-06-18 17:55:38'),(72,1,13,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #13.','Cap nhat don hang','Admin','Chua doc','2026-06-18 17:55:38'),(73,2,13,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #13.','Cap nhat don hang','Admin','Chua doc','2026-06-18 17:55:38'),(74,3,13,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #13.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-18 17:55:38'),(75,4,13,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #13.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-18 17:55:38'),(76,5,13,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #13.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-18 17:55:38'),(77,11,6,'Thanh toán thành công','Thanh toán đơn thuê #6 thành công.','Cap nhat don hang','User','Chua doc','2026-06-18 20:37:52'),(78,10,5,'Thanh toán thành công','Thanh toán đơn thuê #5 thành công.','Cap nhat don hang','User','Chua doc','2026-06-18 20:37:57'),(79,6,43,'Đặt hàng thành công','Đơn thuê #43 đã được tạo thành công.','Dat hang thanh cong','User','Da doc','2026-06-19 12:15:57'),(80,1,43,'Có đơn hàng mới','Đơn thuê #43 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-19 12:15:57'),(81,2,43,'Có đơn hàng mới','Đơn thuê #43 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-19 12:15:57'),(82,3,43,'Có đơn hàng mới','Đơn thuê #43 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 12:15:57'),(83,4,43,'Có đơn hàng mới','Đơn thuê #43 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 12:15:57'),(84,5,43,'Có đơn hàng mới','Đơn thuê #43 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 12:15:57'),(85,6,43,'Hủy đơn hàng thành công','Bạn đã hủy đơn hàng #43 thành công.','Cap nhat don hang','User','Chua doc','2026-06-19 12:32:26'),(86,1,43,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #43.','Cap nhat don hang','Admin','Chua doc','2026-06-19 12:32:26'),(87,2,43,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #43.','Cap nhat don hang','Admin','Chua doc','2026-06-19 12:32:26'),(88,3,43,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #43.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-19 12:32:26'),(89,4,43,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #43.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-19 12:32:26'),(90,5,43,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #43.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-19 12:32:26'),(91,6,44,'Đặt hàng thành công','Đơn thuê #44 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-19 12:32:40'),(92,1,44,'Có đơn hàng mới','Đơn thuê #44 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-19 12:32:40'),(93,2,44,'Có đơn hàng mới','Đơn thuê #44 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-19 12:32:40'),(94,3,44,'Có đơn hàng mới','Đơn thuê #44 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 12:32:40'),(95,4,44,'Có đơn hàng mới','Đơn thuê #44 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 12:32:40'),(96,5,44,'Có đơn hàng mới','Đơn thuê #44 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 12:32:40'),(97,6,44,'Xác nhận đơn thuê','Đơn thuê #44 đã được xác nhận.','Cap nhat don hang','User','Chua doc','2026-06-19 12:34:54'),(98,6,44,'Xác nhận đơn thuê','Đơn thuê #44 đã được xác nhận.','Cap nhat don hang','User','Chua doc','2026-06-19 12:35:00'),(99,6,45,'Đặt hàng thành công','Đơn thuê #45 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-19 12:36:25'),(100,1,45,'Có đơn hàng mới','Đơn thuê #45 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-19 12:36:25'),(101,2,45,'Có đơn hàng mới','Đơn thuê #45 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-19 12:36:25'),(102,3,45,'Có đơn hàng mới','Đơn thuê #45 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 12:36:25'),(103,4,45,'Có đơn hàng mới','Đơn thuê #45 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 12:36:25'),(104,5,45,'Có đơn hàng mới','Đơn thuê #45 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 12:36:25'),(105,6,45,'Xác nhận đơn thuê','Đơn thuê #45 đã được xác nhận.','Cap nhat don hang','User','Chua doc','2026-06-19 12:37:20'),(106,6,44,'Đơn VNPAY đã hết thời gian thanh toán','Đơn thuê #44 đã tự động hủy vì quá 15 phút thanh toán VNPAY.','Cap nhat don hang','User','Chua doc','2026-06-19 13:10:30'),(107,6,46,'Đặt hàng thành công','Đơn thuê #46 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-19 13:18:39'),(108,1,46,'Có đơn hàng mới','Đơn thuê #46 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-19 13:18:39'),(109,2,46,'Có đơn hàng mới','Đơn thuê #46 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-19 13:18:39'),(110,3,46,'Có đơn hàng mới','Đơn thuê #46 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 13:18:39'),(111,4,46,'Có đơn hàng mới','Đơn thuê #46 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 13:18:39'),(112,5,46,'Có đơn hàng mới','Đơn thuê #46 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 13:18:39'),(113,6,46,'Xác nhận đơn thuê','Đơn thuê #46 đã được xác nhận.','Cap nhat don hang','User','Chua doc','2026-06-19 13:19:06'),(114,6,47,'Đặt hàng thành công','Đơn thuê #47 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-19 13:21:56'),(115,1,47,'Có đơn hàng mới','Đơn thuê #47 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-19 13:21:56'),(116,2,47,'Có đơn hàng mới','Đơn thuê #47 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-19 13:21:56'),(117,3,47,'Có đơn hàng mới','Đơn thuê #47 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 13:21:56'),(118,4,47,'Có đơn hàng mới','Đơn thuê #47 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 13:21:56'),(119,5,47,'Có đơn hàng mới','Đơn thuê #47 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 13:21:56'),(120,6,47,'Xác nhận đơn thuê','Đơn thuê #47 đã được xác nhận.','Cap nhat don hang','User','Chua doc','2026-06-19 13:22:26'),(121,6,48,'Đặt hàng thành công','Đơn thuê #48 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-19 14:59:14'),(122,1,48,'Có đơn hàng mới','Đơn thuê #48 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-19 14:59:14'),(123,2,48,'Có đơn hàng mới','Đơn thuê #48 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-19 14:59:14'),(124,3,48,'Có đơn hàng mới','Đơn thuê #48 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 14:59:14'),(125,4,48,'Có đơn hàng mới','Đơn thuê #48 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 14:59:14'),(126,5,48,'Có đơn hàng mới','Đơn thuê #48 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-19 14:59:14'),(127,6,48,'Xác nhận đơn thuê','Đơn thuê #48 đã được xác nhận.','Cap nhat don hang','User','Chua doc','2026-06-19 15:00:58'),(128,6,48,'Đơn thuê hoàn tất','Đơn thuê #48 đã hoàn tất.','Cap nhat don hang','User','Chua doc','2026-06-19 15:43:24'),(129,6,45,'Đơn thuê hoàn tất','Đơn thuê #45 đã hoàn tất.','Cap nhat don hang','User','Chua doc','2026-06-19 15:43:39'),(130,6,49,'Đặt hàng thành công','Đơn thuê #49 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-20 01:34:59'),(131,1,49,'Có đơn hàng mới','Đơn thuê #49 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 01:34:59'),(132,2,49,'Có đơn hàng mới','Đơn thuê #49 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 01:34:59'),(133,3,49,'Có đơn hàng mới','Đơn thuê #49 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 01:34:59'),(134,4,49,'Có đơn hàng mới','Đơn thuê #49 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 01:34:59'),(135,5,49,'Có đơn hàng mới','Đơn thuê #49 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 01:34:59'),(136,6,49,'Xác nhận đơn thuê','Đơn thuê #49 đã được xác nhận.','Cap nhat don hang','User','Chua doc','2026-06-20 01:36:26'),(137,6,49,'Hủy đơn hàng thành công','Bạn đã hủy đơn hàng #49 thành công.','Cap nhat don hang','User','Chua doc','2026-06-20 01:37:09'),(138,1,49,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #49.','Cap nhat don hang','Admin','Chua doc','2026-06-20 01:37:09'),(139,2,49,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #49.','Cap nhat don hang','Admin','Chua doc','2026-06-20 01:37:09'),(140,3,49,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #49.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 01:37:09'),(141,4,49,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #49.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 01:37:09'),(142,5,49,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #49.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 01:37:09'),(143,6,50,'Đặt hàng thành công','Đơn thuê #50 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-20 01:37:51'),(144,1,50,'Có đơn hàng mới','Đơn thuê #50 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 01:37:51'),(145,2,50,'Có đơn hàng mới','Đơn thuê #50 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 01:37:51'),(146,3,50,'Có đơn hàng mới','Đơn thuê #50 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 01:37:51'),(147,4,50,'Có đơn hàng mới','Đơn thuê #50 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 01:37:51'),(148,5,50,'Có đơn hàng mới','Đơn thuê #50 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 01:37:51'),(149,6,50,'Hủy đơn hàng thành công','Bạn đã hủy đơn hàng #50 thành công.','Cap nhat don hang','User','Chua doc','2026-06-20 01:38:11'),(150,1,50,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #50.','Cap nhat don hang','Admin','Chua doc','2026-06-20 01:38:11'),(151,2,50,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #50.','Cap nhat don hang','Admin','Chua doc','2026-06-20 01:38:11'),(152,3,50,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #50.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 01:38:11'),(153,4,50,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #50.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 01:38:11'),(154,5,50,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #50.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 01:38:11'),(155,6,51,'Đặt hàng thành công','Đơn thuê #51 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-20 01:39:09'),(156,1,51,'Có đơn hàng mới','Đơn thuê #51 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 01:39:09'),(157,2,51,'Có đơn hàng mới','Đơn thuê #51 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 01:39:09'),(158,3,51,'Có đơn hàng mới','Đơn thuê #51 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 01:39:09'),(159,4,51,'Có đơn hàng mới','Đơn thuê #51 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 01:39:09'),(160,5,51,'Có đơn hàng mới','Đơn thuê #51 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 01:39:09'),(161,6,51,'Hủy đơn hàng thành công','Bạn đã hủy đơn hàng #51 thành công.','Cap nhat don hang','User','Chua doc','2026-06-20 01:39:23'),(162,1,51,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #51.','Cap nhat don hang','Admin','Chua doc','2026-06-20 01:39:23'),(163,2,51,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #51.','Cap nhat don hang','Admin','Chua doc','2026-06-20 01:39:23'),(164,3,51,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #51.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 01:39:23'),(165,4,51,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #51.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 01:39:23'),(166,5,51,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #51.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 01:39:23'),(167,7,52,'Đặt hàng thành công','Đơn thuê #52 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-20 01:41:39'),(168,1,52,'Có đơn hàng mới','Đơn thuê #52 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 01:41:39'),(169,2,52,'Có đơn hàng mới','Đơn thuê #52 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 01:41:39'),(170,3,52,'Có đơn hàng mới','Đơn thuê #52 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 01:41:39'),(171,4,52,'Có đơn hàng mới','Đơn thuê #52 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 01:41:39'),(172,5,52,'Có đơn hàng mới','Đơn thuê #52 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 01:41:39'),(173,6,55,'Đặt hàng thành công','Đơn thuê #55 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-20 02:29:02'),(174,1,55,'Có đơn hàng mới','Đơn thuê #55 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 02:29:02'),(175,2,55,'Có đơn hàng mới','Đơn thuê #55 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 02:29:02'),(176,3,55,'Có đơn hàng mới','Đơn thuê #55 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 02:29:02'),(177,4,55,'Có đơn hàng mới','Đơn thuê #55 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 02:29:02'),(178,5,55,'Có đơn hàng mới','Đơn thuê #55 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 02:29:02'),(179,6,55,'Hủy đơn hàng thành công','Bạn đã hủy đơn hàng #55 thành công.','Cap nhat don hang','User','Chua doc','2026-06-20 02:30:37'),(180,1,55,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #55.','Cap nhat don hang','Admin','Chua doc','2026-06-20 02:30:37'),(181,2,55,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #55.','Cap nhat don hang','Admin','Chua doc','2026-06-20 02:30:37'),(182,3,55,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #55.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 02:30:37'),(183,4,55,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #55.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 02:30:37'),(184,5,55,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #55.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 02:30:37'),(185,6,56,'Đặt hàng thành công','Đơn thuê #56 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-20 02:31:01'),(186,1,56,'Có đơn hàng mới','Đơn thuê #56 vừa được tạo.','Co don hang moi','Admin','Da doc','2026-06-20 02:31:01'),(187,2,56,'Có đơn hàng mới','Đơn thuê #56 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 02:31:01'),(188,3,56,'Có đơn hàng mới','Đơn thuê #56 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 02:31:01'),(189,4,56,'Có đơn hàng mới','Đơn thuê #56 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 02:31:01'),(190,5,56,'Có đơn hàng mới','Đơn thuê #56 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 02:31:01'),(191,6,57,'Đặt hàng thành công','Đơn thuê #57 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-20 02:41:07'),(192,1,57,'Có đơn hàng mới','Đơn thuê #57 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 02:41:07'),(193,2,57,'Có đơn hàng mới','Đơn thuê #57 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 02:41:07'),(194,3,57,'Có đơn hàng mới','Đơn thuê #57 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 02:41:07'),(195,4,57,'Có đơn hàng mới','Đơn thuê #57 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 02:41:07'),(196,5,57,'Có đơn hàng mới','Đơn thuê #57 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 02:41:07'),(197,6,57,'Hủy đơn hàng thành công','Bạn đã hủy đơn hàng #57 thành công.','Cap nhat don hang','User','Chua doc','2026-06-20 02:47:56'),(198,1,57,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #57.','Cap nhat don hang','Admin','Da doc','2026-06-20 02:47:56'),(199,2,57,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #57.','Cap nhat don hang','Admin','Chua doc','2026-06-20 02:47:56'),(200,3,57,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #57.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 02:47:56'),(201,4,57,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #57.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 02:47:56'),(202,5,57,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #57.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 02:47:56'),(203,6,56,'Hủy đơn hàng thành công','Bạn đã hủy đơn hàng #56 thành công.','Cap nhat don hang','User','Chua doc','2026-06-20 02:48:12'),(204,1,56,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #56.','Cap nhat don hang','Admin','Da doc','2026-06-20 02:48:12'),(205,2,56,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #56.','Cap nhat don hang','Admin','Chua doc','2026-06-20 02:48:12'),(206,3,56,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #56.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 02:48:12'),(207,4,56,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #56.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 02:48:12'),(208,5,56,'Khách hàng hủy đơn hàng','Khách hàng đã hủy đơn hàng #56.','Cap nhat don hang','Nhan vien','Chua doc','2026-06-20 02:48:12'),(209,6,58,'Đặt hàng thành công','Đơn thuê #58 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-20 02:48:30'),(210,1,58,'Có đơn hàng mới','Đơn thuê #58 vừa được tạo.','Co don hang moi','Admin','Da doc','2026-06-20 02:48:30'),(211,2,58,'Có đơn hàng mới','Đơn thuê #58 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 02:48:30'),(212,3,58,'Có đơn hàng mới','Đơn thuê #58 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 02:48:30'),(213,4,58,'Có đơn hàng mới','Đơn thuê #58 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 02:48:30'),(214,5,58,'Có đơn hàng mới','Đơn thuê #58 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 02:48:30'),(215,6,58,'Xác nhận đơn thuê','Đơn thuê #58 đã được xác nhận.','Cap nhat don hang','User','Chua doc','2026-06-20 02:48:54'),(216,6,59,'Đặt hàng thành công','Đơn thuê #59 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-20 09:57:18'),(217,1,59,'Có đơn hàng mới','Đơn thuê #59 vừa được tạo.','Co don hang moi','Admin','Da doc','2026-06-20 09:57:18'),(218,2,59,'Có đơn hàng mới','Đơn thuê #59 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 09:57:18'),(219,3,59,'Có đơn hàng mới','Đơn thuê #59 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 09:57:18'),(220,4,59,'Có đơn hàng mới','Đơn thuê #59 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 09:57:18'),(221,5,59,'Có đơn hàng mới','Đơn thuê #59 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 09:57:18'),(222,6,59,'Xác nhận đơn thuê','Đơn thuê #59 đã được xác nhận.','Cap nhat don hang','User','Chua doc','2026-06-20 09:57:57'),(223,6,60,'Đặt hàng thành công','Đơn thuê #60 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-20 10:22:29'),(224,1,60,'Có đơn hàng mới','Đơn thuê #60 vừa được tạo.','Co don hang moi','Admin','Da doc','2026-06-20 10:22:29'),(225,2,60,'Có đơn hàng mới','Đơn thuê #60 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 10:22:29'),(226,3,60,'Có đơn hàng mới','Đơn thuê #60 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 10:22:29'),(227,4,60,'Có đơn hàng mới','Đơn thuê #60 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 10:22:29'),(228,5,60,'Có đơn hàng mới','Đơn thuê #60 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 10:22:29'),(229,6,60,'Đơn VNPAY đã hết thời gian thanh toán','Đơn thuê #60 đã tự động hủy vì quá 15 phút thanh toán VNPAY.','Cap nhat don hang','User','Chua doc','2026-06-20 15:24:17'),(230,6,61,'Đặt hàng thành công','Đơn thuê #61 đã được tạo thành công.','Dat hang thanh cong','User','Chua doc','2026-06-20 19:28:14'),(231,1,61,'Có đơn hàng mới','Đơn thuê #61 vừa được tạo.','Co don hang moi','Admin','Da doc','2026-06-20 19:28:14'),(232,2,61,'Có đơn hàng mới','Đơn thuê #61 vừa được tạo.','Co don hang moi','Admin','Chua doc','2026-06-20 19:28:14'),(233,3,61,'Có đơn hàng mới','Đơn thuê #61 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 19:28:14'),(234,4,61,'Có đơn hàng mới','Đơn thuê #61 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 19:28:14'),(235,5,61,'Có đơn hàng mới','Đơn thuê #61 vừa được tạo.','Co don hang moi','Nhan vien','Chua doc','2026-06-20 19:28:14'),(236,6,61,'Xác nhận đơn thuê','Đơn thuê #61 đã được xác nhận.','Cap nhat don hang','User','Chua doc','2026-06-20 19:29:20'),(237,6,61,'Đơn thuê hoàn tất','Đơn thuê #61 đã hoàn tất.','Cap nhat don hang','User','Chua doc','2026-06-20 19:31:42');
/*!40000 ALTER TABLE `thong_bao` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tin_nhan_chat`
--

DROP TABLE IF EXISTS `tin_nhan_chat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tin_nhan_chat` (
  `id_tin_nhan` int NOT NULL AUTO_INCREMENT,
  `id_cuoc_tro_chuyen` int NOT NULL,
  `loai_nguoi_gui` enum('CUSTOMER','STAFF') NOT NULL,
  `id_nguoi_gui` int DEFAULT NULL,
  `noi_dung` text NOT NULL,
  `loai_tin_nhan` enum('TEXT','IMAGE','FILE') DEFAULT 'TEXT',
  `da_doc` tinyint(1) DEFAULT '0',
  `ngay_tao` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_tin_nhan`),
  KEY `ix_tin_nhan_chat_cuoc_tro_chuyen` (`id_cuoc_tro_chuyen`),
  KEY `ix_tin_nhan_chat_created_at` (`ngay_tao`),
  CONSTRAINT `tin_nhan_chat_ibfk_1` FOREIGN KEY (`id_cuoc_tro_chuyen`) REFERENCES `cuoc_tro_chuyen` (`id_cuoc_tro_chuyen`)
) ENGINE=InnoDB AUTO_INCREMENT=81 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tin_nhan_chat`
--

LOCK TABLES `tin_nhan_chat` WRITE;
/*!40000 ALTER TABLE `tin_nhan_chat` DISABLE KEYS */;
INSERT INTO `tin_nhan_chat` VALUES (2,1,'CUSTOMER',1,'hello guy','TEXT',1,'2026-06-04 17:29:50'),(3,1,'STAFF',1,'xin chào tôi có thể hỗ trợ gì cho bạn','TEXT',1,'2026-06-04 17:30:20'),(5,1,'CUSTOMER',1,'tôi muốn tư vấn máy ảnh để chụp vintage','TEXT',1,'2026-06-04 17:37:42'),(6,2,'CUSTOMER',1,'tôi muốn tư vấn máy ảnh chụp vintage','TEXT',1,'2026-06-04 17:39:35'),(8,2,'CUSTOMER',1,'chat với nhân viên','TEXT',1,'2026-06-04 17:40:04'),(13,2,'CUSTOMER',1,'tôi muốn tư vấn máy ảnh','TEXT',1,'2026-06-05 17:54:15'),(15,2,'CUSTOMER',1,'tôi muốn tư vấn','TEXT',1,'2026-06-05 19:58:44'),(18,2,'CUSTOMER',1,'hello','TEXT',1,'2026-06-06 00:14:07'),(20,2,'CUSTOMER',1,'AI đâu','TEXT',1,'2026-06-06 00:14:14'),(23,2,'CUSTOMER',1,'hello','TEXT',1,'2026-06-08 00:07:08'),(28,1,'CUSTOMER',1,'hello','TEXT',1,'2026-06-13 03:51:51'),(29,1,'STAFF',1,'uk','TEXT',1,'2026-06-13 03:52:30'),(36,2,'STAFF',1,'Nhân viên đã tiếp nhận cuộc trò chuyện của bạn. Tôi sẽ hỗ trợ anh/chị ngay bây giờ.','TEXT',1,'2026-06-13 21:25:16'),(37,3,'STAFF',1,'a','TEXT',0,'2026-06-13 21:25:26'),(39,1,'CUSTOMER',1,'hello','TEXT',1,'2026-06-13 21:52:15'),(41,1,'CUSTOMER',1,'èweewf','TEXT',1,'2026-06-13 21:52:51'),(42,1,'CUSTOMER',1,'ưefefwf','TEXT',1,'2026-06-13 21:52:52'),(43,1,'CUSTOMER',1,'wefwefwef','TEXT',1,'2026-06-13 21:52:53'),(45,4,'CUSTOMER',2,'hi','TEXT',1,'2026-06-13 21:53:03'),(47,1,'CUSTOMER',1,'hello','TEXT',1,'2026-06-15 18:43:25'),(48,1,'CUSTOMER',1,'xin chào','TEXT',1,'2026-06-15 18:43:29'),(49,1,'CUSTOMER',1,'tôi muốn tư vấn máy ảnh','TEXT',1,'2026-06-15 18:43:35'),(52,1,'CUSTOMER',1,'aádsad','TEXT',1,'2026-06-17 00:02:25'),(53,1,'STAFF',1,'hello','TEXT',1,'2026-06-17 00:02:42'),(59,1,'CUSTOMER',1,'hello','TEXT',1,'2026-06-18 13:32:02'),(60,1,'CUSTOMER',1,'a nho seo oo','TEXT',1,'2026-06-18 13:32:06'),(61,1,'STAFF',1,'halo halo\\','TEXT',0,'2026-06-18 13:32:22'),(62,2,'CUSTOMER',1,'hello','TEXT',1,'2026-06-18 13:32:39'),(64,2,'CUSTOMER',1,'hello','TEXT',1,'2026-06-18 13:32:49'),(65,5,'CUSTOMER',1,'helo','TEXT',1,'2026-06-18 13:33:33'),(67,5,'CUSTOMER',1,'a nho seo ô','TEXT',1,'2026-06-18 13:33:41'),(70,5,'CUSTOMER',1,'2','TEXT',1,'2026-06-18 13:34:06'),(71,2,'STAFF',1,'a','TEXT',0,'2026-06-18 15:00:49'),(72,5,'STAFF',1,'hello','TEXT',1,'2026-06-18 15:01:15'),(75,5,'STAFF',1,'a nho seooo','TEXT',1,'2026-06-18 20:32:12'),(76,5,'CUSTOMER',1,'helo','TEXT',1,'2026-06-18 20:32:52'),(77,5,'CUSTOMER',1,'goooo','TEXT',1,'2026-06-19 01:00:49'),(78,5,'CUSTOMER',1,'a','TEXT',1,'2026-06-19 01:00:55'),(79,5,'STAFF',1,'hello','TEXT',1,'2026-06-19 01:01:22'),(80,5,'CUSTOMER',1,'a nho seoo','TEXT',1,'2026-06-19 13:56:03');
/*!40000 ALTER TABLE `tin_nhan_chat` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `vw_lich_su_thue`
--

DROP TABLE IF EXISTS `vw_lich_su_thue`;
/*!50001 DROP VIEW IF EXISTS `vw_lich_su_thue`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_lich_su_thue` AS SELECT 
 1 AS `Id_don_thue`,
 1 AS `ho_ten`,
 1 AS `ten_thiet_bi`,
 1 AS `ngay_nhan`,
 1 AS `ngay_tra`,
 1 AS `so_luong`,
 1 AS `gia_thue`*/;
SET character_set_client = @saved_cs_client;

--
-- Dumping events for database 'do_an_tot_nghiep'
--

--
-- Dumping routines for database 'do_an_tot_nghiep'
--
/*!50003 DROP FUNCTION IF EXISTS `fn_format_tien` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_format_tien`(
    p_tien DECIMAL(12,2)
) RETURNS varchar(50) CHARSET utf8mb4
    DETERMINISTIC
BEGIN

    RETURN CONCAT(FORMAT(p_tien,0), ' VNĐ');

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP FUNCTION IF EXISTS `fn_kiem_tra_qua_han` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_kiem_tra_qua_han`(
    p_id_don_thue INT
) RETURNS varchar(50) CHARSET utf8mb4
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

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP FUNCTION IF EXISTS `fn_so_ngay_thue` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_so_ngay_thue`(
    p_ngay_nhan DATETIME,
    p_ngay_tra DATETIME
) RETURNS int
    DETERMINISTIC
BEGIN

    RETURN DATEDIFF(p_ngay_tra, p_ngay_nhan);

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP FUNCTION IF EXISTS `fn_so_tb_dang_thue` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_so_tb_dang_thue`() RETURNS int
    DETERMINISTIC
BEGIN

    DECLARE v_count INT;

    SELECT COUNT(*)
    INTO v_count
    FROM THIET_BI
    WHERE tinh_trang = 'Dang thue';

    RETURN v_count;

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP FUNCTION IF EXISTS `fn_ten_danh_muc` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_ten_danh_muc`(
    p_id_danh_muc INT
) RETURNS varchar(100) CHARSET utf8mb4
    DETERMINISTIC
BEGIN

    DECLARE v_ten VARCHAR(100);

    SELECT ten_danh_muc
    INTO v_ten
    FROM DANH_MUC
    WHERE Id_danh_muc = p_id_danh_muc;

    RETURN v_ten;

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP FUNCTION IF EXISTS `fn_tinh_tong_tien` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_tinh_tong_tien`(
    p_id_don_thue INT
) RETURNS decimal(12,2)
    DETERMINISTIC
BEGIN

    DECLARE v_tong_tien DECIMAL(12,2);

    SELECT 
        SUM(gia_thue * so_luong)
    INTO v_tong_tien
    FROM CHI_TIET_DON_THUE
    WHERE id_don_thue = p_id_don_thue;

    RETURN IFNULL(v_tong_tien, 0);

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP FUNCTION IF EXISTS `fn_tong_doanh_thu` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_tong_doanh_thu`() RETURNS decimal(12,2)
    DETERMINISTIC
BEGIN

    DECLARE v_doanh_thu DECIMAL(12,2);

    SELECT SUM(tong_tien)
    INTO v_doanh_thu
    FROM DON_THUE;

    RETURN IFNULL(v_doanh_thu,0);

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_tao_don_thue` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_tao_don_thue`(
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

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_them_chi_tiet_thue` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_them_chi_tiet_thue`(
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

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_tim_thiet_bi` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_tim_thiet_bi`(
    IN p_tu_khoa VARCHAR(100)
)
BEGIN

    SELECT *
    FROM THIET_BI
    WHERE ten_thiet_bi LIKE CONCAT('%', p_tu_khoa, '%')
       OR mo_ta LIKE CONCAT('%', p_tu_khoa, '%');

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Final view structure for view `vw_lich_su_thue`
--

/*!50001 DROP VIEW IF EXISTS `vw_lich_su_thue`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_lich_su_thue` AS select `dt`.`Id_don_thue` AS `Id_don_thue`,`kh`.`ho_ten` AS `ho_ten`,`tb`.`ten_thiet_bi` AS `ten_thiet_bi`,`ctdt`.`ngay_nhan` AS `ngay_nhan`,`ctdt`.`ngay_tra` AS `ngay_tra`,`ctdt`.`so_luong` AS `so_luong`,`ctdt`.`gia_thue` AS `gia_thue` from (((`don_thue` `dt` join `khach_hang` `kh` on((`dt`.`Id_khach_hang` = `kh`.`Id_khach_hang`))) join `chi_tiet_don_thue` `ctdt` on((`dt`.`Id_don_thue` = `ctdt`.`id_don_thue`))) join `thiet_bi` `tb` on((`ctdt`.`id_thiet_bi` = `tb`.`Id_thiet_bi`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-21 14:06:42
