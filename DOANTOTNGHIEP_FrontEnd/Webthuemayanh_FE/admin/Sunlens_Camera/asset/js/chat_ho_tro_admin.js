(function () {
    'use strict';

    const POLL_INTERVAL_MS = 2000;
    const STAFF_HANDOFF_MESSAGE = 'Nhân viên đã tiếp nhận cuộc trò chuyện của bạn. Tôi sẽ hỗ trợ anh/chị ngay bây giờ.';

    const state = {
        conversations: [],
        selectedConversationId: null,
        selectedConversation: null,
        conversationsTimer: null,
        messagesTimer: null,
        staffOnline: false,
        loadingMessages: false,
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

    function layNoiDungVanBan(value) {
        if (value === null || value === undefined) return '';
        if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
            return String(value);
        }
        if (Array.isArray(value)) {
            return value.map(layNoiDungVanBan).filter(Boolean).join('\n');
        }
        if (typeof value === 'object') {
            return layNoiDungVanBan(
                value.noi_dung
                ?? value.noi_dung_tin_nhan
                ?? value.message
                ?? value.content
                ?? value.detail
                ?? value.error
            );
        }
        return '';
    }

    function formatDateTime(value) {
        if (window.AdminApi && typeof AdminApi.formatDateTime === 'function') {
            return AdminApi.formatDateTime(value);
        }
        if (!value) return '-';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleString('vi-VN');
    }

    function normalizeStatus(status) {
        const value = String(status || '').trim().toUpperCase();
        return {
            AI: 'AI',
            AI_DANG_XU_LY: 'AI',
            WAITING_STAFF: 'WAITING_STAFF',
            CHO_NHAN_VIEN: 'WAITING_STAFF',
            IN_PROGRESS: 'IN_PROGRESS',
            NHAN_VIEN_DANG_XU_LY: 'IN_PROGRESS',
            CLOSED: 'CLOSED',
            DA_DONG: 'CLOSED',
        }[value] || value;
    }

    function statusText(status) {
        return {
            AI: '🟢 AI đang xử lý',
            WAITING_STAFF: '🟡 Chờ nhân viên',
            IN_PROGRESS: '🔵 Nhân viên đang xử lý',
            CLOSED: '🔴 Đã đóng',
        }[normalizeStatus(status)] || status || '-';
    }

    function statusClass(status) {
        return {
            AI: 'ai',
            WAITING_STAFF: 'waiting',
            IN_PROGRESS: 'staff',
            CLOSED: 'closed',
        }[normalizeStatus(status)] || 'ai';
    }

    function senderText(senderType) {
        return {
            USER: 'USER',
            CUSTOMER: 'USER',
            AI: 'AI',
            STAFF: 'STAFF',
        }[senderType] || senderType || '-';
    }

    function conversationId(conversation) {
        return conversation?.id_cuoc_tro_chuyen
            || conversation?.Id_cuoc_tro_chuyen
            || conversation?.conversation_id
            || conversation?.id;
    }

    function conversationStatus(conversation) {
        return normalizeStatus(conversation?.trang_thai || conversation?.status);
    }

    function isClosedConversation(conversation) {
        return conversationStatus(conversation) === 'CLOSED';
    }

    function isStaffConversation(conversation) {
        return String(conversation?.che_do_chat || conversation?.chat_mode || '').toUpperCase() === 'STAFF'
            || conversationStatus(conversation) === 'IN_PROGRESS'
            || Boolean(employeeId(conversation));
    }

    function isWaitingForStaff(conversation) {
        return Boolean(conversation?.can_nhan_vien ?? conversation?.need_staff)
            || Number(conversation?.unread_customer_count || conversation?.so_tin_nhan_khach_chua_doc || 0) > 0
            || conversationStatus(conversation) === 'WAITING_STAFF';
    }

    function canAssign(conversation) {
        return Boolean(conversation) && !isClosedConversation(conversation) && !isStaffConversation(conversation);
    }

    function canReply(conversation) {
        return Boolean(conversation) && !isClosedConversation(conversation) && isStaffConversation(conversation);
    }

    function customerName(conversation) {
        return conversation?.ten_khach_hang
            || conversation?.ten_khach_hang
            || conversation?.khach_hang
            || `Khách hàng #${conversation?.id_khach_hang || '-'}`;
    }

    function employeeName(conversation) {
        return conversation?.employee_name
            || conversation?.staff_name
            || conversation?.ten_nhan_vien
            || '';
    }

    function employeeId(conversation) {
        return conversation?.id_nhan_vien
            || conversation?.staff_id
            || conversation?.employee_id
            || null;
    }

    function updatedAt(conversation) {
        return conversation?.ngay_cap_nhat
            || conversation?.updated_at
            || conversation?.updatedAt
            || conversation?.thoi_gian_cap_nhat
            || conversation?.ngay_tao
            || conversation?.created_at
            || '';
    }

    function chatModeText(mode) {
        return String(mode || 'AI').toUpperCase() === 'STAFF' ? 'Nhân viên' : 'AI';
    }

    function layNoiDungTinNhan(message) {
        return layNoiDungVanBan(
            message?.noi_dung
            ?? message?.content
            ?? message?.message
            ?? message?.noi_dung_tin_nhan
        );
    }

    function messageCreatedAt(message) {
        return message?.ngay_tao || message?.created_at || message?.createdAt || message?.thoi_gian_gui || '';
    }

    function messageListFromResponse(response) {
        if (Array.isArray(response)) return response;
        if (Array.isArray(response?.tin_nhan)) return response.tin_nhan;
        if (Array.isArray(response?.danh_sach)) return response.danh_sach;
        if (Array.isArray(response?.messages)) return response.messages;
        if (Array.isArray(response?.items)) return response.items;
        return [];
    }

    function conversationFromResponse(response) {
        if (!response || Array.isArray(response)) return null;
        if (response.cuoc_tro_chuyen || response.conversation || response.data?.cuoc_tro_chuyen || response.data?.conversation) {
            return response.cuoc_tro_chuyen || response.conversation || response.data?.cuoc_tro_chuyen || response.data?.conversation;
        }
        if (conversationId(response) && (response.che_do_chat || response.chat_mode || response.trang_thai || response.status)) {
            return response;
        }
        return null;
    }

    function waitingCountFromItems(items) {
        return items.filter(isWaitingForStaff).length;
    }

    function normalizeConversations(response) {
        const items = Array.isArray(response)
            ? response
            : Array.isArray(response?.danh_sach)
                ? response.danh_sach
                : Array.isArray(response?.items)
                    ? response.items
                    : Array.isArray(response?.conversations)
                        ? response.conversations
                        : [];
        if (Array.isArray(response)) {
            return { items, waitingCount: waitingCountFromItems(items) };
        }
        const waitingCount = response?.unread_message_count
            ?? response?.unreadMessageCount
            ?? response?.so_luong_cho
            ?? response?.waiting_count
            ?? response?.waitingCount
            ?? response?.need_staff_count
            ?? response?.needStaffCount
            ?? waitingCountFromItems(items);
        return {
            items,
            waitingCount: Number(waitingCount || 0),
        };
    }

    function getSelectedConversation() {
        return state.conversations.find((item) => Number(conversationId(item)) === Number(state.selectedConversationId)) || state.selectedConversation;
    }

    function hienThiSoTinNhanMoi(count) {
        const value = Number(count || 0);
        const waitingCount = document.getElementById('waitingCount');
        if (waitingCount) {
            waitingCount.textContent = value > 0 ? String(value) : '';
            waitingCount.hidden = value <= 0;
            waitingCount.style.display = value > 0 ? 'inline-flex' : 'none';
        }
        document.querySelectorAll('[data-admin-chat-waiting-badge]').forEach((badge) => {
            badge.textContent = value > 0 ? String(value) : '';
            badge.hidden = value <= 0;
            badge.style.display = value > 0 ? 'inline-flex' : 'none';
        });
    }

    function renderConversations() {
        const list = document.getElementById('chatConversationList');
        if (!list) return;

        if (!state.conversations.length) {
            list.innerHTML = '<div class="admin-chat-empty">Chưa có cuộc trò chuyện nào.</div>';
            return;
        }

        list.innerHTML = state.conversations.map((conversation) => {
            const id = conversationId(conversation);
            const isActive = Number(id) === Number(state.selectedConversationId);
            const mode = chatModeText(conversation.che_do_chat || conversation.chat_mode);
            const assignedEmployee = employeeName(conversation);
            const status = conversation.trang_thai || conversation.status;
            return `
                <button class="admin-chat-conversation ${isActive ? 'is-active' : ''}" type="button" data-conversation-id="${escapeHtml(id)}">
                    <span class="admin-chat-conversation-head">
                        <span class="admin-chat-customer">${escapeHtml(customerName(conversation))}</span>
                        <span class="chat-status ${statusClass(status)}">${escapeHtml(statusText(status))}</span>
                    </span>
                    <span class="admin-chat-meta">Loại chat: ${escapeHtml(mode)} · Cập nhật ${escapeHtml(formatDateTime(updatedAt(conversation)))}</span>
                    <span class="admin-chat-meta">${assignedEmployee ? `Nhân viên: ${escapeHtml(assignedEmployee)}` : 'Chưa gán nhân viên'}</span>
                </button>
            `;
        }).join('');

        list.querySelectorAll('[data-conversation-id]').forEach((button) => {
            button.addEventListener('click', () => selectConversation(button.dataset.conversationId));
        });
    }

    function setNotice(message, type = 'info') {
        const notice = document.getElementById('chatNotice');
        if (!notice) return;
        notice.textContent = message || '';
        notice.style.color = type === 'error' ? '#dc2626' : '#64748b';
    }

    function updateDetailHeader() {
        const conversation = getSelectedConversation();
        const title = document.getElementById('chatDetailTitle');
        const subtitle = document.getElementById('chatDetailSubtitle');
        const assignBtn = document.getElementById('assignConversationBtn');
        const closeBtn = document.getElementById('closeConversationBtn');
        const input = document.getElementById('adminChatInput');
        const sendBtn = document.getElementById('adminChatSendBtn');

        if (!conversation) {
            if (title) title.textContent = 'Chọn cuộc trò chuyện';
            if (subtitle) subtitle.textContent = 'Xem tin nhắn và trả lời khách hàng';
            [assignBtn, closeBtn, input, sendBtn].forEach((el) => {
                if (el) el.disabled = true;
            });
            return;
        }

        if (title) title.textContent = customerName(conversation);
        if (subtitle) {
            const assignedEmployee = employeeName(conversation);
            const status = conversation.trang_thai || conversation.status;
            subtitle.innerHTML = `
                <span class="chat-status ${statusClass(status)}">${escapeHtml(statusText(status))}</span>
                <span> · Loại chat: ${escapeHtml(chatModeText(conversation.che_do_chat || conversation.chat_mode))}</span>
                ${assignedEmployee ? ` · ${escapeHtml(assignedEmployee)}` : ''}
            `;
        }

        const isClosed = isClosedConversation(conversation);
        const replyEnabled = canReply(conversation);
        if (assignBtn) assignBtn.disabled = !canAssign(conversation);
        if (closeBtn) closeBtn.disabled = isClosed;
        if (input) {
            input.disabled = !replyEnabled;
            input.placeholder = isClosed
                ? 'Cuộc trò chuyện đã đóng.'
                : replyEnabled
                    ? 'Nhập phản hồi cho khách hàng...'
                    : 'Bấm "Nhận xử lý" để trả lời khách hàng.';
        }
        if (sendBtn) sendBtn.disabled = !replyEnabled;
    }

    async function taiDanhSachCuocTroChuyen(silent = false) {
        try {
            const response = await AdminApi.apiFetch('/admin/chat/conversations');
            const normalized = normalizeConversations(response);
            state.conversations = normalized.items;
            hienThiSoTinNhanMoi(normalized.waitingCount);

            if (state.selectedConversationId) {
                state.selectedConversation = getSelectedConversation();
                if (!state.selectedConversation) {
                    state.selectedConversationId = null;
                    clearMessages();
                }
            }

            renderConversations();
            updateDetailHeader();
        } catch (error) {
            console.warn(error);
            if (!silent) {
                const list = document.getElementById('chatConversationList');
                if (list) list.innerHTML = '<div class="admin-chat-empty">Không thể tải cuộc trò chuyện.</div>';
                setNotice(error.message || 'Không thể tải cuộc trò chuyện.', 'error');
            }
        }
    }

    async function selectConversation(conversationId) {
        state.selectedConversationId = Number(conversationId);
        state.selectedConversation = getSelectedConversation();
        renderConversations();
        updateDetailHeader();
        setNotice('');
        await taiTinNhan();
        await taiDanhSachCuocTroChuyen(true);
        startMessagesPolling();
    }

    function clearMessages() {
        const messages = document.getElementById('chatMessageList');
        if (messages) messages.innerHTML = '<div class="admin-chat-empty">Chưa chọn cuộc trò chuyện.</div>';
        updateDetailHeader();
    }

    function hienThiDanhSachTinNhan(items) {
        const messages = document.getElementById('chatMessageList');
        if (!messages) return;

        if (!items.length) {
            messages.innerHTML = '<div class="admin-chat-empty">Chưa có tin nhắn nào.</div>';
            return;
        }

        messages.innerHTML = items.map((item) => {
            const senderType = String(item.loai_nguoi_gui || item.sender_type || item.role || '').toUpperCase();
            const className = senderType === 'STAFF' ? 'staff' : senderType === 'AI' ? 'ai' : 'customer';
            return `
                <article class="admin-chat-message ${className}">
                    <div class="admin-chat-message-meta">
                        <span>${escapeHtml(senderText(senderType))}</span>
                        <span>${escapeHtml(formatDateTime(messageCreatedAt(item)))}</span>
                    </div>
                    <div class="admin-chat-message-text">${escapeHtml(layNoiDungTinNhan(item))}</div>
                </article>
            `;
        }).join('');

        messages.scrollTop = messages.scrollHeight;
    }

    async function taiTinNhan(silent = false) {
        if (!state.selectedConversationId || state.loadingMessages) return;
        state.loadingMessages = true;
        try {
            const response = await AdminApi.apiFetch(`/admin/chat/messages/${state.selectedConversationId}`);
            const conversation = conversationFromResponse(response);
            if (conversation) {
                state.selectedConversation = conversation;
                updateDetailHeader();
            }
            hienThiDanhSachTinNhan(messageListFromResponse(response));
        } catch (error) {
            console.warn(error);
            if (!silent) {
                const messages = document.getElementById('chatMessageList');
                if (messages) messages.innerHTML = '<div class="admin-chat-empty">Không thể tải tin nhắn.</div>';
                setNotice(error.message || 'Không thể tải tin nhắn.', 'error');
            }
        } finally {
            state.loadingMessages = false;
        }
    }

    async function guiPhanHoi(event) {
        event.preventDefault();
        const input = document.getElementById('adminChatInput');
        const message = input ? input.value.trim() : '';
        if (!state.selectedConversationId || !message) return;
        if (!canReply(getSelectedConversation())) {
            setNotice('Bấm "Nhận xử lý" trước khi trả lời khách hàng.', 'error');
            updateDetailHeader();
            return;
        }

        const sendBtn = document.getElementById('adminChatSendBtn');
        if (sendBtn) sendBtn.disabled = true;
        try {
            await AdminApi.apiFetch('/admin/chat/reply', {
                method: 'POST',
                debug: true,
                body: {
                    conversation_id: state.selectedConversationId,
                    message,
                },
            });
            if (input) input.value = '';
            setNotice('');
            await taiTinNhan(true);
            await taiDanhSachCuocTroChuyen(true);
        } catch (error) {
            console.warn(error);
            setNotice(error.message || 'Không thể gửi phản hồi.', 'error');
        } finally {
            updateDetailHeader();
        }
    }

    async function nhanXuLyCuocTroChuyen() {
        if (!state.selectedConversationId) return;
        try {
            const updated = await AdminApi.apiFetch(`/admin/chat/assign/${state.selectedConversationId}`, {
                method: 'PUT',
            });
            state.selectedConversation = conversationFromResponse(updated) || updated;
            setNotice('Đã nhận xử lý cuộc trò chuyện.');
            await taiDanhSachCuocTroChuyen(true);
            await ensureStaffHandoffMessage();
            await taiTinNhan(true);
            updateDetailHeader();
        } catch (error) {
            console.warn(error);
            setNotice(error.message || 'Không thể nhận xử lý cuộc trò chuyện.', 'error');
        }
    }

    async function ensureStaffHandoffMessage() {
        if (!state.selectedConversationId) return;
        try {
            const response = await AdminApi.apiFetch(`/admin/chat/messages/${state.selectedConversationId}`);
            const items = messageListFromResponse(response);
            const hasHandoffMessage = items.some((item) => {
                const senderType = String(item.loai_nguoi_gui || item.sender_type || item.role || '').toUpperCase();
                return senderType === 'STAFF' && layNoiDungTinNhan(item).trim() === STAFF_HANDOFF_MESSAGE;
            });
            if (hasHandoffMessage) return;

            await AdminApi.apiFetch('/admin/chat/reply', {
                method: 'POST',
                debug: true,
                body: {
                    conversation_id: state.selectedConversationId,
                    message: STAFF_HANDOFF_MESSAGE,
                },
            });
        } catch (error) {
            console.warn(error);
        }
    }

    async function dongCuocTroChuyen() {
        if (!state.selectedConversationId) return;
        const ok = window.confirm('Bạn muốn đóng cuộc trò chuyện này?');
        if (!ok) return;

        try {
            const updated = await AdminApi.apiFetch(`/admin/chat/close/${state.selectedConversationId}`, {
                method: 'PUT',
            });
            state.selectedConversation = conversationFromResponse(updated) || updated;
            setNotice('Đã đóng cuộc trò chuyện.');
            await taiDanhSachCuocTroChuyen(true);
            updateDetailHeader();
        } catch (error) {
            console.warn(error);
            setNotice(error.message || 'Không thể đóng cuộc trò chuyện.', 'error');
        }
    }

    function renderOnlineButton() {
        const button = document.getElementById('staffOnlineBtn');
        if (!button) return;
        button.classList.toggle('is-offline', !state.staffOnline);
        button.textContent = state.staffOnline ? 'Online' : 'Offline';
    }

    async function capNhatTrangThaiTrucTuyen(isOnline, silent = false) {
        try {
            await AdminApi.apiFetch('/admin/staff/online', {
                method: 'PUT',
                debug: true,
                body: { is_online: Boolean(isOnline) },
            });
            state.staffOnline = Boolean(isOnline);
            renderOnlineButton();
            if (!silent) {
                setNotice(state.staffOnline ? 'Bạn đang online để nhận chat.' : 'Bạn đã chuyển offline.');
            }
        } catch (error) {
            console.warn(error);
            if (!silent) {
                setNotice(error.message || 'Không thể cập nhật trạng thái online.', 'error');
            }
            state.staffOnline = false;
            renderOnlineButton();
        }
    }

    function stopTimers() {
        if (state.conversationsTimer) {
            clearInterval(state.conversationsTimer);
            state.conversationsTimer = null;
        }
        if (state.messagesTimer) {
            clearInterval(state.messagesTimer);
            state.messagesTimer = null;
        }
    }

    function startConversationsPolling() {
        if (state.conversationsTimer) clearInterval(state.conversationsTimer);
        state.conversationsTimer = setInterval(() => taiDanhSachCuocTroChuyen(true), POLL_INTERVAL_MS);
    }

    function startMessagesPolling() {
        if (state.messagesTimer) clearInterval(state.messagesTimer);
        state.messagesTimer = setInterval(() => taiTinNhan(true), POLL_INTERVAL_MS);
    }

    function bindEvents() {
        const form = document.getElementById('adminChatForm');
        const assignBtn = document.getElementById('assignConversationBtn');
        const closeBtn = document.getElementById('closeConversationBtn');
        const onlineBtn = document.getElementById('staffOnlineBtn');

        if (form) form.addEventListener('submit', guiPhanHoi);
        if (assignBtn) assignBtn.addEventListener('click', nhanXuLyCuocTroChuyen);
        if (closeBtn) closeBtn.addEventListener('click', dongCuocTroChuyen);
        if (onlineBtn) onlineBtn.addEventListener('click', () => capNhatTrangThaiTrucTuyen(!state.staffOnline));
    }

    function sendOfflineBeacon() {
        if (!window.AdminApi || !AdminApi.getToken()) return;
        try {
            fetch(`${AdminApi.API_BASE}/admin/staff/online`, {
                method: 'PUT',
                keepalive: true,
                headers: {
                    Authorization: `Bearer ${AdminApi.getToken()}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ is_online: false }),
            });
        } catch (error) {
            console.warn(error);
        }
    }

    async function init() {
        if (!window.AdminApi || !AdminApi.requireAuth()) return;
        bindEvents();
        renderOnlineButton();

        await capNhatTrangThaiTrucTuyen(true, true);
        await taiDanhSachCuocTroChuyen();
        startConversationsPolling();

        window.addEventListener('beforeunload', () => {
            stopTimers();
            sendOfflineBeacon();
        });
    }

    document.addEventListener('DOMContentLoaded', init);

    window.AdminChat = {
        taiDanhSachCuocTroChuyen,
        taiTinNhan,
        nhanXuLyCuocTroChuyen,
        dongCuocTroChuyen,
        capNhatTrangThaiTrucTuyen,
        loadConversations: taiDanhSachCuocTroChuyen,
        loadMessages: taiTinNhan,
        assignConversation: nhanXuLyCuocTroChuyen,
        closeConversation: dongCuocTroChuyen,
        setStaffOnline: capNhatTrangThaiTrucTuyen,
    };
})();
