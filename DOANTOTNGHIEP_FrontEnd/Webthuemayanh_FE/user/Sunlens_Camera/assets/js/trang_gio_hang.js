(function () {
    'use strict';

    const NO_IMAGE = './assets/images/no-image.png';

    let currentCart = {
        items: [],
        danh_sach: [],
        tong_san_pham: 0,
        tong_so_ngay_thue: 0,
        tong_tien_thue: 0,
    };

    function cartApi() {
        return window.SunlensCart;
    }

    function byId(id) {
        return document.getElementById(id);
    }

    function escapeHTML(value) {
        return String(value ?? '').replace(/[&<>"']/g, function (char) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;',
            }[char];
        });
    }

    function formatCurrency(value) {
        return cartApi().formatCurrency(value).replace('đ', ' VNĐ');
    }

    function formatDate(value) {
        return String(value || '').slice(0, 10);
    }

    function itemId(item) {
        return item.Id_gio_hang || item.id_gio_hang || item.Id_gio_hang;
    }

    function deviceId(item) {
        return item.Id_thiet_bi || item.id_thiet_bi || item.Id_thiet_bi;
    }

    function imagePath(path) {
        return cartApi().normalizeImagePath(path || NO_IMAGE);
    }

    function renderEmptyState(isEmpty) {
        const emptyState = byId('cart-empty');
        const tableWrap = byId('cart-table-wrap');
        const actionWrap = byId('cart-actions');
        const couponWrap = byId('cart-coupon-wrap');
        const noteWrap = byId('cart-note-wrap');

        if (emptyState) {
            emptyState.classList.toggle('d-none', !isEmpty);
            const title = emptyState.querySelector('h4');
            if (title) {
                title.textContent = 'Giỏ hàng của bạn đang trống.';
            }
        }
        if (tableWrap) tableWrap.classList.toggle('d-none', isEmpty);
        if (actionWrap) actionWrap.classList.toggle('d-none', isEmpty);
        if (couponWrap) couponWrap.classList.toggle('d-none', isEmpty);
        if (noteWrap) noteWrap.classList.toggle('d-none', isEmpty);
    }

    function todayValue() {
        return cartApi().todayValue ? cartApi().todayValue() : new Date().toISOString().slice(0, 10);
    }

    function addDaysValue(value, days) {
        if (cartApi().addDaysValue) return cartApi().addDaysValue(value, days);
        const date = new Date(`${formatDate(value) || todayValue()}T00:00:00`);
        if (Number.isNaN(date.getTime())) return todayValue();
        date.setDate(date.getDate() + days);
        return date.toISOString().slice(0, 10);
    }

    function dateErrorMessage(ngayNhan, ngayTra) {
        const dates = { ngay_nhan: formatDate(ngayNhan), ngay_tra: formatDate(ngayTra) };
        if (cartApi().dateErrorMessage) return cartApi().dateErrorMessage(dates);
        const start = new Date(`${dates.ngay_nhan}T00:00:00`);
        const end = new Date(`${dates.ngay_tra}T00:00:00`);
        const today = new Date(`${todayValue()}T00:00:00`);
        if (start < today) return 'Ngày nhận không được nhỏ hơn ngày hiện tại.';
        if (!Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime()) || end <= start) return 'Ngày trả phải lớn hơn ngày nhận.';
        return '';
    }

    function setCheckoutState(errorMessage) {
        const hasInvalidDate = Boolean(errorMessage);
        const error = byId('cart-date-error');
        const checkoutButton = byId('cart-checkout-button');

        if (error) {
            error.textContent = errorMessage || '';
            error.classList.toggle('d-none', !hasInvalidDate);
        }

        if (!checkoutButton) return;

        checkoutButton.classList.toggle('disabled', hasInvalidDate);
        checkoutButton.setAttribute('aria-disabled', hasInvalidDate ? 'true' : 'false');
        checkoutButton.tabIndex = hasInvalidDate ? -1 : 0;
    }

    function dateRangeIsValid(ngayNhan, ngayTra) {
        return !dateErrorMessage(ngayNhan, ngayTra);
    }

    function firstInvalidDateMessage(items) {
        const invalidItem = items.find(function (item) {
            return dateErrorMessage(item.ngay_nhan, item.ngay_tra);
        });
        return invalidItem ? dateErrorMessage(invalidItem.ngay_nhan, invalidItem.ngay_tra) : '';
    }

    function rowPayload(item, overrides) {
        return {
            so_luong: Number((overrides && overrides.so_luong) ?? item.so_luong ?? 1) || 1,
            ngay_nhan: (overrides && overrides.ngay_nhan) || formatDate(item.ngay_nhan),
            ngay_tra: (overrides && overrides.ngay_tra) || formatDate(item.ngay_tra),
        };
    }

    async function checkCartItemAvailability(item, payload) {
        const id = deviceId(item);
        if (!id || !payload.ngay_nhan || !payload.ngay_tra) return;

        const params = new URLSearchParams({
            ngay_nhan: payload.ngay_nhan,
            ngay_tra: payload.ngay_tra,
            so_luong: String(Number(payload.so_luong || 1) || 1),
        });
        const data = await cartApi().apiRequest(`/devices/${encodeURIComponent(id)}/availability?${params.toString()}`, {
            method: 'GET',
            auth: false,
        });
        console.log('Availability Response', data);

        const isAvailable = typeof data.available === 'boolean'
            ? data.available
            : Boolean(data.kha_dung ?? data.con_hang);
        if (!isAvailable) {
            throw new Error(data.message || 'Thiết bị này đã được đặt trong khoảng thời gian bạn chọn.');
        }
    }

    function hienThiGioHang(cartData) {
        currentCart = cartApi().normalizeCartResponse(cartData);
        const cart = currentCart.items;
        const tbody = byId('cart-items');
        const totalItems = byId('cart-total-items');
        const totalDays = byId('cart-total-days');
        const totalMoney = byId('cart-total-money');

        renderEmptyState(cart.length === 0);

        if (!tbody) return;

        tbody.innerHTML = cart.map(function (item) {
            const id = escapeHTML(itemId(item));
            const productId = escapeHTML(deviceId(item));
            const name = escapeHTML(item.ten_thiet_bi || 'Thiết bị chưa đặt tên');
            const status = escapeHTML(item.trang_thai || item.tinh_trang || 'Chưa cập nhật');
            const image = escapeHTML(cartApi().firstImage(item));
            const price = formatCurrency(item.gia_thue);
            const days = Number(item.so_ngay_thue || 0);
            const total = formatCurrency(item.thanh_tien);
            const quantity = Number(item.so_luong || 1);
            const ngayNhan = escapeHTML(formatDate(item.ngay_nhan));
            const ngayTra = escapeHTML(formatDate(item.ngay_tra));
            const invalidClass = dateRangeIsValid(ngayNhan, ngayTra) ? '' : ' is-invalid';
            const minStart = escapeHTML(todayValue());
            const minEnd = escapeHTML(addDaysValue(ngayNhan || todayValue(), 1));

            return `
                <tr data-cart-id="${id}">
                    <td class="text-center">
                        <a href="chi_tiet_thiet_bi.html?id=${productId}">
                            <img src="${image}" alt="${name}" width="90" class="img-thumbnail" onerror="this.src='${NO_IMAGE}'">
                        </a>
                    </td>
                    <td class="text-start text-wrap">
                        <a href="chi_tiet_thiet_bi.html?id=${productId}" class="fw-semibold text-dark">${name}</a>
                        <div class="mt-1">
                            <small class="text-success">Tình trạng: ${status}</small>
                        </div>
                        <div class="mt-2">
                            <button type="button" class="btn btn-danger btn-sm cart-remove-item" data-cart-id="${id}">
                                <i class="bi bi-trash"></i>
                                Xóa
                            </button>
                        </div>
                    </td>
                    <td class="text-center">
                        <input type="date"
                            class="form-control form-control-sm cart-date-input${invalidClass}"
                            value="${ngayNhan}"
                            min="${minStart}"
                            data-cart-id="${id}"
                            data-date-field="ngay_nhan">
                    </td>
                    <td class="text-center">
                        <input type="date"
                            class="form-control form-control-sm cart-date-input${invalidClass}"
                            value="${ngayTra}"
                            min="${minEnd}"
                            data-cart-id="${id}"
                            data-date-field="ngay_tra">
                    </td>
                    <td class="text-center fw-semibold">${days} ngày</td>
                    <td class="text-end">${price}</td>
                    <td class="text-center">
                        <div class="qty-container justify-content-center">
                            <button class="qty-btn-minus cart-qty-minus" type="button" data-cart-id="${id}">
                                <i class="bi bi-dash"></i>
                            </button>
                            <input type="number" min="1" value="${quantity}" class="input-qty input-cornered cart-qty-input" data-cart-id="${id}">
                            <button class="qty-btn-plus cart-qty-plus" type="button" data-cart-id="${id}">
                                <i class="bi bi-plus"></i>
                            </button>
                        </div>
                    </td>
                    <td class="text-end fw-bold">${total}</td>
                </tr>
            `;
        }).join('');

        const invalidDateMessage = firstInvalidDateMessage(cart);

        if (totalItems) totalItems.textContent = String(currentCart.tong_san_pham);
        if (totalDays) totalDays.textContent = `${currentCart.tong_so_ngay_thue} ngày`;
        if (totalMoney) totalMoney.textContent = formatCurrency(currentCart.tong_tien_thue);

        setCheckoutState(invalidDateMessage);
        cartApi().updateCartCount(currentCart);
    }

    async function taiGioHang() {
        if (!cartApi()) return;

        try {
            const data = await cartApi().taiGioHang({ redirectOnUnauthorized: true });
            hienThiGioHang(data);
        } catch (error) {
            if (error && error.status === 401) {
                return;
            }
            console.error(error);
            alert(error.message || 'Không tải được giỏ hàng.');
            hienThiGioHang(cartApi().emptyCartResponse());
        }
    }

    function findItem(cartItemId) {
        return currentCart.items.find(function (item) {
            return String(itemId(item)) === String(cartItemId);
        });
    }

    async function updateCartItem(cartItemId, payload) {
        const item = findItem(cartItemId);
        if (item) {
            await checkCartItemAvailability(item, payload);
        }
        await cartApi().updateCartItem(cartItemId, payload);
        await taiGioHang();
    }

    async function deleteCartItem(cartItemId) {
        await cartApi().deleteCartItem(cartItemId);
        await taiGioHang();
    }

    async function clearCart() {
        if (!confirm('Bạn muốn xóa toàn bộ giỏ hàng?')) return;
        await cartApi().clearCart();
        await taiGioHang();
    }

    async function handleCartClick(event) {
        const plusButton = event.target.closest('.cart-qty-plus');
        const minusButton = event.target.closest('.cart-qty-minus');
        const removeButton = event.target.closest('.cart-remove-item');
        const clearButton = event.target.closest('#cart-clear-all');
        const checkoutButton = event.target.closest('#cart-checkout-button');

        try {
            if (plusButton) {
                const item = findItem(plusButton.dataset.cartId);
                if (!item) return;
                await updateCartItem(itemId(item), rowPayload(item, { so_luong: Number(item.so_luong || 1) + 1 }));
                return;
            }

            if (minusButton) {
                const item = findItem(minusButton.dataset.cartId);
                if (!item) return;
                await updateCartItem(itemId(item), rowPayload(item, { so_luong: Math.max(1, Number(item.so_luong || 1) - 1) }));
                return;
            }

            if (removeButton) {
                await deleteCartItem(removeButton.dataset.cartId);
                return;
            }

            if (clearButton) {
                await clearCart();
                return;
            }

            if (checkoutButton) {
                const message = firstInvalidDateMessage(currentCart.items);
                if (message) {
                    event.preventDefault();
                    setCheckoutState(message);
                    alert(message);
                }
            }
        } catch (error) {
            console.error(error);
            alert(error.message || 'Không cập nhật được giỏ hàng.');
        }
    }

    async function handleCartInput(event) {
        try {
            if (event.target.classList.contains('cart-qty-input')) {
                const item = findItem(event.target.dataset.cartId);
                if (!item) return;
                await updateCartItem(itemId(item), rowPayload(item, { so_luong: Math.max(1, Number(event.target.value) || 1) }));
                return;
            }

            if (event.target.classList.contains('cart-date-input')) {
                const item = findItem(event.target.dataset.cartId);
                if (!item) return;

                const payload = rowPayload(item, {
                    [event.target.dataset.dateField]: event.target.value,
                });

                const message = dateErrorMessage(payload.ngay_nhan, payload.ngay_tra);
                if (message) {
                    alert(message);
                    hienThiGioHang(currentCart);
                    return;
                }

                await updateCartItem(itemId(item), payload);
            }
        } catch (error) {
            console.error(error);
            alert(error.message || 'Không cập nhật được giỏ hàng.');
            hienThiGioHang(currentCart);
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        if (!cartApi()) return;

        taiGioHang();
        document.addEventListener('click', handleCartClick);
        document.addEventListener('change', handleCartInput);
    });
})();

