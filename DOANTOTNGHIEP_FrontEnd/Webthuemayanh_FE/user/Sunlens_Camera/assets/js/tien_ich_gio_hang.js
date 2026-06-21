(function () {
    'use strict';

    const API_ORIGIN = (window.SUNLENS_API_ORIGIN || 'http://127.0.0.1:8000').replace(/\/+$/, '');
    const API_BASE = (window.SUNLENS_API_BASE_URL || `${API_ORIGIN}/api/v1`).replace(/\/+$/, '');
    const CART_API_PATH = '/cart';
    const RENTAL_API_PATH = '/rentals';
    const NO_IMAGE = './assets/images/no-image.png';
    const productCache = new Map();

    function getAuthToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
    }

    function clearAuthTokens() {
        [
            'access_token',
            'refresh_token',
            'token_type',
            'admin_account',
            'user_account',
            'user_customer',
        ].forEach(function (key) {
            localStorage.removeItem(key);
            sessionStorage.removeItem(key);
        });
    }

    function loginUrl() {
        const current = `${window.location.pathname}${window.location.search}`;
        return `dang_nhap.html?next=${encodeURIComponent(current)}`;
    }

    function redirectToLogin() {
        window.location.href = loginUrl();
    }

    function emptyCartResponse() {
        return {
            danh_sach: [],
            tong_san_pham: 0,
            tong_so_ngay_thue: 0,
            tong_tien_thue: 0,
        };
    }

    function isPlainObject(value) {
        return value && typeof value === 'object' && !Array.isArray(value);
    }

    async function readApiResponse(response) {
        if (response.status === 204) return null;

        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            return response.json();
        }

        return response.text();
    }

    function apiError(data, statusCode) {
        if (isPlainObject(data)) {
            const detail = data.detail || data.message || data.error;
            if (Array.isArray(detail)) {
                return detail.map(function (item) {
                    if (item && typeof item === 'object') {
                        const field = Array.isArray(item.loc)
                            ? item.loc.filter(function (part) { return part !== 'body'; }).join('.')
                            : '';
                        const message = item.msg || item.message || 'Dữ liệu không hợp lệ';
                        if (item.type === 'missing' || /field required/i.test(message)) {
                            return field ? `Thiếu trường: ${field}` : 'Thiếu trường bắt buộc';
                        }
                        return field ? `${field}: ${message}` : message;
                    }
                    return String(item);
                }).join('\n');
            }
            if (detail) return detail;
        }

        if (typeof data === 'string' && data.trim()) {
            return data.trim();
        }

        return `API lỗi ${statusCode}`;
    }

    async function apiRequest(path, options = {}) {
        const token = getAuthToken();
        const auth = options.auth !== false;
        const redirectOnUnauthorized = options.redirectOnUnauthorized !== false;
        const requestMethod = String(options.method || 'GET').toUpperCase();
        const isRentalCreate = path === RENTAL_API_PATH && requestMethod === 'POST';

        if (auth && !token) {
            const error = new Error('Bạn cần đăng nhập để tiếp tục.');
            error.status = 401;
            if (redirectOnUnauthorized) {
                redirectToLogin();
            }
            throw error;
        }

        const headers = new Headers(options.headers || {});
        let body = options.body;

        if (auth) {
            headers.set('Authorization', `Bearer ${token}`);
        }

        if (body && !(body instanceof FormData) && typeof body !== 'string') {
            headers.set('Content-Type', 'application/json');
            body = JSON.stringify(body);
        }

        let response;
        const requestUrl = `${API_BASE}${path}`;
        const fetchOptions = { ...options };
        delete fetchOptions.auth;
        delete fetchOptions.redirectOnUnauthorized;
        delete fetchOptions.body;

        if (isRentalCreate) {
            console.log('Rental API Endpoint:', requestUrl);
            console.log('Rental Payload:', options.body);
            console.log(JSON.stringify(options.body, null, 2));
        }

        try {
            response = await fetch(requestUrl, {
                ...fetchOptions,
                headers,
                body,
            });
        } catch (error) {
            console.error(isRentalCreate ? 'Rental API Error:' : 'API Network Error:', error);
            const causeMessage = error && error.message ? ` Chi tiết trình duyệt: ${error.message}.` : '';
            const networkError = new Error(`Không kết nối được API ${requestUrl}.${causeMessage} Vui lòng kiểm tra backend FastAPI và cấu hình CORS.`);
            networkError.status = 0;
            networkError.cause = error;
            networkError.method = requestMethod;
            networkError.url = requestUrl;
            throw networkError;
        }
        const data = await readApiResponse(response);

        if (isRentalCreate) {
            console.log('Rental API Response:', {
                url: requestUrl,
                status: response.status,
                body: data,
            });
        }

        if (response.status === 401) {
            clearAuthTokens();
            if (redirectOnUnauthorized) {
                redirectToLogin();
            }
            const error = new Error('Phiên đăng nhập đã hết hạn.');
            error.status = 401;
            throw error;
        }

        if (!response.ok) {
            const errorMessage = apiError(data, response.status);
            const error = new Error(
                response.status === 422
                    ? `Dữ liệu đơn thuê không hợp lệ: ${errorMessage}`
                    : `HTTP ${response.status}: ${errorMessage}`
            );
            error.status = response.status;
            error.method = requestMethod;
            error.url = requestUrl;
            error.response = data;
            console.error(isRentalCreate ? 'Rental API Error:' : 'API Error:', {
                url: requestUrl,
                method: requestMethod,
                status: response.status,
                response: data,
            });
            throw error;
        }

        return data;
    }

    function normalizeCartResponse(data) {
        if (!isPlainObject(data)) {
            return emptyCartResponse();
        }

        const items = Array.isArray(data.danh_sach) ? data.danh_sach : (Array.isArray(data.items) ? data.items : []);
        return {
            items,
            danh_sach: items,
            tong_san_pham: Number(data.tong_san_pham ?? items.reduce(function (total, item) {
                return total + itemQuantity(item);
            }, 0)) || 0,
            tong_so_ngay_thue: Number(data.tong_so_ngay_thue ?? items.reduce(function (total, item) {
                return total + Number(item.so_ngay_thue || 0);
            }, 0)) || 0,
            tong_tien_thue: Number(data.tong_tien_thue ?? items.reduce(function (total, item) {
                return total + Number(item.thanh_tien || 0);
            }, 0)) || 0,
        };
    }

    async function taiGioHang(options = {}) {
        // Giỏ hàng đã chuyển sang API, không đọc dữ liệu từ localStorage nữa.
        if (!getAuthToken()) {
            if (options.redirectOnUnauthorized === true) {
                const error = new Error('Bạn cần đăng nhập để xem giỏ hàng.');
                error.status = 401;
                redirectToLogin();
                throw error;
            }
            return emptyCartResponse();
        }

        const data = await apiRequest(CART_API_PATH, {
            method: 'GET',
            redirectOnUnauthorized: options.redirectOnUnauthorized === true,
        });
        return normalizeCartResponse(data);
    }

    function itemQuantity(item) {
        return Math.max(1, Number(item && (item.so_luong || item.quantity) || 1) || 1);
    }

    function cartCount(cartData) {
        return normalizeCartResponse(cartData).tong_san_pham;
    }

    function ensureCartBadge(link, count) {
        const iconWrap = link.querySelector('.position-relative') || link;
        let badge = iconWrap.querySelector('#cart-count, .cart-count, .badge');

        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-success cart-count';
            iconWrap.appendChild(badge);
        }

        badge.classList.add('cart-count');
        if (!document.getElementById('cart-count')) {
            badge.id = 'cart-count';
        }
        badge.textContent = String(count);
        badge.style.display = count > 0 ? '' : 'none';
    }

    function renderCartCount(count) {
        const counters = document.querySelectorAll('#cart-count, .cart-count, #cartCount, #cartCountMobile');

        counters.forEach(function (counter) {
            counter.textContent = String(count);
            counter.style.display = count > 0 ? '' : 'none';
        });

        document.querySelectorAll('a[href="gio_hang.html"]').forEach(function (link) {
            if (link.querySelector('.bi-cart')) {
                ensureCartBadge(link, count);
            }
        });
    }

    async function updateCartCount(cartData) {
        if (cartData) {
            renderCartCount(cartCount(cartData));
            return cartCount(cartData);
        }

        if (!getAuthToken()) {
            renderCartCount(0);
            return 0;
        }

        try {
            const data = await taiGioHang({ redirectOnUnauthorized: false });
            const count = cartCount(data);
            renderCartCount(count);
            return count;
        } catch (error) {
            console.warn(error.message || error);
            renderCartCount(0);
            return 0;
        }
    }

    function toDateValue(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function addDays(date, days) {
        const nextDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        nextDate.setDate(nextDate.getDate() + days);
        return nextDate;
    }

    function todayValue() {
        return toDateValue(new Date());
    }

    function addDaysValue(dateValue, days) {
        const date = new Date(`${normalizeDateValue(dateValue) || todayValue()}T00:00:00`);
        if (Number.isNaN(date.getTime())) return todayValue();
        return toDateValue(addDays(date, days));
    }

    function defaultRentalDates() {
        const startDate = addDays(new Date(), 1);
        const endDate = addDays(startDate, 3);

        return {
            ngay_nhan: toDateValue(startDate),
            ngay_tra: toDateValue(endDate),
        };
    }

    function normalizeDateValue(value) {
        if (!value) return '';

        const textValue = String(value).trim();
        if (/^\d{4}-\d{2}-\d{2}$/.test(textValue)) return textValue;

        const date = new Date(textValue);
        if (Number.isNaN(date.getTime())) return '';

        return toDateValue(date);
    }

    function inputValue(root, selectors) {
        for (const selector of selectors) {
            const input = root.querySelector(selector);
            if (input && input.value) {
                return input.value;
            }
        }

        return '';
    }

    function normalizeRentalDates(rentalDates) {
        const defaults = defaultRentalDates();
        const nextDates = rentalDates || {};

        return {
            ngay_nhan: normalizeDateValue(nextDates.ngay_nhan || nextDates.startDate) || defaults.ngay_nhan,
            ngay_tra: normalizeDateValue(nextDates.ngay_tra || nextDates.endDate) || defaults.ngay_tra,
        };
    }

    function rentalDatesFromButton(button) {
        const root = button.closest('form') || button.closest('.product-detail') || button.closest('.card') || document;
        const dates = normalizeRentalDates({
            ngay_nhan: button.dataset.ngayNhan
                || button.dataset.startDate
                || inputValue(root, [
                    '[name="ngay_nhan"]',
                    '[name="start_date"]',
                    '#ngay_nhan',
                    '#rental-start',
                    '.ngay-nhan',
                    '.rental-start',
                ]),
            ngay_tra: button.dataset.ngayTra
                || button.dataset.endDate
                || inputValue(root, [
                    '[name="ngay_tra"]',
                    '[name="end_date"]',
                    '#ngay_tra',
                    '#rental-end',
                    '.ngay-tra',
                    '.rental-end',
                ]),
        });
        dates.so_luong = Math.max(1, Number(
            button.dataset.soLuong
                || button.dataset.quantity
                || inputValue(root, [
                    '[name="so_luong"]',
                    '[name="quantity"]',
                    '#detail-quantity-input',
                    '.so-luong',
                    '.quantity-input',
                ])
                || 1
        ) || 1);
        return dates;
    }

    function dateErrorMessage(dates) {
        if (!dates || !dates.ngay_nhan || !dates.ngay_tra) {
            return 'Vui lòng chọn ngày nhận và ngày trả.';
        }

        const start = new Date(`${normalizeDateValue(dates.ngay_nhan)}T00:00:00`);
        const end = new Date(`${normalizeDateValue(dates.ngay_tra)}T00:00:00`);
        const today = new Date(`${todayValue()}T00:00:00`);

        if (!Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime())) {
            return 'Ngày thuê không hợp lệ.';
        }
        if (start < today) {
            return 'Ngày nhận không được nhỏ hơn ngày hiện tại.';
        }
        if (end <= start) {
            return 'Ngày trả phải lớn hơn ngày nhận.';
        }
        return '';
    }

    function dateRangeIsValid(dates) {
        return !dateErrorMessage(dates);
    }

    function validateRentalDates(rentalDates) {
        const dates = normalizeRentalDates(rentalDates);
        const message = dateErrorMessage(dates);
        if (message) {
            throw new Error(message);
        }
        return dates;
    }

    function normalizeImagePath(path) {
        if (!path) return NO_IMAGE;

        const value = String(path).trim();
        if (!value) return NO_IMAGE;
        if (/^(https?:|data:|blob:)/i.test(value)) return value;
        if (value.startsWith('/')) return `${API_ORIGIN}${value}`;
        if (value.startsWith('./') || value.startsWith('../')) return value;
        if (value.startsWith('assets/')) return `./${value}`;
        return value;
    }

    function firstImage(product) {
        const imageValue = product.hinh_anh
            || product.anh_thiet_bi
            || product.image
            || product.image_url
            || '';

        if (Array.isArray(imageValue)) {
            return normalizeImagePath(imageValue[0]);
        }

        if (typeof imageValue === 'string') {
            const trimmedValue = imageValue.trim();

            if (trimmedValue.startsWith('[')) {
                try {
                    const images = JSON.parse(trimmedValue);
                    if (Array.isArray(images) && images.length) {
                        return normalizeImagePath(images[0]);
                    }
                } catch (error) {
                    console.warn('Không đọc được ảnh sản phẩm.', error);
                }
            }

            return normalizeImagePath(trimmedValue);
        }

        return NO_IMAGE;
    }

    function categoryName(product) {
        return product.ten_danh_muc
            || (product.category && product.category.ten_danh_muc)
            || 'Chưa phân loại';
    }

    function productId(product) {
        return product && (product.Id_thiet_bi || product.id_thiet_bi || product.id);
    }

    function setProducts(products) {
        if (!Array.isArray(products)) return;

        products.forEach(function (product) {
            const id = productId(product);
            if (id !== undefined && id !== null) {
                productCache.set(String(id), product);
            }
        });
    }

    function showLoginRequired() {
        alert('Vui lòng đăng nhập để thêm vào giỏ hàng.');
        redirectToLogin();
    }

    async function addToCart(payload) {
        if (!getAuthToken()) {
            showLoginRequired();
            return null;
        }

        const dates = validateRentalDates(payload);

        // Thêm giỏ hàng bằng API thật thay cho localStorage.
        const data = await apiRequest(CART_API_PATH, {
            method: 'POST',
            body: {
                Id_thiet_bi: Number(payload.Id_thiet_bi || payload.id_thiet_bi) || payload.Id_thiet_bi || payload.id_thiet_bi,
                so_luong: Number(payload.so_luong || 1) || 1,
                ngay_nhan: dates.ngay_nhan,
                ngay_tra: dates.ngay_tra,
            },
        });

        await updateCartCount();
        return data;
    }

    async function addProduct(product, rentalDates) {
        if (!product) return null;

        const id = productId(product);
        if (!id) return null;

        const normalizedRentalDates = normalizeRentalDates(rentalDates);
        const item = await addToCart({
            Id_thiet_bi: id,
            so_luong: Math.max(1, Number((rentalDates && rentalDates.so_luong) || product.so_luong_dat || product.quantity || 1) || 1),
            ...normalizedRentalDates,
        });
        if (!item) return null;

        showToast('Đã thêm sản phẩm vào giỏ hàng');
        return item;
    }

    function addProductById(id, rentalDates) {
        const cachedProduct = productCache.get(String(id));
        return addProduct(cachedProduct || { id_thiet_bi: id }, rentalDates);
    }

    async function updateCartItem(cartItemId, payload) {
        const dates = validateRentalDates(payload);

        // Cập nhật giỏ hàng bằng API thật thay cho localStorage.
        const data = await apiRequest(`${CART_API_PATH}/${encodeURIComponent(cartItemId)}`, {
            method: 'PUT',
            body: {
                so_luong: Number(payload.so_luong || 1) || 1,
                ngay_nhan: dates.ngay_nhan,
                ngay_tra: dates.ngay_tra,
            },
        });

        await updateCartCount();
        return data;
    }

    async function deleteCartItem(cartItemId) {
        // Xóa một dòng giỏ hàng bằng API thật thay cho localStorage.
        await apiRequest(`${CART_API_PATH}/${encodeURIComponent(cartItemId)}`, {
            method: 'DELETE',
        });
        await updateCartCount();
    }

    async function clearCart() {
        // Xóa toàn bộ giỏ hàng bằng API thật thay cho localStorage.
        await apiRequest(CART_API_PATH, {
            method: 'DELETE',
        });
        await updateCartCount(emptyCartResponse());
    }

    function formatCurrency(value) {
        return `${Number(value || 0).toLocaleString('vi-VN')}đ`;
    }

    function formatDate(value) {
        if (!value) return '';
        const dateValue = String(value).slice(0, 10);
        const parts = dateValue.split('-');
        if (parts.length !== 3) return value;
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }

    function toastContainer() {
        let container = document.getElementById('cart-toast-container');
        if (container) return container;

        container = document.createElement('div');
        container.id = 'cart-toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1080';
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
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        container.appendChild(toastElement);

        if (window.bootstrap && window.bootstrap.Toast) {
            const toast = new window.bootstrap.Toast(toastElement, { delay: 1800 });
            toast.show();
            toastElement.addEventListener('hidden.bs.toast', function () {
                toastElement.remove();
            });
            return;
        }

        setTimeout(function () {
            toastElement.remove();
        }, 1800);
    }

    function bindAddToCartButtons(scope) {
        const root = scope || document;

        root.querySelectorAll('.add-to-cart').forEach(function (button) {
            if (button.dataset.cartBound === 'true') return;

            button.dataset.cartBound = 'true';
            button.addEventListener('click', async function (event) {
                event.preventDefault();
                const id = button.dataset.productId || button.getAttribute('data-id');
                if (!id) return;

                const originalText = button.textContent;
                button.classList.add('disabled');
                button.setAttribute('aria-disabled', 'true');

                try {
                    await addProductById(id, rentalDatesFromButton(button));
                } catch (error) {
                    console.error(error);
                    showToast(error.message || 'Không thêm được sản phẩm vào giỏ hàng.', 'danger');
                } finally {
                    button.classList.remove('disabled');
                    button.removeAttribute('aria-disabled');
                    button.textContent = originalText;
                }
            });
        });
    }

    window.SunlensCart = {
        API_ORIGIN,
        API_BASE,
        RENTAL_API_PATH,
        getAuthToken,
        apiRequest,
        taiGioHang,
        addToCart,
        updateCartItem,
        deleteCartItem,
        clearCart,
        formatCurrency,
        formatDate,
        itemQuantity,
        cartCount,
        emptyCartResponse,
        todayValue,
        addDaysValue,
        defaultRentalDates,
        normalizeRentalDates,
        dateErrorMessage,
        dateRangeIsValid,
        validateRentalDates,
        normalizeCartResponse,
        updateCartCount,
        setProducts,
        addProduct,
        addProductById,
        bindAddToCartButtons,
        showToast,
        normalizeImagePath,
        firstImage,
        categoryName,
    };

    document.addEventListener('DOMContentLoaded', function () {
        updateCartCount();
        bindAddToCartButtons(document);
    });
})();

