(function () {
    'use strict';

    let orders = [];
    let customersById = new Map();
    let accounts = [];
    let currentFilter = 'all';
    let displayedOrders = [];
    let dashboardInitialized = false;

    async function loadDashboardStats(filter = 'all') {
        AdminApi.requireAuth();
        currentFilter = filter;
        if (filter === 'all') {
            document.getElementById('dashboardStart').value = '';
            document.getElementById('dashboardEnd').value = '';
        }
        const tbody = document.querySelector('#orderTableDashboard tbody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="5">Đang tải...</td></tr>';
        ['revenueValue', 'accountsValue', 'ordersValue'].forEach((id) => {
            const element = document.getElementById(id);
            if (element) element.textContent = 'Đang tải...';
        });

        try {
            const [rentalItems, customerItems, accountItems] = await Promise.all([
                AdminApi.getAll('/rentals'),
                AdminApi.optional(() => AdminApi.getAll('/customers'), []),
                AdminApi.optional(() => AdminApi.getAll('/accounts'), []),
            ]);
            customersById = new Map(customerItems.map((item) => [item.id_khach_hang, item]));
            accounts = accountItems;
            orders = rentalItems.map((order) => {
                const customer = customersById.get(order.id_khach_hang);
                return {
                    ...order,
                    customer,
                    khach_hang: customer ? customer.ho_ten : `Khách #${order.id_khach_hang || '-'}`,
                    ngay_thue: AdminApi.firstDetailDate(order, 'ngay_nhan'),
                    ngay_tra: AdminApi.firstDetailDate(order, 'ngay_tra'),
                    trang_thai_ui: AdminApi.rentalStatusToUi(order.trang_thai),
                };
            });
            updateStatsAndTable(filter);
        } catch (error) {
            if (tbody) tbody.innerHTML = `<tr><td colspan="5">${AdminApi.escapeHtml(error.message || 'Không tải được dashboard.')}</td></tr>`;
            ['revenueValue', 'accountsValue', 'ordersValue'].forEach((id) => {
                const element = document.getElementById(id);
                if (element) element.textContent = '—';
            });
        }
    }

    function parseDateOnly(value) {
        if (!value) return null;
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return null;
        date.setHours(0, 0, 0, 0);
        return date;
    }

    function animateNumber(el, target, suffix = '') {
        if (!el) return;
        const start = Number(el.dataset.start) || 0;
        const duration = 600;
        const startTime = performance.now();
        function step(now) {
            const t = Math.min(1, (now - startTime) / duration);
            const value = Math.round(start + (target - start) * t);
            el.textContent = value.toLocaleString('vi-VN') + (suffix ? ` ${suffix}` : '');
            if (t < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
        el.dataset.start = target;
    }

    function filterOrdersByDate(startDate, endDate) {
        return orders.filter((order) => {
            const date = parseDateOnly(order.ngay_dat);
            if (!date) return false;
            if (startDate && date < startDate) return false;
            if (endDate && date > endDate) return false;
            return true;
        });
    }

    function getFilteredOrders(filter = currentFilter) {
        if (filter === 'all') return [...orders];
        const startDate = parseDateOnly(document.getElementById('dashboardStart').value);
        const endDate = parseDateOnly(document.getElementById('dashboardEnd').value);
        return filterOrdersByDate(startDate, endDate);
    }

    function loadRecentTransactions(filter = currentFilter) {
        displayedOrders = getFilteredOrders(filter).sort((left, right) => {
            const leftDate = new Date(left.ngay_dat || 0).getTime();
            const rightDate = new Date(right.ngay_dat || 0).getTime();
            return rightDate - leftDate;
        });

        const tbody = document.querySelector('#orderTableDashboard tbody');
        if (!tbody) return;
        tbody.innerHTML = displayedOrders.map((order) => `
            <tr onclick="openOrderDetailPopup(${order.id_don_thue})" style="cursor:pointer">
                <td>${order.id_don_thue}</td>
                <td>${AdminApi.escapeHtml(order.khach_hang)}</td>
                <td>${AdminApi.formatDate(order.ngay_dat)}</td>
                <td>${AdminApi.rentalStatusText(order.trang_thai_ui)}</td>
                <td>${AdminApi.formatCurrency(order.tong_tien)}</td>
            </tr>
        `).join('') || '<tr><td colspan="5" style="text-align:center;padding:18px;">Không có đơn hàng trong khoảng thời gian này.</td></tr>';
    }

    function updateStatsAndTable(filter = currentFilter) {
        currentFilter = filter;
        const filtered = getFilteredOrders(filter);
        const revenue = filtered.reduce((sum, order) => sum + Number(order.tong_tien || 0), 0);
        const uniqueCustomers = new Set(filtered.map((order) => order.id_khach_hang).filter(Boolean)).size;
        const accountCount = accounts.length || uniqueCustomers;

        animateNumber(document.getElementById('revenueValue'), revenue, 'đ');
        animateNumber(document.getElementById('accountsValue'), accountCount);
        animateNumber(document.getElementById('ordersValue'), filtered.length);

        loadRecentTransactions(filter);
    }

    function currentDateQuery() {
        if (currentFilter === 'all') return '';
        const query = new URLSearchParams();
        const startDate = document.getElementById('dashboardStart').value;
        const endDate = document.getElementById('dashboardEnd').value;
        if (startDate) query.set('start_date', startDate);
        if (endDate) query.set('end_date', endDate);
        const text = query.toString();
        return text ? `?${text}` : '';
    }

    function downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    }

    function excelXmlEscape(value) {
        return String(value ?? '').replace(/[&<>"']/g, (char) => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&apos;',
        }[char]));
    }

    function excelColumnName(index) {
        let value = index + 1;
        let name = '';
        while (value > 0) {
            const remainder = (value - 1) % 26;
            name = String.fromCharCode(65 + remainder) + name;
            value = Math.floor((value - 1) / 26);
        }
        return name;
    }

    function buildWorksheetXml(rows) {
        const sheetRows = rows.map((row, rowIndex) => {
            const cells = row.map((value, columnIndex) => {
                const reference = `${excelColumnName(columnIndex)}${rowIndex + 1}`;
                if (typeof value === 'number' && Number.isFinite(value)) {
                    return `<c r="${reference}"><v>${value}</v></c>`;
                }
                return `<c r="${reference}" t="inlineStr"><is><t>${excelXmlEscape(value)}</t></is></c>`;
            }).join('');
            return `<row r="${rowIndex + 1}">${cells}</row>`;
        }).join('');
        return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
                <sheetData>${sheetRows}</sheetData>
            </worksheet>`;
    }

    function crc32(bytes) {
        let crc = 0xffffffff;
        for (const byte of bytes) {
            crc ^= byte;
            for (let bit = 0; bit < 8; bit += 1) {
                crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
            }
        }
        return (crc ^ 0xffffffff) >>> 0;
    }

    function pushUint16(target, value) {
        target.push(value & 0xff, (value >>> 8) & 0xff);
    }

    function pushUint32(target, value) {
        target.push(value & 0xff, (value >>> 8) & 0xff, (value >>> 16) & 0xff, (value >>> 24) & 0xff);
    }

    function zipFiles(files) {
        const encoder = new TextEncoder();
        const localParts = [];
        const centralParts = [];
        let localOffset = 0;

        Object.entries(files).forEach(([filename, content]) => {
            const nameBytes = encoder.encode(filename);
            const dataBytes = encoder.encode(content);
            const checksum = crc32(dataBytes);
            const localHeader = [];
            pushUint32(localHeader, 0x04034b50);
            pushUint16(localHeader, 20);
            pushUint16(localHeader, 0);
            pushUint16(localHeader, 0);
            pushUint16(localHeader, 0);
            pushUint16(localHeader, 0);
            pushUint32(localHeader, checksum);
            pushUint32(localHeader, dataBytes.length);
            pushUint32(localHeader, dataBytes.length);
            pushUint16(localHeader, nameBytes.length);
            pushUint16(localHeader, 0);

            const localPart = new Uint8Array(localHeader.length + nameBytes.length + dataBytes.length);
            localPart.set(localHeader, 0);
            localPart.set(nameBytes, localHeader.length);
            localPart.set(dataBytes, localHeader.length + nameBytes.length);
            localParts.push(localPart);

            const centralHeader = [];
            pushUint32(centralHeader, 0x02014b50);
            pushUint16(centralHeader, 20);
            pushUint16(centralHeader, 20);
            pushUint16(centralHeader, 0);
            pushUint16(centralHeader, 0);
            pushUint16(centralHeader, 0);
            pushUint16(centralHeader, 0);
            pushUint32(centralHeader, checksum);
            pushUint32(centralHeader, dataBytes.length);
            pushUint32(centralHeader, dataBytes.length);
            pushUint16(centralHeader, nameBytes.length);
            pushUint16(centralHeader, 0);
            pushUint16(centralHeader, 0);
            pushUint16(centralHeader, 0);
            pushUint16(centralHeader, 0);
            pushUint32(centralHeader, 0);
            pushUint32(centralHeader, localOffset);

            const centralPart = new Uint8Array(centralHeader.length + nameBytes.length);
            centralPart.set(centralHeader, 0);
            centralPart.set(nameBytes, centralHeader.length);
            centralParts.push(centralPart);
            localOffset += localPart.length;
        });

        const centralSize = centralParts.reduce((sum, part) => sum + part.length, 0);
        const end = [];
        pushUint32(end, 0x06054b50);
        pushUint16(end, 0);
        pushUint16(end, 0);
        pushUint16(end, centralParts.length);
        pushUint16(end, centralParts.length);
        pushUint32(end, centralSize);
        pushUint32(end, localOffset);
        pushUint16(end, 0);

        return new Blob(
            [...localParts, ...centralParts, new Uint8Array(end)],
            { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }
        );
    }

    function exportDashboardLocally() {
        const revenue = displayedOrders.reduce((sum, order) => sum + Number(order.tong_tien || 0), 0);
        const accountCount = accounts.length || new Set(displayedOrders.map((order) => order.id_khach_hang).filter(Boolean)).size;
        const rows = [
            ['Tổng doanh thu', revenue],
            ['Tổng tài khoản', accountCount],
            ['Tổng đơn hàng', displayedOrders.length],
            [],
            ['Mã đơn', 'Tên khách hàng', 'Ngày đặt', 'Trạng thái', 'Tổng tiền'],
            ...displayedOrders.map((order) => [
                Number(order.id_don_thue),
                order.khach_hang,
                AdminApi.formatDate(order.ngay_dat),
                AdminApi.rentalStatusText(order.trang_thai_ui),
                Number(order.tong_tien || 0),
            ]),
        ];
        const files = {
            '[Content_Types].xml': `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
                    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
                    <Default Extension="xml" ContentType="application/xml"/>
                    <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
                    <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
                </Types>`,
            '_rels/.rels': `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
                </Relationships>`,
            'xl/workbook.xml': `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
                    xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
                    <sheets><sheet name="Dashboard" sheetId="1" r:id="rId1"/></sheets>
                </workbook>`,
            'xl/_rels/workbook.xml.rels': `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
                </Relationships>`,
            'xl/worksheets/sheet1.xml': buildWorksheetXml(rows),
        };
        downloadBlob(zipFiles(files), 'dashboard_report.xlsx');
    }

    async function exportDashboard() {
        const button = document.getElementById('dashboardExport');
        if (button) button.disabled = true;
        try {
            const response = await fetch(`${AdminApi.API_BASE}/admin/dashboard/export${currentDateQuery()}`, {
                headers: {
                    Authorization: `Bearer ${AdminApi.getToken()}`,
                },
            });
            if (response.ok) {
                downloadBlob(await response.blob(), 'dashboard_report.xlsx');
                return;
            }
            if (response.status !== 404 && response.status !== 405) {
                throw new Error(`API export lỗi ${response.status}`);
            }
            exportDashboardLocally();
        } catch (error) {
            console.warn(error.message || error);
            exportDashboardLocally();
        } finally {
            if (button) button.disabled = false;
        }
    }

    function openOrderDetailPopup(orderId) {
        renderOrderDetail(orderId);
        const popup = document.getElementById('orderDetailPopup');
        if (popup) {
            popup.style.display = 'flex';
            popup.classList.add('active');
        }
    }

    function closeOrderDetailPopup(event) {
        if (event && event.target !== event.currentTarget) return;
        const popup = document.getElementById('orderDetailPopup');
        if (popup) {
            popup.classList.remove('active');
            popup.style.display = 'none';
        }
    }

    function renderOrderDetail(orderId) {
        const order = orders.find((item) => item.id_don_thue === orderId);
        const rowsContainer = document.getElementById('orderPopupDetailRows');
        const infoContainer = document.getElementById('orderPopupInfo');
        const titleEl = document.getElementById('orderPopupTitle');
        if (!order) {
            if (infoContainer) infoContainer.innerHTML = '<div class="no-order">Không tìm thấy đơn thuê.</div>';
            if (rowsContainer) rowsContainer.innerHTML = '<tr><td colspan="6">Không có chi tiết đơn thuê.</td></tr>';
            return;
        }
        if (titleEl) titleEl.textContent = `Đơn #${order.id_don_thue} - ${order.khach_hang}`;
        if (infoContainer) {
            infoContainer.innerHTML = `
                <div class="detail-card-title">Thông tin đơn thuê</div>
                <div class="detail-row">
                    <div><label>Mã đơn</label><span>${order.id_don_thue}</span></div>
                    <div><label>Trạng thái</label><span>${AdminApi.rentalStatusText(order.trang_thai_ui)}</span></div>
                    <div><label>Ngày đặt</label><span>${AdminApi.formatDate(order.ngay_dat)}</span></div>
                    <div><label>Tổng tiền</label><span>${AdminApi.formatCurrency(order.tong_tien)}</span></div>
                    <div><label>Ghi chú</label><span>${AdminApi.escapeHtml(order.ghi_chu || '')}</span></div>
                </div>
            `;
        }
        if (rowsContainer) {
            rowsContainer.innerHTML = (order.chi_tiet || order.details || []).map((item) => `
                <tr>
                    <td>${item.id_chi_tiet_don_thue}</td>
                    <td>${AdminApi.escapeHtml(item.thiet_bi ? item.thiet_bi.ten_thiet_bi : `Thiết bị #${item.id_thiet_bi}`)}</td>
                    <td>${AdminApi.formatDateTime(item.ngay_nhan)}</td>
                    <td>${AdminApi.formatDateTime(item.ngay_tra)}</td>
                    <td>${item.so_luong || 0}</td>
                    <td>${AdminApi.formatCurrency(item.gia_thue)}</td>
                </tr>
            `).join('') || '<tr><td colspan="6">Không có chi tiết đơn thuê.</td></tr>';
        }
    }

    function initDashboard() {
        if (dashboardInitialized) return;
        dashboardInitialized = true;

        window.parseDateOnly = parseDateOnly;
        window.formatDateTime = AdminApi.formatDateTime;
        window.getStatusText = AdminApi.rentalStatusText;
        window.animateNumber = animateNumber;
        window.filterOrdersByDate = filterOrdersByDate;
        window.updateStatsAndTable = updateStatsAndTable;
        window.loadDashboardStats = loadDashboardStats;
        window.loadRecentTransactions = loadRecentTransactions;
        window.openOrderDetailPopup = openOrderDetailPopup;
        window.closeOrderDetailPopup = closeOrderDetailPopup;
        window.renderOrderDetail = renderOrderDetail;

        const applyBtn = document.getElementById('dashboardApply');
        const resetBtn = document.getElementById('dashboardReset');
        if (applyBtn) {
            applyBtn.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopImmediatePropagation();
                updateStatsAndTable('range');
            }, true);
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopImmediatePropagation();
                document.getElementById('dashboardStart').value = '';
                document.getElementById('dashboardEnd').value = '';
                updateStatsAndTable('all');
            }, true);
        }
        const exportBtn = document.getElementById('dashboardExport');
        if (exportBtn) exportBtn.addEventListener('click', exportDashboard);

        loadDashboardStats('all');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDashboard);
    } else {
        initDashboard();
    }
})();

