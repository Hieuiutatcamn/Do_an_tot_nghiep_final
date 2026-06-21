(function () {
    'use strict';

    let categories = [];
    let devices = [];
    let existingDeviceImages = [];
    let selectedDeviceImages = [];
    let selectedPreviewUrls = [];
    let imagesTouched = false;
    let nextLocalImageId = 1;

    const USER_ASSET_BASE = '../../user/Sunlens_Camera/';
    const THONG_BAO_CAM_QUYEN = 'Bạn không có quyền thực hiện thao tác này.';

    function coQuyenChinhSua() {
        return Boolean(window.AdminApi && AdminApi.coQuyenChinhSuaNoiDung());
    }

    function khoaNut(button, labelKhiKhoa = 'Chỉ xem') {
        if (!button) return;
        button.disabled = true;
        button.hidden = true;
        button.setAttribute('aria-disabled', 'true');
        if (labelKhiKhoa) button.title = labelKhiKhoa;
    }

    function moKhoaNut(button) {
        if (!button) return;
        button.disabled = false;
        button.hidden = false;
        button.removeAttribute('aria-disabled');
        button.removeAttribute('title');
    }

    function dongBoQuyenGiaoDien() {
        const coQuyen = coQuyenChinhSua();
        const addCategoryButton = document.getElementById('addCategoryBtn');
        const addEquipmentButton = document.getElementById('addEquipmentBtn');
        const saveButton = document.getElementById('popupSaveBtn');

        if (coQuyen) {
            moKhoaNut(addCategoryButton);
            moKhoaNut(addEquipmentButton);
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.textContent = 'Lưu';
            }
            return;
        }

        khoaNut(addCategoryButton);
        khoaNut(addEquipmentButton);
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.textContent = 'Chỉ xem';
        }
    }

    function canhBaoKhongCoQuyen() {
        alert(THONG_BAO_CAM_QUYEN);
    }

    function ensureExtraFields() {
        const statusGroup = document.getElementById('statusGroup');
        if (statusGroup && !document.getElementById('quantityGroup')) {
            statusGroup.insertAdjacentHTML('afterend', `
                <div class="form-group" id="quantityGroup">
                    <label for="itemQuantity">Số Lượng</label>
                    <input type="number" id="itemQuantity" placeholder="Nhập số lượng" min="0" step="1" value="0">
                </div>
                <div class="form-group image-upload-group" id="imageGroup">
                    <label for="itemImages">Ảnh Thiết Bị</label>
                    <div class="product-image-toolbar">
                        <button type="button" class="image-upload-button" id="itemImagesButton">Upload hình ảnh</button>
                        <span class="product-image-summary" id="itemImageSummary">Có thể chọn nhiều ảnh cùng lúc.</span>
                    </div>
                    <input type="file" id="itemImages" class="product-image-input" accept="image/*" multiple>
                    <div class="product-image-preview" id="itemImagePreview">
                        <div class="product-image-empty">Chưa có ảnh</div>
                    </div>
                </div>
            `);
        }

        const status = document.getElementById('itemStatus');
        if (status) {
            status.innerHTML = `
                <option value="San sang">Sẵn sàng</option>
                <option value="Dang thue">Đang thuê</option>
                <option value="Bao tri">Bảo trì</option>
                <option value="Hong">Hỏng</option>
            `;
        }

        bindImageInput();
    }

    function bindImageInput() {
        const input = document.getElementById('itemImages');
        const button = document.getElementById('itemImagesButton');
        if (button && !button.dataset.bound) {
            button.dataset.bound = 'true';
            button.addEventListener('click', () => input && input.click());
        }
        if (input && !input.dataset.bound) {
            input.dataset.bound = 'true';
            input.addEventListener('change', () => {
                addSelectedImages(Array.from(input.files || []));
                input.value = '';
            });
        }
        const preview = document.getElementById('itemImagePreview');
        if (preview && !preview.dataset.bound) {
            preview.dataset.bound = 'true';
            preview.addEventListener('click', (event) => {
                if (!(event.target instanceof Element)) return;
                const button = event.target.closest('[data-image-remove]');
                if (!button) return;
                removePreviewImage(button.dataset.imageKind, Number(button.dataset.imageIndex));
            });
        }
    }

    function releasePreviewUrls() {
        selectedPreviewUrls.forEach((url) => URL.revokeObjectURL(url));
        selectedPreviewUrls = [];
    }

    function parseDeviceImagePaths(value) {
        if (!value) return [];
        if (Array.isArray(value)) {
            return value.map((item) => String(item).trim()).filter(Boolean);
        }

        const raw = String(value).trim();
        if (!raw) return [];

        try {
            const parsed = JSON.parse(raw);
            if (Array.isArray(parsed)) {
                return parsed.map((item) => String(item).trim()).filter(Boolean);
            }
            if (typeof parsed === 'string' && parsed.trim()) {
                return [parsed.trim()];
            }
        } catch (error) {
            // hinh_anh cũ có thể chỉ là một chuỗi đường dẫn, không phải JSON.
        }

        if (raw.includes('|')) {
            return raw.split('|').map((item) => item.trim()).filter(Boolean);
        }
        if (raw.includes(',')) {
            return raw.split(',').map((item) => item.trim()).filter(Boolean);
        }
        return [raw];
    }

    function productImageUrl(path) {
        const value = String(path || '').trim();
        if (!value) return '';
        if (/^(blob:|data:|https?:\/\/)/i.test(value)) return value;
        if (value.startsWith('/')) return AdminApi.imageUrl(value, '');
        if (value.startsWith('assets/images/')) return `${USER_ASSET_BASE}${value}`;
        return AdminApi.imageUrl(value, value);
    }

    function renderDeviceImages(value) {
        const paths = parseDeviceImagePaths(value);
        if (!paths.length) return '<span class="text-muted">Chưa có</span>';

        const firstImage = productImageUrl(paths[0]);
        const moreCount = paths.length - 1;
        return `
            <div class="device-thumb-stack">
                <img class="device-thumb" src="${AdminApi.escapeHtml(firstImage)}" alt="Ảnh thiết bị" onerror="this.style.display='none'">
                ${moreCount > 0 ? `<span class="device-thumb-more">+${moreCount}</span>` : ''}
            </div>
        `;
    }

    function normalizeStatusText(status) {
        return String(status || '')
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/đ/g, 'd')
            .replace(/Đ/g, 'D')
            .toLowerCase()
            .trim()
            .replace(/\s+/g, ' ');
    }

    function deviceStatusKey(status) {
        const normalized = normalizeStatusText(status);
        if (
            normalized === 'san sang'
            || normalized.includes('san sang')
            || normalized.includes('available')
            || normalized.includes('ready')
        ) {
            return 'ready';
        }
        if (
            normalized === 'dang thue'
            || normalized.includes('dang thue')
            || normalized.includes('dang duoc thue')
            || normalized.includes('rented')
        ) {
            return 'rented';
        }
        return '';
    }

    function deviceStatusText(status) {
        const key = deviceStatusKey(status);
        if (key === 'ready') return 'Sẵn sàng';
        if (key === 'rented') return 'Đang thuê';
        return String(status || 'Chưa cập nhật').trim();
    }

    function deviceStatusClass(status) {
        const key = deviceStatusKey(status);
        if (key === 'ready') return 'status-ready';
        if (key === 'rented') return 'status-rented';
        return 'status-unknown';
    }

    function deviceStatusBadge(status) {
        return `<span class="status-badge ${deviceStatusClass(status)}">${AdminApi.escapeHtml(deviceStatusText(status))}</span>`;
    }

    function deviceStatusApiValue(status) {
        const key = deviceStatusKey(status);
        if (key === 'ready') return 'San sang';
        if (key === 'rented') return 'Dang thue';
        return status || 'San sang';
    }

    function addSelectedImages(files) {
        if (!files.length) return;
        files.forEach((file) => {
            const url = URL.createObjectURL(file);
            selectedPreviewUrls.push(url);
            selectedDeviceImages.push({
                id: `new-${nextLocalImageId}`,
                file,
                name: file.name || `Ảnh mới ${nextLocalImageId}`,
                url,
            });
            nextLocalImageId += 1;
        });
        imagesTouched = true;
        renderCurrentImagePreview();
    }

    function removePreviewImage(kind, index) {
        if (!Number.isInteger(index) || index < 0) return;

        if (kind === 'existing') {
            existingDeviceImages.splice(index, 1);
        }

        if (kind === 'new') {
            const removed = selectedDeviceImages.splice(index, 1)[0];
            if (removed && removed.url) {
                URL.revokeObjectURL(removed.url);
                selectedPreviewUrls = selectedPreviewUrls.filter((url) => url !== removed.url);
            }
        }

        imagesTouched = true;
        renderCurrentImagePreview();
    }

    function renderImagePreviewItems(items, summaryText) {
        const preview = document.getElementById('itemImagePreview');
        const summary = document.getElementById('itemImageSummary');
        if (!preview) return;

        if (!items.length) {
            preview.innerHTML = '<div class="product-image-empty">Chưa có ảnh</div>';
        } else {
            preview.innerHTML = items.map((item) => `
                <div class="product-preview-item">
                    <div class="product-preview-media">
                        <img src="${AdminApi.escapeHtml(item.src)}" alt="${AdminApi.escapeHtml(item.name)}" onerror="this.closest('.product-preview-item').style.display='none'">
                        <button type="button" class="product-preview-remove" data-image-remove="true" data-image-kind="${item.kind}" data-image-index="${item.index}" title="Xóa ảnh">×</button>
                    </div>
                    <div class="product-preview-meta">
                        <span class="product-preview-name">${AdminApi.escapeHtml(item.name)}</span>
                        <span class="product-preview-badge">${AdminApi.escapeHtml(item.badge)}</span>
                    </div>
                </div>
            `).join('');
        }

        if (summary) {
            summary.textContent = summaryText || 'Có thể chọn nhiều ảnh cùng lúc.';
        }
    }

    function renderCurrentImagePreview() {
        const existingItems = existingDeviceImages.map((path, index) => ({
            kind: 'existing',
            index,
            src: productImageUrl(path),
            name: `Ảnh ${index + 1}`,
            badge: 'Đã lưu',
        }));
        const newItems = selectedDeviceImages.map((item, index) => ({
            kind: 'new',
            index,
            src: item.url,
            name: item.name,
            badge: 'Mới',
        }));
        const items = [...existingItems, ...newItems];
        const total = items.length;
        let summaryText = 'Bấm upload để thêm ảnh sản phẩm.';
        if (total) {
            summaryText = `Đang có ${total} ảnh. Bấm upload để thêm ảnh hoặc xóa từng ảnh trong khung.`;
        }
        if (imagesTouched && !total) {
            summaryText = 'Bạn đã xóa hết ảnh. Bấm Lưu để cập nhật hoặc upload ảnh mới.';
        }
        renderImagePreviewItems(items, summaryText);
    }

    function resetImageSelection(existingImages = '') {
        releasePreviewUrls();
        existingDeviceImages = parseDeviceImagePaths(existingImages);
        selectedDeviceImages = [];
        imagesTouched = false;
        nextLocalImageId = 1;
        const input = document.getElementById('itemImages');
        if (input) input.value = '';
        renderCurrentImagePreview();
    }

    function currentExistingImagePayload() {
        return existingDeviceImages.slice();
    }

    function currentNewImageFiles() {
        return selectedDeviceImages.map((item) => item.file).filter(Boolean);
    }

    async function loadData() {
        AdminApi.requireAuth();
        await AdminApi.optional(() => AdminApi.loadCurrentAccount(), null);
        dongBoQuyenGiaoDien();
        const categoryBody = document.querySelector('#categoryTable tbody');
        const equipmentBody = document.querySelector('#equipmentTable tbody');
        if (categoryBody) categoryBody.innerHTML = '<tr><td colspan="4">Đang tải...</td></tr>';
        if (equipmentBody) equipmentBody.innerHTML = '<tr><td colspan="8">Đang tải...</td></tr>';

        try {
            const [categoryItems, deviceItems] = await Promise.all([
                AdminApi.getAll('/categories'),
                AdminApi.getAll('/devices'),
            ]);
            categories = categoryItems;
            devices = deviceItems;
            renderCategoryTable();
            renderEquipmentTable();
            buildCategoryOptions();
        } catch (error) {
            if (categoryBody) categoryBody.innerHTML = `<tr><td colspan="4">${AdminApi.escapeHtml(error.message)}</td></tr>`;
            if (equipmentBody) equipmentBody.innerHTML = `<tr><td colspan="8">${AdminApi.escapeHtml(error.message)}</td></tr>`;
        }
    }

    function renderCategoryTable() {
        const tbody = document.querySelector('#categoryTable tbody');
        if (!tbody) return;
        tbody.innerHTML = categories.map((item) => `
            <tr>
                <td>${item.id_danh_muc}</td>
                <td>${AdminApi.escapeHtml(item.ten_danh_muc || '')}</td>
                <td>${AdminApi.escapeHtml(item.mo_ta || '')}</td>
                <td>
                    ${coQuyenChinhSua() ? `
                    <div class="table-row-action">
                        <button class="card-btn" onclick="openCategoryForm(${item.id_danh_muc})">Sửa</button>
                        <button class="card-btn btn-danger" onclick="deleteCategory(${item.id_danh_muc})">Xóa</button>
                    </div>
                    ` : '<span class="text-muted">Chỉ xem</span>'}
                </td>
            </tr>
        `).join('') || '<tr><td colspan="4">Không có danh mục.</td></tr>';
    }

    function renderEquipmentTable() {
        const tbody = document.querySelector('#equipmentTable tbody');
        if (!tbody) return;
        tbody.innerHTML = devices.map((item) => {
            const category = item.danh_muc || item.category || categories.find((cat) => cat.id_danh_muc === item.id_danh_muc);
            return `
                <tr>
                    <td>${item.id_thiet_bi}</td>
                    <td>${renderDeviceImages(item.hinh_anh)}</td>
                    <td>${AdminApi.escapeHtml(item.ten_thiet_bi || '')}</td>
                    <td>${AdminApi.escapeHtml(category ? category.ten_danh_muc : 'Chưa xác định')}</td>
                    <td>${AdminApi.formatCurrency(item.gia_thue)}</td>
                    <td>${deviceStatusBadge(item.tinh_trang)}</td>
                    <td>${AdminApi.escapeHtml(item.mo_ta || '')}</td>
                    <td>
                        ${coQuyenChinhSua() ? `
                        <div class="table-row-action">
                            <button class="card-btn" onclick="openEquipmentForm(${item.id_thiet_bi})">Sửa</button>
                            <button class="card-btn btn-danger" onclick="deleteEquipment(${item.id_thiet_bi})">Xóa</button>
                        </div>
                        ` : '<span class="text-muted">Chỉ xem</span>'}
                    </td>
                </tr>
            `;
        }).join('') || '<tr><td colspan="8">Không có thiết bị.</td></tr>';
    }

    function buildCategoryOptions(selectedId) {
        const select = document.getElementById('itemCategory');
        if (!select) return;
        select.innerHTML = categories.map((cat) => `
            <option value="${cat.id_danh_muc}" ${Number(selectedId) === cat.id_danh_muc ? 'selected' : ''}>${AdminApi.escapeHtml(cat.ten_danh_muc || '')}</option>
        `).join('');
    }

    function showPopup() {
        document.getElementById('formPopup').classList.add('active');
    }

    function closeFormPopup() {
        document.getElementById('formPopup').classList.remove('active');
    }

    function openCategoryForm(categoryId = null) {
        if (!coQuyenChinhSua()) {
            canhBaoKhongCoQuyen();
            return;
        }
        ensureExtraFields();
        document.getElementById('formType').value = 'category';
        document.getElementById('categorySelectGroup').style.display = 'none';
        document.getElementById('rentPriceGroup').style.display = 'none';
        document.getElementById('statusGroup').style.display = 'none';
        document.getElementById('quantityGroup').style.display = 'none';
        document.getElementById('imageGroup').style.display = 'none';
        resetImageSelection();
        document.getElementById('descriptionGroup').style.display = 'block';
        document.getElementById('itemName').placeholder = 'Nhập tên danh mục';
        document.getElementById('popupTitle').textContent = categoryId ? 'Sửa danh mục' : 'Thêm danh mục';
        document.getElementById('itemName').value = '';
        document.getElementById('itemDescription').value = '';
        document.getElementById('formId').value = categoryId || '';
        document.getElementById('formNote').textContent = 'Điền tên và mô tả danh mục.';

        if (categoryId) {
            const category = categories.find((item) => item.id_danh_muc === categoryId);
            if (category) {
                document.getElementById('itemName').value = category.ten_danh_muc || '';
                document.getElementById('itemDescription').value = category.mo_ta || '';
            }
        }
        showPopup();
    }

    function openEquipmentForm(equipmentId = null) {
        if (!coQuyenChinhSua()) {
            canhBaoKhongCoQuyen();
            return;
        }
        ensureExtraFields();
        document.getElementById('formType').value = 'equipment';
        document.getElementById('categorySelectGroup').style.display = 'block';
        document.getElementById('rentPriceGroup').style.display = 'block';
        document.getElementById('statusGroup').style.display = 'block';
        document.getElementById('quantityGroup').style.display = 'block';
        document.getElementById('imageGroup').style.display = 'block';
        document.getElementById('descriptionGroup').style.display = 'block';
        document.getElementById('itemName').placeholder = 'Nhập tên thiết bị';
        document.getElementById('popupTitle').textContent = equipmentId ? 'Sửa thiết bị' : 'Thêm thiết bị';
        document.getElementById('itemName').value = '';
        document.getElementById('itemPrice').value = '';
        document.getElementById('itemQuantity').value = '0';
        document.getElementById('itemDescription').value = '';
        document.getElementById('itemStatus').value = 'San sang';
        resetImageSelection();
        document.getElementById('formId').value = equipmentId || '';
        document.getElementById('formNote').textContent = 'Điền đầy đủ thông tin thiết bị, chọn danh mục phù hợp.';
        buildCategoryOptions();

        if (equipmentId) {
            const equipment = devices.find((item) => item.id_thiet_bi === equipmentId);
            if (equipment) {
                document.getElementById('itemName').value = equipment.ten_thiet_bi || '';
                document.getElementById('itemCategory').value = equipment.id_danh_muc || '';
                document.getElementById('itemPrice').value = equipment.gia_thue || 0;
                document.getElementById('itemQuantity').value = equipment.so_luong || 0;
                document.getElementById('itemStatus').value = deviceStatusApiValue(equipment.tinh_trang);
                document.getElementById('itemDescription').value = equipment.mo_ta || '';
                resetImageSelection(equipment.hinh_anh || '');
            }
        }
        showPopup();
    }

    async function uploadDeviceImages(deviceId, keptImages, files) {
        if (!imagesTouched && !files.length) return;
        const formData = new FormData();
        formData.append('existing_images', JSON.stringify(keptImages));
        files.forEach((file) => formData.append('images', file));

        // Trình duyệt chỉ preview/xóa tạm; backend nhận danh sách còn giữ và ảnh mới để cập nhật thật.
        try {
            await AdminApi.apiFetch(`/devices/${deviceId}/images`, {
                method: 'POST',
                body: formData,
            });
        } catch (error) {
            if (/404|not found/i.test(error.message || '')) {
                throw new Error('Chưa có API upload nhiều ảnh sản phẩm. Hãy khởi động lại backend sau khi thêm route /devices/{id}/images.');
            }
            throw error;
        }
    }

    async function saveForm(event) {
        event.preventDefault();
        event.stopImmediatePropagation();

        if (!coQuyenChinhSua()) {
            canhBaoKhongCoQuyen();
            return;
        }

        const type = document.getElementById('formType').value;
        const formId = Number(document.getElementById('formId').value || 0);
        const name = document.getElementById('itemName').value.trim();
        const description = document.getElementById('itemDescription').value.trim();

        if (!name) {
            alert('Tên không được để trống.');
            return;
        }

        try {
            if (type === 'category') {
                const body = { ten_danh_muc: name, mo_ta: description };
                if (formId) {
                    await AdminApi.apiFetch(`/categories/${formId}`, { method: 'PUT', body });
                } else {
                    await AdminApi.apiFetch('/categories', { method: 'POST', body });
                }
            }

            if (type === 'equipment') {
                const categoryId = Number(document.getElementById('itemCategory').value);
                if (!categoryId) {
                    alert('Vui lòng chọn danh mục.');
                    return;
                }
                const body = {
                    ten_thiet_bi: name,
                    id_danh_muc: categoryId,
                    gia_thue: Number(document.getElementById('itemPrice').value) || 0,
                    so_luong: Number(document.getElementById('itemQuantity').value) || 0,
                    tinh_trang: document.getElementById('itemStatus').value,
                    mo_ta: description,
                };
                const saved = formId
                    ? await AdminApi.apiFetch(`/devices/${formId}`, { method: 'PUT', body })
                    : await AdminApi.apiFetch('/devices', { method: 'POST', body });
                await uploadDeviceImages(
                    saved.id_thiet_bi,
                    currentExistingImagePayload(),
                    currentNewImageFiles()
                );
            }

            closeFormPopup();
            await loadData();
        } catch (error) {
            alert(error.message || 'Không lưu được dữ liệu.');
        }
    }

    async function deleteCategory(categoryId) {
        if (!coQuyenChinhSua()) {
            canhBaoKhongCoQuyen();
            return;
        }
        if (!confirm('Bạn có chắc muốn xóa danh mục này không?')) return;
        try {
            await AdminApi.apiFetch(`/categories/${categoryId}`, { method: 'DELETE' });
            await loadData();
        } catch (error) {
            alert(error.message || 'Không thể xóa danh mục.');
        }
    }

    async function deleteEquipment(equipmentId) {
        if (!coQuyenChinhSua()) {
            canhBaoKhongCoQuyen();
            return;
        }
        if (!confirm('Bạn có chắc muốn xóa thiết bị này không?')) return;
        try {
            await AdminApi.apiFetch(`/devices/${equipmentId}`, { method: 'DELETE' });
            await loadData();
        } catch (error) {
            alert(error.message || 'Không thể xóa thiết bị.');
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        ensureExtraFields();
        window.renderCategoryTable = renderCategoryTable;
        window.renderEquipmentTable = renderEquipmentTable;
        window.buildCategoryOptions = buildCategoryOptions;
        window.openCategoryForm = openCategoryForm;
        window.openEquipmentForm = openEquipmentForm;
        window.showPopup = showPopup;
        window.closeFormPopup = closeFormPopup;
        window.saveForm = saveForm;
        window.deleteCategory = deleteCategory;
        window.deleteEquipment = deleteEquipment;

        const form = document.getElementById('popupForm');
        if (form) {
            form.addEventListener('submit', saveForm, true);
        }
        loadData();
    });
})();
