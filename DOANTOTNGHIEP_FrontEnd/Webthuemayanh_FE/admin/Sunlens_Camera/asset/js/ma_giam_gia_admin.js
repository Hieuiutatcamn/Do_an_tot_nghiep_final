(function () {
    'use strict';

    const STATUS_LABELS = {
        dang_hoat_dong: 'Đang hoạt động',
        tam_ngung: 'Tạm ngưng',
        het_han: 'Hết hạn',
    };
    const TYPE_LABELS = {
        phan_tram: 'Phần trăm',
        tien_mat: 'Tiền mặt',
    };
    const CONDITION_LABELS = {
        so_ngay_thue: 'Số ngày thuê',
        tong_tien_don: 'Tổng tiền đơn',
        khong_dieu_kien: 'Không điều kiện',
    };

    let allDiscounts = [];
    let currentDiscounts = [];
    let editingId = null;
    let searchTimer = null;
    const THONG_BAO_CAM_QUYEN = 'Bạn không có quyền thực hiện thao tác này.';

    function byId(id) {
        return document.getElementById(id);
    }

    function coQuyenChinhSua() {
        return Boolean(window.AdminApi && AdminApi.coQuyenChinhSuaNoiDung());
    }

    function dongBoQuyenGiaoDien() {
        const addButton = byId('addDiscountBtn');
        const saveButton = byId('discountSaveBtn');

        if (coQuyenChinhSua()) {
            if (addButton) {
                addButton.disabled = false;
                addButton.hidden = false;
                addButton.removeAttribute('aria-disabled');
            }
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.textContent = 'Lưu mã';
            }
            return;
        }

        if (addButton) {
            addButton.disabled = true;
            addButton.hidden = true;
            addButton.setAttribute('aria-disabled', 'true');
        }
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.textContent = 'Chỉ xem';
        }
    }

    function canhBaoKhongCoQuyen() {
        alert(THONG_BAO_CAM_QUYEN);
    }

    function escapeHtml(value) {
        return window.AdminApi ? AdminApi.escapeHtml(value) : String(value ?? '');
    }

    function getDiscountId(item) {
        return item.id_ma_giam_gia || item.Id_ma_giam_gia || item.ID_ma_giam_gia;
    }

    function toNumber(value) {
        const number = Number(value || 0);
        return Number.isFinite(number) ? number : 0;
    }

    function formatCurrency(value) {
        return window.AdminApi ? AdminApi.formatCurrency(value) : `${toNumber(value).toLocaleString('vi-VN')} đ`;
    }

    function formatDate(value) {
        if (!value) return '-';
        return String(value).slice(0, 10);
    }

    function normalizeText(value) {
        return String(value || '')
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '');
    }

    function statusLabel(status) {
        return STATUS_LABELS[status] || status || '-';
    }

    function typeLabel(type) {
        return TYPE_LABELS[type] || type || '-';
    }

    function conditionLabel(item) {
        const type = item.dieu_kien_loai || 'khong_dieu_kien';
        if (type === 'so_ngay_thue') {
            return `Thuê từ ${toNumber(item.so_ngay_thue_toi_thieu)} ngày`;
        }
        if (type === 'tong_tien_don') {
            return `Đơn từ ${formatCurrency(item.gia_tri_don_toi_thieu)}`;
        }
        return CONDITION_LABELS[type] || 'Không điều kiện';
    }

    function discountValueLabel(item) {
        if (item.loai_giam_gia === 'phan_tram') {
            return `${toNumber(item.gia_tri_giam)}%`;
        }
        return formatCurrency(item.gia_tri_giam);
    }

    function quantityLabel(item) {
        const quantity = toNumber(item.so_luong);
        const used = toNumber(item.da_su_dung);
        if (quantity <= 0) return `Không giới hạn (${used} đã dùng)`;
        return `${used}/${quantity}`;
    }

    function renderStatusBadge(status) {
        const className = {
            dang_hoat_dong: 'status-active',
            tam_ngung: 'status-paused',
            het_han: 'status-expired',
        }[status] || 'status-paused';
        return `<span class="discount-status ${className}">${escapeHtml(statusLabel(status))}</span>`;
    }

    function setTableMessage(message) {
        const tbody = byId('discountTableBody');
        if (!tbody) return;
        tbody.innerHTML = `
            <tr>
                <td colspan="11" class="discount-empty">${escapeHtml(message)}</td>
            </tr>
        `;
    }

    function renderDiscounts(discounts = currentDiscounts) {
        const tbody = byId('discountTableBody');
        if (!tbody) return;

        if (!discounts.length) {
            setTableMessage('Không tìm thấy mã giảm giá phù hợp.');
            return;
        }

        tbody.innerHTML = discounts.map((item) => {
            const id = getDiscountId(item);
            const nextStatus = item.trang_thai === 'dang_hoat_dong' ? 'tam_ngung' : 'dang_hoat_dong';
            const toggleText = item.trang_thai === 'dang_hoat_dong' ? 'Tạm ngưng' : 'Bật';

            return `
                <tr>
                    <td>${escapeHtml(id)}</td>
                    <td><strong>${escapeHtml(item.ma_giam_gia)}</strong></td>
                    <td>${escapeHtml(item.ten_ma || '-')}</td>
                    <td>${escapeHtml(typeLabel(item.loai_giam_gia))}</td>
                    <td>${escapeHtml(discountValueLabel(item))}</td>
                    <td>${escapeHtml(conditionLabel(item))}</td>
                    <td>${escapeHtml(formatDate(item.ngay_bat_dau))}</td>
                    <td>${escapeHtml(formatDate(item.ngay_ket_thuc))}</td>
                    <td>${escapeHtml(quantityLabel(item))}</td>
                    <td>${renderStatusBadge(item.trang_thai)}</td>
                    <td>
                        ${coQuyenChinhSua() ? `
                        <div class="table-row-action">
                            <button class="card-btn" type="button" data-discount-action="edit" data-discount-id="${escapeHtml(id)}">Sửa</button>
                            <button class="card-btn btn-secondary" type="button" data-discount-action="status" data-next-status="${escapeHtml(nextStatus)}" data-discount-id="${escapeHtml(id)}">${escapeHtml(toggleText)}</button>
                            <button class="card-btn btn-danger" type="button" data-discount-action="delete" data-discount-id="${escapeHtml(id)}">Xóa</button>
                        </div>
                        ` : '<span class="discount-empty">Chỉ xem</span>'}
                    </td>
                </tr>
            `;
        }).join('');
    }

    function filterDiscounts() {
        const keyword = normalizeText(byId('discountSearchInput')?.value);
        const status = byId('discountStatusFilter')?.value || 'all';
        const type = byId('discountTypeFilter')?.value || 'all';

        currentDiscounts = allDiscounts.filter((item) => {
            const haystack = normalizeText([
                item.ma_giam_gia,
                item.ten_ma,
                item.mo_ta,
                statusLabel(item.trang_thai),
                typeLabel(item.loai_giam_gia),
            ].join(' '));
            const matchKeyword = !keyword || haystack.includes(keyword);
            const matchStatus = status === 'all' || item.trang_thai === status;
            const matchType = type === 'all' || item.loai_giam_gia === type;
            return matchKeyword && matchStatus && matchType;
        });

        renderDiscounts(currentDiscounts);
    }

    async function loadDiscounts() {
        if (!window.AdminApi || !AdminApi.requireAuth()) return;
        await AdminApi.optional(() => AdminApi.loadCurrentAccount(), null);
        dongBoQuyenGiaoDien();
        setTableMessage('Đang tải mã giảm giá...');
        try {
            allDiscounts = await AdminApi.getAll('/admin/discounts');
            currentDiscounts = [...allDiscounts];
            filterDiscounts();
        } catch (error) {
            console.error(error);
            setTableMessage(error.message || 'Không tải được mã giảm giá.');
        }
    }

    function setFormMessage(message, type = 'error') {
        const element = byId('discountFormMessage');
        if (!element) return;
        element.textContent = message || '';
        element.className = `discount-form-message ${type === 'success' ? 'success' : 'error'}`;
    }

    function setInputValue(id, value) {
        const element = byId(id);
        if (element) element.value = value ?? '';
    }

    function resetForm() {
        const form = byId('discountForm');
        if (form) form.reset();
        editingId = null;
        setInputValue('discountId', '');
        setInputValue('discountConditionType', 'khong_dieu_kien');
        setInputValue('discountStatus', 'dang_hoat_dong');
        setInputValue('discountQuantity', '0');
        setFormMessage('');
        updateConditionInputs();
    }

    function openDiscountForm(id) {
        if (!coQuyenChinhSua()) {
            canhBaoKhongCoQuyen();
            return;
        }
        resetForm();
        const popup = byId('discountFormPopup');
        const title = byId('discountFormTitle');

        if (id) {
            const item = allDiscounts.find((discount) => String(getDiscountId(discount)) === String(id));
            if (!item) return;
            editingId = getDiscountId(item);
            if (title) title.textContent = 'Sửa mã giảm giá';
            setInputValue('discountId', editingId);
            setInputValue('discountCode', item.ma_giam_gia);
            setInputValue('discountName', item.ten_ma);
            setInputValue('discountDescription', item.mo_ta);
            setInputValue('discountType', item.loai_giam_gia || 'phan_tram');
            setInputValue('discountValue', item.gia_tri_giam);
            setInputValue('discountConditionType', item.dieu_kien_loai || 'khong_dieu_kien');
            setInputValue('discountMinDays', item.so_ngay_thue_toi_thieu || 0);
            setInputValue('discountMinTotal', item.gia_tri_don_toi_thieu || 0);
            setInputValue('discountStartDate', formatDate(item.ngay_bat_dau) === '-' ? '' : formatDate(item.ngay_bat_dau));
            setInputValue('discountEndDate', formatDate(item.ngay_ket_thuc) === '-' ? '' : formatDate(item.ngay_ket_thuc));
            setInputValue('discountQuantity', item.so_luong ?? 0);
            setInputValue('discountStatus', item.trang_thai || 'dang_hoat_dong');
        } else if (title) {
            title.textContent = 'Thêm mã giảm giá';
        }

        updateConditionInputs();
        if (popup) popup.classList.add('active');
    }

    function closeDiscountForm(event) {
        if (event && event.target !== event.currentTarget && !event.target.closest('[data-close-discount-form]')) return;
        const popup = byId('discountFormPopup');
        if (popup) popup.classList.remove('active');
    }

    function updateConditionInputs() {
        const condition = byId('discountConditionType')?.value || 'khong_dieu_kien';
        const daysInput = byId('discountMinDays');
        const totalInput = byId('discountMinTotal');
        const daysGroup = byId('discountMinDaysGroup');
        const totalGroup = byId('discountMinTotalGroup');

        if (daysInput) daysInput.disabled = condition !== 'so_ngay_thue';
        if (totalInput) totalInput.disabled = condition !== 'tong_tien_don';
        if (daysGroup) daysGroup.classList.toggle('is-muted', condition !== 'so_ngay_thue');
        if (totalGroup) totalGroup.classList.toggle('is-muted', condition !== 'tong_tien_don');
    }

    function collectPayload() {
        const condition = byId('discountConditionType')?.value || 'khong_dieu_kien';
        return {
            ma_giam_gia: (byId('discountCode')?.value || '').trim().toUpperCase(),
            ten_ma: (byId('discountName')?.value || '').trim() || null,
            mo_ta: (byId('discountDescription')?.value || '').trim() || null,
            loai_giam_gia: byId('discountType')?.value || 'phan_tram',
            gia_tri_giam: toNumber(byId('discountValue')?.value),
            dieu_kien_loai: condition,
            so_ngay_thue_toi_thieu: condition === 'so_ngay_thue' ? toNumber(byId('discountMinDays')?.value) : 0,
            gia_tri_don_toi_thieu: condition === 'tong_tien_don' ? toNumber(byId('discountMinTotal')?.value) : 0,
            ngay_bat_dau: byId('discountStartDate')?.value || null,
            ngay_ket_thuc: byId('discountEndDate')?.value || null,
            so_luong: toNumber(byId('discountQuantity')?.value),
            trang_thai: byId('discountStatus')?.value || 'dang_hoat_dong',
        };
    }

    function validatePayload(payload) {
        if (!payload.ma_giam_gia) return 'Vui lòng nhập mã code.';
        if (payload.loai_giam_gia === 'phan_tram' && (payload.gia_tri_giam < 1 || payload.gia_tri_giam > 100)) {
            return 'Mã giảm theo phần trăm phải từ 1 đến 100.';
        }
        if (payload.loai_giam_gia === 'tien_mat' && payload.gia_tri_giam <= 0) {
            return 'Giá trị giảm tiền mặt phải lớn hơn 0.';
        }
        if (payload.so_luong < 0) return 'Số lượng không được âm.';
        if (payload.ngay_bat_dau && payload.ngay_ket_thuc && payload.ngay_ket_thuc < payload.ngay_bat_dau) {
            return 'Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu.';
        }
        if (payload.dieu_kien_loai === 'so_ngay_thue' && payload.so_ngay_thue_toi_thieu <= 0) {
            return 'Vui lòng nhập số ngày thuê tối thiểu.';
        }
        if (payload.dieu_kien_loai === 'tong_tien_don' && payload.gia_tri_don_toi_thieu <= 0) {
            return 'Vui lòng nhập tổng tiền đơn tối thiểu.';
        }
        return '';
    }

    async function saveDiscount(event) {
        if (event) event.preventDefault();

        if (!coQuyenChinhSua()) {
            canhBaoKhongCoQuyen();
            return;
        }

        const payload = collectPayload();
        const error = validatePayload(payload);
        if (error) {
            setFormMessage(error);
            return;
        }

        const button = byId('discountSaveBtn');
        if (button) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = 'Đang lưu...';
        }

        try {
            if (editingId) {
                await AdminApi.apiFetch(`/admin/discounts/${editingId}`, {
                    method: 'PUT',
                    body: payload,
                });
            } else {
                await AdminApi.apiFetch('/admin/discounts', {
                    method: 'POST',
                    body: payload,
                });
            }
            setFormMessage('Lưu mã giảm giá thành công.', 'success');
            await loadDiscounts();
            closeDiscountForm({ target: byId('discountFormPopup'), currentTarget: byId('discountFormPopup') });
        } catch (saveError) {
            console.error(saveError);
            setFormMessage(saveError.message || 'Không lưu được mã giảm giá.');
        } finally {
            if (button) {
                button.disabled = false;
                button.textContent = button.dataset.originalText || 'Lưu mã';
            }
        }
    }

    async function deleteDiscount(id) {
        if (!coQuyenChinhSua()) {
            canhBaoKhongCoQuyen();
            return;
        }
        if (!id || !confirm('Bạn có chắc muốn xóa mã giảm giá này không?')) return;
        try {
            await AdminApi.apiFetch(`/admin/discounts/${id}`, { method: 'DELETE' });
            await loadDiscounts();
        } catch (error) {
            alert(error.message || 'Không xóa được mã giảm giá.');
        }
    }

    async function toggleDiscountStatus(id, nextStatus) {
        if (!coQuyenChinhSua()) {
            canhBaoKhongCoQuyen();
            return;
        }
        if (!id) return;
        try {
            await AdminApi.apiFetch(`/admin/discounts/${id}/status`, {
                method: 'PATCH',
                body: { trang_thai: nextStatus },
            });
            await loadDiscounts();
        } catch (error) {
            alert(error.message || 'Không cập nhật được trạng thái mã giảm giá.');
        }
    }

    function clearDiscountFilters() {
        setInputValue('discountSearchInput', '');
        setInputValue('discountStatusFilter', 'all');
        setInputValue('discountTypeFilter', 'all');
        filterDiscounts();
    }

    function bindEvents() {
        byId('addDiscountBtn')?.addEventListener('click', () => openDiscountForm());
        byId('discountForm')?.addEventListener('submit', saveDiscount);
        byId('discountConditionType')?.addEventListener('change', updateConditionInputs);
        byId('clearDiscountFilterBtn')?.addEventListener('click', clearDiscountFilters);
        byId('discountStatusFilter')?.addEventListener('change', filterDiscounts);
        byId('discountTypeFilter')?.addEventListener('change', filterDiscounts);
        byId('discountSearchInput')?.addEventListener('input', () => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(filterDiscounts, 300);
        });

        byId('discountTableBody')?.addEventListener('click', (event) => {
            const button = event.target.closest('[data-discount-action]');
            if (!button) return;

            const action = button.dataset.discountAction;
            const id = button.dataset.discountId;
            if (action === 'edit') openDiscountForm(id);
            if (action === 'delete') deleteDiscount(id);
            if (action === 'status') toggleDiscountStatus(id, button.dataset.nextStatus);
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        bindEvents();
        loadDiscounts();
    });

    window.openDiscountForm = openDiscountForm;
    window.closeDiscountForm = closeDiscountForm;
})();
