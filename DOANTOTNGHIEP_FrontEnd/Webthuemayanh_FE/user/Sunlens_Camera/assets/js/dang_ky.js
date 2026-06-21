'use strict';

const REGISTER_API_URL = 'http://127.0.0.1:8000/api/v1/auth/register';
const MAX_IMAGE_SIZE = 5 * 1024 * 1024;
const ALLOWED_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);
const ALLOWED_IMAGE_EXTENSIONS = new Set(['jpg', 'jpeg', 'png', 'webp']);

function validateImageFile(file) {
    if (!file || file.size > MAX_IMAGE_SIZE) {
        return false;
    }

    const extension = file.name.split('.').pop().toLowerCase();
    return ALLOWED_IMAGE_TYPES.has(file.type) && ALLOWED_IMAGE_EXTENSIONS.has(extension);
}

function clearFilePreview(fileNameBox, preview) {
    fileNameBox.textContent = '';
    preview.removeAttribute('src');
    preview.style.display = 'none';
}

function handleFilePreview(inputId, fileNameId, previewId) {
    const input = document.getElementById(inputId);
    const fileNameBox = document.getElementById(fileNameId);
    const preview = document.getElementById(previewId);

    if (!input || !fileNameBox || !preview) {
        return;
    }

    input.addEventListener('change', function () {
        const file = this.files[0];

        if (!file) {
            clearFilePreview(fileNameBox, preview);
            return;
        }

        if (!validateImageFile(file)) {
            this.value = '';
            clearFilePreview(fileNameBox, preview);
            showRegisterError('Vui lòng chọn file ảnh hợp lệ dưới 5MB.');
            this.focus();
            return;
        }

        fileNameBox.textContent = `File đã chọn: ${file.name}`;
        clearRegisterMessage();

        const reader = new FileReader();
        reader.onload = function (event) {
            preview.src = event.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    });
}

function getRegisterForm() {
    return document.getElementById('registerForm');
}

function clearRegisterMessage() {
    const messageBox = document.getElementById('registerMessage');
    if (!messageBox) {
        return;
    }

    messageBox.className = 'register-message';
    messageBox.replaceChildren();
}

function checkRegisterForm() {
    const form = getRegisterForm();
    if (!form) {
        return false;
    }

    const textFieldIds = [
        'registerUsername',
        'registerPassword',
        'registerFullName',
        'registerPhone',
        'registerCccd',
        'registerEmail',
    ];

    for (const fieldId of textFieldIds) {
        const field = document.getElementById(fieldId);
        if (!field || !field.value.trim()) {
            showRegisterError('Vui lòng nhập đầy đủ thông tin đăng ký.');
            if (field) field.focus();
            return false;
        }
    }

    if (!form.checkValidity()) {
        showRegisterError('Vui lòng kiểm tra lại thông tin đăng ký.');
        form.reportValidity();
        return false;
    }

    for (const inputId of ['cccdTruoc', 'cccdSau']) {
        const input = document.getElementById(inputId);
        if (!validateImageFile(input.files[0])) {
            showRegisterError('Vui lòng chọn file ảnh hợp lệ dưới 5MB.');
            input.focus();
            return false;
        }
    }

    return true;
}

function normalizeRegisterErrors(detail) {
    if (Array.isArray(detail)) {
        return detail.map((item) => {
            if (typeof item === 'string') return item;
            if (item && typeof item.msg === 'string') {
                const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : '';
                return field ? `${field}: ${item.msg}` : item.msg;
            }
            return JSON.stringify(item);
        });
    }

    if (typeof detail === 'string' && detail.trim()) {
        return [detail];
    }

    return ['Đăng ký thất bại. Vui lòng thử lại.'];
}

function focusRegisterField(messages) {
    const combinedMessage = messages.join(' ').toLowerCase();
    const fieldMap = [
        { keywords: ['tên đăng nhập', 'username'], id: 'registerUsername' },
        { keywords: ['số điện thoại', 'điện thoại', 'sdt'], id: 'registerPhone' },
        { keywords: ['cccd_truoc'], id: 'cccdTruoc' },
        { keywords: ['cccd_sau'], id: 'cccdSau' },
        { keywords: ['số cccd', 'cccd'], id: 'registerCccd' },
        { keywords: ['email'], id: 'registerEmail' },
        { keywords: ['mật khẩu', 'password'], id: 'registerPassword' },
    ];

    const match = fieldMap.find((item) =>
        item.keywords.some((keyword) => combinedMessage.includes(keyword))
    );

    if (match) {
        document.getElementById(match.id).focus();
    }
}

async function submitRegisterForm() {
    const form = getRegisterForm();
    const submitButton = document.getElementById('registerSubmit');
    let registered = false;

    if (!form || !checkRegisterForm()) {
        return;
    }

    clearRegisterMessage();

    const formData = new FormData();
    formData.append('ten_dang_nhap', document.getElementById('registerUsername').value.trim());
    formData.append('mat_khau', document.getElementById('registerPassword').value);
    formData.append('ho_ten', document.getElementById('registerFullName').value.trim());
    formData.append('sdt', document.getElementById('registerPhone').value.trim());
    formData.append('cccd', document.getElementById('registerCccd').value.trim());
    formData.append('thu_dien_tu', document.getElementById('registerEmail').value.trim());
    formData.append('anh_cccd_mat_truoc', document.getElementById('cccdTruoc').files[0]);
    formData.append('anh_cccd_mat_sau', document.getElementById('cccdSau').files[0]);

    if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Đang đăng ký...';
    }

    try {
        const response = await fetch(REGISTER_API_URL, {
            method: 'POST',
            body: formData,
        });
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            const messages = normalizeRegisterErrors(data.detail);
            showRegisterError(messages);
            focusRegisterField(messages);
            return;
        }

        showRegisterSuccess('Đăng ký thành công');
        registered = true;
        if (submitButton) {
            submitButton.textContent = 'Đăng ký thành công';
        }
        window.setTimeout(() => {
            window.location.href = 'dang_nhap.html';
        }, 1500);
    } catch (error) {
        showRegisterError('Không thể kết nối đến máy chủ. Vui lòng thử lại.');
    } finally {
        if (submitButton && !registered) {
            submitButton.disabled = false;
            submitButton.textContent = 'Đăng ký';
        }
    }
}

function showRegisterError(message) {
    const messageBox = document.getElementById('registerMessage');
    if (!messageBox) {
        return;
    }

    const messages = Array.isArray(message) ? message : [message];
    messageBox.className = 'register-message is-error';
    messageBox.replaceChildren();

    if (messages.length === 1) {
        messageBox.textContent = messages[0];
        return;
    }

    const list = document.createElement('ul');
    messages.forEach((item) => {
        const listItem = document.createElement('li');
        listItem.textContent = item;
        list.appendChild(listItem);
    });
    messageBox.appendChild(list);
}

function showRegisterSuccess(message) {
    const messageBox = document.getElementById('registerMessage');
    if (!messageBox) {
        return;
    }

    messageBox.className = 'register-message is-success';
    messageBox.textContent = message;
}

document.addEventListener('DOMContentLoaded', function () {
    const form = getRegisterForm();
    if (!form) {
        return;
    }

    handleFilePreview('cccdTruoc', 'cccdTruocFileName', 'cccdTruocPreview');
    handleFilePreview('cccdSau', 'cccdSauFileName', 'cccdSauPreview');

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        submitRegisterForm();
    });
});
