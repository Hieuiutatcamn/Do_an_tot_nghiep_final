(function () {
    'use strict';

    const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';
    let complaintOrderId = '';
    let complaintMode = false;

    function getQueryParam(name) {
        return new URLSearchParams(window.location.search).get(name);
    }

    function getAuthToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
    }

    function redirectToLogin() {
        const next = `${window.location.pathname}${window.location.search}`;
        window.location.href = `dang_nhap.html?next=${encodeURIComponent(next)}`;
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

    async function apiRequest(path, options = {}) {
        const token = getAuthToken();
        if (!token) {
            redirectToLogin();
            throw new Error('Bạn cần đăng nhập để gửi khiếu nại.');
        }

        const headers = new Headers(options.headers || {});
        let body = options.body;
        headers.set('Authorization', `Bearer ${token}`);
        if (body && !(body instanceof FormData) && typeof body !== 'string') {
            headers.set('Content-Type', 'application/json');
            body = JSON.stringify(body);
        }

        const response = await fetch(`${API_BASE_URL}${path}`, {
            ...options,
            headers,
            body,
        });
        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json') ? await response.json().catch(() => ({})) : await response.text();

        if (response.status === 401) {
            redirectToLogin();
            const error = new Error('Phiên đăng nhập đã hết hạn.');
            error.status = 401;
            throw error;
        }
        if (!response.ok) {
            const detail = data && typeof data === 'object' ? data.detail || data.message : data;
            if (Array.isArray(detail)) {
                const error = new Error(detail.map((item) => item.msg || item.message || JSON.stringify(item)).join('\n'));
                error.status = response.status;
                throw error;
            }
            const error = new Error(detail || `API lỗi ${response.status}`);
            error.status = response.status;
            throw error;
        }
        return data;
    }

    function extractList(data) {
        if (Array.isArray(data)) return data;
        if (data && Array.isArray(data.danh_sach)) return data.danh_sach;
        if (data && Array.isArray(data.items)) return data.items;
        if (data && Array.isArray(data.chi_tiet)) return data.chi_tiet;
        if (data && Array.isArray(data.details)) return data.details;
        if (data && Array.isArray(data.order_details)) return data.order_details;
        if (data && data.data) return extractList(data.data);
        return [];
    }

    function getDeviceObject(item) {
        return item.thiet_bi || item.device || item.product || {};
    }

    function getDeviceId(item) {
        const device = getDeviceObject(item);
        return item.Id_thiet_bi
            || item.id_thiet_bi
            || item.device_id
            || item.product_id
            || device.Id_thiet_bi
            || device.id_thiet_bi
            || device.id
            || '';
    }

    function getDeviceName(item) {
        const device = getDeviceObject(item);
        return item.ten_thiet_bi
            || item.Ten_thiet_bi
            || item.product_name
            || device.ten_thiet_bi
            || device.Ten_thiet_bi
            || device.name
            || `Thiết bị #${getDeviceId(item) || '-'}`;
    }

    async function loadOrderProductsForComplaint(orderId) {
        try {
            const order = await apiRequest(`/orders/${encodeURIComponent(orderId)}`, { method: 'GET' });
            return extractList(order);
        } catch (error) {
            if (error.status && error.status !== 404) throw error;
        }

        const details = await apiRequest(`/order-details?order_id=${encodeURIComponent(orderId)}`, { method: 'GET' });
        return extractList(details);
    }

    function renderComplaintProducts(items) {
        const select = document.getElementById('complaintProducts');
        if (!select) return;

        const unique = new Map();
        (items || []).forEach((item) => {
            const id = getDeviceId(item);
            if (!id || unique.has(String(id))) return;
            unique.set(String(id), getDeviceName(item));
        });

        if (!unique.size) {
            select.innerHTML = '<option value="">Không tìm thấy sản phẩm trong đơn hàng</option>';
            select.disabled = true;
            return;
        }

        select.disabled = false;
        select.innerHTML = Array.from(unique.entries()).map(([id, name]) => (
            `<option value="${escapeHtml(id)}">${escapeHtml(name)}</option>`
        )).join('');
    }

    function showComplaintSuccess() {
        const message = document.getElementById('contactFormMessage');
        if (message) {
            message.className = 'mb-3 small text-success fw-semibold';
            message.textContent = 'Gửi khiếu nại thành công';
        }
    }

    function showComplaintError(messageText) {
        const message = document.getElementById('contactFormMessage');
        if (message) {
            message.className = 'mb-3 small text-danger fw-semibold';
            message.textContent = messageText || 'Không thể gửi khiếu nại.';
        }
    }

    function clearComplaintMessage() {
        const message = document.getElementById('contactFormMessage');
        if (message) {
            message.className = 'mb-3 small';
            message.textContent = '';
        }
    }

    function selectedComplaintProductIds() {
        const select = document.getElementById('complaintProducts');
        if (!select) return [];
        return Array.from(select.selectedOptions)
            .map((option) => Number(option.value))
            .filter((value) => Number.isInteger(value) && value > 0);
    }

    async function submitComplaint(event) {
        if (!complaintMode) return;
        event.preventDefault();

        const ids = selectedComplaintProductIds();
        const title = (document.getElementById('complaintTitle')?.value || '').trim();
        const content = (document.getElementById('description')?.value || '').trim();
        const submitButton = document.getElementById('contactSubmitBtn');

        if (!ids.length) {
            showComplaintError('Vui lòng chọn ít nhất 1 sản phẩm khiếu nại.');
            return;
        }
        if (!title) {
            showComplaintError('Vui lòng nhập tiêu đề khiếu nại.');
            return;
        }
        if (!content) {
            showComplaintError('Vui lòng nhập mô tả khiếu nại.');
            return;
        }

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Đang gửi...';
        }
        clearComplaintMessage();

        try {
            await apiRequest('/complaints', {
                method: 'POST',
                body: {
                    id_don_thue: Number(complaintOrderId),
                    id_thiet_bi_list: ids,
                    tieu_de: title,
                    noi_dung: content,
                },
            });
            showComplaintSuccess();
            setTimeout(() => {
                window.location.href = 'don_thue_cua_toi.html';
            }, 1500);
        } catch (error) {
            console.error(error);
            showComplaintError(error.message || 'Không thể gửi khiếu nại.');
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = 'Gửi khiếu nại';
            }
        }
    }

    function hideLegacyContactField(id) {
        const field = document.getElementById(id);
        const group = field ? field.closest('.mb-4') : null;
        if (group) group.classList.add('d-none');
        if (field) {
            field.required = false;
            field.disabled = true;
        }
    }

    async function enableComplaintMode(orderId) {
        complaintMode = true;
        complaintOrderId = orderId;

        if (!getAuthToken()) {
            redirectToLogin();
            return;
        }

        const formTitle = document.getElementById('contactFormTitle');
        const pageTitle = document.querySelector('.breadcrumb-container .page-title');
        const submitButton = document.getElementById('contactSubmitBtn');
        if (formTitle) formTitle.textContent = 'Gửi khiếu nại đơn hàng';
        if (pageTitle) pageTitle.textContent = 'Gửi khiếu nại đơn hàng';
        if (submitButton) submitButton.textContent = 'Gửi khiếu nại';
        const description = document.getElementById('description');
        const descriptionLabel = document.getElementById('descriptionLabel');
        if (description) {
            description.required = true;
            description.placeholder = 'Mô tả chi tiết vấn đề bạn gặp phải...';
        }
        if (descriptionLabel) {
            descriptionLabel.innerHTML = 'Mô tả khiếu nại <span class="text-danger">*</span>';
        }

        hideLegacyContactField('fullname');
        hideLegacyContactField('email');
        hideLegacyContactField('subject');
        document.getElementById('complaintProductsGroup')?.classList.remove('d-none');
        document.getElementById('complaintTitleGroup')?.classList.remove('d-none');

        try {
            const items = await loadOrderProductsForComplaint(orderId);
            renderComplaintProducts(items);
        } catch (error) {
            console.error(error);
            showComplaintError(error.message || 'Không tải được sản phẩm trong đơn hàng.');
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        const orderId = getQueryParam('order_id');
        const form = document.getElementById('contact-form');
        if (form) form.addEventListener('submit', submitComplaint);
        if (orderId) enableComplaintMode(orderId);
    });

    window.SunlensContactComplaint = {
        getQueryParam,
        getAuthToken,
        loadOrderProductsForComplaint,
        renderComplaintProducts,
        submitComplaint,
        showComplaintSuccess,
        showComplaintError,
        clearComplaintMessage,
    };
})();
