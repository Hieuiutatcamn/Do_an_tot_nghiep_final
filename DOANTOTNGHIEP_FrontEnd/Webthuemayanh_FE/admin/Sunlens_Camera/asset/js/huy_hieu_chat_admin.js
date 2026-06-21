(function () {
    'use strict';

    const BADGE_POLL_INTERVAL_MS = 10000;
    let timer = null;

    function hienThiHuyHieu(count) {
        const value = Number(count || 0);
        document.querySelectorAll('[data-admin-chat-waiting-badge]').forEach((badge) => {
            badge.textContent = value > 0 ? String(value) : '';
            badge.hidden = value <= 0;
            badge.style.display = value > 0 ? 'inline-flex' : 'none';
        });
    }

    function normalizeStatus(status) {
        const value = String(status || '').trim().toUpperCase();
        return {
            WAITING_STAFF: 'WAITING_STAFF',
            CHO_NHAN_VIEN: 'WAITING_STAFF',
            IN_PROGRESS: 'IN_PROGRESS',
            NHAN_VIEN_DANG_XU_LY: 'IN_PROGRESS',
            CLOSED: 'CLOSED',
            DA_DONG: 'CLOSED',
        }[value] || value;
    }

    function isWaitingForStaff(conversation) {
        return Boolean(conversation?.can_nhan_vien ?? conversation?.need_staff)
            || Number(conversation?.unread_customer_count || conversation?.so_tin_nhan_khach_chua_doc || 0) > 0
            || normalizeStatus(conversation?.trang_thai || conversation?.status) === 'WAITING_STAFF';
    }

    function laySoTinNhanMoiTuPhanHoi(response) {
        const explicitCount = response?.unread_message_count
            ?? response?.unreadMessageCount
            ?? response?.waiting_count
            ?? response?.waitingCount
            ?? response?.need_staff_count
            ?? response?.needStaffCount;
        if (explicitCount !== undefined && explicitCount !== null) {
            return Number(explicitCount || 0);
        }

        const items = Array.isArray(response)
            ? response
            : Array.isArray(response?.items)
                ? response.items
                : Array.isArray(response?.conversations)
                    ? response.conversations
                    : [];
        return items.filter(isWaitingForStaff).length;
    }

    function discountNavHtml(isActive) {
        return `
            <a href="ma_giam_gia.html" class="nav-link${isActive ? ' active' : ''}">
                <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20.59 13.41 12 22l-9-9V4h9l8.59 8.59a2 2 0 0 1 0 2.82z"/>
                    <line x1="7" y1="7" x2="7.01" y2="7"/>
                    <path d="m9 15 6-6"/>
                    <path d="M9.5 9.5h.01"/>
                    <path d="M14.5 14.5h.01"/>
                </svg>
                Mã giảm giá
            </a>
        `;
    }

    function ensureDiscountNavLink() {
        const isDiscountPage = window.location.pathname.toLowerCase().endsWith('/ma_giam_gia.html');
        const existing = document.querySelector('a[href="ma_giam_gia.html"]');
        if (existing) {
            if (isDiscountPage) {
                document.querySelectorAll('.nav-menu .nav-link.active').forEach((link) => {
                    if (link !== existing) link.classList.remove('active');
                });
                existing.classList.add('active');
            }
            return;
        }

        const li = document.createElement('li');
        li.className = 'nav-item';
        li.setAttribute('data-admin-discounts-nav', 'true');
        li.innerHTML = discountNavHtml(isDiscountPage);

        const ordersItem = document.querySelector('.nav-menu a[href="don_thue.html"]')?.closest('.nav-item');
        if (ordersItem) {
            ordersItem.insertAdjacentElement('afterend', li);
            return;
        }

        const mainList = document.querySelector('.nav-menu .nav-section ul');
        if (mainList) {
            mainList.appendChild(li);
        }
    }

    async function taiHuyHieuChat() {
        if (!window.AdminApi || !AdminApi.getToken()) return;
        try {
            const response = await AdminApi.apiFetch('/admin/chat/conversations');
            hienThiHuyHieu(laySoTinNhanMoiTuPhanHoi(response));
        } catch (error) {
            console.warn(error);
            hienThiHuyHieu(0);
        }
    }

    function init() {
        ensureDiscountNavLink();
        if (!document.querySelector('[data-admin-chat-waiting-badge]')) return;
        taiHuyHieuChat();
        timer = setInterval(taiHuyHieuChat, BADGE_POLL_INTERVAL_MS);
        window.addEventListener('beforeunload', () => {
            if (timer) clearInterval(timer);
        });
    }

    document.addEventListener('DOMContentLoaded', init);
})();
