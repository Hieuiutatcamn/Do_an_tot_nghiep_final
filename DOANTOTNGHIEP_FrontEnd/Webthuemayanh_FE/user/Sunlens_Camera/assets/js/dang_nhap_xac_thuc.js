(function () {
    'use strict';

    const API_BASE = 'http://127.0.0.1:8000/api/v1';
    const GOOGLE_LOGIN_URL = `${API_BASE}/auth/google/login`;
    const FACEBOOK_LOGIN_URL = `${API_BASE}/auth/facebook/login`;
    const ADMIN_ROLES = new Set(['Admin', 'Nhan vien']);
    const OAUTH_URL_KEYS = [
        'access_token',
        'refresh_token',
        'token_type',
        'oauth_error',
        'nha_cung_cap',
        'provider',
    ];

    function luu_token_dang_nhap(tokens) {
        localStorage.setItem('access_token', tokens.access_token || '');
        localStorage.setItem('refresh_token', tokens.refresh_token || '');
        localStorage.setItem('token_type', tokens.token_type || 'bearer');
    }

    function xoa_du_lieu_dang_nhap() {
        [
            'access_token',
            'refresh_token',
            'token_type',
            'admin_account',
            'user_account',
            'user_customer',
            'token',
            'user',
            'currentUser',
            'current_user',
            'sunlens_user',
            'admin',
            'adminUser',
            'role',
            'vai_tro',
            'auth_user',
            'id_tai_khoan',
            'id_khach_hang',
            'id_admin',
        ].forEach((key) => {
            localStorage.removeItem(key);
            sessionStorage.removeItem(key);
        });
    }

    async function apiFetch(path, options = {}) {
        const headers = new Headers(options.headers || {});
        let body = options.body;

        if (body && typeof body !== 'string') {
            headers.set('Content-Type', 'application/json');
            body = JSON.stringify(body);
        }

        const response = await fetch(`${API_BASE}${path}`, {
            ...options,
            headers,
            body,
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const detail = Array.isArray(data.detail) ? data.detail.join('\n') : data.detail;
            throw new Error(detail || `API lỗi ${response.status}`);
        }
        return data;
    }

    async function apiFetchAuth(path) {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}${path}`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.detail || `API lỗi ${response.status}`);
        }
        return data;
    }

    function getNextPath() {
        const params = new URLSearchParams(window.location.search);
        return params.get('next') || '';
    }

    function la_duong_dan_admin(path) {
        return path.toLowerCase().includes('/admin/sunlens_camera/');
    }

    function dieu_huong_sau_dang_nhap(me) {
        const account = me.tai_khoan || me.account || {};
        const customer = me.khach_hang || me.customer || {};
        const role = account.vai_tro;
        const next = getNextPath();

        if (ADMIN_ROLES.has(role)) {
            localStorage.setItem('admin_account', JSON.stringify(account));
            if (next && la_duong_dan_admin(next)) {
                window.location.href = next;
                return;
            }
            window.location.href = '../../admin/Sunlens_Camera/tong_quan.html';
            return;
        }

        localStorage.setItem('user_account', JSON.stringify(account));
        localStorage.setItem('user_customer', JSON.stringify(customer));

        if (next && !la_duong_dan_admin(next)) {
            window.location.href = next;
            return;
        }
        window.location.href = 'index.html';
    }

    function hien_thi_thong_bao_dang_nhap(message, type = 'error') {
        const messageBox = document.getElementById('loginMessage');
        if (!messageBox) return;
        messageBox.textContent = message || '';
        messageBox.className = type === 'success'
            ? 'mt-3 small text-success fw-semibold'
            : 'mt-3 small text-danger fw-semibold';
    }

    function lay_tham_so_oauth_tu_url() {
        const queryParams = new URLSearchParams(window.location.search);
        const hashText = window.location.hash.replace(/^#/, '');
        const hashParams = new URLSearchParams(hashText);
        const getValue = (key) => hashParams.get(key) || queryParams.get(key) || '';

        return {
            access_token: getValue('access_token'),
            refresh_token: getValue('refresh_token'),
            token_type: getValue('token_type') || 'bearer',
            oauth_error: getValue('oauth_error'),
            queryParams,
            hashParams,
            hashHasOAuthParams: OAUTH_URL_KEYS.some((key) => hashParams.has(key)),
        };
    }

    function xoa_token_khoi_url(oauthParams) {
        OAUTH_URL_KEYS.forEach((key) => {
            oauthParams.queryParams.delete(key);
            oauthParams.hashParams.delete(key);
        });

        const cleanQuery = oauthParams.queryParams.toString();
        const cleanHash = oauthParams.hashHasOAuthParams
            ? oauthParams.hashParams.toString()
            : window.location.hash.replace(/^#/, '');
        const cleanUrl = `${window.location.pathname}`
            + `${cleanQuery ? `?${cleanQuery}` : ''}`
            + `${cleanHash ? `#${cleanHash}` : ''}`;
        window.history.replaceState({}, document.title, cleanUrl);
    }

    async function xu_ly_callback_dang_nhap_xa_hoi() {
        const oauthParams = lay_tham_so_oauth_tu_url();
        const oauthError = oauthParams.oauth_error;
        const accessToken = oauthParams.access_token;

        if (!oauthError && !accessToken) {
            return false;
        }

        xoa_token_khoi_url(oauthParams);
        if (oauthError) {
            xoa_du_lieu_dang_nhap();
            hien_thi_thong_bao_dang_nhap(oauthError);
            return true;
        }

        try {
            luu_token_dang_nhap({
                access_token: accessToken,
                refresh_token: oauthParams.refresh_token,
                token_type: oauthParams.token_type,
            });
            hien_thi_thong_bao_dang_nhap('Đăng nhập thành công. Đang chuyển hướng...', 'success');
            const me = await apiFetchAuth('/auth/me');
            dieu_huong_sau_dang_nhap(me);
        } catch (error) {
            xoa_du_lieu_dang_nhap();
            hien_thi_thong_bao_dang_nhap('Không lấy được thông tin tài khoản.');
        }
        return true;
    }

    document.addEventListener('DOMContentLoaded', async () => {
        const form = document.getElementById('loginForm');
        if (!form) return;

        const googleLoginButton = document.querySelector('[data-oauth-login="google"]');
        if (googleLoginButton) {
            googleLoginButton.setAttribute('href', GOOGLE_LOGIN_URL);
            googleLoginButton.addEventListener('click', (event) => {
                event.preventDefault();
                window.location.href = GOOGLE_LOGIN_URL;
            });
        }

        const facebookLoginButton = document.getElementById('facebookLoginButton');
        if (facebookLoginButton) {
            facebookLoginButton.addEventListener('click', (event) => {
                event.preventDefault();
                window.location.href = FACEBOOK_LOGIN_URL;
            });
        }

        const message = document.getElementById('loginMessage');
        const submitButton = form.querySelector('button[type="submit"]');
        const handledOAuth = await xu_ly_callback_dang_nhap_xa_hoi();
        if (handledOAuth && localStorage.getItem('access_token')) return;

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (message) {
                message.textContent = '';
                message.className = 'mt-3 small';
            }
            if (submitButton) submitButton.disabled = true;

            try {
                xoa_du_lieu_dang_nhap();
                const tenDangNhap = document.getElementById('loginUsername').value.trim();
                const matKhau = document.getElementById('loginPassword').value;
                const tokens = await apiFetch('/auth/login', {
                    method: 'POST',
                    body: { ten_dang_nhap: tenDangNhap, mat_khau: matKhau },
                });
                luu_token_dang_nhap(tokens);
                const me = await apiFetchAuth('/auth/me');
                dieu_huong_sau_dang_nhap(me);
            } catch (error) {
                xoa_du_lieu_dang_nhap();
                if (message) {
                    hien_thi_thong_bao_dang_nhap(error.message || 'Đăng nhập thất bại.');
                } else {
                    alert(error.message || 'Đăng nhập thất bại.');
                }
            } finally {
                if (submitButton) submitButton.disabled = false;
            }
        });
    });
})();
