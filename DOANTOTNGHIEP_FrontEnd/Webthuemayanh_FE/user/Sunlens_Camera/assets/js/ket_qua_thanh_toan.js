(function () {
    'use strict';

    const API_ORIGIN = (window.SUNLENS_API_ORIGIN || 'http://127.0.0.1:8000').replace(/\/+$/, '');
    const API_URL = `${API_ORIGIN}/api/v1/thanh-toan/vnpay-return`;

    function byId(id) {
        return document.getElementById(id);
    }

    function layThamSoThanhToan() {
        return new URLSearchParams(window.location.search);
    }

    function dinhDangTien(value) {
        const amount = Number(value || 0);
        return Number.isFinite(amount)
            ? amount.toLocaleString('vi-VN', { style: 'currency', currency: 'VND' })
            : '-';
    }

    function dinhDangNgayGio(value) {
        if (!value) return '-';
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? '-' : date.toLocaleString('vi-VN');
    }

    function datNoiDung(id, value) {
        const element = byId(id);
        if (element) element.textContent = value || '-';
    }

    function hienThiTrangThai(type, title, message) {
        const icon = byId('payment-result-icon');
        if (icon) {
            icon.className = `payment-result-icon ${type}`;
            icon.innerHTML = type === 'success'
                ? '<i class="bi bi-check-circle"></i>'
                : '<i class="bi bi-x-circle"></i>';
        }
        datNoiDung('payment-result-title', title);
        datNoiDung('payment-result-message', message);
    }

    function cho(milliseconds) {
        return new Promise(function (resolve) {
            window.setTimeout(resolve, milliseconds);
        });
    }

    async function layKetQuaDaXacThuc(params) {
        const response = await fetch(`${API_URL}?${params.toString()}`, {
            method: 'GET',
            headers: { Accept: 'application/json' },
        });
        const data = await response.json().catch(function () {
            return {};
        });
        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Không thể xác thực kết quả thanh toán.');
        }
        return data;
    }

    async function hienThiKetQuaThanhToan() {
        const params = layThamSoThanhToan();
        const details = byId('payment-result-details');

        if (!params.has('vnp_SecureHash')) {
            hienThiTrangThai(
                'error',
                'Thiếu thông tin thanh toán',
                'Trang kết quả không nhận được dữ liệu xác thực từ VNPAY.'
            );
            return;
        }

        try {
            let data = await layKetQuaDaXacThuc(params);
            for (let attempt = 0; attempt < 4 && data.thanh_cong && !data.da_cap_nhat_he_thong; attempt += 1) {
                datNoiDung('payment-result-message', 'Thanh toán thành công, đang chờ VNPAY đồng bộ trạng thái đơn thuê...');
                await cho(1500);
                data = await layKetQuaDaXacThuc(params);
            }

            if (details) details.classList.remove('d-none');
            datNoiDung(
                'payment-order-id',
                data.id_don_thue ? `DH${String(data.id_don_thue).padStart(4, '0')}` : '-'
            );
            datNoiDung('payment-amount', dinhDangTien(data.so_tien));
            datNoiDung('payment-transaction-id', data.ma_giao_dich || '-');
            datNoiDung('payment-date', dinhDangNgayGio(data.ngay_thanh_toan));
            datNoiDung(
                'payment-system-status',
                data.da_cap_nhat_he_thong ? 'Đã cập nhật đơn thuê' : 'Đang chờ VNPAY đồng bộ IPN'
            );

            if (data.thanh_cong && data.chu_ky_hop_le) {
                hienThiTrangThai('success', 'Thanh toán thành công', data.thong_bao);
                sessionStorage.removeItem('sunlens_vnpay_don_thue_dang_thanh_toan');
                return;
            }
            hienThiTrangThai('error', 'Thanh toán thất bại', data.thong_bao);
        } catch (error) {
            console.error('Không thể kiểm tra kết quả VNPAY:', error);
            hienThiTrangThai(
                'error',
                'Không thể xác thực giao dịch',
                error.message || 'Không kết nối được backend FastAPI.'
            );
        }
    }

    window.layThamSoThanhToan = layThamSoThanhToan;
    window.hienThiKetQuaThanhToan = hienThiKetQuaThanhToan;
    document.addEventListener('DOMContentLoaded', hienThiKetQuaThanhToan);
})();
