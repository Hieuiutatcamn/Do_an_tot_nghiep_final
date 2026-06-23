(function () {
    'use strict';

    let orders = [];
    let allOrders = [];
    let customersById = new Map();
    let selectedOrderId = null;
    let currentSearch = '';
    let currentStatusFilter = 'all';
    let orderSearchTimer = null;
    let initialOrderOpened = false;
    const initialOrderIdFromUrl = new URLSearchParams(window.location.search).get('id');
    const CAC_TRANG_THAI_KE_TIEP_CHI_TIET_DON_THUE = {
        'Cho thanh toan': ['Da huy'],
        'Da dat': ['Da xac nhan', 'Da huy'],
        'Da xac nhan': ['Dang thue', 'Da huy'],
        'Dang thue': ['Da thue', 'Da qua han'],
        'Da qua han': ['Da thue'],
        'Da thue': [],
        'Da huy': [],
    };

    async function taiDanhSachKhachHang() {
        const customers = await AdminApi.optional(() => AdminApi.getAll('/customers'), []);
        customersById = new Map(customers.map((item) => [item.id_khach_hang, item]));
    }

    function chuanHoaDonThue(order) {
        const customer = customersById.get(order.id_khach_hang);
        const start = AdminApi.firstDetailDate(order, 'ngay_nhan');
        const end = AdminApi.firstDetailDate(order, 'ngay_tra');
        return {
            ...order,
            khach_hang: customer ? customer.ho_ten : `Khách #${order.id_khach_hang || '-'}`,
            customer,
            ngay_thue: start,
            ngay_tra: end,
            trang_thai_ui: AdminApi.rentalStatusToUi(order.trang_thai),
        };
    }

    function chuanHoaTuKhoaTimKiem(value) {
        return String(value ?? '')
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/đ/g, 'd')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function taoDuLieuTimKiemDonThue(order) {
        const customer = order.customer || {};
        const details = order.chi_tiet || order.details || [];
        const maDon = order.ma_don || `DH${String(order.id_don_thue || '').padStart(4, '0')}`;
        return chuanHoaTuKhoaTimKiem([
            order.id_don_thue,
            maDon,
            order.khach_hang,
            customer.ho_ten,
            customer.sdt,
            customer.so_dien_thoai,
            customer.thu_dien_tu,
            order.trang_thai,
            order.trang_thai_ui,
            AdminApi.rentalStatusText(order.trang_thai),
            AdminApi.rentalStatusText(order.trang_thai_ui),
            layTenTrangThaiDonThue(order.trang_thai),
            layTenTrangThaiDonThue(order.trang_thai_ui),
            order.ngay_dat,
            order.ngay_thue,
            order.ngay_tra,
            ...details.flatMap((detail) => [
                detail.ngay_nhan,
                detail.ngay_tra,
            ]),
        ].filter(Boolean).join(' '));
    }

    function layTrangThaiHieuLucDonThue(order) {
        return order.trang_thai_ui;
    }

    function locDonThueNoiBo(items = allOrders, search = currentSearch, status = currentStatusFilter) {
        const keyword = chuanHoaTuKhoaTimKiem(search);
        const statusValue = status || 'all';

        return items.filter((order) => {
            const keywordMatched = !keyword || taoDuLieuTimKiemDonThue(order).includes(keyword);
            const statusMatched = statusValue === 'all' || layTrangThaiHieuLucDonThue(order) === statusValue;
            return keywordMatched && statusMatched;
        });
    }

    function coBoLocDonThueDangHoatDong() {
        return Boolean(chuanHoaTuKhoaTimKiem(currentSearch)) || currentStatusFilter !== 'all';
    }

    function layTenTrangThaiDonThue(status) {
        const ui = AdminApi.rentalStatusToUi(status);
        return {
            'payment-pending': 'Chờ thanh toán',
            pending: 'Đã đặt',
            confirmed: 'Đã xác nhận',
            renting: 'Đang thuê',
            completed: 'Đã thuê',
            overdue: 'Quá hạn',
            cancelled: 'Đã hủy',
        }[ui] || AdminApi.rentalStatusText(status);
    }

    function taoLuaChonTrangThaiChiTiet(trangThaiHienTai) {
        const cacLuaChon = [trangThaiHienTai, ...(CAC_TRANG_THAI_KE_TIEP_CHI_TIET_DON_THUE[trangThaiHienTai] || [])]
            .filter(Boolean)
            .filter((giaTri, index, danhSach) => danhSach.indexOf(giaTri) === index);
        return cacLuaChon.map((giaTri) => (
            `<option value="${AdminApi.escapeHtml(giaTri)}" ${giaTri === trangThaiHienTai ? 'selected' : ''}>${AdminApi.escapeHtml(AdminApi.rentalStatusText(giaTri))}</option>`
        )).join('');
    }

    function locDonThue() {
        orders = locDonThueNoiBo(allOrders, currentSearch, currentStatusFilter);
        hienThiDonThue();
    }

    function hienThiDonThue() {
        hienThiBangDonThue();
    }

    async function taiDanhSachDonThue(search = currentSearch, options = {}) {
        AdminApi.requireAuth();
        currentSearch = search || '';
        const forceReload = Boolean(options.forceReload);
        const orderBody = document.querySelector('#orderTable tbody');
        if (orderBody) orderBody.innerHTML = '<tr><td colspan="9">Đang tải...</td></tr>';

        try {
            if (!allOrders.length || forceReload) {
                await taiDanhSachKhachHang();
                const rentalItems = await AdminApi.getAll('/rentals');
                allOrders = rentalItems.map(chuanHoaDonThue);
            }
            locDonThue();
            moDonThueBanDauTuUrl();
        } catch (error) {
            const message = AdminApi.escapeHtml(error.message || 'Không tải được đơn thuê.');
            if (orderBody) orderBody.innerHTML = `<tr><td colspan="9">${message}</td></tr>`;
        }
    }

    function taoHuyHieuTrangThai(status) {
        const ui = AdminApi.rentalStatusToUi(status);
        const className = {
            'payment-pending': 'status-pending',
            pending: 'status-pending',
            confirmed: 'status-confirmed',
            renting: 'status-renting',
            completed: 'status-completed',
            overdue: 'status-overdue',
            cancelled: 'status-cancelled',
        }[ui] || 'status-pending';
        return `<span class="status-badge ${className}">${layTenTrangThaiDonThue(ui)}</span>`;
    }

    function laDonQuaHan(order) {
        return order.trang_thai_ui === 'overdue';
    }

    function laThanhToanVnpay(order) {
        return String(order?.phuong_thuc_thanh_toan || '').trim().toUpperCase() === 'VNPAY';
    }

    function laThanhToanThuCong(order) {
        return String(order?.phuong_thuc_thanh_toan || '').trim() === 'Chuyen khoan thu cong';
    }

    function hienThiThongTinThanhToan(order, transferImage) {
        const paidAmount = Number(order.so_tien_da_thanh_toan || 0);
        let paymentMethod = '-';
        if (laThanhToanVnpay(order)) {
            paymentMethod = 'VNPAY';
        } else if (laThanhToanThuCong(order)) {
            paymentMethod = 'Chuyển khoản thủ công';
        }

        const paymentFields = [
            `<div><label>Phương thức thanh toán</label><span>${AdminApi.escapeHtml(paymentMethod)}</span></div>`,
            `<div><label>Số tiền đã thanh toán</label><span>${AdminApi.formatCurrency(paidAmount)}</span></div>`,
        ];

        if (laThanhToanVnpay(order)) {
            const transactionId = order.ma_giao_dich_vnpay || '-';
            const paymentDate = order.ngay_thanh_toan
                ? AdminApi.formatDateTime(order.ngay_thanh_toan)
                : '-';
            const paymentDeadline = order.han_thanh_toan_vnpay
                ? AdminApi.formatDateTime(order.han_thanh_toan_vnpay)
                : '-';
            paymentFields.push(
                `<div><label>Mã giao dịch VNPAY</label><span>${AdminApi.escapeHtml(transactionId)}</span></div>`,
                `<div><label>Hạn thanh toán VNPAY</label><span>${AdminApi.escapeHtml(paymentDeadline)}</span></div>`,
                `<div><label>Ngày thanh toán</label><span>${AdminApi.escapeHtml(paymentDate)}</span></div>`,
            );
        } else if (laThanhToanThuCong(order) || transferImage) {
            paymentFields.push(
                `<div><label>Ảnh chuyển khoản</label><span>${transferImage ? `<img src="${transferImage}" alt="Chuyển khoản" style="max-width:100px;max-height:100px;" onclick="moHopThoaiAnh('${transferImage}')">` : '-'}</span></div>`,
            );
        }

        return paymentFields.join('');
    }

    function taoNutThaoTac(order) {
        if (order.trang_thai_ui === 'payment-pending') {
            return '<button class="card-btn btn-secondary" disabled>Chờ thanh toán</button>';
        }
        if (order.trang_thai_ui === 'pending') {
            return `<button class="card-btn" onclick="event.stopPropagation(); xacNhanDonThue(${order.id_don_thue})">Xác nhận</button>`;
        }
        return '<button class="card-btn btn-secondary" disabled>Không có thao tác</button>';
    }

    function taoDongDonThue(order) {
        return `
            <tr onclick="chonDonThue(${order.id_don_thue})">
                <td>${order.id_don_thue}</td>
                <td>${AdminApi.escapeHtml(order.khach_hang)}</td>
                <td>${AdminApi.escapeHtml(order.customer?.sdt || order.customer?.so_dien_thoai || '-')}</td>
                <td>${AdminApi.formatDate(order.ngay_dat)}</td>
                <td>${AdminApi.formatDateTime(order.ngay_thue)}</td>
                <td>${AdminApi.formatDateTime(order.ngay_tra)}</td>
                <td>${AdminApi.formatCurrency(order.tong_tien)}</td>
                <td>${taoHuyHieuTrangThai(order.trang_thai)}</td>
                <td><div class="table-row-action">${taoNutThaoTac(order)}</div></td>
            </tr>
        `;
    }

    function hienThiBangDonThue() {
        const tbody = document.querySelector('#orderTable tbody');
        if (!tbody) return;
        if (coBoLocDonThueDangHoatDong() && !orders.length) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;">Không tìm thấy đơn hàng phù hợp.</td></tr>';
            return;
        }
        tbody.innerHTML = orders.map(taoDongDonThue).join('')
            || `<tr><td colspan="9" style="text-align:center;padding:20px;">${coBoLocDonThueDangHoatDong() ? 'Không tìm thấy đơn hàng phù hợp.' : 'Không có đơn thuê.'}</td></tr>`;
    }

    async function capNhatTrangThai(orderId, uiStatus) {
        await AdminApi.apiFetch(`/rentals/${orderId}/status`, {
            method: 'PATCH',
            body: { trang_thai: AdminApi.rentalStatusToApi(uiStatus) },
        });
        await taiDanhSachDonThue(currentSearch, { forceReload: true });
        if (selectedOrderId === orderId) {
            hienThiChiTietDonThue(orderId);
        }
    }

    async function xacNhanDonThue(orderId) {
        if (!confirm('Bạn có chắc muốn xác nhận đơn thuê này?')) return;
        try {
            await capNhatTrangThai(orderId, 'confirmed');
        } catch (error) {
            alert(error.message || 'Không cập nhật được đơn thuê.');
        }
    }

    function xuLyTimKiemDonThue(event) {
        const keyword = event && event.target ? event.target.value.trim() : '';
        window.clearTimeout(orderSearchTimer);
        orderSearchTimer = window.setTimeout(() => {
            currentSearch = keyword;
            locDonThue();
        }, 300);
    }

    function xuLyLocTrangThaiDonThue(event) {
        currentStatusFilter = event && event.target ? event.target.value : 'all';
        locDonThue();
    }

    function xoaTimKiemDonThue() {
        const input = document.getElementById('orderSearchInput');
        if (input) input.value = '';
        currentSearch = '';
        window.clearTimeout(orderSearchTimer);
        locDonThue();
    }

    function ganSuKienTimKiemDonThue() {
        const input = document.getElementById('orderSearchInput');
        const statusSelect = document.getElementById('orderStatusFilter');
        const clearButton = document.getElementById('clearOrderSearchBtn');
        if (input && input.dataset.orderSearchBound !== 'true') {
            input.dataset.orderSearchBound = 'true';
            input.addEventListener('input', xuLyTimKiemDonThue);
        }
        if (statusSelect && statusSelect.dataset.orderStatusBound !== 'true') {
            statusSelect.dataset.orderStatusBound = 'true';
            statusSelect.addEventListener('change', xuLyLocTrangThaiDonThue);
        }
        if (clearButton && clearButton.dataset.orderSearchBound !== 'true') {
            clearButton.dataset.orderSearchBound = 'true';
            clearButton.addEventListener('click', xoaTimKiemDonThue);
        }
    }

    function chonDonThue(orderId) {
        selectedOrderId = orderId;
        moPopupChiTietDonThue(orderId);
    }

    function moPopupChiTietDonThue(orderId) {
        hienThiChiTietDonThue(orderId);
        document.getElementById('orderDetailPopup').classList.add('active');
    }

    function moDonThueBanDauTuUrl() {
        if (initialOrderOpened || !initialOrderIdFromUrl) return;
        const orderId = Number(initialOrderIdFromUrl);
        if (!Number.isFinite(orderId) || !allOrders.some((item) => Number(item.id_don_thue) === orderId)) return;
        initialOrderOpened = true;
        chonDonThue(orderId);
    }

    function dongPopupChiTietDonThue(event) {
        if (event && event.target !== event.currentTarget) return;
        document.getElementById('orderDetailPopup').classList.remove('active');
    }

    function moHopThoaiAnh(imageSrc) {
        document.getElementById('modalImage').src = imageSrc;
        document.getElementById('imageModal').classList.add('active');
    }

    function dongHopThoaiAnh(event) {
        if (event && event.target !== event.currentTarget) return;
        document.getElementById('imageModal').classList.remove('active');
    }

    async function capNhatTrangThaiDonThue(orderId) {
        const statusSelect = document.getElementById('statusSelect');
        if (!statusSelect) return;
        try {
            await capNhatTrangThai(orderId, statusSelect.value);
        } catch (error) {
            alert(error.message || 'Không cập nhật được trạng thái.');
        }
    }

    function hienThiChiTietDonThue(orderId) {
        const order = orders.find((item) => item.id_don_thue === orderId)
            || allOrders.find((item) => item.id_don_thue === orderId);
        const infoContainer = document.getElementById('orderPopupInfo');
        const rowsContainer = document.getElementById('orderPopupDetailRows');
        const actionButtonEl = document.getElementById('orderPopupActionButton');

        if (!order) {
            if (infoContainer) infoContainer.innerHTML = '<div class="no-order">Không tìm thấy đơn thuê.</div>';
            if (rowsContainer) rowsContainer.innerHTML = '<tr><td colspan="7">Không có chi tiết đơn thuê.</td></tr>';
            if (actionButtonEl) actionButtonEl.disabled = true;
            return;
        }

        const customer = order.customer || {};
        document.getElementById('orderPopupTitle').textContent = `Đơn #${order.id_don_thue} - ${order.khach_hang}`;
        const frontImage = AdminApi.imageUrl(customer.anh_cccd_mat_truoc, '');
        const backImage = AdminApi.imageUrl(customer.anh_cccd_mat_sau, '');
        const transferImage = AdminApi.imageUrl(order.anh_chuyen_khoan, '');
        const paymentInformation = hienThiThongTinThanhToan(order, transferImage);
        const statusOptions = {
            'payment-pending': [
                ['payment-pending', 'Chờ thanh toán'],
                ['cancelled', 'Đã hủy'],
            ],
            pending: [
                ['pending', 'Đã đặt'],
                ['confirmed', 'Đã xác nhận'],
                ['cancelled', 'Đã hủy'],
            ],
            confirmed: [
                ['confirmed', 'Đã xác nhận'],
                ['renting', 'Đang thuê máy'],
                ['cancelled', 'Đã hủy'],
            ],
            renting: [
                ['renting', 'Đang thuê máy'],
                ['completed', 'Đã thuê'],
                ['overdue', 'Quá hạn'],
            ],
            overdue: [
                ['overdue', 'Quá hạn'],
                ['completed', 'Đã thuê'],
            ],
            completed: [['completed', 'Đã thuê']],
            cancelled: [['cancelled', 'Đã hủy']],
        }[order.trang_thai_ui] || [];
        const statusSelectOptions = statusOptions.map(([value, label]) => (
            `<option value="${value}" ${order.trang_thai_ui === value ? 'selected' : ''}>${label}</option>`
        )).join('');

        infoContainer.innerHTML = `
            <div class="detail-card-title">Thông tin đơn thuê</div>
            <div class="detail-row">
                <div><label>Ngày đặt</label><span>${AdminApi.formatDate(order.ngay_dat)}</span></div>
                <div><label>Trạng thái</label><span>
                    <select id="statusSelect" onchange="capNhatTrangThaiDonThue(${order.id_don_thue})" style="padding:6px 12px;border-radius:8px;border:1px solid rgba(15,23,42,.2);font-size:14px;color:#111827;">
                        ${statusSelectOptions}
                    </select>
                </span></div>
                <div><label>Ngày thuê</label><span>${AdminApi.formatDateTime(order.ngay_thue)}</span></div>
                <div><label>Ngày trả</label><span>${AdminApi.formatDateTime(order.ngay_tra)}</span></div>
                <div><label>Tổng tiền</label><span>${AdminApi.formatCurrency(order.tong_tien)}</span></div>
                ${paymentInformation}
                <div><label>Ghi chú</label><span>${AdminApi.escapeHtml(order.ghi_chu || '')}</span></div>
                <div><label>Ảnh CCCD mặt trước</label><span>${frontImage ? `<img src="${frontImage}" alt="CCCD mặt trước" style="max-width:100px;max-height:100px;" onclick="moHopThoaiAnh('${frontImage}')">` : '-'}</span></div>
                <div><label>Ảnh CCCD mặt sau</label><span>${backImage ? `<img src="${backImage}" alt="CCCD mặt sau" style="max-width:100px;max-height:100px;" onclick="moHopThoaiAnh('${backImage}')">` : '-'}</span></div>
            </div>
        `;

        rowsContainer.innerHTML = (order.chi_tiet || order.details || []).map((item) => `
            <tr>
                <td>${item.id_chi_tiet_don_thue}</td>
                <td>${AdminApi.escapeHtml((item.thiet_bi || item.device) ? (item.thiet_bi || item.device).ten_thiet_bi : `Thiết bị #${item.id_thiet_bi}`)}</td>
                <td>
                    <select
                        onchange="capNhatTrangThaiChiTietDonThue(${item.id_chi_tiet_don_thue}, this.value)"
                        style="padding:6px 12px;border-radius:8px;border:1px solid rgba(15,23,42,.2);font-size:14px;color:#111827;min-width:160px;"
                    >
                        ${taoLuaChonTrangThaiChiTiet(item.trang_thai || order.trang_thai)}
                    </select>
                </td>
                <td>${AdminApi.formatDateTime(item.ngay_nhan)}</td>
                <td>${AdminApi.formatDateTime(item.ngay_tra)}</td>
                <td>${item.so_luong || 0}</td>
                <td>${AdminApi.formatCurrency(item.gia_thue)}</td>
            </tr>
        `).join('') || '<tr><td colspan="7">Không có chi tiết đơn thuê.</td></tr>';

        if (actionButtonEl) {
            if (order.trang_thai_ui === 'payment-pending') {
                actionButtonEl.textContent = 'Chờ thanh toán';
                actionButtonEl.onclick = null;
                actionButtonEl.disabled = true;
            } else if (order.trang_thai_ui === 'pending') {
                actionButtonEl.textContent = 'Xác nhận';
                actionButtonEl.onclick = () => xacNhanDonThue(orderId);
                actionButtonEl.disabled = false;
            } else {
                actionButtonEl.textContent = 'Không có thao tác';
                actionButtonEl.onclick = null;
                actionButtonEl.disabled = true;
            }
        }
    }

    async function capNhatTrangThaiChiTietDonThue(idChiTietDonThue, trangThaiMoi) {
        try {
            await AdminApi.apiFetch(`/chi-tiet-don-hang/${idChiTietDonThue}/trang-thai`, {
                method: 'PATCH',
                body: { trang_thai: trangThaiMoi },
            });
            await taiDanhSachDonThue(currentSearch, { forceReload: true });
            if (selectedOrderId) {
                hienThiChiTietDonThue(selectedOrderId);
            }
        } catch (error) {
            alert(error.message || 'Không cập nhật được trạng thái chi tiết đơn thuê.');
            if (selectedOrderId) {
                await taiDanhSachDonThue(currentSearch, { forceReload: true });
                hienThiChiTietDonThue(selectedOrderId);
            }
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        window.taoHuyHieuTrangThai = taoHuyHieuTrangThai;
        window.hienThiBangDonThue = hienThiBangDonThue;
        window.hienThiDonThue = hienThiDonThue;
        window.xuLyTimKiemDonThue = xuLyTimKiemDonThue;
        window.xuLyLocTrangThaiDonThue = xuLyLocTrangThaiDonThue;
        window.locDonThue = locDonThue;
        window.locDonThueNoiBo = locDonThueNoiBo;
        window.taiDanhSachDonThue = taiDanhSachDonThue;
        window.xoaTimKiemDonThue = xoaTimKiemDonThue;
        window.xacNhanDonThue = xacNhanDonThue;
        window.laThanhToanVnpay = laThanhToanVnpay;
        window.laThanhToanThuCong = laThanhToanThuCong;
        window.hienThiThongTinThanhToan = hienThiThongTinThanhToan;
        window.chonDonThue = chonDonThue;
        window.moPopupChiTietDonThue = moPopupChiTietDonThue;
        window.dongPopupChiTietDonThue = dongPopupChiTietDonThue;
        window.moHopThoaiAnh = moHopThoaiAnh;
        window.dongHopThoaiAnh = dongHopThoaiAnh;
        window.capNhatTrangThaiDonThue = capNhatTrangThaiDonThue;
        window.capNhatTrangThaiChiTietDonThue = capNhatTrangThaiChiTietDonThue;
        window.hienThiChiTietDonThue = hienThiChiTietDonThue;
        window.getStatusText = AdminApi.rentalStatusText;
        window.chuanHoaDonThue = chuanHoaDonThue;
        window.chuanHoaTuKhoaTimKiem = chuanHoaTuKhoaTimKiem;
        window.taoDuLieuTimKiemDonThue = taoDuLieuTimKiemDonThue;
        window.layTrangThaiHieuLucDonThue = layTrangThaiHieuLucDonThue;
        window.coBoLocDonThueDangHoatDong = coBoLocDonThueDangHoatDong;
        window.layTenTrangThaiDonThue = layTenTrangThaiDonThue;
        window.taoLuaChonTrangThaiChiTiet = taoLuaChonTrangThaiChiTiet;
        window.laDonQuaHan = laDonQuaHan;
        window.taoNutThaoTac = taoNutThaoTac;
        window.taoDongDonThue = taoDongDonThue;
        window.capNhatTrangThai = capNhatTrangThai;
        window.moDonThueBanDauTuUrl = moDonThueBanDauTuUrl;
        window.taiDanhSachKhachHang = taiDanhSachKhachHang;
        window.ganSuKienTimKiemDonThue = ganSuKienTimKiemDonThue;
        ganSuKienTimKiemDonThue();
        taiDanhSachDonThue();
        setInterval(() => taiDanhSachDonThue(currentSearch, { forceReload: true }), 60000);
    });
})();
