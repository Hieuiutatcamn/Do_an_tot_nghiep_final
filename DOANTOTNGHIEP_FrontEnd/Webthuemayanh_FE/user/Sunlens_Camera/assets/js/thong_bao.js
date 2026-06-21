(function () {
    'use strict';

    if (window.SunlensNotifications && window.SunlensNotifications.__ready) return;

    const API_BASE_URL = window.SUNLENS_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
    const TOKEN_KEYS = ['access_token', 'token', 'auth_token'];
    const USER_ACCOUNT_KEYS = ['user_account', 'user_customer', 'user', 'current_user', 'sunlens_user'];
    const ADMIN_ACCOUNT_KEYS = ['admin_account', 'admin_user', 'current_admin'];

    const state = {
        role: null,
        roots: [],
        notifications: [],
        unreadCount: 0,
        loaded: false,
        loading: false,
        unauthorized: false,
    };

    function ready(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
            return;
        }

        callback();
    }

    function getStorageValue(key) {
        return localStorage.getItem(key) || sessionStorage.getItem(key) || '';
    }

    function readJson(key) {
        const raw = getStorageValue(key);
        if (!raw) return null;

        try {
            return JSON.parse(raw);
        } catch (error) {
            return null;
        }
    }

    function getAuthToken() {
        for (const key of TOKEN_KEYS) {
            const value = getStorageValue(key);
            if (value) return value;
        }
        return '';
    }

    function isAdminPath() {
        return window.location.pathname.toLowerCase().includes('/admin/');
    }

    function getStoredAccount() {
        const keys = isAdminPath() ? ADMIN_ACCOUNT_KEYS.concat(USER_ACCOUNT_KEYS) : USER_ACCOUNT_KEYS.concat(ADMIN_ACCOUNT_KEYS);
        for (const key of keys) {
            const value = readJson(key);
            if (value) return value;
        }
        return {};
    }

    function getCurrentRole() {
        if (isAdminPath()) return 'Admin';

        const account = getStoredAccount();
        const rawRole = account.vai_tro || account.role || account.loai_tai_khoan || account.quyen || '';
        const role = String(rawRole).toLowerCase();

        if (role.includes('admin') || role.includes('nhan vien') || role.includes('nhân viên') || role.includes('staff') || role.includes('quan tri') || role.includes('quản trị')) {
            return 'Admin';
        }

        return 'User';
    }

    function getCurrentAccountId() {
        const account = getStoredAccount();
        return account.id_tai_khoan
            || account.Id_tai_khoan
            || account.ID_tai_khoan
            || account.id_account
            || account.Id_account
            || account.id
            || account.Id
            || account.id_khach_hang
            || account.Id_khach_hang
            || '';
    }

    function ensureStylesheet() {
        if (
            document.querySelector('link[data-sunlens-notifications-css]')
            || document.querySelector('link[href*="assets/css/notifications.css"]')
        ) return;

        const currentScript = document.currentScript
            || document.querySelector('script[data-sunlens-notifications-js]')
            || document.querySelector('script[src*="thong_bao.js"]');
        let href = isAdminPath()
            ? '../../user/Sunlens_Camera/assets/css/notifications.css'
            : './assets/css/notifications.css';

        if (currentScript && currentScript.src) {
            try {
                const cssUrl = new URL(currentScript.src, window.location.href);
                if (/\/assets\/js\/[^/]+\.js$/.test(cssUrl.pathname)) {
                    cssUrl.pathname = cssUrl.pathname.replace(/\/assets\/js\/[^/]+\.js$/, '/assets/css/notifications.css');
                    cssUrl.search = '';
                    cssUrl.hash = '';
                    href = cssUrl.href;
                }
            } catch (error) {
                href = currentScript.src.replace(/\/assets\/js\/thong_bao\.js(?:\?.*)?$/, '/assets/css/notifications.css');
            }
        }

        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        link.setAttribute('data-sunlens-notifications-css', 'true');
        document.head.appendChild(link);
    }

    function buildApiUrl(url) {
        if (/^https?:\/\//i.test(url)) return url;
        return `${API_BASE_URL}${url.startsWith('/') ? url : `/${url}`}`;
    }

    async function apiRequest(url, options = {}) {
        const token = getAuthToken();
        if (!token) {
            const error = new Error('Unauthorized');
            error.status = 401;
            throw error;
        }

        const headers = new Headers(options.headers || {});
        let body = options.body;

        headers.set('Authorization', `Bearer ${token}`);
        headers.set('Accept', 'application/json');
        if (!(body instanceof FormData) && !headers.has('Content-Type')) {
            headers.set('Content-Type', 'application/json');
        }

        if (body && !(body instanceof FormData) && typeof body !== 'string') {
            body = JSON.stringify(body);
        }

        const response = await fetch(buildApiUrl(url), {
            ...options,
            headers,
            body,
        });

        if (response.status === 401) {
            handleUnauthorized();
            const error = new Error('Unauthorized');
            error.status = 401;
            throw error;
        }

        if (response.status === 204) return null;

        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json')
            ? await response.json().catch(() => ({}))
            : await response.text();

        if (!response.ok) {
            const message = typeof data === 'object' && data && data.detail
                ? data.detail
                : `API lỗi ${response.status}`;
            const error = new Error(message);
            error.status = response.status;
            throw error;
        }

        return data;
    }

    function normalizeText(value) {
        return String(value || '')
            .trim()
            .toLowerCase();
    }

    function getNotificationId(item) {
        return item.Id_thong_bao
            || item.id_thong_bao
            || item.ID_thong_bao
            || item.id
            || item.Id
            || '';
    }

    function getNotificationStatus(item) {
        const keys = ['trang_thai', 'Trang_thai', 'status', 'is_read', 'read'];
        for (const key of keys) {
            if (Object.prototype.hasOwnProperty.call(item, key) && item[key] !== undefined && item[key] !== null) {
                return item[key];
            }
        }
        return '';
    }

    function isUnread(item) {
        const status = getNotificationStatus(item);

        if (typeof status === 'boolean') return !status;
        if (Number(status) === 0 && String(status).trim() !== '') return true;

        const text = normalizeText(status);
        return text.includes('chua doc') || text.includes('chưa đọc') || text === 'unread' || text === 'new';
    }

    function notificationTitle(item) {
        return item.tieu_de || item.Tieu_de || item.title || item.loai_thong_bao || item.Loai_thong_bao || 'Thông báo';
    }

    function notificationContent(item) {
        return item.noi_dung || item.Noi_dung || item.content || item.message || '';
    }

    function notificationDate(item) {
        return item.ngay_tao || item.Ngay_tao || item.created_at || item.createdAt || '';
    }

    function notificationTarget(item) {
        return item.doi_tuong_nhan || item.Doi_tuong_nhan || item.target_role || item.role || '';
    }

    function notificationAccountId(item) {
        return item.id_tai_khoan
            || item.Id_tai_khoan
            || item.ID_tai_khoan
            || item.id_nguoi_nhan
            || item.Id_nguoi_nhan
            || item.id_khach_hang
            || item.Id_khach_hang
            || '';
    }

    function normalizeNotificationResponse(data) {
        if (Array.isArray(data)) return data;
        if (data && Array.isArray(data.danh_sach)) return data.danh_sach;
        if (data && Array.isArray(data.items)) return data.items;
        if (data && Array.isArray(data.notifications)) return data.notifications;
        if (data && Array.isArray(data.data)) return data.data;
        return [];
    }

    function belongsToCurrentRole(item) {
        const target = normalizeText(notificationTarget(item));
        const role = state.role || getCurrentRole();
        const currentAccountId = String(getCurrentAccountId() || '');
        const targetAccountId = String(notificationAccountId(item) || '');

        if (targetAccountId && currentAccountId && targetAccountId === currentAccountId) {
            return true;
        }

        if (!target || target === 'all' || target === 'tat ca' || target === 'tất cả' || target === 'chung') {
            return true;
        }

        if (role === 'Admin') {
            return target.includes('admin')
                || target.includes('nhan vien')
                || target.includes('nhân viên')
                || target.includes('staff')
                || target.includes('quan tri')
                || target.includes('quản trị');
        }

        return target.includes('user')
            || target.includes('khach')
            || target.includes('khách')
            || target.includes('khach hang')
            || target.includes('khách hàng')
            || target.includes('nguoi dung')
            || target.includes('người dùng');
    }

    function countUnread(items) {
        return items.reduce((total, item) => total + (isUnread(item) ? 1 : 0), 0);
    }

    function formatDate(value) {
        if (!value) return '';

        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return String(value);

        return new Intl.DateTimeFormat('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        }).format(date);
    }

    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function shorten(value, maxLength) {
        const text = String(value || '').trim();
        if (text.length <= maxLength) return text;
        return `${text.slice(0, maxLength - 1).trim()}...`;
    }

    function bellSvg() {
        return [
            '<svg class="notification-bell-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">',
            '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/>',
            '<path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
            '</svg>',
        ].join('');
    }

    function dropdownMarkup() {
        return [
            '<div class="notification-dropdown" aria-hidden="true">',
            '<div class="notification-header">',
            '<strong>Thông báo</strong>',
            '<button type="button" class="notification-mark-all">Đánh dấu tất cả đã đọc</button>',
            '</div>',
            '<div class="notification-list">',
            '<div class="notification-empty">Không có thông báo nào.</div>',
            '</div>',
            '</div>',
        ].join('');
    }

    function createUserWrapper() {
        const wrapper = document.createElement('div');
        wrapper.className = 'list-inline-item me-4 notification-wrapper notification-user';
        wrapper.setAttribute('data-sunlens-notification-root', 'true');
        wrapper.innerHTML = [
            '<button type="button" class="notification-btn text-muted d-flex flex-column justity-content-center align-items-center" aria-label="Thông báo" aria-expanded="false">',
            '<span class="notification-icon"><i class="bi bi-bell" aria-hidden="true"></i><span class="notification-badge">0</span></span>',
            '<span class="notification-label">Thông báo</span>',
            '</button>',
            dropdownMarkup(),
        ].join('');
        return wrapper;
    }

    function createAdminWrapper() {
        const wrapper = document.createElement('div');
        wrapper.className = 'notification-wrapper notification-admin';
        wrapper.setAttribute('data-sunlens-notification-root', 'true');
        wrapper.innerHTML = [
            '<button type="button" class="nav-btn notification-btn" aria-label="Thông báo" aria-expanded="false">',
            '<span class="notification-icon">',
            bellSvg(),
            '<span class="notification-badge">0</span>',
            '</span>',
            '</button>',
            dropdownMarkup(),
        ].join('');
        return wrapper;
    }

    function mountUserNotifications() {
        const cartLinks = Array.from(document.querySelectorAll('header a[href*="gio_hang.html"]'));
        cartLinks.forEach((link) => {
            const cartItem = link.closest('.list-inline-item');
            if (!cartItem || !cartItem.parentElement) return;
            const hasNotification = Array.from(cartItem.parentElement.children).some((child) => (
                child.matches('[data-sunlens-notification-root]')
            ));
            if (hasNotification) return;

            cartItem.insertAdjacentElement('afterend', createUserWrapper());
        });
    }

    function mountAdminNotifications() {
        const themeToggle = document.getElementById('theme-toggle');
        const navbarRight = themeToggle ? themeToggle.closest('.navbar-right') : document.querySelector('.navbar-right');
        if (!navbarRight || navbarRight.querySelector('[data-sunlens-notification-root]')) return;

        const wrapper = createAdminWrapper();
        if (themeToggle) {
            navbarRight.insertBefore(wrapper, themeToggle);
            return;
        }

        navbarRight.appendChild(wrapper);
    }

    function resetDropdownPosition(dropdown) {
        if (!dropdown) return;
        dropdown.style.left = '';
        dropdown.style.right = '';
        dropdown.style.maxHeight = '';
    }

    function shouldUseFixedMobileDropdown() {
        return window.matchMedia && window.matchMedia('(max-width: 575.98px)').matches;
    }

    function positionDropdown(root) {
        if (!root || shouldUseFixedMobileDropdown()) {
            const mobileDropdown = root && root.querySelector('.notification-dropdown');
            resetDropdownPosition(mobileDropdown);
            return;
        }

        const dropdown = root.querySelector('.notification-dropdown');
        if (!dropdown) return;

        resetDropdownPosition(dropdown);

        const viewportPadding = 12;
        const rootRect = root.getBoundingClientRect();
        const width = Math.min(dropdown.offsetWidth || 360, window.innerWidth - (viewportPadding * 2));
        const targetLeft = Math.min(
            window.innerWidth - viewportPadding - width,
            Math.max(viewportPadding, rootRect.right - width)
        );
        const relativeLeft = targetLeft - rootRect.left;

        dropdown.style.left = `${Math.round(relativeLeft)}px`;
        dropdown.style.right = 'auto';
        dropdown.style.maxHeight = `${Math.max(240, window.innerHeight - rootRect.bottom - 24)}px`;
    }

    function positionOpenDropdowns() {
        state.roots.forEach((root) => {
            if (root.classList.contains('open')) {
                positionDropdown(root);
            }
        });
    }
    function refreshRoots() {
        state.roots = Array.from(document.querySelectorAll('[data-sunlens-notification-root]'));
        bindRootEvents();
    }

    function setBadge(count) {
        const safeCount = Math.max(0, Number(count) || 0);
        state.unreadCount = safeCount;

        state.roots.forEach((root) => {
            const badge = root.querySelector('.notification-badge');
            if (!badge) return;

            badge.textContent = safeCount > 99 ? '99+' : String(safeCount);
            badge.classList.toggle('is-visible', safeCount > 0);
        });
    }

    function closeAllDropdowns() {
        state.roots.forEach((root) => {
            root.classList.remove('open');
            const button = root.querySelector('.notification-btn');
            const dropdown = root.querySelector('.notification-dropdown');
            if (button) button.setAttribute('aria-expanded', 'false');
            if (dropdown) {
                dropdown.setAttribute('aria-hidden', 'true');
                resetDropdownPosition(dropdown);
            }
        });
    }

    function handleUnauthorized() {
        state.unauthorized = true;
        state.notifications = [];
        state.loaded = false;
        closeAllDropdowns();
        setBadge(0);
    }

    function setListState(html) {
        state.roots.forEach((root) => {
            const list = root.querySelector('.notification-list');
            if (list) list.innerHTML = html;
        });
    }

    function setLoadingState() {
        setListState('<div class="notification-loading">Đang tải thông báo...</div>');
    }

    function setErrorState() {
        setListState('<div class="notification-error">Không thể tải thông báo.</div>');
    }

    function hienThiThongBao(notifications) {
        const items = Array.isArray(notifications) ? notifications : [];
        const unreadTotal = countUnread(items);

        if (!items.length) {
            setListState('<div class="notification-empty">Không có thông báo nào.</div>');
            setBadge(0);
            return;
        }

        const html = items.map((item) => {
            const id = getNotificationId(item);
            const unread = isUnread(item);
            const statusText = unread ? 'Chưa đọc' : 'Đã đọc';
            const title = escapeHtml(notificationTitle(item));
            const content = escapeHtml(shorten(notificationContent(item), 120));
            const date = escapeHtml(formatDate(notificationDate(item)));
            const disabled = unread && id ? '' : ' disabled';

            return [
                `<button type="button" class="notification-item${unread ? ' is-unread' : ''}" data-notification-id="${escapeHtml(id)}"${disabled}>`,
                '<div class="notification-title-row">',
                `<span class="notification-title">${title}</span>`,
                unread ? '<span class="notification-unread-dot" aria-hidden="true"></span>' : '',
                '</div>',
                content ? `<div class="notification-content">${content}</div>` : '',
                '<div class="notification-meta">',
                `<span>${date}</span>`,
                `<span class="notification-status">${statusText}</span>`,
                '</div>',
                '</button>',
            ].join('');
        }).join('');

        setListState(html);
        setBadge(unreadTotal);
    }

    async function taiThongBao() {
        if (!getAuthToken()) {
            handleUnauthorized();
            return [];
        }

        state.loading = true;
        setLoadingState();

        try {
            const data = await apiRequest('/notifications');
            const items = normalizeNotificationResponse(data).filter(belongsToCurrentRole);
            console.log('Notification API data:', items);
            state.notifications = items;
            state.loaded = true;
            state.unauthorized = false;
            hienThiThongBao(items);
            return items;
        } catch (error) {
            if (error.status !== 401) {
                console.warn(error.message || error);
                setErrorState();
            }
            return [];
        } finally {
            state.loading = false;
        }
    }

    async function loadUnreadCount() {
        if (!getAuthToken()) {
            handleUnauthorized();
            return 0;
        }

        try {
            const data = await apiRequest('/notifications/unread-count');
            const count = Number(data && (data.unread_count || data.unreadCount || data.count)) || 0;
            state.unreadCount = count;
            setBadge(state.loaded ? countUnread(state.notifications) : count);
            return state.unreadCount;
        } catch (error) {
            if (error.status !== 401) {
                console.warn(error.message || error);
                setBadge(0);
            }
            return 0;
        }
    }

    async function refreshNotifications() {
        await taiThongBao();
        await loadUnreadCount();
        if (state.loaded) {
            setBadge(countUnread(state.notifications));
        }
    }

    async function markNotificationAsRead(id) {
        if (!id) return;

        try {
            await apiRequest(`/notifications/${encodeURIComponent(id)}/read`, {
                method: 'PUT',
            });
            await refreshNotifications();
        } catch (error) {
            if (error.status !== 401) {
                console.warn(error.message || error);
                setErrorState();
            }
        }
    }

    async function markAllNotificationsAsRead() {
        try {
            await apiRequest('/notifications/read-all', {
                method: 'PUT',
            });
            await refreshNotifications();
        } catch (error) {
            if (error.status !== 401) {
                console.warn(error.message || error);
                setErrorState();
            }
        }
    }

    function toggleNotificationDropdown(event) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }

        if (!getAuthToken()) {
            closeAllDropdowns();
            setBadge(0);
            return;
        }

        const root = event
            ? event.currentTarget.closest('[data-sunlens-notification-root]')
            : state.roots[0];

        if (!root) return;

        const willOpen = !root.classList.contains('open');
        closeAllDropdowns();

        root.classList.toggle('open', willOpen);
        const button = root.querySelector('.notification-btn');
        const dropdown = root.querySelector('.notification-dropdown');
        if (button) button.setAttribute('aria-expanded', String(willOpen));
        if (dropdown) dropdown.setAttribute('aria-hidden', String(!willOpen));

        if (willOpen) {
            window.requestAnimationFrame(() => positionDropdown(root));
        }

        if (willOpen && (!state.loaded || !state.notifications.length)) {
            refreshNotifications();
        }
    }

    function closeNotificationDropdownOnOutsideClick() {
        if (document.documentElement.dataset.sunlensNotificationOutsideBound === 'true') return;

        document.documentElement.dataset.sunlensNotificationOutsideBound = 'true';
        document.addEventListener('click', (event) => {
            if (!event.target.closest('[data-sunlens-notification-root]')) {
                closeAllDropdowns();
            }
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                closeAllDropdowns();
            }
        });

        window.addEventListener('resize', positionOpenDropdowns);
        window.addEventListener('scroll', positionOpenDropdowns, true);
    }

    function bindRootEvents() {
        state.roots.forEach((root) => {
            if (root.dataset.sunlensNotificationBound === 'true') return;

            root.dataset.sunlensNotificationBound = 'true';
            const button = root.querySelector('.notification-btn');
            const markAllButton = root.querySelector('.notification-mark-all');
            const list = root.querySelector('.notification-list');

            if (button) {
                button.addEventListener('click', toggleNotificationDropdown);
            }

            if (markAllButton) {
                markAllButton.addEventListener('click', (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    markAllNotificationsAsRead();
                });
            }

            if (list) {
                list.addEventListener('click', (event) => {
                    const item = event.target.closest('.notification-item.is-unread');
                    if (!item || item.disabled) return;

                    event.preventDefault();
                    event.stopPropagation();
                    markNotificationAsRead(item.dataset.notificationId);
                });
            }
        });
    }

    function init() {
        ensureStylesheet();
        state.role = getCurrentRole();

        if (state.role === 'Admin') {
            mountAdminNotifications();
        } else {
            mountUserNotifications();
        }

        refreshRoots();
        closeNotificationDropdownOnOutsideClick();

        if (!getAuthToken()) {
            setBadge(0);
            return;
        }

        refreshNotifications();
    }

    window.SunlensNotifications = {
        __ready: true,
        API_BASE_URL,
        getAuthToken,
        getCurrentRole,
        apiRequest,
        taiThongBao,
        loadUnreadCount,
        hienThiThongBao,
        markNotificationAsRead,
        markAllNotificationsAsRead,
        toggleNotificationDropdown,
        closeNotificationDropdownOnOutsideClick,
        refresh: refreshNotifications,
    };

    ready(init);
})();
