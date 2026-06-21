(function () {
    'use strict';

    const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';
    // Chatbot AI chay tren n8n (webhook). Workflow phai duoc ACTIVATE trong n8n.
    // Khi test trong editor n8n (chua active): doi thanh .../webhook-test/chat
    const AI_API_URL = 'http://127.0.0.1:5678/webhook/chat';
    const AI_CONVERSATION_STORAGE_KEY = 'sunlens_ai_conversation_id';
    const AI_HISTORY_STORAGE_KEY = 'sunlens_ai_history';
    const POLLING_INTERVAL_MS = 3000;
    const STAFF_HANDOFF_MESSAGE = 'Nhân viên đã tiếp nhận cuộc trò chuyện của bạn. Tôi sẽ hỗ trợ anh/chị ngay bây giờ.';
    const WAITING_STAFF_MESSAGE = 'Yêu cầu của anh/chị cần nhân viên SunLens hỗ trợ trực tiếp. Mình đã chuyển cuộc trò chuyện này cho nhân viên và sẽ giữ toàn bộ lịch sử tư vấn tại đây.';
    const STAFF_KEYWORDS = [
        'khiếu nại',
        'khieu nai',
        'hoàn tiền',
        'hoan tien',
        'refund',
        'hỏng thiết bị',
        'hong thiet bi',
        'thiết bị hỏng',
        'thiet bi hong',
        'mất thiết bị',
        'mat thiet bi',
        'thiết bị mất',
        'thiet bi mat',
        'tranh chấp',
        'tranh chap',
        'yêu cầu đặc biệt',
        'yeu cau dac biet',
    ];
    let databaseChatAvailable = true;

    let widget = null;
    let panel = null;
    let body = null;
    let footer = null;
    let input = null;
    let title = null;
    let statusText = null;
    let backButton = null;
    let sendButton = null;
    let currentMode = null;
    // Loai ticket + tom tat do AI (n8n) phan loai, dung khi escalate sang nhan vien
    let pendingTicketCategory = null;
    let pendingTicketSummary = null;
    // Lich su chat AI [{role:'user'|'ai', text}] - khach vang lai luu localStorage, da dang nhap luu DB
    let aiHistory = [];
    let currentConversationId = null;
    let currentView = 'menu';
    let pollingTimer = null;
    const chatViews = {};
    const chatState = {
        AI: {
            conversationId: localStorage.getItem(AI_CONVERSATION_STORAGE_KEY) || null,
            initialized: false,
            loading: false,
            closed: false,
            waitingStaff: false,
            staffControlled: false,
            conversation: null,
            renderedMessageIds: '',
            title: 'SunLens AI Assistant',
            status: 'Tư vấn sản phẩm, giá thuê và gợi ý thiết bị',
        },
        STAFF: {
            conversationId: null,
            initialized: false,
            loading: false,
            connectionError: '',
            closed: false,
            waitingStaff: false,
            staffControlled: false,
            conversation: null,
            renderedMessageIds: '',
            title: '👨‍💼 Nhân viên SunLens',
            status: 'Đang kiểm tra nhân viên online...',
        },
    };

    function getAuthToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
    }

    function redirectToLogin() {
        window.location.href = `dang_nhap.html?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
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

    function taoThongBaoLoiApi(data, statusCode) {
        const detail = data && typeof data === 'object'
            ? (data.detail ?? data.message ?? data.error)
            : data;
        if (Array.isArray(detail)) {
            const messages = detail.map(function (item) {
                if (!item || typeof item !== 'object') return layNoiDungVanBan(item);
                const field = Array.isArray(item.loc)
                    ? item.loc.filter(function (part) { return part !== 'body'; }).join('.')
                    : '';
                const message = item.msg || item.message || item.type || 'Dữ liệu không hợp lệ';
                return field ? `${field}: ${message}` : message;
            }).filter(Boolean);
            return messages.length ? messages.join('\n') : `API lỗi ${statusCode}`;
        }
        return layNoiDungVanBan(detail) || `API lỗi ${statusCode}`;
    }

    function normalizeText(value) {
        return String(value || '')
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/đ/g, 'd')
            .replace(/Đ/g, 'D')
            .toLowerCase()
            .trim();
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

    function conversationStatus(conversation) {
        return normalizeStatus(conversation && (conversation.trang_thai || conversation.status));
    }

    function isClosedConversation(conversation) {
        return conversationStatus(conversation) === 'CLOSED';
    }

    function isWaitingForStaff(conversation) {
        return Boolean(conversation && (conversation.can_nhan_vien ?? conversation.need_staff))
            || conversationStatus(conversation) === 'WAITING_STAFF';
    }

    function isStaffControlled(conversation) {
        return String((conversation && (conversation.che_do_chat || conversation.chat_mode)) || '').toUpperCase() === 'STAFF'
            || conversationStatus(conversation) === 'IN_PROGRESS';
    }

    function staffReasonFromText(content) {
        const normalized = normalizeText(content);
        const keyword = STAFF_KEYWORDS.find(function (item) {
            return normalized.includes(normalizeText(item));
        });
        return keyword ? `AI phát hiện nội dung cần nhân viên: ${keyword}` : '';
    }

    function isConversationActiveForAI(mode) {
        const state = chatState[mode];
        if (!state || state.closed) return false;
        return !(state.waitingStaff || state.staffControlled);
    }

    async function goiApi(path, options = {}) {
        const token = getAuthToken();
        if (!token) {
            redirectToLogin();
            throw new Error('Bạn cần đăng nhập để sử dụng chat.');
        }

        const headers = new Headers(options.headers || {});
        let requestBody = options.body;
        const requestData = requestBody;
        headers.set('Authorization', `Bearer ${token}`);
        if (requestBody && !(requestBody instanceof FormData) && typeof requestBody !== 'string') {
            headers.set('Content-Type', 'application/json');
            requestBody = JSON.stringify(requestBody);
        }

        const requestUrl = `${API_BASE_URL}${path}`;
        console.log('Request:', {
            url: requestUrl,
            method: options.method || 'GET',
            body: requestData ?? null,
        });

        let response;
        try {
            response = await fetch(requestUrl, {
                ...options,
                headers,
                body: requestBody,
            });
        } catch (error) {
            console.error('API request failed:', {
                url: requestUrl,
                method: options.method || 'GET',
                error,
            });
            throw error;
        }
        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json') ? await response.json() : await response.text();
        const responseLog = {
            url: requestUrl,
            status: response.status,
            data,
        };
        if (response.ok) {
            console.log('Response:', responseLog);
        } else {
            console.error('API error response:', responseLog);
        }

        if (response.status === 401) {
            redirectToLogin();
            throw new Error('Phiên đăng nhập đã hết hạn.');
        }
        if (!response.ok) {
            const error = new Error(taoThongBaoLoiApi(data, response.status));
            error.status = response.status;
            error.response = data;
            throw error;
        }
        return data;
    }

    function normalizeAIReply(data) {
        if (typeof data === 'string') {
            return { message: data, needStaff: false, reason: '', loaiYeuCau: 'KHAC', tomTat: '' };
        }
        const message = layNoiDungVanBan(data.response
            || data.answer
            || data.reply
            || data.message
            || data.result
            || data.content
            || 'AI chưa có phản hồi.');
        return {
            message,
            needStaff: Boolean(data.need_staff || data.needStaff || data.requires_staff || data.require_staff),
            reason: data.staff_reason || data.reason || '',
            loaiYeuCau: (data.loai_yeu_cau || data.ticket_type || data.category || 'KHAC'),
            tomTat: (data.tom_tat || data.summary || ''),
        };
    }

    async function requestAIReply(message, lichSu) {
        const response = await fetch(AI_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                noi_dung_tin_nhan: message,
                lich_su: lichSu || '',
                conversation_id: chatState.AI.conversationId || null,
            }),
        });
        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json') ? await response.json() : await response.text();

        if (!response.ok) {
            const detail = typeof data === 'object' && data && (data.detail || data.message || data.error);
            throw new Error(detail || `Chatbot AI lỗi ${response.status}`);
        }

        return normalizeAIReply(data);
    }

    // ===== Lich su chat AI: khach vang lai -> localStorage, da dang nhap -> DB =====
    function mapVaiTroToRole(value) {
        return String(value || '').toUpperCase() === 'AI' ? 'ai' : 'user';
    }

    function saveGuestAIHistory() {
        try {
            localStorage.setItem(AI_HISTORY_STORAGE_KEY, JSON.stringify(aiHistory.slice(-50)));
        } catch (error) { /* localStorage loi/day -> bo qua */ }
    }

    function loadGuestAIHistory() {
        try {
            const raw = localStorage.getItem(AI_HISTORY_STORAGE_KEY);
            const arr = raw ? JSON.parse(raw) : [];
            return Array.isArray(arr) ? arr.filter(function (m) { return m && m.text; }) : [];
        } catch (error) {
            return [];
        }
    }

    async function loadAIHistory() {
        if (getAuthToken()) {
            try {
                const rows = await goiApi('/chat/ai/messages', { method: 'GET' });
                if (Array.isArray(rows)) {
                    return rows
                        .map(function (r) {
                            return { role: mapVaiTroToRole(r.vai_tro), text: layNoiDungVanBan(r.noi_dung) };
                        })
                        .filter(function (m) { return m.text; });
                }
            } catch (error) {
                console.warn('Khong tai duoc lich su AI tu DB:', error.message || error);
            }
            return [];
        }
        return loadGuestAIHistory();
    }

    function persistAIMessage(role, text) {
        if (!text) return;
        aiHistory.push({ role: role, text: text });
        if (aiHistory.length > 60) aiHistory = aiHistory.slice(-60);
        if (getAuthToken()) {
            // Da dang nhap -> luu DB (fire-and-forget, khong chan UI)
            goiApi('/chat/ai/messages', {
                method: 'POST',
                body: { vai_tro: role === 'ai' ? 'AI' : 'USER', noi_dung: text },
            }).catch(function (error) {
                console.warn('Khong luu lich su AI vao DB:', error.message || error);
            });
        } else {
            // Khach vang lai -> localStorage
            saveGuestAIHistory();
        }
    }

    function layLichSuGanDay(n) {
        return aiHistory
            .slice(-n)
            .map(function (m) { return (m.role === 'ai' ? 'AI' : 'Khách') + ': ' + m.text; })
            .join('\n');
    }

    function ticketLabel(category) {
        return {
            KHIEU_NAI: 'Khiếu nại',
            HUY_DON: 'Hủy đơn',
            HOAN_TIEN: 'Hoàn tiền',
            CAN_XAC_NHAN: 'Cần xác nhận / Đổi-trả-Bảo trì',
            KHAC: 'Hỗ trợ khác',
        }[String(category || 'KHAC').toUpperCase()] || 'Hỗ trợ khác';
    }

    function conversationIdFromResponse(data) {
        const conversation = data && (data.cuoc_tro_chuyen || data.conversation || data);
        return conversation && (
            conversation.id_cuoc_tro_chuyen
            || conversation.Id_cuoc_tro_chuyen
            || conversation.conversation_id
            || conversation.id
        );
    }

    function conversationFromResponse(data) {
        if (!data || Array.isArray(data)) return null;
        if (data.cuoc_tro_chuyen || data.conversation || data.data?.conversation) {
            return data.cuoc_tro_chuyen || data.conversation || data.data?.conversation;
        }
        if (conversationIdFromResponse(data) && (data.che_do_chat || data.chat_mode || data.trang_thai || data.status)) {
            return data;
        }
        return null;
    }

    function messageListFromResponse(data) {
        if (Array.isArray(data)) return data;
        if (data && Array.isArray(data.tin_nhan)) return data.tin_nhan;
        if (data && Array.isArray(data.danh_sach)) return data.danh_sach;
        if (data && Array.isArray(data.messages)) return data.messages;
        if (data && Array.isArray(data.items)) return data.items;
        return [];
    }

    function messageContent(message) {
        return layNoiDungVanBan(
            message && (
                message.noi_dung
                ?? message.noi_dung_tin_nhan
                ?? message.message
                ?? message.content
            )
        );
    }

    function messageKey(message, index) {
        return message?.id_tin_nhan
            || message?.id
            || message?.message_id
            || `${message?.loai_nguoi_gui || message?.sender_type || message?.role || ''}:${messageContent(message)}:${message?.ngay_tao || message?.created_at || index}`;
    }

    function updateConversationState(mode, conversation) {
        if (!mode || !chatState[mode] || !conversation) return;
        const state = chatState[mode];
        state.conversation = conversation;
        state.conversationId = conversationIdFromResponse(conversation) || state.conversationId;
        state.closed = isClosedConversation(conversation);
        state.waitingStaff = isWaitingForStaff(conversation);
        state.staffControlled = isStaffControlled(conversation);
        if (mode === 'AI' && state.conversationId) {
            localStorage.setItem(AI_CONVERSATION_STORAGE_KEY, String(state.conversationId));
        }
        syncHeaderFromConversation(mode);
        updateInputAvailability();
    }

    function updateConversationFromResponse(data, mode) {
        const conversation = conversationFromResponse(data);
        if (conversation) updateConversationState(mode, conversation);
    }

    function saveAIConversationId(conversationId) {
        chatState.AI.conversationId = conversationId || null;
        if (conversationId) {
            localStorage.setItem(AI_CONVERSATION_STORAGE_KEY, String(conversationId));
        } else {
            localStorage.removeItem(AI_CONVERSATION_STORAGE_KEY);
            chatState.AI.conversation = null;
            chatState.AI.closed = false;
            chatState.AI.waitingStaff = false;
            chatState.AI.staffControlled = false;
        }
        if (currentMode === 'AI') currentConversationId = chatState.AI.conversationId;
        updateInputAvailability();
    }

    function disableDatabaseChat(error) {
        if (error) console.warn('API lưu lịch sử chat chưa sẵn sàng:', error.message || error);
        databaseChatAvailable = false;
        saveAIConversationId(null);
    }

    async function createAIConversation() {
        return chatState.AI.conversationId;
    }

    async function getAIConversationMessages(conversationId) {
        const data = await goiApi(`/chat/messages/${encodeURIComponent(conversationId)}`, {
            method: 'GET',
        });
        updateConversationFromResponse(data, 'AI');
        return messageListFromResponse(data);
    }

    async function openAIConversation() {
        if (!databaseChatAvailable) return [];
        if (!getAuthToken()) {
            disableDatabaseChat();
            return [];
        }

        const storedConversationId = chatState.AI.conversationId;
        if (storedConversationId) {
            try {
                return await getAIConversationMessages(storedConversationId);
            } catch (error) {
                disableDatabaseChat(error);
                return [];
            }
        }

        try {
            await createAIConversation();
        } catch (error) {
            disableDatabaseChat(error);
        }
        return [];
    }

    async function saveAIMessage(senderType, content) {
        if (!databaseChatAvailable || senderType !== 'USER') return null;
        if (!getAuthToken()) {
            disableDatabaseChat();
            return null;
        }

        try {
            const data = await goiApi('/chat/send', {
                method: 'POST',
                body: {
                    chat_mode: 'AI',
                    message: content,
                },
            });
            updateConversationFromResponse(data, 'AI');
            const conversationId = conversationIdFromResponse(data);
            if (conversationId) saveAIConversationId(conversationId);
            return data;
        } catch (error) {
            disableDatabaseChat(error);
            return null;
        }
    }

    async function refreshConversation(conversationId, mode) {
        if (!conversationId || !databaseChatAvailable) return null;
        try {
            const data = await goiApi(`/chat/conversations/${encodeURIComponent(conversationId)}`, {
                method: 'GET',
            });
            updateConversationFromResponse(data, mode);
            return conversationFromResponse(data) || data;
        } catch (error) {
            if (error.status && error.status !== 404 && error.status !== 405) {
                console.warn(error.message || error);
            }
            return null;
        }
    }

    async function requestStaffForAIConversation(reason) {
        if (!databaseChatAvailable) return false;

        let conversationId = chatState.AI.conversationId;
        if (!conversationId) {
            try {
                conversationId = await createAIConversation();
            } catch (error) {
                disableDatabaseChat(error);
                return false;
            }
        }

        const payload = {
            conversation_id: conversationId ? Number(conversationId) : null,
        };

        const attempts = [
            { method: 'POST', path: '/chat/request-staff', body: payload },
        ];

        for (const attempt of attempts) {
            try {
                const data = await goiApi(attempt.path, {
                    method: attempt.method,
                    body: attempt.body,
                });
                const nextConversationId = conversationIdFromResponse(data);
                if (!nextConversationId || Number(nextConversationId) === Number(conversationId)) {
                    updateConversationFromResponse(data, 'AI');
                    chatState.AI.waitingStaff = true;
                    if (chatState.AI.conversation) {
                        chatState.AI.conversation.can_nhan_vien = true;
                        chatState.AI.conversation.trang_thai = 'WAITING_STAFF';
                    }
                    syncHeaderFromConversation('AI');
                    updateInputAvailability();
                    return true;
                }
            } catch (error) {
                if (!error.status || (error.status !== 404 && error.status !== 405)) {
                    console.warn(error.message || error);
                }
            }
        }

        chatState.AI.waitingStaff = true;
        if (chatState.AI.conversation) {
            chatState.AI.conversation.can_nhan_vien = true;
            chatState.AI.conversation.trang_thai = 'WAITING_STAFF';
        }
        syncHeaderFromConversation('AI');
        updateInputAvailability();
        return false;
    }

    async function saveUserMessageToConversation(conversationId, message, mode) {
        if (!conversationId) return null;
        const data = await goiApi('/chat/send-staff-message', {
            method: 'POST',
            body: {
                conversation_id: Number(conversationId),
                message,
            },
        });
        updateConversationFromResponse(data, mode);
        return data;
    }
    async function closeAIConversation() {
        saveAIConversationId(null);
        chatState.AI.initialized = false;
        chatState.AI.renderedMessageIds = '';

        const container = messagesContainer('AI');
        if (container) container.innerHTML = '';
    }
    function createWidget() {
        if (document.querySelector('.sunlens-chat-widget')) return;

        widget = document.createElement('div');
        widget.className = 'sunlens-chat-widget';
        widget.innerHTML = `
            <div class="sunlens-chat-panel d-none" id="sunlensChatPanel">
                <div class="sunlens-chat-header">
                    <div class="sunlens-chat-header-main">
                        <button type="button" class="sunlens-chat-back d-none" id="sunlensChatBack" aria-label="Quay lại màn hình lựa chọn">
                            <span aria-hidden="true">←</span>
                            <span>Quay lại</span>
                        </button>
                        <div class="sunlens-chat-header-copy">
                            <p class="sunlens-chat-title" id="sunlensChatTitle">SunLens Camera Hỗ Trợ</p>
                            <div class="sunlens-chat-status" id="sunlensChatStatus">Chọn kênh hỗ trợ</div>
                        </div>
                    </div>
                    <button type="button" class="sunlens-chat-close" id="sunlensChatClose" aria-label="Đóng">×</button>
                </div>
                <div class="sunlens-chat-body" id="sunlensChatBody">
                    <section class="sunlens-chat-view support-menu is-active" data-chat-view="menu">
                        <div class="sunlens-chat-selector">
                            <h3>SunLens Camera Hỗ Trợ</h3>
                            <p>Bạn muốn:</p>
                            <button type="button" class="sunlens-chat-mode-btn" data-chat-mode="AI">
                                <span class="sunlens-chat-mode-main">💬 Chat với AI</span>
                                <span class="sunlens-chat-mode-status">Tư vấn tự động 24/7</span>
                            </button>
                            <button type="button" class="sunlens-chat-mode-btn" data-chat-mode="STAFF">
                                <span class="sunlens-chat-mode-main">👨‍💼 Chat với Nhân viên</span>
                                <span class="sunlens-chat-mode-status" id="sunlensStaffStatus">Đang kiểm tra trạng thái...</span>
                            </button>
                        </div>
                    </section>
                    <section class="sunlens-chat-view chat-ai-view" data-chat-view="ai">
                        <div class="sunlens-chat-messages" id="sunlensChatMessagesAI"></div>
                    </section>
                    <section class="sunlens-chat-view chat-staff-view" data-chat-view="staff">
                        <div class="sunlens-chat-messages" id="sunlensChatMessagesSTAFF"></div>
                    </section>
                </div>
                <form class="sunlens-chat-footer d-none" id="sunlensChatForm">
                    <input class="sunlens-chat-input" id="sunlensChatInput" autocomplete="off" placeholder="Nhập tin nhắn...">
                    <button class="sunlens-chat-send" type="submit" aria-label="Gửi">➤</button>
                </form>
            </div>
            <button type="button" class="sunlens-chat-fab" id="sunlensChatFab" aria-label="Mở chat">💬</button>
        `;
        document.body.appendChild(widget);

        panel = document.getElementById('sunlensChatPanel');
        body = document.getElementById('sunlensChatBody');
        footer = document.getElementById('sunlensChatForm');
        input = document.getElementById('sunlensChatInput');
        sendButton = footer.querySelector('.sunlens-chat-send');
        title = document.getElementById('sunlensChatTitle');
        statusText = document.getElementById('sunlensChatStatus');
        backButton = document.getElementById('sunlensChatBack');
        body.querySelectorAll('[data-chat-view]').forEach(function (view) {
            chatViews[view.dataset.chatView] = view;
        });

        document.getElementById('sunlensChatFab').addEventListener('click', function () {
            panel.classList.toggle('d-none');
            if (!panel.classList.contains('d-none') && currentView === 'menu') {
                showChatModeSelector();
            }
        });
        document.getElementById('sunlensChatClose').addEventListener('click', function () {
            panel.classList.add('d-none');
        });
        backButton.addEventListener('click', showChatModeSelector);
        body.querySelector('[data-chat-mode="AI"]').addEventListener('click', showAIChat);
        body.querySelector('[data-chat-mode="STAFF"]').addEventListener('click', showStaffChat);
        footer.addEventListener('submit', function (event) {
            event.preventDefault();
            if (currentMode === 'AI') {
                guiTinNhanAi();
            } else if (currentMode === 'STAFF') {
                guiTinNhanNhanVien();
            }
        });

        showChatModeSelector();
    }

    function setHeaderForMode(mode, header, status) {
        if (mode && chatState[mode]) {
            chatState[mode].title = header;
            chatState[mode].status = status || '';
        }

        if (!mode || currentMode === mode) {
            title.textContent = header;
            statusText.textContent = status || '';
        }
    }

    function syncHeaderFromConversation(mode) {
        const state = chatState[mode];
        if (!state) return;

        if (state.closed) {
            setHeaderForMode(mode, mode === 'STAFF' ? '👨‍💼 Nhân viên SunLens' : '🤖 SunLens AI Assistant', '🔴 Cuộc trò chuyện đã đóng');
            return;
        }

        if (state.staffControlled) {
            setHeaderForMode(mode, '👨‍💼 Nhân viên SunLens', '🔵 Nhân viên đang xử lý');
            return;
        }

        if (state.waitingStaff) {
            setHeaderForMode(mode, '👨‍💼 Nhân viên SunLens', '🟡 Đang chờ nhân viên hỗ trợ');
            return;
        }

        if (mode === 'AI') {
            setHeaderForMode(mode, '🤖 SunLens AI Assistant', '🟢 AI đang tư vấn');
        }
    }

    function updateInputAvailability() {
        if (!input || !sendButton) return;
        if (!currentMode) {
            input.disabled = false;
            sendButton.disabled = false;
            input.placeholder = 'Nhập tin nhắn...';
            return;
        }

        const state = chatState[currentMode];
        const missingStaffConversation = currentMode === 'STAFF' && !state?.conversationId;
        const disabled = !state || state.loading || state.closed || missingStaffConversation;
        input.disabled = disabled;
        sendButton.disabled = disabled;

        if (state && state.closed) {
            input.placeholder = 'Cuộc trò chuyện đã đóng.';
        } else if (missingStaffConversation && state.connectionError) {
            input.placeholder = 'Kết nối lỗi. Hãy quay lại và thử lại.';
        } else if (missingStaffConversation) {
            input.placeholder = 'Chưa kết nối được cuộc trò chuyện.';
        } else if (state && (state.waitingStaff || state.staffControlled)) {
            input.placeholder = 'Nhắn cho nhân viên SunLens...';
        } else {
            input.placeholder = 'Nhập tin nhắn...';
        }
    }

    function switchView(nextView) {
        if (!chatViews[nextView]) return;

        Object.keys(chatViews).forEach(function (viewName) {
            chatViews[viewName].classList.toggle('is-active', viewName === nextView);
        });

        currentView = nextView;
        currentMode = nextView === 'ai' ? 'AI' : nextView === 'staff' ? 'STAFF' : null;
        currentConversationId = currentMode ? chatState[currentMode].conversationId : null;

        backButton.classList.toggle('d-none', nextView === 'menu');
        footer.classList.toggle('d-none', nextView === 'menu');
        body.scrollTop = nextView === 'menu' ? 0 : body.scrollHeight;

        if (!currentMode) {
            title.textContent = 'SunLens Camera Hỗ Trợ';
            statusText.textContent = 'Bạn muốn:';
            input.disabled = false;
            if (sendButton) sendButton.disabled = false;
            return;
        }

        const state = chatState[currentMode];
        title.textContent = state.title;
        statusText.textContent = state.status;
        updateInputAvailability();

        window.setTimeout(function () {
            if (currentView === nextView && !input.disabled) input.focus();
        }, 220);
    }

    function showChatModeSelector() {
        stopPolling();
        switchView('menu');
        loadStaffStatusForSelector();
    }

    async function loadStaffStatusForSelector() {
        const staffStatus = document.getElementById('sunlensStaffStatus');
        if (!staffStatus) return;
        try {
            const response = await fetch(`${API_BASE_URL}/chat/staff-status`);
            if (!response.ok) throw new Error('Cannot load staff status');
            const data = await response.json();
            const isOnline = Boolean(data.staff_online ?? data.online ?? data.nhan_vien_truc_tuyen);
            staffStatus.textContent = isOnline ? 'Đang có nhân viên online' : 'Nhân viên hiện offline, hệ thống sẽ tạo ticket';
            staffStatus.classList.toggle('online', isOnline);
            staffStatus.classList.toggle('offline', !isOnline);
        } catch (error) {
            console.warn(error.message || error);
            staffStatus.textContent = 'Không kiểm tra được trạng thái nhân viên';
            staffStatus.classList.add('offline');
        }
    }

    async function showAIChat() {
        stopPolling();
        switchView('ai');

        const state = chatState.AI;
        if (state.initialized) {
            updateInputAvailability();
            if (currentMode === 'AI' && !input.disabled) input.focus();
            return;
        }

        // Chat AI qua n8n. Lich su: khach vang lai -> localStorage, da dang nhap -> DB.
        state.initialized = true;
        state.loading = true;
        updateInputAvailability();
        try {
            aiHistory = await loadAIHistory();
        } catch (error) {
            aiHistory = [];
        }
        if (aiHistory.length) {
            aiHistory.forEach(function (m) {
                if (m.role === 'ai') renderAIMessage(m.text, 'AI');
                else renderCustomerMessage(m.text, 'AI');
            });
        } else {
            renderAIMessage('Xin chào! Mình là trợ lý AI của SunLens. Bạn cần tư vấn máy ảnh, lens, flycam, giá thuê hay khuyến mãi?', 'AI');
        }
        state.loading = false;
        updateInputAvailability();
        if (currentMode === 'AI' && !input.disabled) input.focus();
    }

    async function showStaffChat() {
        stopPolling();

        if (chatState.AI.conversationId && !chatState.AI.closed) {
            await showAIChat();
            if (chatState.AI.closed) {
                saveAIConversationId(null);
                chatState.AI.initialized = false;
                chatState.AI.renderedMessageIds = '';
                stopPolling();
            } else {
                await requestStaffForAIConversation('Khách yêu cầu nhân viên hỗ trợ');
                if (chatState.AI.conversationId) {
                    await taiTinNhan(chatState.AI.conversationId, 'AI');
                    if (currentMode === 'AI') startConversationPolling('AI');
                }
                return;
            }
        }

        switchView('staff');

        const state = chatState.STAFF;
        if (state.initialized) {
            if (state.conversationId) startStaffPolling();
            return;
        }

        state.initialized = true;
        state.loading = true;
        state.connectionError = '';
        input.disabled = true;

        const ticketCategory = pendingTicketCategory;
        const ticketSummary = pendingTicketSummary;
        pendingTicketCategory = null;
        pendingTicketSummary = null;
        try {
            const response = await goiApi('/chat/request-staff', {
                method: 'POST',
                body: ticketCategory ? { loai_yeu_cau: ticketCategory } : {},
            });
            if (!response || response.success !== true) {
                const error = new Error(layNoiDungVanBan(response) || 'API chưa xác nhận tạo cuộc trò chuyện.');
                error.response = response;
                throw error;
            }

            updateConversationFromResponse(response, 'STAFF');
            state.conversationId = response.conversation?.id_cuoc_tro_chuyen || null;
            if (!state.conversationId) {
                const error = new Error('API không trả về mã cuộc trò chuyện.');
                error.response = response;
                throw error;
            }
            if (currentMode === 'STAFF') currentConversationId = state.conversationId;

            // Escalate tu AI: gui truoc 1 tin nhan tom tat ticket cho nhan vien (kem Ticket ID)
            if (ticketSummary) {
                const tid = response.ticket_id ? ('#' + response.ticket_id + ' ') : '';
                try {
                    await saveUserMessageToConversation(
                        state.conversationId,
                        '🎫 [Ticket ' + tid + '· ' + ticketLabel(ticketCategory) + ']\n' + ticketSummary,
                        'STAFF'
                    );
                    renderSystemMessage('Đã tạo ticket ' + (response.ticket_id ? '#' + response.ticket_id + ' ' : '') + '(' + ticketLabel(ticketCategory) + ') và gửi nội dung cho nhân viên. Bạn có thể nhắn thêm tại đây.', 'STAFF');
                } catch (e) {
                    console.warn('Khong gui duoc tom tat ticket:', e.message || e);
                }
            }

            setHeaderForMode(
                'STAFF',
                '👨‍💼 Nhân viên SunLens',
                (response.staff_online ?? response.nhan_vien_truc_tuyen) ? '🟢 Đang chat với nhân viên' : '🟡 Chờ nhân viên hỗ trợ'
            );
            if (state.conversationId) {
                await taiTinNhan(state.conversationId, 'STAFF');
                if (currentMode === 'STAFF') startStaffPolling();
            } else {
                renderSystemMessage(layNoiDungVanBan(response.message) || 'Yêu cầu của bạn đã được ghi nhận.', 'STAFF');
            }
        } catch (error) {
            console.error('Không thể tạo cuộc trò chuyện với nhân viên:', error.response || error);
            state.initialized = false;
            state.connectionError = error.message || 'Không thể kết nối máy chủ.';
            setHeaderForMode('STAFF', '👨‍💼 Nhân viên SunLens', '🔴 Kết nối thất bại');
            renderSystemMessage(`Không thể kết nối nhân viên: ${state.connectionError}`, 'STAFF');
        } finally {
            state.loading = false;
            if (currentMode === 'STAFF') {
                updateInputAvailability();
                if (!input.disabled) input.focus();
            }
        }
    }

    function messagesContainer(mode) {
        return document.getElementById(`sunlensChatMessages${mode || currentMode || ''}`);
    }

    function appendMessage(content, className, mode) {
        const container = messagesContainer(mode);
        if (!container) return;
        const text = layNoiDungVanBan(content);
        if (!text) return;
        const message = document.createElement('div');
        message.className = `sunlens-chat-message ${className}`;
        message.textContent = text;
        container.appendChild(message);
        cuonTinNhanXuongCuoi(mode);
    }

    function renderAIMessage(message, mode) {
        appendMessage(message, 'ai', mode);
    }

    function renderStaffMessage(message, mode) {
        appendMessage(message, 'staff', mode || 'STAFF');
    }

    function renderCustomerMessage(message, mode) {
        appendMessage(message, 'customer', mode);
    }

    function renderSystemMessage(message, mode) {
        appendMessage(message, 'system', mode);
    }

    function hienThiDanhSachTinNhan(messages, mode) {
        const container = messagesContainer(mode);
        const state = chatState[mode];
        if (!container || !Array.isArray(messages)) return;
        const nextIds = messages.map(function (message, index) {
            return messageKey(message, index);
        }).join(',');
        if (state && nextIds === state.renderedMessageIds) return;
        if (state) state.renderedMessageIds = nextIds;
        container.innerHTML = '';
        messages.forEach(function (message) {
            const senderType = String(message.loai_nguoi_gui || message.sender_type || message.role || '').toUpperCase();
            const content = messageContent(message);
            if (senderType === 'CUSTOMER' || senderType === 'USER') {
                renderCustomerMessage(content, mode);
            } else if (senderType === 'STAFF' || senderType === 'NHAN_VIEN') {
                renderStaffMessage(content, mode);
            } else {
                renderAIMessage(content, mode);
            }
        });
        cuonTinNhanXuongCuoi(mode);
    }

    function cuonTinNhanXuongCuoi(mode) {
        const container = messagesContainer(mode);
        if (container) container.scrollTop = container.scrollHeight;
        if (body && (!mode || currentMode === mode)) body.scrollTop = body.scrollHeight;
    }

    function showAITyping() {
        removeAITyping();
        const container = messagesContainer('AI');
        if (!container) return;
        const message = document.createElement('div');
        message.id = 'sunlensAiTyping';
        message.className = 'sunlens-chat-message ai typing';
        message.textContent = 'AI đang trả lời...';
        container.appendChild(message);
        body.scrollTop = body.scrollHeight;
    }

    function removeAITyping() {
        const typing = document.getElementById('sunlensAiTyping');
        if (typing) typing.remove();
    }

    async function guiTinNhanAi() {
        const message = input.value.trim();
        if (!message) return;
        input.value = '';
        renderCustomerMessage(message, 'AI');
        chatState.AI.loading = true;
        updateInputAvailability();

        // Lay 3 tin nhan gan nhat lam ngu canh (truoc khi them tin hien tai), roi luu tin cua khach
        const lichSu = layLichSuGanDay(3);
        persistAIMessage('user', message);

        try {
            // Goi webhook n8n kem lich su gan day -> nhan { response, need_staff, loai_yeu_cau }
            const reply = await requestAIReply(message, lichSu);
            renderAIMessage(reply.message || 'SunLens AI chưa có phản hồi.', 'AI');
            persistAIMessage('ai', reply.message || '');
            if (reply.needStaff) {
                if (getAuthToken()) {
                    // AI quyet dinh can nguoi: tao ticket + tu gui tom tat cho nhan vien
                    pendingTicketCategory = reply.loaiYeuCau || 'KHAC';
                    pendingTicketSummary = (reply.tomTat || '').toString().trim() || message;
                    renderSystemMessage('🎫 Đang tạo ticket hỗ trợ (' + ticketLabel(pendingTicketCategory) + ') và kết nối bạn với nhân viên SunLens…', 'AI');
                    await showStaffChat();
                    return;
                }
                renderSystemMessage('Yêu cầu đổi/trả hàng hoặc khiếu nại sản phẩm cần nhân viên xử lý. Bạn vui lòng ĐĂNG KÝ và ĐĂNG NHẬP để hệ thống tạo ticket và nhân viên SunLens hỗ trợ bạn nhé.', 'AI');
            }
        } catch (error) {
            renderAIMessage(error.message || 'Xin lỗi, trợ lý AI đang gặp sự cố. Vui lòng thử lại sau giây lát.', 'AI');
        } finally {
            chatState.AI.loading = false;
            if (currentMode === 'AI') {
                updateInputAvailability();
                if (!input.disabled) input.focus();
            }
        }
    }
    async function guiTinNhanNhanVien() {
        const message = input.value.trim();
        if (!message || chatState.STAFF.closed) return;
        if (!chatState.STAFF.conversationId) {
            renderSystemMessage('Chưa kết nối được cuộc trò chuyện với nhân viên.', 'STAFF');
            updateInputAvailability();
            return;
        }
        input.value = '';
        renderCustomerMessage(message, 'STAFF');
        chatState.STAFF.loading = true;
        updateInputAvailability();

        try {
            const requestData = {
                conversation_id: Number(chatState.STAFF.conversationId),
                message,
            };
            const response = await goiApi('/chat/send-staff-message', {
                method: 'POST',
                body: requestData,
            });
            updateConversationFromResponse(response, 'STAFF');
            if (response.cuoc_tro_chuyen || response.conversation) {
                const conversation = response.cuoc_tro_chuyen || response.conversation;
                chatState.STAFF.conversationId = conversation.id_cuoc_tro_chuyen;
                if (currentMode === 'STAFF') currentConversationId = chatState.STAFF.conversationId;
                setHeaderForMode(
                    'STAFF',
                    '👨‍💼 Nhân viên SunLens',
                    (response.staff_online ?? response.nhan_vien_truc_tuyen) ? '🟢 Đang chat với nhân viên' : '🟡 Chờ nhân viên hỗ trợ'
                );
            }
            if (chatState.STAFF.conversationId) {
                await taiTinNhan(chatState.STAFF.conversationId, 'STAFF');
                if (currentMode === 'STAFF') startStaffPolling();
            }
        } catch (error) {
            renderAIMessage(error.message || 'Không gửi được tin nhắn.', 'STAFF');
        } finally {
            chatState.STAFF.loading = false;
            if (currentMode === 'STAFF') {
                updateInputAvailability();
                if (!input.disabled) input.focus();
            }
        }
    }

    async function taiTinNhan(conversationId, mode) {
        if (!conversationId) return;
        const data = await goiApi(`/chat/messages/${encodeURIComponent(conversationId)}`, {
            method: 'GET',
        });
        const targetMode = mode || currentMode;
        updateConversationFromResponse(data, targetMode);
        const items = messageListFromResponse(data);
        if (targetMode === 'AI' && items.some(function (item) {
            return String(item.loai_nguoi_gui || item.sender_type || item.role || '').toUpperCase() === 'STAFF';
        })) {
            chatState.AI.staffControlled = true;
            syncHeaderFromConversation('AI');
        }
        hienThiDanhSachTinNhan(items, targetMode);
        updateInputAvailability();
    }
    function startConversationPolling(mode) {
        stopPolling();
        const state = chatState[mode];
        const conversationId = state && state.conversationId;
        if (!conversationId || currentMode !== mode) return;
        pollingTimer = window.setInterval(function () {
            taiTinNhan(conversationId, mode).catch(function (error) {
                console.warn(error.message || error);
            });
        }, POLLING_INTERVAL_MS);
    }

    function startStaffPolling() {
        startConversationPolling('STAFF');
    }

    function stopPolling() {
        if (pollingTimer) {
            window.clearInterval(pollingTimer);
            pollingTimer = null;
        }
    }

    document.addEventListener('DOMContentLoaded', createWidget);

    window.SunlensChat = {
        showChatModeSelector,
        showAIChat,
        showStaffChat,
        guiTinNhanAi,
        guiTinNhanNhanVien,
        taiTinNhan,
        hienThiDanhSachTinNhan,
        renderStaffMessage,
        renderAIMessage,
        renderCustomerMessage,
        loadStaffStatusForSelector,
        sendAIMessage: guiTinNhanAi,
        sendStaffMessage: guiTinNhanNhanVien,
        closeAIConversation,
        loadMessages: taiTinNhan,
        startStaffPolling,
        stopPolling,
    };
})();
