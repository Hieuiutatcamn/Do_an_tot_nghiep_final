(function () {
    'use strict';

    const API_BASE_URL = window.SUNLENS_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
    const STORAGE_KEY = 'sunlens_user_management_items';

    let users = loadUsers();
    let editingId = null;
    let selectedFiles = {
        front: null,
        back: null,
    };

    const form = document.getElementById('userForm');
    const messageBox = document.getElementById('userMessage');
    const tableBody = document.getElementById('userTableBody');
    const submitBtn = document.getElementById('submitBtn');
    const cancelEditBtn = document.getElementById('cancelEditBtn');
    const newUserBtn = document.getElementById('newUserBtn');
    const userCount = document.getElementById('userCount');
    const formTitle = document.getElementById('formTitle');
    const formModeBadge = document.getElementById('formModeBadge');

    const fields = {
        id: document.getElementById('userId'),
        fullName: document.getElementById('fullName'),
        phone: document.getElementById('phone'),
        email: document.getElementById('email'),
        address: document.getElementById('address'),
        identityNumber: document.getElementById('identityNumber'),
        frontInput: document.getElementById('cccdFront'),
        backInput: document.getElementById('cccdBack'),
        frontPreviewWrap: document.getElementById('frontPreviewWrap'),
        backPreviewWrap: document.getElementById('backPreviewWrap'),
        frontPreview: document.getElementById('frontPreview'),
        backPreview: document.getElementById('backPreview'),
        frontPath: document.getElementById('frontPath'),
        backPath: document.getElementById('backPath'),
    };

    function loadUsers() {
        try {
            const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            return Array.isArray(saved) ? saved : [];
        } catch (error) {
            console.warn('Không đọc được dữ liệu người dùng trong localStorage.', error);
            return [];
        }
    }

    function saveUsers() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(users));
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

    function imageSrc(path) {
        if (!path) return '';
        if (/^(blob:|data:|https?:)/i.test(path)) return path;
        const separator = path.includes('?') ? '&' : '?';
        return `${path}${separator}v=${Date.now()}`;
    }

    function nextUserId() {
        const ids = users
            .map((user) => Number(user.id))
            .filter((id) => Number.isFinite(id));
        return (ids.length ? Math.max(...ids) : 0) + 1;
    }

    function showMessage(text, type = 'success') {
        messageBox.textContent = text;
        messageBox.className = `alert alert-${type}`;
        messageBox.classList.remove('d-none');
    }

    function hideMessage() {
        messageBox.classList.add('d-none');
        messageBox.textContent = '';
    }

    function setPreview(type, src, pathText) {
        const previewWrap = type === 'front' ? fields.frontPreviewWrap : fields.backPreviewWrap;
        const preview = type === 'front' ? fields.frontPreview : fields.backPreview;
        const path = type === 'front' ? fields.frontPath : fields.backPath;

        if (!src) {
            preview.src = '';
            path.textContent = '';
            previewWrap.classList.add('d-none');
            return;
        }

        preview.src = imageSrc(src);
        path.textContent = pathText || src;
        previewWrap.classList.remove('d-none');
    }

    function clearPreviews() {
        setPreview('front', '', '');
        setPreview('back', '', '');
    }

    function renderImageCell(path, alt) {
        if (!path) {
            return '<span class="text-muted">Chưa có</span>';
        }

        return `
            <a href="${escapeHtml(path)}" target="_blank" rel="noopener">
                <img class="cccd-thumb" src="${escapeHtml(imageSrc(path))}" alt="${escapeHtml(alt)}">
            </a>
            <span class="table-image-path">${escapeHtml(path)}</span>
        `;
    }

    function renderUsers() {
        userCount.textContent = users.length;

        if (!users.length) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">Chưa có người dùng.</td></tr>';
            return;
        }

        tableBody.innerHTML = users.map((user) => `
            <tr data-id="${escapeHtml(user.id)}">
                <td>${escapeHtml(user.id)}</td>
                <td>
                    <strong>${escapeHtml(user.fullName)}</strong>
                    <div class="user-contact">${escapeHtml(user.address)}</div>
                </td>
                <td>
                    <div>${escapeHtml(user.phone)}</div>
                    <div class="user-contact">${escapeHtml(user.thu_dien_tu || user.email)}</div>
                </td>
                <td>${escapeHtml(user.identityNumber)}</td>
                <td>${renderImageCell(user.cccdFrontPath, 'CCCD mặt trước')}</td>
                <td>${renderImageCell(user.cccdBackPath, 'CCCD mặt sau')}</td>
                <td>
                    <button type="button" class="btn btn-sm btn-outline-primary" data-action="edit" data-id="${escapeHtml(user.id)}">
                        <i class="bi bi-pencil-square me-1"></i>
                        <span>Sửa</span>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    function updateFormMode(user = null) {
        const isEditing = Boolean(user);
        formTitle.textContent = isEditing ? 'Cập nhật người dùng' : 'Thêm người dùng';
        formModeBadge.textContent = isEditing ? 'Sửa' : 'Thêm';
        submitBtn.innerHTML = isEditing
            ? '<i class="bi bi-save me-1"></i><span>Cập nhật</span>'
            : '<i class="bi bi-plus-circle me-1"></i><span>Thêm</span>';
        cancelEditBtn.classList.toggle('d-none', !isEditing);

        fields.frontInput.required = !isEditing || !user.cccdFrontPath;
        fields.backInput.required = !isEditing || !user.cccdBackPath;
    }

    function resetForm() {
        editingId = null;
        selectedFiles = { front: null, back: null };
        form.reset();
        form.classList.remove('was-validated');
        fields.id.value = '';
        clearPreviews();
        updateFormMode(null);
        hideMessage();
    }

    function getFormPayload(userId) {
        return {
            id: userId,
            fullName: fields.fullName.value.trim(),
            phone: fields.phone.value.trim(),
            thu_dien_tu: fields.email.value.trim(),
            address: fields.address.value.trim(),
            identityNumber: fields.identityNumber.value.trim(),
        };
    }

    function validateImageFile(input, type) {
        const file = input.files && input.files[0];
        selectedFiles[type] = null;

        if (!file) return;

        if (!file.type.startsWith('image/')) {
            input.value = '';
            showMessage('Vui lòng chọn đúng file ảnh.', 'danger');
            return;
        }

        selectedFiles[type] = file;
        setPreview(type, URL.createObjectURL(file), file.name);
        hideMessage();
    }

    async function uploadCccdImage(file, side, userId) {
        if (!file) return '';

        const formData = new FormData();
        formData.append('file', file);
        formData.append('side', side);
        formData.append('user_id', String(userId));

        try {
            const response = await fetch(`${API_BASE_URL}/users/upload-cccd`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(data.detail || `Upload ảnh thất bại (${response.status}).`);
            }
            if (!data.path) {
                throw new Error('API upload chưa trả về đường dẫn ảnh.');
            }
            return data.path;
        } catch (error) {
            if (error instanceof TypeError) {
                throw new Error('Không kết nối được API upload. Hãy chạy FastAPI mẫu trước khi lưu ảnh.');
            }
            throw error;
        }
    }

    async function handleSubmit(event) {
        event.preventDefault();
        event.stopPropagation();

        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }

        const isEditing = editingId !== null;
        const nguoiDungHienTai = isEditing
            ? users.find((user) => String(user.id) === String(editingId))
            : null;

        if (isEditing && !nguoiDungHienTai) {
            showMessage('Không tìm thấy người dùng cần cập nhật.', 'danger');
            return;
        }

        const userId = isEditing ? nguoiDungHienTai.id : nextUserId();

        if (!isEditing && (!selectedFiles.front || !selectedFiles.back)) {
            showMessage('Vui lòng chọn đủ ảnh CCCD mặt trước và mặt sau.', 'danger');
            return;
        }

        setSubmitting(true);
        hideMessage();

        try {
            let cccdFrontPath = nguoiDungHienTai ? nguoiDungHienTai.cccdFrontPath : '';
            let cccdBackPath = nguoiDungHienTai ? nguoiDungHienTai.cccdBackPath : '';

            // Trình duyệt không tự ghi file vào folder local; file được gửi API để backend lưu.
            if (selectedFiles.front) {
                cccdFrontPath = await uploadCccdImage(selectedFiles.front, 'front', userId);
            }
            if (selectedFiles.back) {
                cccdBackPath = await uploadCccdImage(selectedFiles.back, 'back', userId);
            }

            const payload = {
                ...getFormPayload(userId),
                cccdFrontPath,
                cccdBackPath,
                updatedAt: new Date().toISOString(),
            };

            const successMessage = isEditing
                ? 'Cập nhật người dùng thành công.'
                : 'Thêm người dùng thành công.';

            if (isEditing) {
                users = users.map((user) => String(user.id) === String(userId) ? payload : user);
            } else {
                users.unshift({
                    ...payload,
                    createdAt: new Date().toISOString(),
                });
            }

            saveUsers();
            renderUsers();
            resetForm();
            showMessage(successMessage);
        } catch (error) {
            showMessage(error.message || 'Không lưu được dữ liệu.', 'danger');
        } finally {
            setSubmitting(false);
        }
    }

    function setSubmitting(isSubmitting) {
        submitBtn.disabled = isSubmitting;
        cancelEditBtn.disabled = isSubmitting;
        if (isSubmitting) {
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span><span>Đang lưu...</span>';
            return;
        }
        const nguoiDungHienTai = editingId !== null
            ? users.find((user) => String(user.id) === String(editingId))
            : null;
        updateFormMode(nguoiDungHienTai || null);
    }

    function authToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
    }

    async function readPasswordResponse(response) {
        const contentType = response.headers.get('content-type') || '';
        if (response.status === 204) return null;
        return contentType.includes('application/json')
            ? response.json()
            : response.text();
    }

    function passwordApiMessage(data, statusCode) {
        if (data && typeof data === 'object') {
            const detail = data.detail || data.message || data.error;
            if (Array.isArray(detail)) {
                return detail.map((item) => item.msg || item.message || JSON.stringify(item)).join('\n');
            }
            if (detail) return detail;
        }
        if (typeof data === 'string' && data.trim()) return data.trim();
        return `API lỗi ${statusCode}`;
    }

    function setChangePasswordMessage(message, type = 'success') {
        const messageEl = document.getElementById('changePasswordMessage');
        if (!messageEl) return;
        messageEl.textContent = message || '';
        messageEl.className = `small mt-3 fw-semibold ${type === 'success' ? 'text-success' : 'text-danger'}`;
    }

    async function changePasswordRequest(payload) {
        const token = authToken();
        if (!token) {
            throw new Error('Bạn cần đăng nhập để đổi mật khẩu.');
        }

        const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
            method: 'PUT',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });
        const data = await readPasswordResponse(response);
        if (!response.ok) {
            throw new Error(passwordApiMessage(data, response.status));
        }
        return data;
    }

    async function handleChangePasswordSubmit(event) {
        event.preventDefault();

        const changePasswordForm = document.getElementById('changePasswordForm');
        const button = document.getElementById('changePasswordBtn');
        const currentPassword = document.getElementById('currentPassword');
        const newPassword = document.getElementById('newPassword');
        const confirmPassword = document.getElementById('confirmPassword');

        if (!changePasswordForm || !currentPassword || !newPassword || !confirmPassword) return;
        setChangePasswordMessage('', 'success');

        if (!currentPassword.value.trim() || !newPassword.value.trim() || !confirmPassword.value.trim()) {
            changePasswordForm.classList.add('was-validated');
            setChangePasswordMessage('Vui lòng nhập đầy đủ thông tin đổi mật khẩu.', 'danger');
            return;
        }
        if (newPassword.value.length < 6) {
            setChangePasswordMessage('Mật khẩu mới tối thiểu 6 ký tự.', 'danger');
            return;
        }
        if (newPassword.value !== confirmPassword.value) {
            setChangePasswordMessage('Xác nhận mật khẩu không khớp.', 'danger');
            return;
        }

        if (button) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = 'Đang lưu...';
        }

        try {
            const data = await changePasswordRequest({
                mat_khau_hien_tai: currentPassword.value,
                mat_khau_moi: newPassword.value,
            });
            changePasswordForm.reset();
            changePasswordForm.classList.remove('was-validated');
            setChangePasswordMessage((data && data.message) || 'Đổi mật khẩu thành công.', 'success');
        } catch (error) {
            setChangePasswordMessage(error.message || 'Không đổi được mật khẩu.', 'danger');
        } finally {
            if (button) {
                button.disabled = false;
                button.textContent = button.dataset.originalText || 'Lưu mật khẩu';
            }
        }
    }

    function startEdit(userId) {
        const user = users.find((item) => String(item.id) === String(userId));
        if (!user) return;

        editingId = user.id;
        selectedFiles = { front: null, back: null };
        form.classList.remove('was-validated');

        fields.id.value = user.id;
        fields.fullName.value = user.fullName || '';
        fields.phone.value = user.phone || '';
        fields.email.value = user.thu_dien_tu || user.email || '';
        fields.address.value = user.address || '';
        fields.identityNumber.value = user.identityNumber || '';
        fields.frontInput.value = '';
        fields.backInput.value = '';

        setPreview('front', user.cccdFrontPath, user.cccdFrontPath);
        setPreview('back', user.cccdBackPath, user.cccdBackPath);
        updateFormMode(user);
        hideMessage();
        form.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    fields.frontInput.addEventListener('change', () => validateImageFile(fields.frontInput, 'front'));
    fields.backInput.addEventListener('change', () => validateImageFile(fields.backInput, 'back'));
    form.addEventListener('submit', handleSubmit);
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', handleChangePasswordSubmit);
    }
    cancelEditBtn.addEventListener('click', resetForm);
    newUserBtn.addEventListener('click', resetForm);
    tableBody.addEventListener('click', (event) => {
        const button = event.target.closest('[data-action="edit"]');
        if (button) {
            startEdit(button.dataset.id);
        }
    });

    updateFormMode(null);
    renderUsers();
})();
