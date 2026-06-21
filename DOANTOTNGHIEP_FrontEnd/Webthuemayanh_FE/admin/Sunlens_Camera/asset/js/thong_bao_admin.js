(function () {
    'use strict';

    if (window.SunlensAdminNotifications) return;

    const POLL_INTERVAL_MS = 10000;
    const state = {
        items: [],
        unreadCount: 0,
        timer: null,
        open: false,
    };

    function escapeHtml(value) {
        if (window.AdminApi && typeof AdminApi.escapeHtml === 'function') {
            return AdminApi.escapeHtml(value);
        }
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

    function idThongBao(item) {
        return item?.id_thong_bao || item?.Id_thong_bao || item?.notification_id || item?.id;
    }

    function idDonThue(item) {
        return item?.id_don_thue || item?.Id_don_thue || item?.rental_id || item?.order_id || null;
    }

    function isUnread(item) {
        return String(item?.trang_thai || item?.status || '').toLowerCase() !== 'da doc'
            && String(item?.trang_thai || item?.status || '').toLowerCase() !== 'đã đọc';
    }

    function timeText(value) {
        if (window.AdminApi && typeof AdminApi.formatDateTime === 'function') {
            return AdminApi.formatDateTime(value);
        }
        if (!value) return '';
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? value : date.toLocaleString('vi-VN');
    }

    function ensureStyles() {
        if (document.getElementById('admin-notification-styles')) return;

        const style = document.createElement('style');
        style.id = 'admin-notification-styles';
        style.textContent = `
            .admin-notification-widget {
                position: relative;
                display: inline-flex;
                align-items: center;
                margin-right: 10px;
                z-index: 10000;
            }
            .admin-notification-button {
                position: relative;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 40px;
                height: 40px;
                border: 1px solid rgba(15, 23, 42, 0.12);
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.82);
                color: #1f2937;
                cursor: pointer;
            }
            .admin-notification-badge {
                position: absolute;
                top: -6px;
                right: -6px;
                min-width: 18px;
                height: 18px;
                padding: 0 5px;
                border-radius: 999px;
                background: #dc2626;
                color: #fff;
                font-size: 11px;
                font-weight: 700;
                line-height: 18px;
                text-align: center;
                box-shadow: 0 0 0 2px #fff;
            }
            .admin-notification-badge[hidden] {
                display: none !important;
            }
            .admin-notification-dropdown {
                position: absolute;
                top: calc(100% + 10px);
                right: 0;
                width: min(380px, calc(100vw - 32px));
                max-height: 460px;
                overflow: hidden;
                border: 1px solid rgba(15, 23, 42, 0.12);
                border-radius: 14px;
                background: #fff;
                box-shadow: 0 24px 60px rgba(15, 23, 42, 0.16);
                z-index: 10001;
            }
            .admin-notification-dropdown[hidden] {
                display: none !important;
            }
            .admin-notification-head,
            .admin-notification-foot {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                padding: 12px 14px;
                border-bottom: 1px solid rgba(15, 23, 42, 0.08);
            }
            .admin-notification-foot {
                border-top: 1px solid rgba(15, 23, 42, 0.08);
                border-bottom: 0;
            }
            .admin-notification-title {
                margin: 0;
                color: #111827;
                font-size: 15px;
                font-weight: 700;
            }
            .admin-notification-action {
                border: 0;
                background: transparent;
                color: #9b5f3c;
                font-size: 12px;
                font-weight: 700;
                cursor: pointer;
            }
            .admin-notification-list {
                max-height: 360px;
                overflow-y: auto;
            }
            .admin-notification-empty {
                padding: 28px 16px;
                color: #64748b;
                text-align: center;
            }
            .admin-notification-item {
                width: 100%;
                display: block;
                border: 0;
                border-bottom: 1px solid rgba(15, 23, 42, 0.08);
                background: #fff;
                padding: 12px 14px;
                text-align: left;
            }
            .admin-notification-item.is-unread {
                background: #fff7ed;
            }
            .admin-notification-item:hover {
                background: #f8fafc;
            }
            .admin-notification-item strong {
                display: block;
                margin-bottom: 4px;
                color: #111827;
                font-size: 13px;
            }
            .admin-notification-item p {
                margin: 0 0 6px;
                color: #475569;
                font-size: 12px;
                line-height: 1.45;
            }
            .admin-notification-meta {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                color: #64748b;
                font-size: 11px;
            }
            .admin-notification-open {
                width: 100%;
                border: 0;
                background: transparent;
                padding: 0;
                color: inherit;
                text-align: left;
                cursor: pointer;
            }
            .admin-notification-read-one {
                margin-top: 8px;
                border: 1px solid rgba(155, 95, 60, 0.25);
                border-radius: 999px;
                background: #fff;
                color: #9b5f3c;
                font-size: 11px;
                font-weight: 700;
                padding: 4px 10px;
                cursor: pointer;
            }
        `;
        document.head.appendChild(style);
    }

    function createWidget() {
        if (document.querySelector('[data-admin-notification-widget]')) return;

        ensureStyles();
        const widget = document.createElement('div');
        widget.className = 'admin-notification-widget';
        widget.setAttribute('data-admin-notification-widget', 'true');
        widget.innerHTML = `
            <button class="admin-notification-button" type="button" aria-label="Thông báo" data-admin-notification-toggle>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 7h18s-3 0-3-7"></path>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
                <span class="admin-notification-badge" data-admin-notification-badge hidden>0</span>
            </button>
            <div class="admin-notification-dropdown" data-admin-notification-dropdown hidden>
                <div class="admin-notification-head">
                    <h3 class="admin-notification-title">Thông báo</h3>
                    <button class="admin-notification-action" type="button" data-admin-notification-read-all>Đánh dấu tất cả đã đọc</button>
                </div>
                <div class="admin-notification-list" data-admin-notification-list>
                    <div class="admin-notification-empty">Đang tải thông báo...</div>
                </div>
            </div>
        `;

        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle && themeToggle.parentElement) {
            themeToggle.parentElement.insertBefore(widget, themeToggle);
        } else {
            widget.style.position = 'fixed';
            widget.style.top = '18px';
            widget.style.right = '70px';
            document.body.appendChild(widget);
        }
    }

    function renderBadge() {
        const badge = document.querySelector('[data-admin-notification-badge]');
        if (!badge) return;

        const value = Number(state.unreadCount || 0);
        badge.textContent = value > 99 ? '99+' : String(value);
        badge.hidden = value <= 0;
    }

    function renderList() {
        const list = document.querySelector('[data-admin-notification-list]');
        if (!list) return;

        if (!state.items.length) {
            list.innerHTML = '<div class="admin-notification-empty">Chưa có thông báo.</div>';
            return;
        }

        list.innerHTML = state.items.map((item) => {
            const notificationId = idThongBao(item);
            const rentalId = idDonThue(item);
            const customerName = item.ten_khach_hang || item.customer_name || '';
            const unread = isUnread(item);
            return `
                <article class="admin-notification-item ${unread ? 'is-unread' : ''}" data-admin-notification-id="${escapeHtml(notificationId)}" data-rental-id="${escapeHtml(rentalId || '')}">
                    <button class="admin-notification-open" type="button" data-admin-notification-open>
                        <strong>${escapeHtml(item.tieu_de || item.title || 'Thông báo')}</strong>
                        <p>${escapeHtml(item.noi_dung || item.content || '')}</p>
                        <span class="admin-notification-meta">
                            ${rentalId ? `<span>Đơn #${escapeHtml(rentalId)}</span>` : ''}
                            ${customerName ? `<span>${escapeHtml(customerName)}</span>` : ''}
                            <span>${escapeHtml(timeText(item.ngay_tao || item.created_at))}</span>
                            <span>${unread ? 'Chưa đọc' : 'Đã đọc'}</span>
                        </span>
                    </button>
                    ${unread ? '<button class="admin-notification-read-one" type="button" data-admin-notification-read-one>Đánh dấu đã đọc</button>' : ''}
                </article>
            `;
        }).join('');
    }

    async function loadNotifications(silent = false) {
        if (!window.AdminApi || !AdminApi.getToken()) return;
        try {
            const countData = await AdminApi.apiFetch('/notifications/unread-count');
            state.unreadCount = Number(
                countData?.dem_thong_bao_chua_doc
                ?? countData?.unread_count
                ?? countData?.count
                ?? 0
            );
            const items = await AdminApi.apiFetch('/notifications');
            state.items = Array.isArray(items) ? items : (items?.items || items?.danh_sach || []);
            renderBadge();
            renderList();
        } catch (error) {
            console.warn(error.message || error);
            if (!silent) {
                const list = document.querySelector('[data-admin-notification-list]');
                if (list) list.innerHTML = '<div class="admin-notification-empty">Không thể tải thông báo.</div>';
            }
        }
    }

    async function markRead(notificationId) {
        if (!notificationId) return;
        await AdminApi.apiFetch(`/notifications/${encodeURIComponent(notificationId)}/read`, { method: 'PUT' });
    }

    async function markAllRead() {
        await AdminApi.apiFetch('/notifications/read-all', { method: 'PUT' });
        await loadNotifications(true);
    }

    function toggleDropdown() {
        const dropdown = document.querySelector('[data-admin-notification-dropdown]');
        if (!dropdown) return;

        state.open = dropdown.hidden;
        dropdown.hidden = !state.open;
        if (state.open) {
            loadNotifications(true);
        }
    }

    async function handleClick(event) {
        const readAllButton = event.target.closest('[data-admin-notification-read-all]');
        const readOneButton = event.target.closest('[data-admin-notification-read-one]');
        const toggle = event.target.closest('[data-admin-notification-toggle]');
        const openButton = event.target.closest('[data-admin-notification-open]');
        const item = event.target.closest('[data-admin-notification-id]');

        if (readAllButton) {
            event.preventDefault();
            await markAllRead();
            return;
        }

        if (readOneButton && item) {
            event.preventDefault();
            await markRead(item.dataset.adminNotificationId);
            await loadNotifications(true);
            return;
        }

        if (toggle) {
            event.preventDefault();
            toggleDropdown();
            return;
        }

        if (openButton && item) {
            event.preventDefault();
            const notificationId = item.dataset.adminNotificationId;
            const rentalId = item.dataset.rentalId;
            try {
                await markRead(notificationId);
            } catch (error) {
                console.warn(error.message || error);
            }
            if (rentalId) {
                window.location.href = `don_thue.html?id=${encodeURIComponent(rentalId)}`;
            } else {
                await loadNotifications(true);
            }
            return;
        }

        if (!event.target.closest('[data-admin-notification-widget]')) {
            const dropdown = document.querySelector('[data-admin-notification-dropdown]');
            if (dropdown) {
                dropdown.hidden = true;
                state.open = false;
            }
        }
    }

    function init() {
        if (!window.AdminApi || !AdminApi.getToken()) return;
        createWidget();
        document.addEventListener('click', handleClick);
        loadNotifications();
        state.timer = window.setInterval(() => loadNotifications(true), POLL_INTERVAL_MS);
        window.addEventListener('beforeunload', () => {
            if (state.timer) window.clearInterval(state.timer);
        });
    }

    window.SunlensAdminNotifications = {
        refresh: loadNotifications,
        markAllRead,
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
