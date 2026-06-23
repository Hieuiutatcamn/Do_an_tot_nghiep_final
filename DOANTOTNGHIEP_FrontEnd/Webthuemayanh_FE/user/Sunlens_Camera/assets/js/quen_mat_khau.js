(function () {
    'use strict';

    const API_BASE_URL = window.SUNLENS_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
    const THONG_BAO_THANH_CONG = 'Vui lòng kiểm tra email để đặt lại mật khẩu.';
    const THONG_BAO_EMAIL_KHONG_TON_TAI = 'Email không tồn tại trong hệ thống.';
    const THONG_BAO_LOI_SERVER = 'Không thể gửi yêu cầu đặt lại mật khẩu.';

    function hienThiThongBaoQuenMatKhau(noiDung, loai) {
        const messageEl = document.getElementById('forgotPasswordMessage');
        if (!messageEl) return;

        messageEl.textContent = noiDung || '';
        messageEl.className = `mt-3 alert alert-${loai === 'success' ? 'success' : 'danger'}`;
        if (!noiDung) {
            messageEl.classList.add('d-none');
            return;
        }
        messageEl.classList.remove('d-none');
    }

    function kiemTraEmailHopLe(email) {
        const emailDaTrim = (email || '').trim();
        if (!emailDaTrim) {
            return 'Vui lòng nhập email.';
        }

        const mauEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!mauEmail.test(emailDaTrim)) {
            return 'Email không đúng định dạng.';
        }

        return '';
    }

    async function guiYeuCauDatLaiMatKhau(email) {
        const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email }),
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error(THONG_BAO_EMAIL_KHONG_TON_TAI);
            }
            throw new Error(data.detail || THONG_BAO_LOI_SERVER);
        }
        return data;
    }

    function capNhatTrangThaiNutDangGui(button, dangGui) {
        if (!button) return;

        if (!button.dataset.originalText) {
            button.dataset.originalText = button.innerHTML;
        }

        button.disabled = dangGui;
        button.innerHTML = dangGui
            ? '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Đang gửi...'
            : button.dataset.originalText;
    }

    async function xuLyQuenMatKhau(event) {
        event.preventDefault();

        const form = event.currentTarget;
        const emailInput = document.getElementById('quenMatKhauEmail');
        const submitButton = document.getElementById('forgotPasswordSubmitButton');
        const email = (emailInput?.value || '').trim();

        hienThiThongBaoQuenMatKhau('', 'danger');

        const loiEmail = kiemTraEmailHopLe(email);
        if (loiEmail) {
            hienThiThongBaoQuenMatKhau(loiEmail, 'danger');
            emailInput?.focus();
            return;
        }

        capNhatTrangThaiNutDangGui(submitButton, true);

        try {
            await guiYeuCauDatLaiMatKhau(email);
            form?.reset();
            hienThiThongBaoQuenMatKhau(THONG_BAO_THANH_CONG, 'success');
        } catch (error) {
            hienThiThongBaoQuenMatKhau(
                error instanceof Error ? error.message : THONG_BAO_LOI_SERVER,
                'danger',
            );
        } finally {
            capNhatTrangThaiNutDangGui(submitButton, false);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        const form = document.getElementById('forgotPasswordForm');
        if (!form) return;

        form.addEventListener('submit', xuLyQuenMatKhau);
    });
})();
