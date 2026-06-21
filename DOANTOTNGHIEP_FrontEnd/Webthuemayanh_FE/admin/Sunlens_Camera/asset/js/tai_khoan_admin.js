(function () {
    'use strict';

    let accounts = [];
    let customers = [];
    let employees = [];
    let rows = [];
    let addCccdFiles = {
        front: null,
        back: null,
    };

    async function loadUsers() {
        AdminApi.requireAuth();
        const tbody = document.querySelector('.data-table tbody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="6">Đang tải...</td></tr>';

        try {
            const [accountItems, customerItems, employeeItems] = await Promise.all([
                AdminApi.getAll('/accounts'),
                AdminApi.optional(() => AdminApi.getAll('/customers'), []),
                AdminApi.optional(() => AdminApi.getAll('/employees'), []),
            ]);
            accounts = accountItems;
            customers = customerItems;
            employees = employeeItems;
            rows = accounts.map(buildRow);
            renderUsers();
        } catch (error) {
            if (tbody) tbody.innerHTML = `<tr><td colspan="6">${AdminApi.escapeHtml(error.message || 'Không tải được tài khoản. Tài khoản hiện tại cần quyền Admin.')}</td></tr>`;
        }
    }

    function buildRow(account) {
        const customer = customers.find((item) => item.id_tai_khoan === account.id_tai_khoan);
        const employee = employees.find((item) => item.id_tai_khoan === account.id_tai_khoan);
        const profile = customer || employee || null;
        return {
            account,
            customer,
            employee,
            profile,
            name: profile ? profile.ho_ten : account.dang_nhap,
            role: AdminApi.roleToUi(account.vai_tro),
            status: AdminApi.accountStatusToUi(account),
        };
    }

    function renderUsers() {
        const tbody = document.querySelector('.data-table tbody');
        if (!tbody) return;
        tbody.innerHTML = rows.map((row) => {
            const account = row.account;
            const initials = AdminApi.initials(row.name);
            const statusLabel = row.status === 'active' ? 'active' : 'locked';
            const statusClass = row.status === 'active' ? 'completed' : 'danger';
            const buttonClass = row.status === 'active' ? 'btn-lock' : 'btn-unlock';
            const buttonText = row.status === 'active' ? 'Khóa TK' : 'Mở Khóa';
            return `
                <tr data-id="${account.id_tai_khoan}" data-username="${AdminApi.escapeHtml(account.dang_nhap)}" data-role="${row.role}" data-status="${row.status}">
                    <td>${account.id_tai_khoan}</td>
                    <td>${AdminApi.escapeHtml(account.dang_nhap)}</td>
                    <td><div class="table-user"><div class="table-avatar">${initials}</div><div class="table-user-info"><span class="table-user-name">${AdminApi.escapeHtml(row.name)}</span></div></div></td>
                    <td>${AdminApi.escapeHtml(row.role)}</td>
                    <td><span class="status-badge ${statusClass}">${statusLabel}</span></td>
                    <td>
                        <button class="card-btn btn-edit" style="padding:6px 12px;margin-right:6px;" onclick="event.stopPropagation(); editUser(${account.id_tai_khoan})">Sửa</button>
                        <button class="card-btn ${buttonClass}" style="padding:6px 12px;" onclick="event.stopPropagation(); toggleLockAccount(${account.id_tai_khoan}, '${row.status}')">${buttonText}</button>
                    </td>
                </tr>
            `;
        }).join('') || '<tr><td colspan="6">Không có tài khoản.</td></tr>';

        tbody.querySelectorAll('tr[data-id]').forEach((tr) => {
            tr.style.cursor = 'pointer';
            tr.addEventListener('click', () => editUser(tr.dataset.id));
        });
    }

    function editUser(userId) {
        window.location.href = `chi_tiet_tai_khoan.html?id=${userId}`;
    }

    async function toggleLockAccount(userId, currentStatus) {
        const nextStatus = currentStatus === 'locked' ? 'active' : 'locked';
        const message = nextStatus === 'active' ? 'mở khóa' : 'khóa';
        if (!confirm(`Bạn có chắc muốn ${message} tài khoản này?`)) return;

        try {
            await AdminApi.apiFetch(`/accounts/${userId}`, {
                method: 'PUT',
                body: AdminApi.accountStatusToApi(nextStatus),
            });
            await loadUsers();
            alert(`Tài khoản ${userId} đã ${message} thành công!`);
        } catch (error) {
            alert(error.message || 'Không cập nhật được tài khoản.');
        }
    }

    function roleNeedsProfile(role) {
        return role === 'Khach hang' || role === 'Nhan vien';
    }

    function updateAddUserProfileFields() {
        const role = document.getElementById('addRole').value;
        const showProfile = roleNeedsProfile(role);
        const showCustomer = role === 'Khach hang';
        const fullName = document.getElementById('addFullName');
        const note = document.getElementById('addUserNote');

        document.querySelectorAll('.profile-field').forEach((item) => {
            item.style.display = showProfile ? 'block' : 'none';
        });
        document.querySelectorAll('.profile-only-customer').forEach((item) => {
            item.style.display = showCustomer ? 'block' : 'none';
        });

        if (fullName) {
            fullName.required = showProfile;
        }
        if (note) {
            note.textContent = showProfile
                ? 'Tài khoản sẽ được tạo trước, sau đó tạo hồ sơ tương ứng trong KHACH_HANG hoặc NHAN_VIEN.'
                : 'Vai trò Admin chỉ tạo tài khoản quản trị, không cần hồ sơ khách hàng/nhân viên.';
        }

        if (!showCustomer) {
            clearAddCccdFiles();
        }
    }

    function resetAddUserForm() {
        const form = document.getElementById('addUserForm');
        if (form) form.reset();
        clearAddCccdFiles();
        updateAddUserProfileFields();
    }

    function openAddUserModal() {
        resetAddUserForm();
        document.getElementById('addUserModal').classList.add('active');
        document.getElementById('addUsername').focus();
    }

    function closeAddUserModal(event) {
        if (event && event.target !== event.currentTarget) return;
        const modal = document.getElementById('addUserModal');
        if (modal) modal.classList.remove('active');
    }

    function textValue(id) {
        const input = document.getElementById(id);
        return input ? input.value.trim() : '';
    }

    function clearAddCccdFiles() {
        addCccdFiles = {
            front: null,
            back: null,
        };

        [
            ['addCitizenFront', 'addCitizenFrontPreviewWrap', 'addCitizenFrontPreview', 'addCitizenFrontName'],
            ['addCitizenBack', 'addCitizenBackPreviewWrap', 'addCitizenBackPreview', 'addCitizenBackName'],
        ].forEach(([inputId, wrapId, previewId, nameId]) => {
            const input = document.getElementById(inputId);
            const wrap = document.getElementById(wrapId);
            const preview = document.getElementById(previewId);
            const name = document.getElementById(nameId);
            if (input) input.value = '';
            if (preview) preview.removeAttribute('src');
            if (name) name.textContent = '';
            if (wrap) wrap.classList.remove('active');
        });
    }

    function setAddCccdPreview(side, file) {
        const isFront = side === 'front';
        const wrap = document.getElementById(isFront ? 'addCitizenFrontPreviewWrap' : 'addCitizenBackPreviewWrap');
        const preview = document.getElementById(isFront ? 'addCitizenFrontPreview' : 'addCitizenBackPreview');
        const name = document.getElementById(isFront ? 'addCitizenFrontName' : 'addCitizenBackName');

        if (!file) {
            if (wrap) wrap.classList.remove('active');
            if (preview) preview.removeAttribute('src');
            if (name) name.textContent = '';
            return;
        }

        if (preview) preview.src = URL.createObjectURL(file);
        if (name) name.textContent = file.name;
        if (wrap) wrap.classList.add('active');
    }

    function handleAddCccdFile(side, input) {
        const file = input.files && input.files[0];
        addCccdFiles[side] = null;

        if (!file) {
            setAddCccdPreview(side, null);
            return;
        }

        if (!file.type.startsWith('image/')) {
            input.value = '';
            setAddCccdPreview(side, null);
            alert('Vui lòng chọn đúng file ảnh.');
            return;
        }

        addCccdFiles[side] = file;
        setAddCccdPreview(side, file);
    }

    async function uploadCustomerCccdImage(customerId, side, file) {
        if (!file) return null;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('side', side);

        try {
            return await AdminApi.apiFetch(`/customers/${customerId}/cccd-image`, {
                method: 'POST',
                body: formData,
            });
        } catch (error) {
            if (/not found|404/i.test(error.message || '')) {
                throw new Error('Backend chưa có route upload CCCD hoặc chưa restart server. Hãy restart lại FastAPI rồi thêm tài khoản.');
            }
            throw error;
        }
    }

    async function uploadAddCccdImages(customerId) {
        let updatedCustomer = null;
        if (addCccdFiles.front) {
            updatedCustomer = await uploadCustomerCccdImage(customerId, 'front', addCccdFiles.front);
        }
        if (addCccdFiles.back) {
            updatedCustomer = await uploadCustomerCccdImage(customerId, 'back', addCccdFiles.back);
        }
        return updatedCustomer;
    }

    async function saveNewUser(event) {
        event.preventDefault();
        event.stopImmediatePropagation();

        const submitButton = document.getElementById('addUserSubmit');
        const role = document.getElementById('addRole').value;
        const fullName = textValue('addFullName');

        if (roleNeedsProfile(role) && !fullName) {
            alert('Vui lòng nhập họ tên cho tài khoản này.');
            return;
        }

        if (submitButton) submitButton.disabled = true;
        let createdAccount = null;
        let createdCustomer = null;

        try {
            createdAccount = await AdminApi.apiFetch('/accounts', {
                method: 'POST',
                body: {
                    dang_nhap: textValue('addUsername'),
                    mat_khau: document.getElementById('addPassword').value,
                    vai_tro: role,
                    ...AdminApi.accountStatusToApi(document.getElementById('addStatus').value),
                },
            });

            if (role === 'Khach hang') {
                createdCustomer = await AdminApi.apiFetch('/customers', {
                    method: 'POST',
                    body: {
                        id_tai_khoan: createdAccount.id_tai_khoan,
                        ho_ten: fullName,
                        sdt: textValue('addPhone') || null,
                        thu_dien_tu: textValue('addEmail') || null,
                        so_cccd: textValue('addCitizenId') || null,
                    },
                });

                await uploadAddCccdImages(createdCustomer.id_khach_hang);
            }

            if (role === 'Nhan vien') {
                await AdminApi.apiFetch('/employees', {
                    method: 'POST',
                    body: {
                        id_tai_khoan: createdAccount.id_tai_khoan,
                        ho_ten: fullName,
                        sdt: textValue('addPhone') || null,
                    },
                });
            }

            closeAddUserModal();
            await loadUsers();
            alert('Đã thêm tài khoản thành công!');
        } catch (error) {
            const prefix = createdAccount
                ? 'Tài khoản đã được tạo nhưng tạo hồ sơ thất bại: '
                : '';
            alert(prefix + (error.message || 'Không thêm được tài khoản.'));
            if (createdAccount) {
                await loadUsers();
            }
        } finally {
            if (submitButton) submitButton.disabled = false;
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        window.editUser = editUser;
        window.toggleLockAccount = toggleLockAccount;
        window.openAddUserModal = openAddUserModal;
        window.closeAddUserModal = closeAddUserModal;
        window.updateAddUserProfileFields = updateAddUserProfileFields;

        const roleSelect = document.getElementById('addRole');
        if (roleSelect) {
            roleSelect.addEventListener('change', updateAddUserProfileFields);
        }
        const form = document.getElementById('addUserForm');
        if (form) {
            form.addEventListener('submit', saveNewUser, true);
        }
        const frontInput = document.getElementById('addCitizenFront');
        const backInput = document.getElementById('addCitizenBack');
        if (frontInput) {
            frontInput.addEventListener('change', () => handleAddCccdFile('front', frontInput));
        }
        if (backInput) {
            backInput.addEventListener('change', () => handleAddCccdFile('back', backInput));
        }

        updateAddUserProfileFields();
        loadUsers();
    });
})();
