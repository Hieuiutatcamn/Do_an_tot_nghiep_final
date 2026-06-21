(function () {
    'use strict';

    let currentAccount = null;
    let currentCustomer = null;
    let currentEmployee = null;
    let selectedCccdFiles = {
        front: null,
        back: null,
    };

    const CUSTOMER_IMAGE_PREFIX = '../../user/Sunlens_Camera/';
    const NO_IMAGE = 'https://via.placeholder.com/400x260?text=No+Image';

    async function loadUserData() {
        AdminApi.requireAuth();
        const params = new URLSearchParams(window.location.search);
        const userId = Number(params.get('id'));
        if (!userId) {
            alert('Không tìm thấy tài khoản!');
            window.location.href = 'tai_khoan.html';
            return;
        }

        try {
            const [account, customers, employees] = await Promise.all([
                AdminApi.apiFetch(`/accounts/${userId}`),
                AdminApi.optional(() => AdminApi.getAll('/customers'), []),
                AdminApi.optional(() => AdminApi.getAll('/employees'), []),
            ]);
            currentAccount = account;
            currentCustomer = customers.find((item) => item.id_tai_khoan === account.id_tai_khoan) || null;
            currentEmployee = employees.find((item) => item.id_tai_khoan === account.id_tai_khoan) || null;
            renderAccount();
        } catch (error) {
            alert(error.message || 'Không tải được tài khoản.');
            window.location.href = 'tai_khoan.html';
        }
    }

    function renderAccount() {
        const account = currentAccount;
        document.getElementById('id_tai_khoan').value = account.id_tai_khoan;
        document.getElementById('dang_nhap').value = account.dang_nhap;
        document.getElementById('vai_tro').value = AdminApi.roleText(account.vai_tro);
        document.getElementById('trang_thai').value = AdminApi.accountStatusToUi(account);
        document.getElementById('breadcrumb-username').textContent = account.dang_nhap;

        document.getElementById('khachHangSection').classList.remove('active');
        document.getElementById('nhanVienSection').classList.remove('active');

        if (currentCustomer) {
            showCustomerSection(currentCustomer);
        } else if (currentEmployee) {
            showEmployeeSection(currentEmployee);
        }
    }

    function clearSelectedCccdFiles() {
        selectedCccdFiles = {
            front: null,
            back: null,
        };

        const frontInput = document.getElementById('kh_anh_cccd_mat_truoc_file');
        const backInput = document.getElementById('kh_anh_cccd_mat_sau_file');
        if (frontInput) frontInput.value = '';
        if (backInput) backInput.value = '';
    }

    function customerImageUrl(path) {
        if (!path) return NO_IMAGE;
        if (/^(blob:|data:|https?:)/i.test(path)) return path;
        if (path.startsWith('/')) return AdminApi.imageUrl(path, NO_IMAGE);
        if (path.startsWith('../') || path.startsWith('./')) return path;

        return `${CUSTOMER_IMAGE_PREFIX}${path}`;
    }

    function setCustomerImage(side, path, previewSrc = '') {
        const isFront = side === 'front';
        const hiddenInput = document.getElementById(isFront ? 'kh_anh_cccd_mat_truoc' : 'kh_anh_cccd_mat_sau');
        const preview = document.getElementById(isFront ? 'kh_anh_cccd_mat_truoc_img' : 'kh_anh_cccd_mat_sau_img');
        const pathText = document.getElementById(isFront ? 'kh_anh_cccd_mat_truoc_path' : 'kh_anh_cccd_mat_sau_path');

        if (hiddenInput) {
            hiddenInput.value = path || '';
        }
        if (preview) {
            preview.src = previewSrc || customerImageUrl(path);
        }
        if (pathText) {
            pathText.textContent = path || 'Chưa có ảnh';
        }
    }

    function handleCccdFileChange(side, input) {
        const file = input.files && input.files[0];
        selectedCccdFiles[side] = null;

        if (!file) return;

        if (!file.type.startsWith('image/')) {
            input.value = '';
            alert('Vui lòng chọn đúng file ảnh.');
            return;
        }

        selectedCccdFiles[side] = file;
        const currentPath = document.getElementById(side === 'front' ? 'kh_anh_cccd_mat_truoc' : 'kh_anh_cccd_mat_sau').value;
        setCustomerImage(side, currentPath, URL.createObjectURL(file));

        const pathText = document.getElementById(side === 'front' ? 'kh_anh_cccd_mat_truoc_path' : 'kh_anh_cccd_mat_sau_path');
        if (pathText) {
            pathText.textContent = `Ảnh mới: ${file.name}`;
        }
    }

    async function uploadCccdImage(side, file) {
        if (!file) return '';

        const formData = new FormData();
        formData.append('file', file);
        formData.append('side', side);

        let data;
        try {
            data = await AdminApi.apiFetch(`/customers/${currentCustomer.id_khach_hang}/cccd-image`, {
                method: 'POST',
                body: formData,
            });
        } catch (error) {
            if (/not found|404/i.test(error.message || '')) {
                throw new Error('Backend chưa có route upload CCCD hoặc chưa restart server. Hãy restart lại FastAPI rồi lưu ảnh.');
            }
            throw error;
        }

        const imagePath = side === 'front'
            ? data && data.anh_cccd_mat_truoc
            : data && data.anh_cccd_mat_sau;

        if (!imagePath) {
            throw new Error('API upload chưa trả về đường dẫn ảnh.');
        }

        currentCustomer = data;
        return imagePath;
    }

    async function uploadSelectedCccdImages() {
        if (!currentCustomer) return;

        if (selectedCccdFiles.front) {
            const frontPath = await uploadCccdImage('front', selectedCccdFiles.front);
            setCustomerImage('front', frontPath);
        }

        if (selectedCccdFiles.back) {
            const backPath = await uploadCccdImage('back', selectedCccdFiles.back);
            setCustomerImage('back', backPath);
        }
    }

    function showCustomerSection(customer) {
        const section = document.getElementById('khachHangSection');
        section.classList.add('active');
        clearSelectedCccdFiles();
        document.getElementById('kh_ho_ten').value = customer.ho_ten || '';
        document.getElementById('kh_id_tai_khoan').value = customer.id_tai_khoan || '';
        document.getElementById('kh_so_cccd').value = customer.so_cccd || '';
        document.getElementById('kh_sdt').value = customer.sdt || '';
        document.getElementById('kh_email').value = customer.thu_dien_tu || '';
        document.getElementById('kh_ngay_sinh').value = customer.ngay_sinh ? String(customer.ngay_sinh).slice(0, 10) : '';
        document.getElementById('kh_dia_chi').value = customer.dia_chi || '';
        setCustomerImage('front', customer.anh_cccd_mat_truoc || '');
        setCustomerImage('back', customer.anh_cccd_mat_sau || '');
    }

    function showEmployeeSection(employee) {
        const section = document.getElementById('nhanVienSection');
        section.classList.add('active');
        document.getElementById('nv_ho_ten').value = employee.ho_ten || '';
        document.getElementById('nv_id_tai_khoan').value = employee.id_tai_khoan || '';
        document.getElementById('nv_sdt').value = employee.sdt || '';
    }

    async function saveChanges(event) {
        event.preventDefault();
        event.stopImmediatePropagation();

        if (!currentAccount) return;

        const status = document.getElementById('trang_thai').value;
        const password = document.getElementById('mat_khau').value;
        const confirmPassword = document.getElementById('xac_nhan_mat_khau').value;

        if (password && password !== confirmPassword) {
            alert('Mật khẩu không khớp!');
            return;
        }

        try {
            await AdminApi.apiFetch(`/accounts/${currentAccount.id_tai_khoan}`, {
                method: 'PUT',
                body: AdminApi.accountStatusToApi(status),
            });

            if (password) {
                await AdminApi.apiFetch(`/accounts/${currentAccount.id_tai_khoan}/password`, {
                    method: 'PATCH',
                    body: { mat_khau: password },
                });
            }

            if (currentCustomer) {
                await uploadSelectedCccdImages();

                await AdminApi.apiFetch(`/customers/${currentCustomer.id_khach_hang}`, {
                    method: 'PUT',
                    body: {
                        ho_ten: document.getElementById('kh_ho_ten').value.trim(),
                        sdt: document.getElementById('kh_sdt').value.trim(),
                        so_cccd: document.getElementById('kh_so_cccd').value.trim(),
                        thu_dien_tu: document.getElementById('kh_email').value.trim() || null,
                        ngay_sinh: document.getElementById('kh_ngay_sinh').value || null,
                        dia_chi: document.getElementById('kh_dia_chi').value.trim() || null,
                        anh_cccd_mat_truoc: document.getElementById('kh_anh_cccd_mat_truoc').value || null,
                        anh_cccd_mat_sau: document.getElementById('kh_anh_cccd_mat_sau').value || null,
                    },
                });
            }

            if (currentEmployee) {
                await AdminApi.apiFetch(`/employees/${currentEmployee.id_nhan_vien}`, {
                    method: 'PUT',
                    body: {
                        ho_ten: document.getElementById('nv_ho_ten').value.trim(),
                        sdt: document.getElementById('nv_sdt').value.trim(),
                    },
                });
            }

            alert(currentCustomer ? '✅ Cập nhật thông tin khách hàng thành công' : 'Lưu thay đổi thành công!');
            clearSelectedCccdFiles();
            await loadUserData();
            document.getElementById('mat_khau').value = '';
            document.getElementById('xac_nhan_mat_khau').value = '';
        } catch (error) {
            alert(error.message || 'Không lưu được thay đổi.');
        }
    }

    function goBack() {
        window.location.href = 'tai_khoan.html';
    }

    document.addEventListener('DOMContentLoaded', () => {
        window.loadUserData = loadUserData;
        window.showCustomerSection = showCustomerSection;
        window.showEmployeeSection = showEmployeeSection;
        window.saveChanges = saveChanges;
        window.goBack = goBack;
        const form = document.getElementById('accountForm');
        if (form) form.addEventListener('submit', saveChanges, true);
        const frontInput = document.getElementById('kh_anh_cccd_mat_truoc_file');
        const backInput = document.getElementById('kh_anh_cccd_mat_sau_file');
        if (frontInput) {
            frontInput.addEventListener('change', () => handleCccdFileChange('front', frontInput));
        }
        if (backInput) {
            backInput.addEventListener('change', () => handleCccdFileChange('back', backInput));
        }
        loadUserData();
    });
})();
