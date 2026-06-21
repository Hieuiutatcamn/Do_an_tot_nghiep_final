(function () {
    'use strict';

    let currentAccount = null;
    let currentEmployee = null;

    function getElement(id) {
        return document.getElementById(id);
    }

    function getValue(id) {
        const element = getElement(id);
        return element ? element.value.trim() : '';
    }

    function setValue(id, value) {
        const element = getElement(id);
        if (element) {
            element.value = value || '';
        }
    }

    function setButtonLoading(button, isLoading, loadingText) {
        if (!button) return;

        if (isLoading) {
            button.dataset.originalText = button.textContent;
            button.textContent = loadingText;
            button.disabled = true;
            return;
        }

        button.textContent = button.dataset.originalText || button.textContent;
        button.disabled = false;
    }

    function sameAccountId(left, right) {
        return Number(left) === Number(right);
    }

    function renderProfile() {
        setValue('ho_ten', currentEmployee ? currentEmployee.ho_ten : '');
        setValue('sdt', currentEmployee ? currentEmployee.sdt : '');
        setValue('dang_nhap', currentAccount ? currentAccount.dang_nhap : '');
        setValue('vai_tro', currentAccount ? currentAccount.vai_tro : '');
        setValue('trang_thai', currentAccount ? currentAccount.trang_thai : '');
    }

    async function getCurrentAccountFromAccounts() {
        const me = await AdminApi.loadCurrentAccount();
        const account = me && (me.tai_khoan || me.account) ? (me.tai_khoan || me.account) : me;

        if (!account || !account.id_tai_khoan) {
            throw new Error('Không tìm thấy tài khoản đang đăng nhập.');
        }

        try {
            return await AdminApi.apiFetch(`/accounts/${account.id_tai_khoan}`);
        } catch (error) {
            console.warn(error.message || error);
            return account;
        }
    }

    async function loadProfile() {
        AdminApi.requireAuth();

        try {
            const [account, employees] = await Promise.all([
                getCurrentAccountFromAccounts(),
                AdminApi.optional(() => AdminApi.getAll('/employees'), []),
            ]);

            currentAccount = account;
            currentEmployee = employees.find((item) => (
                sameAccountId(item.id_tai_khoan, currentAccount.id_tai_khoan)
            )) || null;

            renderProfile();
        } catch (error) {
            console.error(error);
            if (!/hết hạn|đăng nhập/i.test(error.message || '')) {
                alert(error.message || 'Không tải được thông tin hồ sơ.');
            }
        }
    }

    async function handleProfileSubmit(event) {
        event.preventDefault();

        if (!currentEmployee) {
            alert('Không tìm thấy hồ sơ nhân viên của tài khoản đang đăng nhập.');
            return;
        }

        const submitButton = getElement('profile-save-btn');
        const payload = {
            ho_ten: getValue('ho_ten'),
            sdt: getValue('sdt'),
        };

        setButtonLoading(submitButton, true, 'Đang lưu...');

        try {
            const updatedEmployee = await AdminApi.apiFetch(`/employees/${currentEmployee.id_nhan_vien}`, {
                method: 'PUT',
                body: payload,
            });

            currentEmployee = {
                ...currentEmployee,
                ...(updatedEmployee || {}),
                ...payload,
            };
            renderProfile();
            alert('Cập nhật thông tin thành công');
        } catch (error) {
            console.error(error);
            if (!/hết hạn|đăng nhập/i.test(error.message || '')) {
                alert(error.message || 'Không cập nhật được thông tin hồ sơ.');
            }
        } finally {
            setButtonLoading(submitButton, false);
        }
    }

    function validatePasswordForm(values) {
        if (!values.mat_khau_cu || !values.mat_khau_moi || !values.xac_nhan_mat_khau) {
            return 'Vui lòng không để trống thông tin mật khẩu.';
        }

        if (values.mat_khau_moi.length < 6) {
            return 'Mật khẩu mới phải có ít nhất 6 ký tự.';
        }

        if (values.mat_khau_moi !== values.xac_nhan_mat_khau) {
            return 'Xác nhận mật khẩu phải khớp mật khẩu mới.';
        }

        if (values.mat_khau_moi === values.mat_khau_cu) {
            return 'Mật khẩu mới không được trùng mật khẩu cũ.';
        }

        return '';
    }

    async function handleChangePasswordSubmit(event) {
        event.preventDefault();

        if (!currentAccount) {
            alert('Không tìm thấy tài khoản đang đăng nhập.');
            return;
        }

        const form = event.currentTarget;
        const submitButton = getElement('change-password-btn');
        const payload = {
            mat_khau_cu: getValue('mat_khau_cu'),
            mat_khau_moi: getValue('mat_khau_moi'),
            xac_nhan_mat_khau: getValue('xac_nhan_mat_khau'),
        };
        const validationError = validatePasswordForm(payload);

        if (validationError) {
            alert(validationError);
            return;
        }

        setButtonLoading(submitButton, true, 'Đang đổi...');

        try {
            await AdminApi.apiFetch(`/accounts/${currentAccount.id_tai_khoan}/password`, {
                method: 'PATCH',
                body: { mat_khau: payload.mat_khau_moi },
            });

            form.reset();
            alert('Đổi mật khẩu thành công');
        } catch (error) {
            console.error(error);
            if (!/hết hạn|đăng nhập/i.test(error.message || '')) {
                alert(error.message || 'Không đổi được mật khẩu.');
            }
        } finally {
            setButtonLoading(submitButton, false);
        }
    }

    function initSettingsPage() {
        const profileForm = getElement('profile-form');
        const profileCancelButton = getElement('profile-cancel-btn');
        const changePasswordForm = getElement('change-password-form');

        if (profileForm) {
            profileForm.addEventListener('submit', handleProfileSubmit);
        }

        if (profileCancelButton) {
            profileCancelButton.addEventListener('click', renderProfile);
        }

        if (changePasswordForm) {
            changePasswordForm.addEventListener('submit', handleChangePasswordSubmit);
        }

        loadProfile();
    }

    document.addEventListener('DOMContentLoaded', initSettingsPage);
})();
