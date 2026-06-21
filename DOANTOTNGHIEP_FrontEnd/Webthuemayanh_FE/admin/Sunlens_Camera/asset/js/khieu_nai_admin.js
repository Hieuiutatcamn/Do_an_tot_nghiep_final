document.addEventListener('DOMContentLoaded', () => {
    loadComplaints();
});

const COMPLAINT_STATUSES = [
    'Chờ xử lý',
    'Đang xử lý',
    'Đã tiếp nhận',
    'Chờ phản hồi',
    'Đã xử lý',
];

let complaints = [];

function getComplaintId(item) {
    return item.Id_khieu_nai || item.id_khieu_nai || item.id || '';
}

function formatComplaintProducts(jsonString) {
    if (!jsonString) return '-';
    if (Array.isArray(jsonString)) return jsonString.join(', ');

    try {
        const parsed = JSON.parse(jsonString);
        if (Array.isArray(parsed)) return parsed.join(', ');
    } catch (error) {
        console.warn(error.message || error);
    }

    return String(jsonString);
}

function formatDateTime(date) {
    if (window.AdminApi && typeof AdminApi.formatDateTime === 'function') {
        return AdminApi.formatDateTime(date);
    }
    if (!date) return '-';
    const value = new Date(date);
    if (Number.isNaN(value.getTime())) return date;
    return value.toLocaleString('vi-VN');
}

function statusOptions(status) {
    const values = [...COMPLAINT_STATUSES];
    if (status && !values.includes(status)) values.unshift(status);
    return values.map((value) => `
        <option value="${AdminApi.escapeHtml(value)}" ${status === value ? 'selected' : ''}>
            ${AdminApi.escapeHtml(value)}
        </option>
    `).join('');
}

async function loadComplaints() {
    AdminApi.requireAuth();
    const tbody = document.getElementById('complaints-tbody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="9">Đang tải...</td></tr>';

    try {
        const data = await AdminApi.apiFetch('/admin/complaints?page=1&page_size=100');
        complaints = Array.isArray(data) ? data : (data.danh_sach || data.items || []);
        renderComplaints(complaints);
    } catch (error) {
        console.error(error);
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="9">${AdminApi.escapeHtml(error.message || 'Không tải được khiếu nại.')}</td></tr>`;
        }
    }
}

function renderComplaints(items) {
    const tbody = document.getElementById('complaints-tbody');
    if (!tbody) return;

    if (!items || items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9">Không có khiếu nại</td></tr>';
        return;
    }

    tbody.innerHTML = items.map((item) => {
        const id = getComplaintId(item);
        const products = formatComplaintProducts(item.san_pham_khieu_nai);
        const phone = item.sdt || '';
        return `
            <tr>
                <td style="padding:8px;border-bottom:1px solid #eee;">${AdminApi.escapeHtml(item.ten_khach_hang || '-')}</td>
                <td style="padding:8px;border-bottom:1px solid #eee;">${AdminApi.escapeHtml(phone || '-')}</td>
                <td style="padding:8px;border-bottom:1px solid #eee;">${AdminApi.escapeHtml(item.ma_don || (item.id_don_thue ? `DH${String(item.id_don_thue).padStart(4, '0')}` : '-'))}</td>
                <td style="padding:8px;border-bottom:1px solid #eee;">${AdminApi.escapeHtml(products)}</td>
                <td style="padding:8px;border-bottom:1px solid #eee;"><strong>${AdminApi.escapeHtml(item.tieu_de || '-')}</strong></td>
                <td style="padding:8px;border-bottom:1px solid #eee;">${AdminApi.escapeHtml(item.noi_dung || '').slice(0, 140)}</td>
                <td style="padding:8px;border-bottom:1px solid #eee;">
                    <select class="status-select" data-id="${AdminApi.escapeHtml(id)}" style="padding:6px;border-radius:6px;border:1px solid #d1d5db;">
                        ${statusOptions(item.trang_thai || 'Chờ xử lý')}
                    </select>
                </td>
                <td style="padding:8px;border-bottom:1px solid #eee;">${formatDateTime(item.ngay_khieu_nai)}</td>
                <td style="padding:8px;border-bottom:1px solid #eee;">
                    <button class="view-detail-btn" data-id="${AdminApi.escapeHtml(id)}" style="padding:6px 10px;border-radius:6px;border:1px solid #d1d5db;background:#fff;cursor:pointer;margin-right:8px;">Chi tiết</button>
                    ${phone ? `<a href="tel:${AdminApi.escapeHtml(phone)}" style="padding:6px 10px;border-radius:6px;border:none;background:#059669;color:#fff;text-decoration:none;display:inline-block;">Gọi</a>` : ''}
                </td>
            </tr>
        `;
    }).join('');

    document.querySelectorAll('.status-select').forEach((select) => {
        select.addEventListener('change', (event) => {
            updateComplaintStatus(event.currentTarget.dataset.id, event.currentTarget.value);
        });
    });

    document.querySelectorAll('.view-detail-btn').forEach((button) => {
        button.addEventListener('click', (event) => {
            openComplaintDetail(event.currentTarget.dataset.id);
        });
    });
}

async function updateComplaintStatus(id, status) {
    try {
        await AdminApi.apiFetch(`/admin/complaints/${encodeURIComponent(id)}/status`, {
            method: 'PUT',
            body: { trang_thai: status },
        });
        await loadComplaints();
    } catch (error) {
        alert(error.message || 'Không cập nhật được trạng thái.');
        await loadComplaints();
    }
}

function openComplaintDetail(id) {
    const modal = document.getElementById('complaint-modal');
    const detail = complaints.find((item) => String(getComplaintId(item)) === String(id));
    if (!detail) {
        alert('Không tìm thấy chi tiết khiếu nại');
        return;
    }

    const phone = detail.sdt || '';
    document.getElementById('modal-title').textContent = `Khiếu nại #${getComplaintId(detail)}`;
    document.getElementById('modal-customer').textContent = detail.ten_khach_hang || '-';
    document.getElementById('modal-phone').textContent = phone || '-';
    document.getElementById('modal-order').textContent = detail.ma_don || (detail.id_don_thue ? `DH${String(detail.id_don_thue).padStart(4, '0')}` : '-');
    document.getElementById('modal-products').textContent = formatComplaintProducts(detail.san_pham_khieu_nai);
    document.getElementById('modal-subject').textContent = detail.tieu_de || '-';
    document.getElementById('modal-content').textContent = detail.noi_dung || '-';
    document.getElementById('modal-status').textContent = detail.trang_thai || '-';
    document.getElementById('modal-created').textContent = formatDateTime(detail.ngay_khieu_nai);
    document.getElementById('modal-call').href = phone ? `tel:${phone}` : '#';
    document.getElementById('modal-call').style.display = phone ? 'inline-block' : 'none';
    document.getElementById('modal-mark-resolved').onclick = async function () {
        if (!confirm('Xác nhận đánh dấu khiếu nại là đã xử lý?')) return;
        await updateComplaintStatus(id, 'Đã xử lý');
        modal.style.display = 'none';
    };
    document.getElementById('modal-close').onclick = function () {
        modal.style.display = 'none';
    };
    modal.style.display = 'flex';
}

window.loadComplaints = loadComplaints;
window.renderComplaints = renderComplaints;
window.formatComplaintProducts = formatComplaintProducts;
window.formatDateTime = formatDateTime;
window.updateComplaintStatus = updateComplaintStatus;
window.openComplaintDetail = openComplaintDetail;
