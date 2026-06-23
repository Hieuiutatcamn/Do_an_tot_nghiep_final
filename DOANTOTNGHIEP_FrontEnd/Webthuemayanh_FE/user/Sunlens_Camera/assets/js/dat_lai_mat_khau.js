(function () {
    'use strict';

    const API_BASE_URL = window.SUNLENS_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
    const THONG_BAO_TOKEN_KHONG_HOP_LE = 'Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.';

    function hienThiThongBaoDatLaiMatKhau(noiDung, loai) {
        const messageEl = document.getElementById('resetPasswordMessage');
        if (!messageEl) return;

        messageEl.textContent = noiDung || '';
        messageEl.className = `mt-3 alert alert-${loai === 'success' ? 'success' : 'danger'}`;
        if (!noiDung) {
            messageEl.classList.add('d-none');
            return;
        }
        messageEl.classList.remove('d-none');
    }

    function layTokenDatLaiMatKhau() {
        const params = new URLSearchParams(window.location.search);
        return (params.get('token') || '').trim();
    }

    function capNhatTrangThaiNut(button, dangXuLy) {
        if (!button) return;

        if (!button.dataset.originalText) {
            button.dataset.originalText = button.innerHTML;
        }

        button.disabled = dangXuLy;
        button.innerHTML = dangXuLy
            ? '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Đang cập nhật...'
            : button.dataset.originalText;
    }

    function kiemTraDuLieuDatLaiMatKhau(token, matKhauMoi, xacNhanMatKhau) {
        if (!token) {
            return THONG_BAO_TOKEN_KHONG_HOP_LE;
        }
        if (!matKhauMoi.trim()) {
            return 'Vui lòng nhập mật khẩu mới.';
        }
        if (matKhauMoi.length < 6) {
            return 'Mật khẩu mới phải có ít nhất 6 ký tự.';
        }
        if (!xacNhanMatKhau.trim()) {
            return 'Vui lòng nhập lại mật khẩu.';
        }
        if (matKhauMoi !== xacNhanMatKhau) {
            return 'Mật khẩu xác nhận không khớp.';
        }
        return '';
    }

    async function guiYeuCauCapNhatMatKhau(token, matKhauMoi) {
        const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token,
                mat_khau_moi: matKhauMoi,
            }),
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.detail || 'Không thể đặt lại mật khẩu.');
        }
        return data;
    }

    async function xuLyDatLaiMatKhau(event) {
        event.preventDefault();

        const submitButton = document.getElementById('resetPasswordSubmitButton');
        const matKhauMoiInput = document.getElementById('matKhauMoi');
        const xacNhanMatKhauInput = document.getElementById('xacNhanMatKhauMoi');
        const token = layTokenDatLaiMatKhau();
        const matKhauMoi = matKhauMoiInput?.value || '';
        const xacNhanMatKhau = xacNhanMatKhauInput?.value || '';

        hienThiThongBaoDatLaiMatKhau('', 'danger');

        const loi = kiemTraDuLieuDatLaiMatKhau(token, matKhauMoi, xacNhanMatKhau);
        if (loi) {
            hienThiThongBaoDatLaiMatKhau(loi, 'danger');
            if (!token) return;
            if (!matKhauMoi.trim()) {
                matKhauMoiInput?.focus();
                return;
            }
            xacNhanMatKhauInput?.focus();
            return;
        }

        capNhatTrangThaiNut(submitButton, true);

        try {
            const data = await guiYeuCauCapNhatMatKhau(token, matKhauMoi);
            hienThiThongBaoDatLaiMatKhau(
                data.message || 'Đặt lại mật khẩu thành công. Đang chuyển về trang đăng nhập...',
                'success',
            );
            window.setTimeout(() => {
                window.location.href = 'dang_nhap.html';
            }, 2500);
        } catch (error) {
            hienThiThongBaoDatLaiMatKhau(
                error instanceof Error ? error.message : 'Không thể đặt lại mật khẩu.',
                'danger',
            );
        } finally {
            capNhatTrangThaiNut(submitButton, false);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        const form = document.getElementById('resetPasswordForm');
        if (!form) return;

        if (!layTokenDatLaiMatKhau()) {
            hienThiThongBaoDatLaiMatKhau(THONG_BAO_TOKEN_KHONG_HOP_LE, 'danger');
        }

        form.addEventListener('submit', xuLyDatLaiMatKhau);
    });
})();
