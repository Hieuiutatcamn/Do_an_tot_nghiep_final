(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        const form = document.getElementById('adminLoginForm');
        if (!form) return;

        const errorEl = document.getElementById('loginError');
        const submitBtn = form.querySelector('button[type="submit"]');

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (errorEl) errorEl.textContent = '';
            if (submitBtn) submitBtn.disabled = true;

            const tenDangNhap = document.getElementById('username').value.trim();
            const matKhau = document.getElementById('password').value;

            try {
                const tokens = await AdminApi.apiFetch('/auth/login', {
                    method: 'POST',
                    auth: false,
                    body: { ten_dang_nhap: tenDangNhap, mat_khau: matKhau },
                });
                AdminApi.setTokens(tokens);

                const me = await AdminApi.loadCurrentAccount();
                const account = me.tai_khoan || me.account;
                if (!account || !AdminApi.STAFF_ROLES.has(account.vai_tro)) {
                    throw new Error('Tài khoản này không có quyền vào trang quản trị.');
                }

                const params = new URLSearchParams(window.location.search);
                const next = params.get('next');
                window.location.href = next || 'tong_quan.html';
            } catch (error) {
                AdminApi.clearTokens();
                if (errorEl) errorEl.textContent = error.message || 'Đăng nhập thất bại.';
            } finally {
                if (submitBtn) submitBtn.disabled = false;
            }
        });
    });
})();
