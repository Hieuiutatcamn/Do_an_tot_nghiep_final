(function () {
    'use strict';

    const DEPOSIT_AMOUNT = 200000;
    const DISCOUNT_AMOUNT = 0;
    const THUE_NGAY_STORAGE_KEY = 'thue_ngay';

    let checkoutCart = {
        items: [],
        danh_sach: [],
        tong_san_pham: 0,
        tong_so_ngay_thue: 0,
        tong_tien_thue: 0,
    };
    let checkoutTotals = {
        tongTien: 0,
        tienCoc: DEPOSIT_AMOUNT,
        giamGia: DISCOUNT_AMOUNT,
        tongThanhToan: DEPOSIT_AMOUNT,
    };
    let maGiamGia = {
        applied: false,
        id: null,
        maGiamGia: '',
        loaiGiamGia: '',
        giaTriGiam: 0,
        soTienGiam: 0,
    };
    let lastCartSignature = '';
    let transferPreviewUrl = '';

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
        return cartApi().formatCurrency(value);
    }

    function formatDate(value) {
        return cartApi().formatDate(value);
    }

    function dateTimeValue(value) {
        const dateValue = String(value || '').slice(0, 10);
        return dateValue ? `${dateValue}T00:00:00` : '';
    }

    function itemId(item) {
        return item.Id_gio_hang || item.id_gio_hang;
    }

    function deviceId(item) {
        return item.Id_thiet_bi || item.id_thiet_bi;
    }

    function setText(id, value) {
        const element = byId(id);
        if (element) {
            element.textContent = value;
        }
    }

    function laLuongThueNgay() {
        const params = new URLSearchParams(window.location.search);
        return params.get('mode') === 'thue-ngay';
    }

    function layDuLieuThueNgay() {
        try {
            const rawValue = sessionStorage.getItem(THUE_NGAY_STORAGE_KEY);
            if (!rawValue) return null;
            const data = JSON.parse(rawValue);
            return data && typeof data === 'object' && !Array.isArray(data) ? data : null;
        } catch (error) {
            console.warn('Không đọc được dữ liệu thuê ngay:', error);
            return null;
        }
    }

    function tinhSoNgayThue(ngayNhan, ngayTra) {
        const start = new Date(`${String(ngayNhan || '').slice(0, 10)}T00:00:00`);
        const end = new Date(`${String(ngayTra || '').slice(0, 10)}T00:00:00`);
        if (!Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime())) return 0;
        return Math.max(1, Math.ceil((end - start) / 86400000));
    }

    function chuanHoaDuLieuThueNgay(data) {
        if (!data || typeof data !== 'object') return null;

        const idThietBi = Number(data.id_thiet_bi || data.Id_thiet_bi || data.id);
        const soLuong = Math.max(1, Number(data.so_luong || data.quantity || 1) || 1);
        const giaThue = Number(data.gia_thue || data.gia_thue_ngay || 0) || 0;
        const ngayNhan = String(data.ngay_nhan || data.startDate || '').slice(0, 10);
        const ngayTra = String(data.ngay_tra || data.endDate || '').slice(0, 10);

        if (!idThietBi || !ngayNhan || !ngayTra) return null;
        if (cartApi().dateErrorMessage && cartApi().dateErrorMessage({ ngay_nhan: ngayNhan, ngay_tra: ngayTra })) {
            return null;
        }

        const soNgayThue = Number(data.so_ngay_thue || data.rental_days || tinhSoNgayThue(ngayNhan, ngayTra)) || 0;
        const thanhTien = Number(data.thanh_tien || (giaThue * soLuong * soNgayThue)) || 0;
        const item = {
            id_thiet_bi: idThietBi,
            Id_thiet_bi: idThietBi,
            ten_thiet_bi: data.ten_thiet_bi || data.name || 'Thiết bị chưa đặt tên',
            gia_thue: giaThue,
            so_luong: soLuong,
            ngay_nhan: ngayNhan,
            ngay_tra: ngayTra,
            so_ngay_thue: soNgayThue,
            thanh_tien: thanhTien,
            hinh_anh: data.hinh_anh || data.image || '',
            danh_muc: data.danh_muc || data.category || '',
            la_thue_ngay: true,
        };

        return {
            items: [item],
            danh_sach: [item],
            tong_san_pham: soLuong,
            tong_so_ngay_thue: soNgayThue,
            tong_tien_thue: thanhTien,
        };
    }

    function renderThueNgayKhongHopLe() {
        checkoutCart = cartApi().normalizeCartResponse(cartApi().emptyCartResponse());
        const tbody = byId('checkoutCartItems');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center text-muted">
                        Không tìm thấy dữ liệu thuê ngay. Vui lòng quay lại chọn thiết bị.
                    </td>
                </tr>
            `;
        }
        resetDiscount();
        updateTotals(checkoutCart);
        setConfirmState(checkoutCart);
    }

    function hienThiSanPhamThueNgay() {
        const data = chuanHoaDuLieuThueNgay(layDuLieuThueNgay());
        if (!data) {
            renderThueNgayKhongHopLe();
            return;
        }

        hienThiGioHang(data);
    }

    function taoPayloadDatThueTuThueNgay(cart) {
        return rentalItemsFromCart(cart);
    }

    function xoaDuLieuThueNgaySauKhiDat() {
        sessionStorage.removeItem(THUE_NGAY_STORAGE_KEY);
    }

    function setDiscountMessage(message, type) {
        const element = byId('discount-message');
        if (!element) return;

        element.textContent = message || '';
        element.className = `small mt-2 ${type === 'success' ? 'text-success fw-semibold' : 'text-danger fw-semibold'}`;
    }

    function setDiscountAppliedVisible(isVisible) {
        const row = byId('checkout-discount-code-row');
        const wrap = byId('discount-applied');
        if (row) row.classList.toggle('d-none', !isVisible);
        if (wrap) wrap.classList.toggle('d-none', !isVisible);
    }

    function renderAppliedDiscount() {
        const code = maGiamGia.applied ? maGiamGia.maGiamGia : '-';
        setText('checkout-discount-code', code);
        setText('discount-applied-code', code);
        setDiscountAppliedVisible(maGiamGia.applied);
    }

    function cartSignature(cartData) {
        const normalized = cartApi().normalizeCartResponse(cartData);
        return JSON.stringify({
            total: normalized.tong_tien_thue,
            days: normalized.tong_so_ngay_thue,
            items: normalized.items.map(function (item) {
                return [
                    itemId(item),
                    deviceId(item),
                    item.so_luong,
                    item.ngay_nhan,
                    item.ngay_tra,
                    item.thanh_tien,
                ];
            }),
        });
    }

    function resetDiscount(message) {
        maGiamGia = {
            applied: false,
            id: null,
            maGiamGia: '',
            loaiGiamGia: '',
            giaTriGiam: 0,
            soTienGiam: 0,
        };
        renderAppliedDiscount();
        if (message) {
            setDiscountMessage(message, 'error');
        } else {
            setDiscountMessage('', 'success');
        }
    }

    function syncDiscountWithCart(cartData) {
        const nextSignature = cartSignature(cartData);
        if (maGiamGia.applied && lastCartSignature && nextSignature !== lastCartSignature) {
            resetDiscount('Giỏ hàng đã thay đổi. Vui lòng áp dụng lại mã giảm giá.');
        }
        lastCartSignature = nextSignature;
    }

    function renderEmptyCart() {
        const tbody = byId('checkoutCartItems');

        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center text-muted">
                        Giỏ hàng của bạn đang trống.
                    </td>
                </tr>
            `;
        }
    }

    function hienThiGioHang(cartData) {
        checkoutCart = cartApi().normalizeCartResponse(cartData);
        const cart = checkoutCart.items;
        const tbody = byId('checkoutCartItems');

        if (!tbody) return;

        if (!cart.length) {
            renderEmptyCart();
            syncDiscountWithCart(checkoutCart);
            resetDiscount();
            updateTotals(checkoutCart);
            setConfirmState(checkoutCart);
            return;
        }

        tbody.innerHTML = cart.map(function (item) {
            const name = escapeHTML(item.ten_thiet_bi || 'Thiết bị chưa đặt tên');
            const quantity = Number(item.so_luong || 1);
            const days = Number(item.so_ngay_thue || 0);
            const price = Number(item.gia_thue || 0);
            const total = Number(item.thanh_tien || 0);
            const startLabel = escapeHTML(formatDate(item.ngay_nhan));
            const endLabel = escapeHTML(formatDate(item.ngay_tra));

            return `
                <tr data-cart-id="${escapeHTML(itemId(item))}">
                    <td class="text-start">
                        <strong>${name}</strong>
                    </td>
                    <td class="text-start">
                        <small>
                            Nhận:
                            <br>
                            <strong>${startLabel}</strong>
                            <br><br>
                            Trả:
                            <br>
                            <strong>${endLabel}</strong>
                            <br><br>
                            Số ngày thuê: <strong>${days} ngày</strong>
                            <br>
                            Giá thuê/ngày: <strong>${formatCurrency(price)}</strong>
                            <br>
                            Số lượng: <strong>${quantity}</strong>
                        </small>
                    </td>
                    <td class="text-end fw-semibold">
                        ${formatCurrency(total)}
                    </td>
                </tr>
            `;
        }).join('');

        syncDiscountWithCart(checkoutCart);
        updateTotals(checkoutCart);
        setConfirmState(checkoutCart);
        if (!laLuongThueNgay()) {
            cartApi().updateCartCount(checkoutCart);
        }
    }

    function updateTotals(cartData) {
        const normalizedCart = cartApi().normalizeCartResponse(cartData);
        const tongTien = Number(normalizedCart.tong_tien_thue || 0);

        checkoutTotals = {
            tongTien,
            tienCoc: DEPOSIT_AMOUNT,
            giamGia: maGiamGia.applied ? Number(maGiamGia.soTienGiam || 0) : DISCOUNT_AMOUNT,
            tongThanhToan: tongTien + DEPOSIT_AMOUNT - (maGiamGia.applied ? Number(maGiamGia.soTienGiam || 0) : DISCOUNT_AMOUNT),
        };

        setText('checkout-subtotal', formatCurrency(checkoutTotals.tongTien));
        setText('checkout-deposit', formatCurrency(checkoutTotals.tienCoc));
        setText('checkout-discount', checkoutTotals.giamGia > 0
            ? `-${formatCurrency(checkoutTotals.giamGia)}`
            : formatCurrency(0));
        setText('checkout-grand-total', formatCurrency(checkoutTotals.tongThanhToan));
        setText('deposit-amount', Number(DEPOSIT_AMOUNT).toLocaleString('vi-VN'));
        renderAppliedDiscount();
    }

    function cartDateErrorMessage(cartData) {
        const normalizedCart = cartApi().normalizeCartResponse(cartData);
        const invalidItem = normalizedCart.items.find(function (item) {
            return cartApi().dateErrorMessage && cartApi().dateErrorMessage({
                ngay_nhan: String(item.ngay_nhan || '').slice(0, 10),
                ngay_tra: String(item.ngay_tra || '').slice(0, 10),
            });
        });
        return invalidItem && cartApi().dateErrorMessage
            ? cartApi().dateErrorMessage({
                ngay_nhan: String(invalidItem.ngay_nhan || '').slice(0, 10),
                ngay_tra: String(invalidItem.ngay_tra || '').slice(0, 10),
            })
            : '';
    }

    function setConfirmState(cartData) {
        const button = byId('confirm-rental-btn');
        if (!button) return;

        button.disabled = !cartData.items.length || Boolean(cartDateErrorMessage(cartData));
    }

    async function taiGioHang() {
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

    function inputValue(id) {
        const input = byId(id);
        return input ? input.value.trim() : '';
    }

    function hasFile(id) {
        const input = byId(id);
        return !!(input && input.files && input.files.length > 0);
    }

    function fileFromInput(id) {
        const input = byId(id);
        return input && input.files && input.files.length ? input.files[0] : null;
    }

    function isValidTransferImage(file) {
        if (!file) return false;
        const allowedTypes = new Set(['image/jpeg', 'image/png', 'image/webp']);
        const allowedExtensions = /\.(jpe?g|png|webp)$/i;
        return allowedTypes.has(file.type) || allowedExtensions.test(file.name || '');
    }

    function clearTransferPreview(resetInput = true) {
        if (transferPreviewUrl) {
            URL.revokeObjectURL(transferPreviewUrl);
            transferPreviewUrl = '';
        }
        const input = byId('transfer-proof');
        const wrap = byId('transfer-proof-preview-wrap');
        const img = byId('transfer-proof-preview');
        const fileName = byId('transfer-proof-file-name');
        if (resetInput && input) input.value = '';
        if (img) {
            img.removeAttribute('src');
            img.classList.add('d-none');
        }
        if (fileName) fileName.textContent = '';
        if (wrap) wrap.classList.add('d-none');
    }

    function renderTransferPreview(file) {
        const wrap = byId('transfer-proof-preview-wrap');
        const img = byId('transfer-proof-preview');
        const fileName = byId('transfer-proof-file-name');
        if (!file || !wrap || !img || !fileName) return;

        if (transferPreviewUrl) URL.revokeObjectURL(transferPreviewUrl);
        transferPreviewUrl = URL.createObjectURL(file);
        img.src = transferPreviewUrl;
        img.classList.remove('d-none');
        fileName.textContent = file.name || 'Ảnh chuyển khoản đã chọn';
        wrap.classList.remove('d-none');
    }

    function bindTransferProofPreview() {
        const input = byId('transfer-proof');
        const removeButton = byId('transfer-proof-remove');
        if (input && input.dataset.transferPreviewBound !== 'true') {
            input.dataset.transferPreviewBound = 'true';
            input.addEventListener('change', function () {
                const file = fileFromInput('transfer-proof');
                clearTransferPreview(false);
                if (!file) return;
                if (!isValidTransferImage(file)) {
                    alert('Vui lòng chọn file ảnh hợp lệ.');
                    clearTransferPreview(true);
                    return;
                }
                renderTransferPreview(file);
            });
        }
        if (removeButton && removeButton.dataset.transferPreviewBound !== 'true') {
            removeButton.dataset.transferPreviewBound = 'true';
            removeButton.addEventListener('click', function () {
                clearTransferPreview(true);
            });
        }
    }

    function checkoutProfile() {
        return window.SunlensCheckoutProfile || null;
    }

    function isUserLoggedIn() {
        return Boolean(cartApi().getAuthToken());
    }

    function redirectToLogin() {
        const currentPath = `${window.location.pathname}${window.location.search}`;
        window.location.href = `dang_nhap.html?next=${encodeURIComponent(currentPath)}`;
    }

    function hasRequiredCccdImages() {
        const profile = checkoutProfile();
        if (profile && typeof profile.hasRequiredCccd === 'function') {
            return profile.hasRequiredCccd();
        }

        return hasFile('cccd-front') && hasFile('cccd-back');
    }

    function setCccdMessage(message, type) {
        const profile = checkoutProfile();
        if (profile && typeof profile.setCccdMessage === 'function') {
            profile.setCccdMessage(message, type);
            return;
        }

        const messageElement = byId('cccd-message');
        if (messageElement) {
            messageElement.textContent = message || '';
            messageElement.className = `small mb-3 fw-semibold ${type === 'success' ? 'text-success' : 'text-danger'}`;
        }
    }

    function isChecked(id) {
        const input = byId(id);
        return !!(input && input.checked);
    }

    function transferContent() {
        const element = byId('transfer-content');
        return element ? element.textContent.trim() : '';
    }

    function layPhuongThucThanhToan() {
        const selected = document.querySelector('input[name="payment-method"]:checked');
        return selected ? selected.value : 'VNPAY';
    }

    function laChuyenKhoanThuCong() {
        return layPhuongThucThanhToan() === 'Chuyen khoan thu cong';
    }

    function capNhatGiaoDienPhuongThucThanhToan() {
        const manualPanel = byId('manual-payment-panel');
        const vnpayPanel = byId('vnpay-payment-panel');
        const submitButton = byId('confirm-rental-btn');
        const manual = laChuyenKhoanThuCong();

        if (manualPanel) manualPanel.classList.toggle('d-none', !manual);
        if (vnpayPanel) vnpayPanel.classList.toggle('d-none', manual);
        if (submitButton) {
            submitButton.textContent = manual
                ? 'Xác nhận chuyển khoản thủ công'
                : 'Thanh toán qua VNPAY';
        }
        if (manual && typeof window.updateTransferFields === 'function') {
            window.updateTransferFields();
        }
    }

    function bindPhuongThucThanhToan() {
        document.querySelectorAll('input[name="payment-method"]').forEach(function (input) {
            if (input.dataset.paymentMethodBound === 'true') return;
            input.dataset.paymentMethodBound = 'true';
            input.addEventListener('change', capNhatGiaoDienPhuongThucThanhToan);
        });
        capNhatGiaoDienPhuongThucThanhToan();
    }

    function orderIsValid(cart) {
        const thongTinHopLe = inputValue('full-name')
            && inputValue('phone')
            && inputValue('email')
            && inputValue('cccd')
            && inputValue('address')
            && hasRequiredCccdImages()
            && isChecked('terms')
            && cart.items.length > 0;
        return thongTinHopLe && (!laChuyenKhoanThuCong() || hasFile('transfer-proof'));
    }

    function rentalItemsFromCart(cart) {
        return cart.items.map(function (item) {
            return {
                id_thiet_bi: Number(deviceId(item)),
                ngay_nhan: dateTimeValue(item.ngay_nhan),
                ngay_tra: dateTimeValue(item.ngay_tra),
                so_luong: Number(item.so_luong || 1),
            };
        });
    }

    function validateRentalPayload(payload) {
        const danhSachThietBi = payload.danh_sach_thiet_bi || payload.items || [];
        if (!danhSachThietBi.length) {
            throw new Error('Giỏ hàng không có thiết bị để tạo đơn thuê.');
        }

        danhSachThietBi.forEach(function (item, index) {
            const itemNumber = index + 1;
            if (!Number.isInteger(item.id_thiet_bi) || item.id_thiet_bi <= 0) {
                throw new Error(`Thiết bị thứ ${itemNumber} không có id_thiet_bi hợp lệ.`);
            }
            if (!Number.isInteger(item.so_luong) || item.so_luong <= 0) {
                throw new Error(`Thiết bị thứ ${itemNumber} không có so_luong hợp lệ.`);
            }
            const startTime = Date.parse(item.ngay_nhan);
            const endTime = Date.parse(item.ngay_tra);
            if (!item.ngay_nhan || !item.ngay_tra
                || Number.isNaN(startTime) || Number.isNaN(endTime)
                || endTime <= startTime) {
                throw new Error(`Thiết bị thứ ${itemNumber} có ngày nhận/trả không hợp lệ.`);
            }
            if (cartApi().dateErrorMessage) {
                const message = cartApi().dateErrorMessage({
                    ngay_nhan: String(item.ngay_nhan || '').slice(0, 10),
                    ngay_tra: String(item.ngay_tra || '').slice(0, 10),
                });
                if (message) throw new Error(message);
            }
        });
    }

    function noteValue() {
        const textarea = document.querySelector('#checkout-form textarea');
        return textarea ? textarea.value.trim() : '';
    }

    async function createRentalFromCart(cart, phuongThucThanhToan) {
        const rentalApiPath = cartApi().RENTAL_API_PATH || '/rentals';
        const payload = {
            ghi_chu: noteValue() || null,
            anh_chuyen_khoan: null,
            phuong_thuc_thanh_toan: phuongThucThanhToan,
            danh_sach_thiet_bi: laLuongThueNgay()
                ? taoPayloadDatThueTuThueNgay(cart)
                : rentalItemsFromCart(cart),
        };
        const profile = checkoutProfile();
        if (profile && typeof profile.layThongTinHoSoTuThanhToan === 'function') {
            payload.thong_tin_khach_hang_tu_thanh_toan = profile.layThongTinHoSoTuThanhToan();
        }
        if (maGiamGia.applied && maGiamGia.maGiamGia) {
            payload.ma_code = maGiamGia.maGiamGia;
            payload.ma_giam_gia = maGiamGia.maGiamGia;
            if (maGiamGia.id) {
                payload.id_ma_giam_gia = maGiamGia.id;
            }
        }

        validateRentalPayload(payload);
        console.log('Rental Payload:', payload);

        return cartApi().apiRequest(rentalApiPath, {
            method: 'POST',
            body: payload,
        });
    }

    function rentalIdFromResponse(data) {
        const rental = data && (data.order || data.rental || data.don_thue || data.data || data);
        return rental && (
            rental.id_don_thue
            || rental.Id_don_thue
            || rental.ID_don_thue
            || rental.order_id
            || rental.rental_id
            || rental.id
        );
    }

    async function uploadTransferProof(orderId) {
        const file = fileFromInput('transfer-proof');
        if (!file || !orderId) return null;

        const formData = new FormData();
        formData.append('anh_chuyen_khoan', file);

        const paths = [
            `/rentals/${encodeURIComponent(orderId)}/payment-image`,
            `/orders/${encodeURIComponent(orderId)}/payment-image`,
        ];
        let lastError = null;

        for (const path of paths) {
            try {
                return await cartApi().apiRequest(path, {
                    method: 'PUT',
                    body: formData,
                });
            } catch (error) {
                lastError = error;
                if (error.status && (error.status === 404 || error.status === 405)) {
                    continue;
                }
                throw error;
            }
        }

        throw lastError || new Error('Không thể tải ảnh chuyển khoản lên đơn thuê.');
    }

    async function taoThanhToanVnpay(orderId) {
        const maDonThue = `DH${String(orderId).padStart(4, '0')}`;
        const response = await cartApi().apiRequest('/thanh-toan/vnpay-tao-url', {
            method: 'POST',
            body: {
                id_don_thue: Number(orderId),
                so_tien: DEPOSIT_AMOUNT,
                noi_dung_thanh_toan: `Thanh toán cọc đơn thuê ${maDonThue}`,
            },
        });

        if (!response || !response.thanh_cong || !response.duong_dan_thanh_toan) {
            throw new Error('Backend không trả về đường dẫn thanh toán VNPAY hợp lệ.');
        }
        sessionStorage.setItem('sunlens_vnpay_don_thue_dang_thanh_toan', String(orderId));
        window.location.href = response.duong_dan_thanh_toan;
    }

    async function damBaoGioHangDaXoa() {
        try {
            const gioHangSauDatThue = await cartApi().taiGioHang({
                redirectOnUnauthorized: false,
            });
            const gioHangChuanHoa = cartApi().normalizeCartResponse(gioHangSauDatThue);
            if (gioHangChuanHoa.items.length) {
                await cartApi().clearCart();
                return;
            }
            await cartApi().updateCartCount(cartApi().emptyCartResponse());
        } catch (error) {
            console.warn('Không thể đồng bộ lại giỏ hàng sau khi đặt thuê:', error);
        }
    }

    function thongBaoLoiDatThue(error) {
        if (!error) return 'Không thể tạo đơn thuê. Vui lòng thử lại.';
        if (error.status === 401) {
            return 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.';
        }
        if (error.status === 422 && error.response && Array.isArray(error.response.detail)) {
            const chiTiet = error.response.detail.map(function (item) {
                const field = Array.isArray(item.loc)
                    ? item.loc.filter(function (part) { return part !== 'body'; }).join('.')
                    : '';
                const message = item.msg || item.message || 'Dữ liệu không hợp lệ';
                return item.type === 'missing' || /field required/i.test(message)
                    ? `Thiếu trường: ${field || 'không xác định'}`
                    : `${field ? `${field}: ` : ''}${message}`;
            }).join('\n');
            return `Dữ liệu đơn thuê không hợp lệ:\n${chiTiet}`;
        }
        return error.message || 'Không thể tạo đơn thuê. Vui lòng thử lại.';
    }

    async function applyDiscount(event) {
        if (event) event.preventDefault();

        const input = byId('discount-code-input');
        const button = byId('apply-discount-btn');
        const code = input ? input.value.trim().toUpperCase() : '';

        setDiscountMessage('', 'success');

        if (!code) {
            resetDiscount();
            setDiscountMessage('Vui lòng nhập mã giảm giá.', 'error');
            return;
        }
        if (!checkoutCart.items.length) {
            resetDiscount();
            setDiscountMessage('Giỏ hàng của bạn đang trống.', 'error');
            return;
        }
        if (maGiamGia.applied && maGiamGia.maGiamGia === code) {
            setDiscountMessage('Mã giảm giá này đã được áp dụng.', 'success');
            return;
        }

        if (button) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = 'Đang áp dụng...';
        }

        try {
            const discountPayload = {
                ma_code: code,
                ma_giam_gia: code,
                tong_tien: Number(checkoutCart.tong_tien_thue || 0),
                so_ngay_thue: Number(checkoutCart.tong_so_ngay_thue || 0),
            };
            console.log('Discount payload:', discountPayload);

            const data = await cartApi().apiRequest('/discounts/apply', {
                method: 'POST',
                auth: false,
                body: discountPayload,
            });
            console.log('Discount response:', data);

            if (!data || !(data.hop_le ?? data.valid)) {
                resetDiscount();
                setDiscountMessage((data && (data.noi_dung_tin_nhan || data.message)) || 'Mã giảm giá không hợp lệ.', 'error');
                updateTotals(checkoutCart);
                return;
            }

            maGiamGia = {
                applied: true,
                id: data.id_ma_giam_gia || null,
                maGiamGia: data.ma_giam_gia || data.ma_code || code,
                loaiGiamGia: data.loai_giam_gia || '',
                giaTriGiam: Number(data.gia_tri_giam || 0),
                soTienGiam: Number(data.so_tien_giam || 0),
            };
            if (input) input.value = maGiamGia.maGiamGia;
            lastCartSignature = cartSignature(checkoutCart);
            updateTotals(checkoutCart);
            setDiscountMessage(data.noi_dung_tin_nhan || data.message || 'Áp dụng mã giảm giá thành công', 'success');
        } catch (error) {
            console.error('Discount response error:', {
                status: error.status,
                message: error.message,
                response: error.response,
            });
            resetDiscount();
            updateTotals(checkoutCart);
            setDiscountMessage(error.message || 'Không áp dụng được mã giảm giá.', 'error');
        } finally {
            if (button) {
                button.disabled = false;
                button.textContent = button.dataset.originalText || 'Áp dụng mã';
            }
        }
    }

    function setSubmitLoading(button, isLoading, manualPayment = false) {
        if (!button) return;

        if (isLoading) {
            button.dataset.originalText = button.textContent;
            button.textContent = manualPayment
                ? 'Đang tạo đơn thuê...'
                : 'Đang chuyển đến VNPAY...';
            button.disabled = true;
            return;
        }

        button.textContent = button.dataset.originalText || button.textContent;
        button.disabled = false;
    }

    async function uploadSelectedCccdImages() {
        const profile = checkoutProfile();
        if (!profile || typeof profile.uploadSelectedCccdImages !== 'function') {
            return;
        }

        await profile.uploadSelectedCccdImages();
    }

    async function handleSubmit(event) {
        event.preventDefault();

        const submitButton = byId('confirm-rental-btn');
        const phuongThucThanhToan = layPhuongThucThanhToan();
        const manualPayment = phuongThucThanhToan === 'Chuyen khoan thu cong';

        if (!isUserLoggedIn()) {
            alert('Bạn cần đăng nhập để đặt thuê.');
            redirectToLogin();
            return;
        }

        if (!hasRequiredCccdImages()) {
            const message = 'Vui lòng bổ sung ảnh CCCD trước khi đặt thuê.';
            setCccdMessage(message, 'error');
            alert(message);
            return;
        }

        const dateMessage = cartDateErrorMessage(checkoutCart);
        if (dateMessage) {
            alert(dateMessage);
            return;
        }

        if (!orderIsValid(checkoutCart)) {
            alert(manualPayment
                ? 'Vui lòng nhập đầy đủ thông tin và tải ảnh chuyển khoản.'
                : 'Vui lòng nhập đầy đủ thông tin thuê máy.');
            return;
        }

        setSubmitLoading(submitButton, true, manualPayment);
        let rentalId = null;

        try {
            await uploadSelectedCccdImages();
            setCccdMessage('', 'success');

            const profile = checkoutProfile();
            if (profile && typeof profile.saveCustomerInfo === 'function') {
                profile.saveCustomerInfo();
            }

            const rental = await createRentalFromCart(checkoutCart, phuongThucThanhToan);
            rentalId = rentalIdFromResponse(rental);
            if (!rentalId) {
                throw new Error('API đã tạo đơn nhưng không trả về id_don_thue.');
            }

            if (!manualPayment) {
                if (laLuongThueNgay()) {
                    xoaDuLieuThueNgaySauKhiDat();
                } else {
                    await damBaoGioHangDaXoa();
                }
                await taoThanhToanVnpay(rentalId);
                return;
            }

            try {
                await uploadTransferProof(rentalId);
            } catch (uploadError) {
                uploadError.donThueDaTao = true;
                uploadError.idDonThue = rentalId;
                throw uploadError;
            }

            if (laLuongThueNgay()) {
                xoaDuLieuThueNgaySauKhiDat();
            } else {
                await damBaoGioHangDaXoa();
            }
            alert('Đặt thuê thành công.');
            window.location.href = 'don_thue_cua_toi.html';
        } catch (error) {
            console.error('Rental API Error:', error);
            if (!manualPayment && rentalId) {
                if (laLuongThueNgay()) {
                    xoaDuLieuThueNgaySauKhiDat();
                } else {
                    await damBaoGioHangDaXoa();
                }
                alert(
                    `Đơn thuê #${rentalId} đã được tạo nhưng chưa mở được cổng VNPAY.\n`
                    + `${thongBaoLoiDatThue(error)}\n`
                    + 'Vui lòng liên hệ hỗ trợ hoặc kiểm tra lại đơn thuê của bạn.'
                );
                window.location.href = 'don_thue_cua_toi.html';
                return;
            }
            if (error.donThueDaTao && error.idDonThue) {
                if (laLuongThueNgay()) {
                    xoaDuLieuThueNgaySauKhiDat();
                } else {
                    await damBaoGioHangDaXoa();
                }
                alert(
                    `Đơn thuê #${error.idDonThue} đã được tạo nhưng chưa tải được ảnh chuyển khoản.\n`
                    + `${thongBaoLoiDatThue(error)}\n`
                    + 'Bạn có thể bổ sung ảnh trong trang Đơn thuê của tôi.'
                );
                window.location.href = 'don_thue_cua_toi.html';
                return;
            }
            alert(`Lỗi đặt thuê: ${thongBaoLoiDatThue(error)}`);
        } finally {
            setSubmitLoading(submitButton, false, manualPayment);
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        const form = byId('checkout-form');
        const discountForm = byId('discount-form');
        const phoneInput = byId('phone');

        if (!cartApi()) return;

        if (laLuongThueNgay()) {
            hienThiSanPhamThueNgay();
        } else {
            taiGioHang();
        }

        if (phoneInput && typeof window.updateTransferFields === 'function') {
            phoneInput.addEventListener('input', window.updateTransferFields);
        }

        if (form) {
            form.addEventListener('submit', handleSubmit);
        }
        if (discountForm) {
            discountForm.addEventListener('submit', applyDiscount);
        }
        bindTransferProofPreview();
        bindPhuongThucThanhToan();
    });

    window.taoThanhToanVnpay = taoThanhToanVnpay;
})();

