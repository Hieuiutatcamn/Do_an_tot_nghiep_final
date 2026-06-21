(function () {
    'use strict';

    const API_ORIGIN = 'http://127.0.0.1:8000';
    const API_BASE_URL = `${API_ORIGIN}/api/v1`;
    const AUTH_KEYS = [
        'access_token',
        'refresh_token',
        'token_type',
        'admin_account',
        'user_account',
        'user_customer',
    ];

    let danhSachDonThue = [];
    let currentOrderDetail = null;
    let selectedPaymentImageFile = null;
    let dangCapNhatDonThue = false;
    let anhChuyenKhoanMoiUrl = '';
    let dangTaiLaiSauHetHan = false;

    function getAuthToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
    }

    function clearAuthStorage() {
        AUTH_KEYS.forEach(function (key) {
            localStorage.removeItem(key);
            sessionStorage.removeItem(key);
        });
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

    async function readApiResponse(response) {
        if (response.status === 204) return null;

        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            return response.json().catch(function () {
                return {};
            });
        }

        return response.text();
    }

    function apiErrorMessage(response, data) {
        if (response.status === 404) return 'Không tìm thấy đơn hàng';
        if (response.status >= 500) return 'Có lỗi xảy ra, vui lòng thử lại';

        if (data && typeof data === 'object') {
            const detail = data.detail || data.message || data.error;
            if (Array.isArray(detail)) {
                return detail.map(function (item) {
                    return item.msg || item.message || JSON.stringify(item);
                }).join('\n');
            }
            if (detail) return detail;
        }

        if (typeof data === 'string' && data.trim()) return data.trim();
        return `API lỗi ${response.status}`;
    }

    async function apiRequest(path, options = {}) {
        const token = getAuthToken();
        if (!token) {
            redirectToLogin();
            const error = new Error('Bạn cần đăng nhập để tiếp tục.');
            error.status = 401;
            throw error;
        }

        const headers = new Headers(options.headers || {});
        let body = options.body;

        headers.set('Authorization', `Bearer ${token}`);

        if (body && !(body instanceof FormData) && typeof body !== 'string') {
            headers.set('Content-Type', 'application/json');
            body = JSON.stringify(body);
        }

        let response;
        try {
            response = await fetch(`${API_BASE_URL}${path}`, {
                ...options,
                headers,
                body,
            });
        } catch (fetchError) {
            const error = new Error('Không kết nối được backend. Vui lòng kiểm tra server FastAPI.');
            error.status = 0;
            error.cause = fetchError;
            throw error;
        }

        const data = await readApiResponse(response);

        if (response.status === 401) {
            clearAuthStorage();
            redirectToLogin();
            const error = new Error('Phiên đăng nhập đã hết hạn.');
            error.status = 401;
            throw error;
        }

        if (!response.ok) {
            const error = new Error(apiErrorMessage(response, data));
            error.status = response.status;
            throw error;
        }

        return data;
    }

    function normalizeText(value) {
        return String(value || '')
            .trim()
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/đ/g, 'd')
            .replace(/Đ/g, 'D');
    }

    function extractList(data) {
        if (Array.isArray(data)) return data;
        if (data && Array.isArray(data.danh_sach)) return data.danh_sach;
        if (data && Array.isArray(data.items)) return data.items;
        if (data && Array.isArray(data.orders)) return data.orders;
        if (data && Array.isArray(data.data)) return data.data;
        return [];
    }

    function extractOrder(data) {
        if (!data || typeof data !== 'object') return {};
        return data.order || data.don_thue || data.data || data;
    }

    function getOrderItems(order) {
        if (!order || typeof order !== 'object') return [];
        return order.items
            || order.details
            || order.order_details
            || order.order_items
            || order.chi_tiet
            || order.chi_tiet_don_thue
            || [];
    }

    function getOrderId(order) {
        return order.Id_don_thue
            || order.id_don_thue
            || order.ID_don_thue
            || order.order_id
            || order.Id_order
            || order.id
            || order.Id
            || '';
    }

    function getOrderCode(order) {
        const id = getOrderId(order);
        return order.ma_don
            || order.Ma_don
            || order.ma_don_thue
            || order.code
            || (id ? `DH${String(id).padStart(4, '0')}` : 'DH---');
    }

    function getOrderStatus(order) {
        return order.trang_thai || order.Trang_thai || order.status || '';
    }

    function getOrderCreatedDate(order) {
        return order.ngay_dat || order.Ngay_dat || order.ngay_tao || order.created_at || order.createdAt || '';
    }

    function firstDetailDate(order, field, mode) {
        const dates = getOrderItems(order)
            .map(function (item) {
                return item[field]
                    || item[field.charAt(0).toUpperCase() + field.slice(1)]
                    || item[field === 'ngay_nhan' ? 'start_date' : 'end_date'];
            })
            .filter(Boolean)
            .map(function (value) {
                return new Date(value);
            })
            .filter(function (date) {
                return !Number.isNaN(date.getTime());
            });

        if (!dates.length) return '';

        const times = dates.map(function (date) {
            return date.getTime();
        });
        const time = mode === 'max' ? Math.max.apply(null, times) : Math.min.apply(null, times);
        return new Date(time).toISOString();
    }

    function getOrderReceiveDate(order) {
        return order.ngay_nhan
            || order.Ngay_nhan
            || order.ngay_thue
            || order.start_date
            || firstDetailDate(order, 'ngay_nhan', 'min')
            || '';
    }

    function getOrderReturnDate(order) {
        return order.ngay_tra
            || order.Ngay_tra
            || order.end_date
            || firstDetailDate(order, 'ngay_tra', 'max')
            || '';
    }

    function getOrderTotal(order) {
        return order.tong_tien
            ?? order.Tong_tien
            ?? order.tong_thanh_toan
            ?? order.total_amount
            ?? order.total
            ?? 0;
    }

    function getDeviceObject(item) {
        return item.thiet_bi || item.thiet_bi || item.product || {};
    }

    function getDeviceId(item) {
        const device = getDeviceObject(item);
        return item.Id_thiet_bi
            || item.id_thiet_bi
            || item.ID_thiet_bi
            || item.thiet_bi_id
            || item.thiet_bi_id
            || item.product_id
            || device.Id_thiet_bi
            || device.id_thiet_bi
            || device.ID_thiet_bi
            || device.id
            || '';
    }

    function getDeviceName(item) {
        const device = getDeviceObject(item);
        return item.ten_thiet_bi
            || item.Ten_thiet_bi
            || item.ten_san_pham
            || item.name
            || device.ten_thiet_bi
            || device.Ten_thiet_bi
            || device.ten_san_pham
            || device.name
            || `Thiết bị #${item.Id_thiet_bi || item.id_thiet_bi || '-'}`;
    }

    function getDeviceCategory(item) {
        const device = getDeviceObject(item);
        const category = item.danh_muc
            || item.ten_danh_muc
            || item.category
            || device.danh_muc
            || device.ten_danh_muc
            || device.category
            || {};

        if (typeof category === 'string') return category;
        return category.ten_danh_muc || category.name || category.Ten_danh_muc || '-';
    }

    function pickImageValue(value) {
        if (!value) return '';

        if (Array.isArray(value)) {
            for (const item of value) {
                const image = pickImageValue(item);
                if (image) return image;
            }
            return '';
        }

        if (typeof value === 'object') {
            return pickImageValue(
                value.duong_dan
                || value.url
                || value.src
                || value.path
                || value.file_url
                || value.hinh_anh
                || value.image
            );
        }

        const text = String(value).trim();
        if (!text || text === 'null' || text === 'undefined') return '';

        const looksLikeJson = (text.startsWith('[') && text.endsWith(']'))
            || (text.startsWith('{') && text.endsWith('}'))
            || (text.startsWith('"') && text.endsWith('"'));

        if (looksLikeJson) {
            try {
                return pickImageValue(JSON.parse(text));
            } catch (error) {
                console.warn('Không đọc được dữ liệu ảnh sản phẩm.', error);
            }
        }

        return text.split(/[;,|]/).map(function (part) {
            return part.trim();
        }).find(Boolean) || '';
    }

    function getDeviceImage(item) {
        const device = getDeviceObject(item);
        const candidates = [
            item.hinh_anh,
            item.Hinh_anh,
            item.anh_thiet_bi,
            item.image,
            item.image_url,
            item.hinhAnh,
            item.url,
            item.duong_dan,
            item.images,
            item.hinh_anh_urls,
            item.hinh_anh_list,
            device.hinh_anh,
            device.Hinh_anh,
            device.anh_thiet_bi,
            device.image,
            device.image_url,
            device.hinhAnh,
            device.url,
            device.duong_dan,
            device.images,
            device.hinh_anh_urls,
            device.hinh_anh_list,
        ];

        for (const candidate of candidates) {
            const image = pickImageValue(candidate);
            if (image) return getImageUrl(image);
        }

        return '';
    }

    function getImageUrl(path) {
        if (!path) return '';

        const value = String(path).trim().replace(/\\/g, '/');
        if (!value) return '';
        if (/^(https?:|data:|blob:)/i.test(value)) return value;
        if (value.startsWith('/')) return `${API_ORIGIN}${value}`;
        if (/^(uploads|static)\//i.test(value)) return `${API_ORIGIN}/${value}`;

        const uploadIndex = value.indexOf('/uploads/');
        if (uploadIndex >= 0) return `${API_ORIGIN}${value.slice(uploadIndex)}`;

        return value;
    }

    function getPaymentImagePath(order) {
        return order.anh_chuyen_khoan
            || order.Anh_chuyen_khoan
            || order.payment_image
            || order.paymentImage
            || '';
    }

    function getPaymentMethod(order) {
        return order.phuong_thuc_thanh_toan
            || order.Phuong_thuc_thanh_toan
            || (getPaymentImagePath(order) ? 'Chuyen khoan thu cong' : '');
    }

    function getVnpayTransactionId(order) {
        return order.ma_giao_dich_vnpay
            || order.Ma_giao_dich_vnpay
            || '';
    }

    function getPaidAmount(order) {
        return Number(
            order.so_tien_da_thanh_toan
            ?? order.So_tien_da_thanh_toan
            ?? 0
        ) || 0;
    }

    function getVnpayDeadline(order) {
        return order.han_thanh_toan_vnpay
            || order.Han_thanh_toan_vnpay
            || '';
    }

    function getPaymentDate(order) {
        return order.ngay_thanh_toan
            || order.Ngay_thanh_toan
            || '';
    }

    function hasSuccessfulVnpayPayment(order) {
        return isVnpayPayment(order)
            && Boolean(getVnpayTransactionId(order))
            && getPaidAmount(order) > 0;
    }

    function isVnpayPayment(order) {
        return normalizeText(getPaymentMethod(order)) === 'vnpay';
    }

    function getCustomer(order) {
        if (!order || typeof order !== 'object') return {};
        return order.khach_hang || order.customer || {};
    }

    function getCustomerIdentityNumber(customer) {
        return customer.so_cccd || customer.cccd || customer.So_CCCD || '';
    }

    function getOrderNote(order) {
        return order.ghi_chu || order.Ghi_chu || order.note || '';
    }

    function canUpdateRentalInformation(order) {
        return normalizeText(getOrderStatus(order)) === 'da dat';
    }

    function clearTemporaryPaymentPreview() {
        if (anhChuyenKhoanMoiUrl) {
            URL.revokeObjectURL(anhChuyenKhoanMoiUrl);
            anhChuyenKhoanMoiUrl = '';
        }
    }

    function getItemPrice(item) {
        const device = getDeviceObject(item);
        return item.gia_thue
            ?? item.Gia_thue
            ?? item.gia_thue_ngay
            ?? item.price_per_day
            ?? device.gia_thue
            ?? device.Gia_thue
            ?? device.gia_thue_ngay
            ?? 0;
    }

    function getItemQuantity(item) {
        return item.so_luong ?? item.So_luong ?? item.quantity ?? 1;
    }

    function getItemRentalDays(item) {
        if (item.so_ngay_thue ?? item.So_ngay_thue ?? item.rental_days) {
            return item.so_ngay_thue ?? item.So_ngay_thue ?? item.rental_days;
        }

        const start = new Date(item.ngay_nhan || item.Ngay_nhan || item.start_date || '');
        const end = new Date(item.ngay_tra || item.Ngay_tra || item.end_date || '');
        if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return '-';

        return Math.max(1, Math.ceil((end - start) / 86400000));
    }

    function getItemTotal(item) {
        if (item.thanh_tien ?? item.Thanh_tien ?? item.total) {
            return item.thanh_tien ?? item.Thanh_tien ?? item.total;
        }

        const price = Number(getItemPrice(item));
        const quantity = Number(getItemQuantity(item));
        const days = Number(getItemRentalDays(item));
        if ([price, quantity, days].some(Number.isNaN)) return 0;

        return price * quantity * days;
    }

    function formatCurrency(value) {
        const number = Number(value || 0);
        if (Number.isNaN(number)) return escapeHtml(value);
        return `${number.toLocaleString('vi-VN')} VNĐ`;
    }

    function formatDate(value) {
        if (!value) return '-';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return escapeHtml(value);
        return date.toLocaleDateString('vi-VN');
    }

    function formatDateTime(value) {
        if (!value) return '-';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return escapeHtml(value);
        return date.toLocaleString('vi-VN');
    }

    function getStatusKey(status) {
        const text = normalizeText(status);
        if (['payment-pending', 'cho thanh toan'].includes(text)) return 'payment-pending';
        if (['confirmed', 'da xac nhan'].includes(text)) return 'confirmed';
        if (['renting', 'dang thue'].includes(text)) return 'renting';
        if (['completed', 'da thue', 'da tra', 'da tra may'].includes(text)) return 'completed';
        if (['overdue', 'qua han', 'da qua han'].includes(text)) return 'overdue';
        if (['cancelled', 'canceled', 'da huy', 'huy don', 'don da huy'].includes(text)) return 'cancelled';
        return 'pending';
    }

    function getStatusText(status) {
        return {
            'payment-pending': 'Chờ thanh toán',
            pending: 'Chờ xác nhận',
            confirmed: 'Đã xác nhận',
            renting: 'Đang thuê',
            completed: 'Đã thuê',
            overdue: 'Đã quá hạn',
            cancelled: 'Đã hủy',
        }[getStatusKey(status)] || 'Chờ xác nhận';
    }

    function getStatusBadge(status) {
        const key = getStatusKey(status);
        const className = key === 'payment-pending' ? 'pending' : key;
        return `<span class="status-badge-user status-${className}">${getStatusText(status)}</span>`;
    }

    function canCancelOrder(status) {
        return ['payment-pending', 'pending', 'confirmed'].includes(getStatusKey(status));
    }

    function canComplainOrder(status) {
        return ['confirmed', 'renting', 'completed', 'overdue'].includes(getStatusKey(status));
    }

    function renderCancelButton(order, isBlockButton) {
        if (!canCancelOrder(getOrderStatus(order))) return '';

        const id = getOrderId(order);
        if (!id) return '';

        const className = isBlockButton
            ? 'btn btn-outline-danger w-100 mt-2'
            : 'btn btn-outline-danger';

        return `
            <button type="button" class="${className}" data-order-cancel="${escapeHtml(id)}">
                Hủy đơn
            </button>
        `;
    }

    function findOrderInList(orderId) {
        const idText = String(orderId || '');
        return danhSachDonThue.find(function (order) {
            return String(getOrderId(order)) === idText || String(getOrderCode(order)) === idText;
        }) || {};
    }

    function mergeOrderData(baseOrder, detailOrder, detailItems) {
        const merged = {
            ...baseOrder,
            ...detailOrder,
        };

        if (detailItems && detailItems.length) {
            merged.chi_tiet = detailItems;
            merged.items = detailItems;
        } else if (!getOrderItems(merged).length && getOrderItems(baseOrder).length) {
            merged.items = getOrderItems(baseOrder);
        }

        return merged;
    }

    function attachDeviceData(item, deviceData) {
        if (!deviceData || typeof deviceData !== 'object') return;

        const currentDevice = getDeviceObject(item);
        const mergedDevice = {
            ...deviceData,
            ...currentDevice,
        };

        if (item.thiet_bi) {
            item.thiet_bi = mergedDevice;
        } else if (item.thiet_bi) {
            item.thiet_bi = mergedDevice;
        } else if (item.product) {
            item.product = mergedDevice;
        } else {
            item.thiet_bi = mergedDevice;
        }
    }

    async function hydrateMissingDeviceImages(order) {
        const items = getOrderItems(order);
        const deviceIds = Array.from(new Set(items
            .filter(function (item) {
                return !getDeviceImage(item) && getDeviceId(item);
            })
            .map(function (item) {
                return String(getDeviceId(item));
            })));

        if (!deviceIds.length) return order;

        const deviceEntries = await Promise.all(deviceIds.map(async function (deviceId) {
            try {
                const response = await apiRequest(`/devices/${encodeURIComponent(deviceId)}`, {
                    method: 'GET',
                });
                const device = response && typeof response === 'object'
                    ? (response.data || response.device || response.thiet_bi || response)
                    : null;
                return [deviceId, device];
            } catch (error) {
                console.warn(`Không tải được ảnh thiết bị #${deviceId}.`, error);
                return [deviceId, null];
            }
        }));

        const devicesById = new Map(deviceEntries.filter(function (entry) {
            return entry[1];
        }));

        items.forEach(function (item) {
            const deviceData = devicesById.get(String(getDeviceId(item)));
            attachDeviceData(item, deviceData);
        });

        return order;
    }

    function showState(target) {
        ['ordersLoading', 'ordersError', 'ordersEmpty', 'ordersList'].forEach(function (id) {
            const element = document.getElementById(id);
            if (element) element.classList.toggle('d-none', id !== target);
        });
    }

    function setErrorMessage(message) {
        const messageElement = document.getElementById('ordersErrorMessage');
        if (messageElement) messageElement.textContent = message || 'Có lỗi xảy ra, vui lòng thử lại';
        showState('ordersError');
    }

    function setPaymentImageMessage(message, type) {
        const messageElement = document.getElementById('paymentImageMessage');
        if (!messageElement) return;

        messageElement.textContent = message || '';
        messageElement.className = `small mt-2 fw-semibold ${type === 'success' ? 'text-success' : 'text-danger'}`;
    }

    function toastContainer() {
        let container = document.getElementById('orders-toast-container');
        if (container) return container;

        container = document.createElement('div');
        container.id = 'orders-toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '2000';
        document.body.appendChild(container);
        return container;
    }

    function showToast(message, type) {
        const container = toastContainer();
        const toastElement = document.createElement('div');
        toastElement.className = `toast align-items-center text-bg-${type === 'danger' ? 'danger' : 'success'} border-0`;
        toastElement.setAttribute('role', 'alert');
        toastElement.setAttribute('aria-live', 'assertive');
        toastElement.setAttribute('aria-atomic', 'true');
        toastElement.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${escapeHtml(message)}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        container.appendChild(toastElement);
        if (window.bootstrap && window.bootstrap.Toast) {
            const toast = new window.bootstrap.Toast(toastElement, { delay: 2200 });
            toast.show();
            toastElement.addEventListener('hidden.bs.toast', function () {
                toastElement.remove();
            });
            return;
        }

        window.setTimeout(function () {
            toastElement.remove();
        }, 2200);
    }

    async function apiRequestFirst(paths, options = {}) {
        let lastError = null;

        for (const path of paths) {
            try {
                return await apiRequest(path, options);
            } catch (error) {
                lastError = error;
                if (error.status !== 404) throw error;
            }
        }

        throw lastError || new Error('Không tìm thấy đơn hàng');
    }

    function hienThiDonThue() {
        const container = document.getElementById('ordersList');
        if (!container) return;

        if (!danhSachDonThue.length) {
            container.innerHTML = '';
            showState('ordersEmpty');
            return;
        }

        container.innerHTML = danhSachDonThue.map(function (order) {
            const id = getOrderId(order);
            const deadline = getVnpayDeadline(order);
            const deadlineRow = getStatusKey(getOrderStatus(order)) === 'payment-pending'
                && deadline
                ? `
                    <div class="order-meta-row">
                        <span>Thời gian thanh toán còn lại</span>
                        <strong data-vnpay-deadline="${escapeHtml(deadline)}">Đang tính...</strong>
                    </div>
                `
                : '';
            return `
                <div class="col-12 col-md-6 col-xl-4">
                    <article class="order-card">
                        <div class="order-card-header">
                            <div>
                                <h3 class="order-code">Mã đơn: ${escapeHtml(getOrderCode(order))}</h3>
                                <p class="order-device">Đơn thuê thiết bị</p>
                            </div>
                            ${getStatusBadge(getOrderStatus(order))}
                        </div>
                        <div class="order-meta">
                            <div class="order-meta-row">
                                <span>Ngày đặt</span>
                                <strong>${formatDate(getOrderCreatedDate(order))}</strong>
                            </div>
                            <div class="order-meta-row">
                                <span>Ngày nhận</span>
                                <strong>${formatDate(getOrderReceiveDate(order))}</strong>
                            </div>
                            <div class="order-meta-row">
                                <span>Ngày trả</span>
                                <strong>${formatDate(getOrderReturnDate(order))}</strong>
                            </div>
                            <div class="order-meta-row">
                                <span>Tổng tiền</span>
                                <strong>${formatCurrency(getOrderTotal(order))}</strong>
                            </div>
                            ${deadlineRow}
                        </div>
                        <div class="d-grid gap-2">
                            <button type="button" class="btn btn-primary w-100" data-order-detail="${escapeHtml(id)}">
                                Xem chi tiết
                            </button>
                            ${renderCancelButton(order, true)}
                        </div>
                    </article>
                </div>
            `;
        }).join('');

        showState('ordersList');
        capNhatDongHoThanhToan();
    }

    async function taiDonThue() {
        if (!getAuthToken()) {
            redirectToLogin();
            return;
        }

        showState('ordersLoading');

        try {
            const data = await apiRequestFirst([
                '/orders/my-orders',
                '/rentals/me/history?page=1&page_size=100',
                '/rentals?page=1&page_size=100',
            ], {
                method: 'GET',
            });
            danhSachDonThue = extractList(data);
            hienThiDonThue();
        } catch (error) {
            if (error.status !== 401) {
                console.error(error);
                setErrorMessage(error.message);
            }
        }
    }

    function detailBox(label, value) {
        return `
            <div class="detail-box">
                <label>${escapeHtml(label)}</label>
                <span>${value || '-'}</span>
            </div>
        `;
    }

    function hienThiThongTinKhachHang(khachHang, cheDoCapNhat) {
        const hoTen = khachHang.ho_ten || khachHang.Ho_ten || '';
        const soDienThoai = khachHang.sdt || khachHang.SDT || khachHang.so_dien_thoai || '';
        const diaChi = khachHang.dia_chi || khachHang.Dia_chi || '';
        const email = khachHang.email || khachHang.thu_dien_tu || '';
        const soCccd = getCustomerIdentityNumber(khachHang);

        if (!cheDoCapNhat) {
            return `
                <h6 class="fw-bold mb-3">Thông tin khách hàng</h6>
                <div class="order-detail-grid mb-4">
                    ${detailBox('Họ tên', escapeHtml(hoTen))}
                    ${detailBox('Số điện thoại', escapeHtml(soDienThoai))}
                    ${detailBox('Địa chỉ', escapeHtml(diaChi))}
                    ${detailBox('Email', escapeHtml(email))}
                    ${detailBox('Số CCCD', escapeHtml(soCccd))}
                </div>
            `;
        }

        return `
            <h6 class="fw-bold mb-3">Thông tin khách hàng</h6>
            <div class="rental-edit-grid mb-4">
                <div class="rental-edit-field">
                    <label for="rentalCustomerName">Họ tên <span class="text-danger">*</span></label>
                    <input type="text" class="form-control" id="rentalCustomerName" maxlength="100" value="${escapeHtml(hoTen)}">
                </div>
                <div class="rental-edit-field">
                    <label for="rentalCustomerPhone">Số điện thoại <span class="text-danger">*</span></label>
                    <input type="tel" class="form-control" id="rentalCustomerPhone" maxlength="20" value="${escapeHtml(soDienThoai)}">
                </div>
                <div class="rental-edit-field full-width">
                    <label for="rentalCustomerAddress">Địa chỉ <span class="text-danger">*</span></label>
                    <input type="text" class="form-control" id="rentalCustomerAddress" maxlength="255" value="${escapeHtml(diaChi)}">
                </div>
                <div class="rental-edit-field">
                    <label for="rentalCustomerEmail">Email</label>
                    <input type="text" class="form-control" id="rentalCustomerEmail" value="${escapeHtml(email)}" disabled>
                </div>
                <div class="rental-edit-field">
                    <label for="rentalCustomerIdentity">Số CCCD</label>
                    <input type="text" class="form-control" id="rentalCustomerIdentity" value="${escapeHtml(soCccd)}" disabled>
                </div>
            </div>
        `;
    }

    function hienThiGhiChuDonThue(donThue, cheDoCapNhat) {
        const ghiChu = getOrderNote(donThue);
        if (!cheDoCapNhat) {
            return `
                <h6 class="fw-bold mb-3">Ghi chú</h6>
                <div class="detail-box mb-4">
                    <span>${escapeHtml(ghiChu) || 'Không có ghi chú'}</span>
                </div>
            `;
        }

        return `
            <h6 class="fw-bold mb-3">Ghi chú</h6>
            <div class="rental-edit-field mb-4">
                <label for="rentalOrderNote">Nội dung ghi chú</label>
                <textarea class="form-control" id="rentalOrderNote" rows="3" maxlength="255">${escapeHtml(ghiChu)}</textarea>
            </div>
        `;
    }

    function renderOrderItems(order) {
        const items = getOrderItems(order);
        if (!items.length) {
            return '<p class="text-muted mb-0">Không có chi tiết thiết bị thuê.</p>';
        }

        return items.map(function (item) {
            const image = getDeviceImage(item);
            const name = getDeviceName(item);
            return `
                <div class="rental-item">
                    <div class="rental-thumb">
                        ${image
                            ? `<img src="${escapeHtml(image)}" alt="${escapeHtml(name)}" onerror="this.parentElement.innerHTML='<div class=&quot;rental-thumb-placeholder&quot;><i class=&quot;bi bi-camera&quot;></i></div>';">`
                            : '<div class="rental-thumb-placeholder"><i class="bi bi-camera"></i></div>'}
                    </div>
                    <div>
                        <h6>${escapeHtml(name)}</h6>
                        <div class="rental-item-meta">
                            <div>Danh mục: <strong>${escapeHtml(getDeviceCategory(item))}</strong></div>
                            <div>Giá thuê/ngày: <strong>${formatCurrency(getItemPrice(item))}</strong></div>
                            <div>Số lượng: <strong>${escapeHtml(getItemQuantity(item))}</strong></div>
                            <div>Số ngày thuê: <strong>${escapeHtml(getItemRentalDays(item))}</strong></div>
                            <div>Thành tiền: <strong>${formatCurrency(getItemTotal(item))}</strong></div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderPaymentImage(order, cheDoCapNhat) {
        if (isVnpayPayment(order)) return '';

        const orderId = getOrderId(order);
        const currentImage = getImageUrl(getPaymentImagePath(order));
        const previewImage = currentImage || '';
        const previewMarkup = previewImage
            ? `<img src="${escapeHtml(previewImage)}" alt="Ảnh chuyển khoản" class="payment-image-preview" id="paymentImagePreview">`
            : `<div class="payment-image-placeholder" id="paymentImagePlaceholder">
                    <i class="bi bi-receipt"></i>
                    <span>Chưa có ảnh chuyển khoản</span>
               </div>`;
        const selectLabel = currentImage ? 'Thay đổi ảnh' : 'Chọn ảnh chuyển khoản';
        const editActions = cheDoCapNhat
            ? `
                <div class="payment-image-actions">
                    <input type="file" id="paymentImageInput" class="d-none" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" data-payment-order-id="${escapeHtml(orderId)}">
                    <button type="button" class="btn btn-outline-primary" data-payment-select>
                        ${escapeHtml(selectLabel)}
                    </button>
                    <p class="text-muted small mb-0">Chấp nhận JPG, JPEG, PNG, WEBP. Tối đa 5MB.</p>
                    <p class="small mt-2 mb-0" id="paymentImageMessage"></p>
                </div>
            `
            : '';

        return `
            <h6 class="fw-bold mb-3">Ảnh chuyển khoản</h6>
            <div class="payment-image-panel mb-4 ${cheDoCapNhat ? '' : 'payment-image-readonly'}" data-payment-order-id="${escapeHtml(orderId)}">
                <div class="payment-image-frame">
                    ${previewMarkup}
                </div>
                ${editActions}
            </div>
        `;
    }

    function renderPaymentInformation(order) {
        const method = getPaymentMethod(order);
        const transactionId = getVnpayTransactionId(order);
        const orderId = getOrderId(order);
        const statusKey = getStatusKey(getOrderStatus(order));
        const deadline = getVnpayDeadline(order);
        const methodLabel = isVnpayPayment(order)
            ? 'VNPAY'
            : (method ? 'Chuyển khoản thủ công' : 'Chưa xác định');
        const retryButton = isVnpayPayment(order)
            && statusKey === 'payment-pending'
            ? `
                <button type="button"
                        class="btn btn-primary mb-4"
                        data-vnpay-retry="${escapeHtml(orderId)}">
                    Thanh toán lại qua VNPAY
                </button>
            `
            : '';

        return `
            <h6 class="fw-bold mb-3">Thông tin thanh toán</h6>
            <div class="order-detail-grid mb-4">
                ${detailBox('Phương thức', escapeHtml(methodLabel))}
                ${detailBox(
                    'Kết quả thanh toán',
                    hasSuccessfulVnpayPayment(order)
                        ? 'Đã thanh toán cọc'
                        : (statusKey === 'payment-pending' ? 'Chưa thanh toán' : '-')
                )}
                ${detailBox('Số tiền đã thanh toán', formatCurrency(getPaidAmount(order)))}
                ${detailBox('Mã giao dịch VNPAY', escapeHtml(transactionId || '-'))}
                ${detailBox('Ngày thanh toán', formatDateTime(getPaymentDate(order)))}
                ${detailBox(
                    'Hạn thanh toán VNPAY',
                    deadline
                        ? `<span data-vnpay-deadline="${escapeHtml(deadline)}">${formatDateTime(deadline)}</span>`
                        : '-'
                )}
            </div>
            ${retryButton}
        `;
    }

    function capNhatDongHoThanhToan() {
        const hienTai = Date.now();
        let coDonVuaHetHan = false;
        document.querySelectorAll('[data-vnpay-deadline]').forEach(function (element) {
            const deadline = new Date(element.dataset.vnpayDeadline || '');
            if (Number.isNaN(deadline.getTime())) return;
            const remaining = deadline.getTime() - hienTai;
            if (remaining <= 0) {
                element.textContent = 'Đã hết hạn';
                coDonVuaHetHan = true;
                return;
            }
            const totalSeconds = Math.ceil(remaining / 1000);
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = totalSeconds % 60;
            element.textContent = `${minutes}:${String(seconds).padStart(2, '0')}`;
        });

        if (coDonVuaHetHan && !dangTaiLaiSauHetHan) {
            dangTaiLaiSauHetHan = true;
            taiDonThue().finally(function () {
                dangTaiLaiSauHetHan = false;
            });
        }
    }

    async function thanhToanLaiVnpay(orderId, button) {
        if (!orderId || !button) return;
        const originalText = button.textContent;
        button.disabled = true;
        button.textContent = 'Đang chuyển đến VNPAY...';

        try {
            const response = await apiRequest('/thanh-toan/vnpay-tao-url', {
                method: 'POST',
                body: {
                    id_don_thue: Number(orderId),
                    so_tien: 200000,
                    noi_dung_thanh_toan: `Thanh toán cọc đơn thuê DH${String(orderId).padStart(4, '0')}`,
                },
            });
            if (!response || !response.duong_dan_thanh_toan) {
                throw new Error('Backend không trả về đường dẫn thanh toán VNPAY.');
            }
            window.location.href = response.duong_dan_thanh_toan;
        } catch (error) {
            button.disabled = false;
            button.textContent = originalText;
            window.alert(error.message || 'Không thể mở cổng thanh toán VNPAY.');
        }
    }

    function updateDetailCancelButton(order) {
        const button = document.getElementById('cancelOrderDetailBtn');
        if (!button) return;

        const orderId = order ? getOrderId(order) : '';
        const shouldShow = orderId && canCancelOrder(getOrderStatus(order));
        button.classList.toggle('d-none', !shouldShow);
        button.disabled = false;

        if (shouldShow) {
            button.dataset.orderCancel = orderId;
        } else {
            delete button.dataset.orderCancel;
        }
    }

    function updateDetailComplaintButton(order) {
        const button = document.getElementById('complaintBtn');
        if (!button) return;

        const orderId = order ? getOrderId(order) : '';
        const shouldShow = orderId && canComplainOrder(getOrderStatus(order));
        button.classList.toggle('d-none', !shouldShow);
        button.disabled = false;

        if (shouldShow) {
            button.dataset.orderComplaint = orderId;
        } else {
            delete button.dataset.orderComplaint;
        }
    }

    function updateRentalEditButtons(order, cheDoCapNhat) {
        const updateButton = document.getElementById('updateOrderInfoBtn');
        const cancelEditButton = document.getElementById('cancelOrderEditBtn');
        const saveButton = document.getElementById('saveOrderUpdateBtn');
        const canUpdate = Boolean(order && canUpdateRentalInformation(order));

        if (updateButton) {
            updateButton.classList.toggle('d-none', !canUpdate || cheDoCapNhat);
            updateButton.disabled = false;
        }
        if (cancelEditButton) {
            cancelEditButton.classList.toggle('d-none', !cheDoCapNhat);
            cancelEditButton.disabled = false;
        }
        if (saveButton) {
            saveButton.classList.toggle('d-none', !cheDoCapNhat);
            saveButton.disabled = false;
            saveButton.textContent = 'Lưu cập nhật';
        }

        updateDetailCancelButton(cheDoCapNhat ? null : order);
        updateDetailComplaintButton(cheDoCapNhat ? null : order);
    }

    function renderOrderDetail(order, cheDoCapNhat = false) {
        currentOrderDetail = order;
        dangCapNhatDonThue = Boolean(cheDoCapNhat && canUpdateRentalInformation(order));
        clearTemporaryPaymentPreview();
        selectedPaymentImageFile = null;
        const status = getOrderStatus(order);
        const customer = getCustomer(order);
        const title = document.getElementById('orderDetailModalLabel');
        const subtitle = document.getElementById('orderDetailSubtitle');
        const body = document.getElementById('orderDetailBody');

        if (title) title.textContent = `Chi tiết đơn ${getOrderCode(order)}`;
        if (subtitle) subtitle.textContent = `${getStatusText(status)} · ${formatCurrency(getOrderTotal(order))}`;

        if (!body) return;
        body.innerHTML = `
            <h6 class="fw-bold mb-3">Thông tin đơn thuê</h6>
            <div class="order-detail-grid mb-4">
                ${detailBox('Mã đơn', escapeHtml(getOrderCode(order)))}
                ${detailBox('Ngày đặt', formatDate(getOrderCreatedDate(order)))}
                ${detailBox('Ngày nhận', formatDate(getOrderReceiveDate(order)))}
                ${detailBox('Ngày trả', formatDate(getOrderReturnDate(order)))}
                ${detailBox('Trạng thái', getStatusBadge(status))}
                ${detailBox('Tổng tiền', formatCurrency(getOrderTotal(order)))}
            </div>

            ${hienThiThongTinKhachHang(customer, dangCapNhatDonThue)}
            ${hienThiGhiChuDonThue(order, dangCapNhatDonThue)}

            <h6 class="fw-bold mb-3">Danh sách thiết bị</h6>
            <div>
                ${renderOrderItems(order)}
            </div>

            ${renderPaymentInformation(order)}
            ${renderPaymentImage(order, dangCapNhatDonThue)}
            ${dangCapNhatDonThue ? '<p class="rental-update-message mb-0" id="rentalUpdateMessage"></p>' : ''}
        `;
        updateRentalEditButtons(order, dangCapNhatDonThue);
        capNhatDongHoThanhToan();
    }

    function replacePaymentPreview(src) {
        const frame = document.querySelector('.payment-image-frame');
        if (!frame) return;

        frame.innerHTML = `<img src="${escapeHtml(src)}" alt="Ảnh chuyển khoản" class="payment-image-preview" id="paymentImagePreview">`;
    }

    function restoreCurrentPaymentPreview() {
        const frame = document.querySelector('.payment-image-frame');
        if (!frame) return;
        const currentImage = getImageUrl(getPaymentImagePath(currentOrderDetail || {}));
        frame.innerHTML = currentImage
            ? `<img src="${escapeHtml(currentImage)}" alt="Ảnh chuyển khoản" class="payment-image-preview" id="paymentImagePreview">`
            : `<div class="payment-image-placeholder" id="paymentImagePlaceholder">
                    <i class="bi bi-receipt"></i>
                    <span>Chưa có ảnh chuyển khoản</span>
               </div>`;
    }

    function hienThiAnhChuyenKhoanMoi(event) {
        const input = event.target;
        const file = input.files && input.files[0];
        clearTemporaryPaymentPreview();
        selectedPaymentImageFile = null;

        if (!file) {
            restoreCurrentPaymentPreview();
            return;
        }

        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
        const allowedExtensions = /\.(jpe?g|png|webp)$/i;
        const maxSize = 5 * 1024 * 1024;

        if (!allowedTypes.includes(file.type) || !allowedExtensions.test(file.name || '')) {
            input.value = '';
            restoreCurrentPaymentPreview();
            setPaymentImageMessage('Vui lòng chọn ảnh JPG, JPEG, PNG hoặc WEBP.', 'error');
            return;
        }

        if (file.size > maxSize) {
            input.value = '';
            restoreCurrentPaymentPreview();
            setPaymentImageMessage('Ảnh chuyển khoản không được vượt quá 5MB.', 'error');
            return;
        }

        selectedPaymentImageFile = file;
        anhChuyenKhoanMoiUrl = URL.createObjectURL(file);
        replacePaymentPreview(anhChuyenKhoanMoiUrl);
        setPaymentImageMessage('', 'success');
    }

    function setRentalUpdateMessage(message, type) {
        const element = document.getElementById('rentalUpdateMessage');
        if (!element) return;
        element.textContent = message || '';
        element.className = `rental-update-message mb-0 ${type === 'error' ? 'text-danger' : 'text-success'}`;
    }

    function moCheDoCapNhatDonThue() {
        if (!currentOrderDetail || !canUpdateRentalInformation(currentOrderDetail)) return;
        renderOrderDetail(currentOrderDetail, true);
    }

    function huyCapNhatDonThue() {
        if (!currentOrderDetail) return;
        clearTemporaryPaymentPreview();
        selectedPaymentImageFile = null;
        renderOrderDetail(currentOrderDetail, false);
    }

    function kiemTraDuLieuCapNhatDonThue() {
        const hoTen = document.getElementById('rentalCustomerName')?.value.trim() || '';
        const soDienThoai = document.getElementById('rentalCustomerPhone')?.value.trim() || '';
        const diaChi = document.getElementById('rentalCustomerAddress')?.value.trim() || '';
        const ghiChu = document.getElementById('rentalOrderNote')?.value.trim() || '';

        if (!hoTen) throw new Error('Họ tên không được trống.');
        if (!soDienThoai) throw new Error('Số điện thoại không được trống.');
        if (!diaChi) throw new Error('Địa chỉ không được trống.');

        if (selectedPaymentImageFile) {
            const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
            const allowedExtensions = /\.(jpe?g|png|webp)$/i;
            if (!allowedTypes.includes(selectedPaymentImageFile.type)
                || !allowedExtensions.test(selectedPaymentImageFile.name || '')) {
                throw new Error('Vui lòng chọn ảnh JPG, JPEG, PNG hoặc WEBP.');
            }
        }

        return {
            hoTen,
            soDienThoai,
            diaChi,
            ghiChu,
        };
    }

    async function luuCapNhatDonThueNguoiDung() {
        if (!currentOrderDetail || !dangCapNhatDonThue) return;
        const orderId = getOrderId(currentOrderDetail);
        const saveButton = document.getElementById('saveOrderUpdateBtn');

        let values;
        try {
            values = kiemTraDuLieuCapNhatDonThue();
        } catch (error) {
            setRentalUpdateMessage(error.message, 'error');
            return;
        }

        if (saveButton) {
            saveButton.disabled = true;
            saveButton.textContent = 'Đang lưu...';
        }
        setRentalUpdateMessage('', 'success');

        try {
            const formData = new FormData();
            formData.append('ho_ten', values.hoTen);
            formData.append('sdt', values.soDienThoai);
            formData.append('dia_chi', values.diaChi);
            formData.append('ghi_chu', values.ghiChu);
            if (selectedPaymentImageFile) {
                formData.append('anh_chuyen_khoan', selectedPaymentImageFile);
            }

            await apiRequest(`/rentals/${encodeURIComponent(orderId)}/khach_hang_update`, {
                method: 'PUT',
                body: formData,
            });

            clearTemporaryPaymentPreview();
            selectedPaymentImageFile = null;
            dangCapNhatDonThue = false;
            await taiDonThue();
            const refreshedOrder = await loadOrderDetail(orderId);
            renderOrderDetail(refreshedOrder, false);
            showToast('Cập nhật đơn thuê thành công.', 'success');
        } catch (error) {
            if (error.status !== 401) {
                console.error(error);
                setRentalUpdateMessage(error.message || 'Không thể cập nhật đơn thuê.', 'error');
            }
        } finally {
            const currentSaveButton = document.getElementById('saveOrderUpdateBtn');
            if (currentSaveButton && dangCapNhatDonThue) {
                currentSaveButton.disabled = false;
                currentSaveButton.textContent = 'Lưu cập nhật';
            }
        }
    }

    function cancelErrorMessage(error) {
        if (error.status === 0) return 'Không kết nối được backend. Vui lòng kiểm tra server FastAPI.';
        if (error.status === 403) return 'Bạn không có quyền hủy đơn hàng này';
        if (error.status === 400) return 'Đơn hàng hiện tại không thể hủy';
        if (error.status === 404) return 'Không tìm thấy đơn hàng';
        return error.message || 'Không thể hủy đơn hàng';
    }

    function markOrderCancelledLocally(orderId) {
        const idText = String(orderId || '');
        danhSachDonThue = danhSachDonThue.map(function (order) {
            if (String(getOrderId(order)) !== idText && String(getOrderCode(order)) !== idText) {
                return order;
            }

            return {
                ...order,
                trang_thai: 'Da huy',
                Trang_thai: 'Da huy',
                status: 'Da huy',
            };
        });

        if (currentOrderDetail && (
            String(getOrderId(currentOrderDetail)) === idText
            || String(getOrderCode(currentOrderDetail)) === idText
        )) {
            currentOrderDetail = {
                ...currentOrderDetail,
                trang_thai: 'Da huy',
                Trang_thai: 'Da huy',
                status: 'Da huy',
            };
        }
    }

    async function syncOrdersAfterCancel() {
        const data = await apiRequestFirst([
            '/orders/my-orders',
            '/rentals/me/history?page=1&page_size=100',
            '/rentals?page=1&page_size=100',
        ], {
            method: 'GET',
        });
        danhSachDonThue = extractList(data);
        hienThiDonThue();
    }

    async function reloadOrdersAfterCancel(orderId) {
        const modalElement = document.getElementById('orderDetailModal');
        if (modalElement && window.bootstrap && window.bootstrap.Modal) {
            const modal = window.bootstrap.Modal.getInstance(modalElement);
            if (modal) modal.hide();
        }

        markOrderCancelledLocally(orderId);
        currentOrderDetail = null;
        updateRentalEditButtons(null, false);
        hienThiDonThue();

        try {
            await syncOrdersAfterCancel();
        } catch (error) {
            if (error.status !== 401) {
                console.warn('Đã hủy đơn nhưng chưa tải lại được danh sách đơn hàng.', error);
                showToast('Đã hủy đơn. Chưa tải lại được danh sách mới nhất.', 'danger');
            }
        }
    }

    async function cancelOrder(orderId) {
        if (!orderId) return;
        if (!window.confirm('Bạn có chắc muốn hủy đơn hàng này không?')) return;

        const cancelButtons = Array.from(document.querySelectorAll('[data-order-cancel]')).filter(function (button) {
            return String(button.dataset.orderCancel) === String(orderId);
        });
        cancelButtons.forEach(function (button) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = 'Đang hủy...';
        });

        try {
            await apiRequestFirst([
                `/orders/${encodeURIComponent(orderId)}/cancel`,
                `/rentals/${encodeURIComponent(orderId)}/cancel`,
            ], {
                method: 'PATCH',
                body: {
                    ly_do_huy: 'Khách hàng tự hủy đơn',
                },
            });

            showToast('Hủy đơn hàng thành công', 'success');
            await reloadOrdersAfterCancel(orderId);
        } catch (error) {
            if (error.status !== 401) {
                console.error(error);
                showToast(cancelErrorMessage(error), 'danger');
            }
        } finally {
            cancelButtons.forEach(function (button) {
                button.disabled = false;
                button.textContent = button.dataset.originalText || 'Hủy đơn';
                delete button.dataset.originalText;
            });
        }
    }

    async function loadOrderDetail(orderId) {
        const baseOrder = findOrderInList(orderId);
        let orderData = {};
        let detailItems = [];
        let orderError = null;

        try {
            orderData = extractOrder(await apiRequestFirst([
                `/orders/${encodeURIComponent(orderId)}`,
                `/rentals/${encodeURIComponent(orderId)}`,
            ], {
                method: 'GET',
            }));
        } catch (error) {
            orderError = error;
            if (error.status !== 404) throw error;
        }

        if (!getOrderItems(orderData).length || (orderError && orderError.status === 404)) {
            try {
                const detailResponse = await apiRequest(`/order-details?order_id=${encodeURIComponent(orderId)}`, {
                    method: 'GET',
                });
                detailItems = extractList(detailResponse);
            } catch (error) {
                if (error.status !== 404 || !Object.keys(orderData).length) {
                    throw error;
                }
            }
        }

        const mergedOrder = mergeOrderData(baseOrder, orderData, detailItems);
        return hydrateMissingDeviceImages(mergedOrder);
    }

    async function viewOrderDetail(orderId) {
        const modalElement = document.getElementById('orderDetailModal');
        const body = document.getElementById('orderDetailBody');
        const title = document.getElementById('orderDetailModalLabel');
        const subtitle = document.getElementById('orderDetailSubtitle');

        if (!modalElement || !window.bootstrap || !window.bootstrap.Modal) return;

        const modal = window.bootstrap.Modal.getOrCreateInstance(modalElement);
        if (title) title.textContent = 'Chi tiết đơn thuê';
        if (subtitle) subtitle.textContent = '';
        updateRentalEditButtons(null, false);
        if (body) {
            body.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-success mb-3" role="status"></div>
                    <p class="text-muted mb-0">Đang tải chi tiết đơn...</p>
                </div>
            `;
        }
        modal.show();

        try {
            const order = await loadOrderDetail(orderId);
            renderOrderDetail(order);
        } catch (error) {
            if (error.status === 401) return;

            console.error(error);
            if (body) {
                body.innerHTML = `
                    <div class="orders-state">
                        <div>
                            <div class="orders-state-icon">
                                <i class="bi bi-exclamation-triangle"></i>
                            </div>
                            <h5 class="mb-2">${escapeHtml(error.message || 'Có lỗi xảy ra, vui lòng thử lại')}</h5>
                        </div>
                    </div>
                `;
            }
        }
    }

    function bindEvents() {
        const retryButton = document.getElementById('retryOrdersBtn');
        const list = document.getElementById('ordersList');
        const detailBody = document.getElementById('orderDetailBody');
        const detailCancelButton = document.getElementById('cancelOrderDetailBtn');
        const complaintButton = document.getElementById('complaintBtn');
        const updateButton = document.getElementById('updateOrderInfoBtn');
        const cancelEditButton = document.getElementById('cancelOrderEditBtn');
        const saveUpdateButton = document.getElementById('saveOrderUpdateBtn');
        const modalElement = document.getElementById('orderDetailModal');

        if (retryButton) {
            retryButton.addEventListener('click', taiDonThue);
        }

        if (list) {
            list.addEventListener('click', function (event) {
                const cancelButton = event.target.closest('[data-order-cancel]');
                if (cancelButton) {
                    cancelOrder(cancelButton.dataset.orderCancel);
                    return;
                }

                const button = event.target.closest('[data-order-detail]');
                if (!button) return;
                viewOrderDetail(button.dataset.orderDetail);
            });
        }

        if (detailCancelButton) {
            detailCancelButton.addEventListener('click', function () {
                cancelOrder(detailCancelButton.dataset.orderCancel);
            });
        }

        if (complaintButton) {
            complaintButton.addEventListener('click', function () {
                const orderId = complaintButton.dataset.orderComplaint;
                if (!orderId) return;
                window.location.href = `lien_he.html?order_id=${encodeURIComponent(orderId)}`;
            });
        }

        if (updateButton) {
            updateButton.addEventListener('click', moCheDoCapNhatDonThue);
        }

        if (cancelEditButton) {
            cancelEditButton.addEventListener('click', huyCapNhatDonThue);
        }

        if (saveUpdateButton) {
            saveUpdateButton.addEventListener('click', luuCapNhatDonThueNguoiDung);
        }

        if (modalElement) {
            modalElement.addEventListener('hidden.bs.modal', function () {
                clearTemporaryPaymentPreview();
                selectedPaymentImageFile = null;
                dangCapNhatDonThue = false;
                currentOrderDetail = null;
                updateRentalEditButtons(null, false);
            });
        }

        if (detailBody) {
            detailBody.addEventListener('click', function (event) {
                const selectButton = event.target.closest('[data-payment-select]');

                if (selectButton) {
                    const input = document.getElementById('paymentImageInput');
                    if (input) input.click();
                }

                const retryVnpayButton = event.target.closest('[data-vnpay-retry]');
                if (retryVnpayButton) {
                    thanhToanLaiVnpay(
                        retryVnpayButton.dataset.vnpayRetry,
                        retryVnpayButton
                    );
                }
            });

            detailBody.addEventListener('change', function (event) {
                if (event.target && event.target.id === 'paymentImageInput') {
                    hienThiAnhChuyenKhoanMoi(event);
                }
            });
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        if (!getAuthToken()) {
            redirectToLogin();
            return;
        }

        bindEvents();
        taiDonThue();
        window.setInterval(capNhatDongHoThanhToan, 1000);
    });

    window.SunlensUserOrders = {
        getAuthToken,
        taiDonThue,
        hienThiDonThue,
        viewOrderDetail,
        renderOrderDetail,
        getStatusBadge,
        formatCurrency,
        formatDate,
        renderPaymentImage,
        hienThiThongTinKhachHang,
        hienThiAnhChuyenKhoanMoi,
        moCheDoCapNhatDonThue,
        huyCapNhatDonThue,
        luuCapNhatDonThueNguoiDung,
        kiemTraDuLieuCapNhatDonThue,
        getImageUrl,
        canCancelOrder,
        canComplainOrder,
        cancelOrder,
        renderCancelButton,
        reloadOrdersAfterCancel,
    };
})();
