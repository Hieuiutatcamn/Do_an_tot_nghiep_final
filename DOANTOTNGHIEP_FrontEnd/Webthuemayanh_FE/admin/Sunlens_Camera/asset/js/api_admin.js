(function () {
    'use strict';

    const API_ORIGIN = 'http://127.0.0.1:8000';
    const API_BASE = `${API_ORIGIN}/api/v1`;
    const LOGIN_PAGE = '../../user/Sunlens_Camera/dang_nhap.html';
    const STAFF_ROLES = new Set(['Admin', 'Nhan vien']);

    function isLoginPage() {
        const path = window.location.pathname.toLowerCase();
        return path.endsWith('/user/sunlens_camera/dang_nhap.html') || path.endsWith('/admin/sunlens_camera/dang_nhap.html');
    }

    function getToken() {
        return localStorage.getItem('access_token') || '';
    }

    function setTokens(tokens) {
        localStorage.setItem('access_token', tokens.access_token || '');
        localStorage.setItem('refresh_token', tokens.refresh_token || '');
        localStorage.setItem('token_type', tokens.token_type || 'bearer');
    }

    function clearTokens() {
        [
            'access_token',
            'refresh_token',
            'token_type',
            'admin_account',
            'token',
            'user',
            'currentUser',
            'current_user',
            'admin',
            'adminUser',
            'role',
            'vai_tro',
            'auth_user',
            'id_tai_khoan',
            'id_khach_hang',
            'id_admin',
            'user_account',
            'user_customer',
            'sunlens_user',
        ].forEach((key) => {
            localStorage.removeItem(key);
            sessionStorage.removeItem(key);
        });
    }

    function loginUrl() {
        const current = `${window.location.pathname}${window.location.search}`;
        return `${LOGIN_PAGE}?next=${encodeURIComponent(current)}`;
    }

    function redirectToLogin() {
        if (!isLoginPage()) {
            window.location.href = loginUrl();
        }
    }

    function requireAuth() {
        if (!getToken()) {
            redirectToLogin();
            return false;
        }
        return true;
    }

    function apiErrorMessage(data, statusCode) {
        if (data && typeof data === 'object') {
            const detail = data.detail ?? data.message ?? data.error;
            if (Array.isArray(detail)) {
                const messages = detail.map((item) => {
                    if (!item || typeof item !== 'object') return String(item || '');
                    const field = Array.isArray(item.loc)
                        ? item.loc.filter((part) => part !== 'body').join('.')
                        : '';
                    const message = item.msg || item.message || item.type || 'Dữ liệu không hợp lệ';
                    return field ? `${field}: ${message}` : message;
                }).filter(Boolean);
                return messages.length ? messages.join('\n') : `API lỗi ${statusCode}`;
            }
            if (detail && typeof detail === 'object') {
                return detail.noi_dung || detail.message || JSON.stringify(detail);
            }
            if (detail) return String(detail);
        }
        if (typeof data === 'string' && data.trim()) return data.trim();
        return `API lỗi ${statusCode}`;
    }

    async function apiFetch(path, options = {}) {
        const auth = options.auth !== false;
        const debug = options.debug === true;
        const headers = new Headers(options.headers || {});
        let body = options.body;
        const requestData = body;

        if (auth) {
            const token = getToken();
            if (!token) {
                redirectToLogin();
                throw new Error('Bạn cần đăng nhập để tiếp tục.');
            }
            headers.set('Authorization', `Bearer ${token}`);
        }

        if (body && !(body instanceof FormData) && typeof body !== 'string') {
            headers.set('Content-Type', 'application/json');
            body = JSON.stringify(body);
        }

        const requestUrl = `${API_BASE}${path}`;
        if (debug) {
            console.log('Request:', {
                url: requestUrl,
                method: options.method || 'GET',
                body: requestData ?? null,
            });
        }

        const requestOptions = { ...options };
        delete requestOptions.auth;
        delete requestOptions.debug;
        const response = await fetch(requestUrl, {
            ...requestOptions,
            headers,
            body,
        });

        if (response.status === 401) {
            clearTokens();
            redirectToLogin();
            throw new Error('Phiên đăng nhập đã hết hạn.');
        }

        if (response.status === 204) {
            return null;
        }

        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json')
            ? await response.json()
            : await response.text();
        if (debug) {
            console.log('Response:', {
                url: requestUrl,
                status: response.status,
                data,
            });
        }

        if (!response.ok) {
            const error = new Error(apiErrorMessage(data, response.status));
            error.status = response.status;
            error.response = data;
            throw error;
        }

        return data;
    }

    function buildQuery(params = {}) {
        const query = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                query.set(key, value);
            }
        });
        const text = query.toString();
        return text ? `?${text}` : '';
    }

    async function getPage(path, params = {}) {
        return apiFetch(`${path}${buildQuery(params)}`);
    }

    async function getAll(path, params = {}) {
        const firstPage = await getPage(path, { page: 1, page_size: 100, ...params });
        if (Array.isArray(firstPage)) return firstPage;

        const pageItems = firstPage.danh_sach || firstPage.items || [];
        const items = [...pageItems];
        const totalPages = Number(firstPage.tong_so_trang || firstPage.total_pages || 1);
        for (let page = 2; page <= totalPages; page += 1) {
            const nextPage = await getPage(path, { page, page_size: firstPage.page_size || 100, ...params });
            items.push(...(nextPage.danh_sach || nextPage.items || []));
        }
        return items;
    }

    async function optional(fn, fallback) {
        try {
            return await fn();
        } catch (error) {
            console.warn(error.message || error);
            return fallback;
        }
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, function (char) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;',
            }[char];
        });
    }

    function formatCurrency(value) {
        return `${Number(value || 0).toLocaleString('vi-VN')} đ`;
    }

    function formatDateTime(value) {
        if (!value) return '-';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
    }

    function formatDate(value) {
        if (!value) return '-';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    }

    function duongDanAnh(duongDan, duongDanDuPhong = '') {
        if (!duongDan) return duongDanDuPhong;

        const giaTri = String(duongDan).trim().replace(/\\/g, '/');
        if (!giaTri) return duongDanDuPhong;
        if (/^(https?:|data:|blob:)/i.test(giaTri)) return giaTri;

        const duongDanChuanHoa = giaTri.replace(/^\.?\//, '');
        if (duongDanChuanHoa.startsWith('uploads/')) {
            return `${API_ORIGIN}/${duongDanChuanHoa}`;
        }
        if (duongDanChuanHoa.startsWith('assets/')) {
            return new URL(
                `../../user/Sunlens_Camera/${duongDanChuanHoa}`,
                window.location.href
            ).href;
        }
        if (duongDanChuanHoa.startsWith('Webthuemayanh_FE/')) {
            return new URL(`/${duongDanChuanHoa}`, window.location.origin).href;
        }
        if (giaTri.startsWith('/')) {
            return `${API_ORIGIN}${giaTri}`;
        }

        return duongDanChuanHoa;
    }

    function imageUrl(path, fallback = '') {
        return duongDanAnh(path, fallback);
    }

    function rentalStatusToUi(status) {
        return {
            'Cho thanh toan': 'payment-pending',
            'Da dat': 'pending',
            'Da xac nhan': 'confirmed',
            'Dang thue': 'renting',
            'Da thue': 'completed',
            'Da qua han': 'overdue',
            'Da huy': 'cancelled',
        }[status] || status || 'pending';
    }

    function rentalStatusToApi(status) {
        return {
            pending: 'Da dat',
            confirmed: 'Da xac nhan',
            renting: 'Dang thue',
            completed: 'Da thue',
            overdue: 'Da qua han',
            cancelled: 'Da huy',
        }[status] || status;
    }

    function rentalStatusText(status) {
        return {
            'payment-pending': 'Chờ thanh toán',
            pending: 'Đã đặt',
            confirmed: 'Đã xác nhận',
            renting: 'Đang thuê',
            completed: 'Đã thuê',
            overdue: 'Quá hạn',
            cancelled: 'Đã hủy',
            'Cho thanh toan': 'Chờ thanh toán',
            'Da dat': 'Đã đặt',
            'Da xac nhan': 'Đã xác nhận',
            'Dang thue': 'Đang thuê',
            'Da thue': 'Đã thuê',
            'Da qua han': 'Quá hạn',
            'Da huy': 'Đã hủy',
        }[status] || status || '-';
    }

    function accountStatusToUi(account) {
        if (!account) return 'locked';
        return account.trang_thai === 'Hoat dong' && account.kich_hoat !== false ? 'active' : 'locked';
    }

    function accountStatusToApi(status) {
        return status === 'active'
            ? { trang_thai: 'Hoat dong', kich_hoat: true }
            : { trang_thai: 'Ngung hoat dong', kich_hoat: false };
    }

    function roleToUi(role) {
        return {
            'Khach hang': 'customer',
            'Nhan vien': 'employee',
            Admin: 'admin',
        }[role] || role || '';
    }

    function roleText(role) {
        return {
            'Khach hang': 'Khách hàng',
            'Nhan vien': 'Nhân viên',
            Admin: 'Admin',
            customer: 'Khách hàng',
            employee: 'Nhân viên',
            admin: 'Admin',
        }[role] || role || '-';
    }

    function getStoredAccount() {
        const raw = localStorage.getItem('admin_account');
        if (!raw) return null;
        try {
            return JSON.parse(raw);
        } catch (error) {
            console.warn(error);
            return null;
        }
    }

    function currentRole() {
        return getStoredAccount()?.vai_tro || '';
    }

    function laAdmin() {
        return currentRole() === 'Admin';
    }

    function laNhanVien() {
        return currentRole() === 'Nhan vien';
    }

    function coQuyenChinhSuaNoiDung() {
        return laAdmin();
    }

    function firstDetailDate(order, field, fallback = '') {
        const dates = (order.chi_tiet || order.details || [])
            .map((item) => item[field])
            .filter(Boolean)
            .map((value) => new Date(value))
            .filter((date) => !Number.isNaN(date.getTime()));
        if (!dates.length) return fallback;
        const target = field === 'ngay_tra'
            ? new Date(Math.max(...dates.map((date) => date.getTime())))
            : new Date(Math.min(...dates.map((date) => date.getTime())));
        return target.toISOString();
    }

    function initials(name) {
        const words = String(name || '').trim().split(/\s+/).filter(Boolean);
        if (!words.length) return 'AD';
        return words.slice(-2).map((word) => word[0]).join('').toUpperCase();
    }

    async function loadCurrentAccount() {
        const me = await apiFetch('/auth/me');
        const account = me.tai_khoan || me.account;
        localStorage.setItem('admin_account', JSON.stringify(account || {}));
        if (!account || !STAFF_ROLES.has(account.vai_tro)) {
            clearTokens();
            throw new Error('Tài khoản này không có quyền vào trang quản trị.');
        }
        return me;
    }

    function bindLogout() {
        document.querySelectorAll('a').forEach((link) => {
            const label = link.textContent.trim().toLowerCase();
            if (label === 'logout' || label === 'đăng xuất' || label === 'dang xuat') {
                link.addEventListener('click', (event) => {
                    event.preventDefault();
                    clearTokens();
                    window.location.href = LOGIN_PAGE;
                });
            }
        });
    }

    function updateSidebarProfile() {
        const raw = localStorage.getItem('admin_account');
        if (!raw) return;
        try {
            const account = JSON.parse(raw);
            const nameEl = document.querySelector('.sidebar-footer .user-name');
            const roleEl = document.querySelector('.sidebar-footer .user-role');
            const avatarEl = document.querySelector('.sidebar-footer .user-avatar');
            if (nameEl) nameEl.textContent = account.dang_nhap || 'Admin';
            if (roleEl) roleEl.textContent = roleText(account.vai_tro);
            if (avatarEl) avatarEl.textContent = initials(account.dang_nhap || account.vai_tro);
        } catch (error) {
            console.warn(error);
        }
    }

    function loadAdminNotificationsWidget() {
        if (isLoginPage() || !getToken()) return;
        if (window.SunlensAdminNotifications || document.querySelector('script[data-admin-notifications-js]')) return;

        const script = document.createElement('script');
        script.src = 'thong_bao_admin.js';
        script.defer = true;
        script.setAttribute('data-admin-notifications-js', 'true');
        document.body.appendChild(script);
    }

    window.AdminApi = {
        API_BASE,
        API_ORIGIN,
        STAFF_ROLES,
        getToken,
        setTokens,
        clearTokens,
        requireAuth,
        apiFetch,
        getPage,
        getAll,
        optional,
        escapeHtml,
        formatCurrency,
        formatDate,
        formatDateTime,
        duongDanAnh,
        imageUrl,
        rentalStatusToUi,
        rentalStatusToApi,
        rentalStatusText,
        accountStatusToUi,
        accountStatusToApi,
        roleToUi,
        roleText,
        getStoredAccount,
        currentRole,
        laAdmin,
        laNhanVien,
        coQuyenChinhSuaNoiDung,
        firstDetailDate,
        initials,
        loadCurrentAccount,
    };

    if (!isLoginPage()) {
        requireAuth();
    }

    document.addEventListener('DOMContentLoaded', () => {
        bindLogout();
        updateSidebarProfile();
        if (!isLoginPage() && getToken()) {
            loadCurrentAccount()
                .then(() => {
                    updateSidebarProfile();
                    loadAdminNotificationsWidget();
                })
                .catch((error) => {
                    console.warn(error.message || error);
                    clearTokens();
                    alert(error.message || 'Bạn cần đăng nhập bằng tài khoản quản trị.');
                    redirectToLogin();
                });
        }
    });
})();
