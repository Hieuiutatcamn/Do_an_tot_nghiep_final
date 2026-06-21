(function () {
    'use strict';

    if (window.SunlensUserAccount) return;

    const API_ORIGIN = 'http://127.0.0.1:8000';
    const API_DOI_MAT_KHAU = `${API_ORIGIN}/api/v1/xac-thuc/change-password`;
    const LOGIN_URL = 'dang_nhap.html';
    const USER_LINKS = {
        orders: 'don_thue_cua_toi.html',
        complaints: 'lien_he.html#contact-form',
    };
    const STAFF_ROLES = new Set(['admin', 'nhan vien', 'nhân viên', 'employee']);
    const USER_API_BASES = [
        window.SUNLENS_USER_API_BASE,
        `${API_ORIGIN}/api/v1`,
        `${API_ORIGIN}/api`,
    ].filter(function (value, index, list) {
        return value && list.indexOf(value) === index;
    });
    const AUTH_KEYS = [
        'access_token',
        'refresh_token',
        'token_type',
        'user_account',
        'user_customer',
        'user',
        'current_user',
        'sunlens_user',
        'token',
        'currentUser',
        'admin',
        'adminUser',
        'admin_account',
        'role',
        'vai_tro',
        'auth_user',
        'id_tai_khoan',
        'id_khach_hang',
        'id_admin',
    ];
    const USER_STORAGE_KEYS = [
        'user_customer',
        'user',
        'current_user',
        'sunlens_user',
    ];
    const USER_IMAGE_FIELDS = {
        avatar: {
            fileId: 'userSettingAvatarFile',
            pathId: 'userSettingAvatarPath',
            previewId: 'userSettingAvatarPreview',
            imgId: 'userSettingAvatarImg',
            field: 'anh_cccd',
            uploadSide: 'avatar',
            aliases: [
                'avatar',
                'anh_dai_dien',
                'anh_avatar',
                'image',
                'image_url',
                'anh_cccd',
                'Anh_cccd',
                'Anh_CCCD',
            ],
            payloadFields: ['anh_cccd', 'Anh_cccd', 'Anh_CCCD', 'avatar', 'anh_dai_dien'],
        },
        front: {
            fileId: 'userSettingCccdFrontFile',
            pathId: 'userSettingCccdFrontPath',
            previewId: 'userSettingCccdFrontPreview',
            imgId: 'userSettingCccdFrontImg',
            field: 'anh_cccd_mat_truoc',
            uploadSide: 'front',
            aliases: ['anh_cccd_mat_truoc', 'Anh_cccd_mat_truoc', 'Anh_CCCD_mat_truoc', 'cccdFrontPath'],
            payloadFields: ['anh_cccd_mat_truoc', 'Anh_cccd_mat_truoc', 'Anh_CCCD_mat_truoc'],
        },
        back: {
            fileId: 'userSettingCccdBackFile',
            pathId: 'userSettingCccdBackPath',
            previewId: 'userSettingCccdBackPreview',
            imgId: 'userSettingCccdBackImg',
            field: 'anh_cccd_mat_sau',
            uploadSide: 'back',
            aliases: ['anh_cccd_mat_sau', 'Anh_cccd_mat_sau', 'Anh_CCCD_mat_sau', 'cccdBackPath'],
            payloadFields: ['anh_cccd_mat_sau', 'Anh_cccd_mat_sau', 'Anh_CCCD_mat_sau'],
        },
    };

    let isUserLoggedIn = false;
    let nguoiDungHienTai = null;
    let myComplaints = [];
    const selectedUserImages = {
        avatar: null,
        front: null,
        back: null,
    };

    function ready(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
            return;
        }

        callback();
    }

    function loadNotificationsWidget() {
        if (window.SunlensNotifications || document.querySelector('script[data-sunlens-notifications-js]')) return;

        const script = document.createElement('script');
        script.src = './assets/js/thong_bao.js';
        script.defer = true;
        script.setAttribute('data-sunlens-notifications-js', 'true');
        document.body.appendChild(script);
    }

    function loadUserAccountStyles() {
        if (
            document.querySelector('link[data-sunlens-user-account-css]')
            || document.querySelector('link[href*="user-account.css"]')
        ) return;

        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = './assets/css/user-account.css';
        link.setAttribute('data-sunlens-user-account-css', 'true');
        document.head.appendChild(link);
    }

    function readJson(storage, key) {
        try {
            const raw = storage.getItem(key);
            return raw ? JSON.parse(raw) : null;
        } catch (error) {
            console.warn(`Không đọc được ${key}.`, error);
            return null;
        }
    }

    function getStoredJson(key) {
        return readJson(localStorage, key) || readJson(sessionStorage, key);
    }

    function getToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
    }

    function isPlainObject(value) {
        return value && typeof value === 'object' && !Array.isArray(value);
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

    function normalizeUser(data) {
        if (!isPlainObject(data)) return {};

        const profile = data.khach_hang || data.customer || data.user || data.profile || data;
        const account = data.tai_khoan || data.account || {};

        return {
            ...data,
            ...account,
            ...profile,
            dang_nhap: profile.dang_nhap || profile.username || account.dang_nhap || account.username,
            id_tai_khoan: profile.id_tai_khoan || account.id_tai_khoan || data.id_tai_khoan,
        };
    }

    function isStaffAccount(user) {
        const role = String(user?.vai_tro || user?.role || user?.loai_tai_khoan || '')
            .trim()
            .toLowerCase();
        return STAFF_ROLES.has(role);
    }

    function getCachedUser() {
        const account = getStoredJson('user_account') || {};
        const customer = getStoredJson('user_customer')
            || getStoredJson('user')
            || getStoredJson('current_user')
            || getStoredJson('sunlens_user')
            || {};
        const cached = normalizeUser({ account, customer });

        return Object.keys(cached).some(function (key) {
            return cached[key] !== undefined && cached[key] !== '';
        })
            ? cached
            : null;
    }

    function saveUserToStorage(user) {
        const payload = JSON.stringify(user || {});
        let updatedExistingKey = false;

        USER_STORAGE_KEYS.forEach(function (key) {
            if (localStorage.getItem(key)) {
                localStorage.setItem(key, payload);
                updatedExistingKey = true;
            }
            if (sessionStorage.getItem(key)) {
                sessionStorage.setItem(key, payload);
                updatedExistingKey = true;
            }
        });

        if (!updatedExistingKey) {
            localStorage.setItem('user_customer', payload);
        }
    }

    function clearAuthStorage() {
        AUTH_KEYS.forEach(function (key) {
            localStorage.removeItem(key);
            sessionStorage.removeItem(key);
        });
    }

    function toDateInput(value) {
        if (!value) return '';
        if (/^\d{4}-\d{2}-\d{2}/.test(value)) {
            return String(value).slice(0, 10);
        }

        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return '';
        return date.toISOString().slice(0, 10);
    }

    function userImagePath(user, type) {
        const config = USER_IMAGE_FIELDS[type];
        if (!config || !user) return '';

        for (const key of config.aliases) {
            if (user[key]) return user[key];
        }

        return '';
    }

    function imageSource(path) {
        if (!path) return '';
        if (/^(https?:|data:|blob:)/i.test(path)) return path;
        if (path.startsWith('/')) return `${API_ORIGIN}${path}`;
        return path;
    }

    function cssImageUrl(path) {
        return `url("${imageSource(path).replace(/"/g, '%22')}")`;
    }

    function accountMarkup() {
        return `
            <a href="${LOGIN_URL}" class="text-muted d-flex flex-column justity-content-center align-items-center user-account-trigger" data-user-trigger aria-haspopup="true" aria-expanded="false">
                <span class="user-account-icon">
                    <img class="user-account-avatar" alt="">
                    <i class="bi bi-person"></i>
                </span>
                <span class="d-none d-sm-none d-md-none d-lg-block user-account-label">Tài khoản</span>
            </a>
            <div class="user-dropdown-menu" data-user-dropdown>
                <a href="${USER_LINKS.orders}" class="user-dropdown-item" data-user-orders>
                    <i class="bi bi-bag-check"></i>
                    <span>Đơn hàng đã đặt</span>
                </a>
                <a href="${USER_LINKS.complaints}" class="user-dropdown-item" data-user-complaints>
                    <i class="bi bi-chat-left-text"></i>
                    <span>Khiếu nại</span>
                </a>
                <button type="button" class="user-dropdown-item" data-user-settings>
                    <i class="bi bi-gear"></i>
                    <span>Cài đặt tài khoản</span>
                </button>
                <button type="button" class="user-dropdown-item user-logout-item" data-user-logout>
                    <i class="bi bi-box-arrow-right"></i>
                    <span>Đăng xuất</span>
                </button>
            </div>
        `;
    }

    function isAccountCandidate(item) {
        if (!item.closest('header')) return false;
        if (item.hasAttribute('data-user-menu') || item.querySelector('[data-user-trigger]')) return true;

        const link = item.querySelector('a');
        if (!link) return false;

        const label = item.textContent.replace(/\s+/g, ' ').trim().toLowerCase();
        const hasPersonIcon = !!link.querySelector('.bi-person, .bi-person-circle');

        return label.includes('tài khoản') || label === 'user' || hasPersonIcon;
    }

    function ensureAccountMenus() {
        document.querySelectorAll('header .list-inline-item').forEach(function (item) {
            if (!isAccountCandidate(item)) return;

            item.classList.add('user-account-menu');
            item.setAttribute('data-user-menu', '');
            item.innerHTML = accountMarkup();
        });

        markActiveDropdownItems();
    }

    function markActiveDropdownItems() {
        const currentPage = window.location.pathname.split('/').pop() || 'index.html';

        document.querySelectorAll('[data-user-orders]').forEach(function (link) {
            link.classList.toggle('active', currentPage === 'don_thue_cua_toi.html');
        });
    }

    function displayName(user) {
        return user.ho_ten
            || user.fullName
            || user.name
            || user.dang_nhap
            || user.username
            || user.thu_dien_tu
            || user.email
            || 'User';
    }

    function setLoggedOut() {
        isUserLoggedIn = false;
        nguoiDungHienTai = null;

        document.querySelectorAll('[data-user-menu]').forEach(function (menu) {
            menu.classList.remove('is-authenticated', 'open');

            const trigger = menu.querySelector('[data-user-trigger]');
            const iconWrap = menu.querySelector('.user-account-icon');
            const avatar = menu.querySelector('.user-account-avatar');
            const icon = menu.querySelector('.user-account-icon i');
            const label = menu.querySelector('.user-account-label');

            if (trigger) {
                trigger.setAttribute('href', LOGIN_URL);
                trigger.setAttribute('aria-expanded', 'false');
                trigger.removeAttribute('title');
            }
            if (iconWrap) {
                iconWrap.classList.remove('has-image');
                iconWrap.style.backgroundImage = '';
            }
            if (avatar) {
                avatar.removeAttribute('src');
                avatar.hidden = true;
            }
            if (icon) {
                icon.className = 'bi bi-person';
            }
            if (label) {
                label.textContent = 'Tài khoản';
            }
        });
    }

    function setLoggedIn(user) {
        isUserLoggedIn = true;
        nguoiDungHienTai = user || {};

        document.querySelectorAll('[data-user-menu]').forEach(function (menu) {
            menu.classList.add('is-authenticated');

            const trigger = menu.querySelector('[data-user-trigger]');
            const iconWrap = menu.querySelector('.user-account-icon');
            const avatar = menu.querySelector('.user-account-avatar');
            const icon = menu.querySelector('.user-account-icon i');
            const label = menu.querySelector('.user-account-label');
            const orderLink = menu.querySelector('[data-user-orders]');
            const complaintLink = menu.querySelector('[data-user-complaints]');
            const name = displayName(nguoiDungHienTai);
            const avatarPath = userImagePath(nguoiDungHienTai, 'avatar');

            if (trigger) {
                trigger.setAttribute('href', '#');
                trigger.setAttribute('title', name);
            }
            if (iconWrap) {
                iconWrap.classList.toggle('has-image', Boolean(avatarPath));
                iconWrap.style.backgroundImage = '';
            }
            if (avatar) {
                if (avatarPath) {
                    avatar.src = imageSource(avatarPath);
                    avatar.alt = name;
                    avatar.hidden = false;
                } else {
                    avatar.removeAttribute('src');
                    avatar.hidden = true;
                }
            }
            if (icon) {
                icon.className = 'bi bi-person-circle';
            }
            if (label) {
                label.textContent = 'User';
            }
            if (orderLink) {
                orderLink.setAttribute('href', USER_LINKS.orders);
            }
            if (complaintLink) {
                complaintLink.setAttribute('href', USER_LINKS.complaints);
            }
        });
    }

    function closeUserMenus() {
        document.querySelectorAll('[data-user-menu]').forEach(function (menu) {
            menu.classList.remove('open');

            const trigger = menu.querySelector('[data-user-trigger]');
            if (trigger) {
                trigger.setAttribute('aria-expanded', 'false');
            }
        });
    }

    function settingsModalMarkup() {
        return `
            <div class="modal fade user-settings-modal" id="userSettingsModal" tabindex="-1" aria-labelledby="userSettingsModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered modal-lg">
                    <div class="modal-content border-0">
                        <div class="modal-header">
                            <h5 class="modal-title fw-bold" id="userSettingsModalLabel">Cài đặt tài khoản</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Đóng"></button>
                        </div>
                        <div class="cai-dat-tai-khoan-tabs px-3 pt-3" role="tablist" aria-label="Cài đặt tài khoản">
                            <button class="cai-dat-tai-khoan-tab active" id="tabThongTinTaiKhoan" type="button"
                                    data-bs-toggle="tab" data-bs-target="#userSettingsForm"
                                    role="tab" aria-controls="userSettingsForm" aria-selected="true">
                                Thông tin tài khoản
                            </button>
                            <button class="cai-dat-tai-khoan-tab" id="tabDoiMatKhau" type="button"
                                    data-bs-toggle="tab" data-bs-target="#formDoiMatKhau"
                                    role="tab" aria-controls="formDoiMatKhau" aria-selected="false">
                                Đổi mật khẩu
                            </button>
                        </div>
                        <div class="tab-content">
                            <form id="userSettingsForm" class="tab-pane fade show active" role="tabpanel"
                                  aria-labelledby="tabThongTinTaiKhoan">
                                <div id="khuVucThongTinTaiKhoan">
                                    <div class="modal-body">
                                        <div class="row g-3">
                                    <div class="col-md-6">
                                        <label for="userSettingName" class="form-label">Họ tên</label>
                                        <input type="text" class="form-control" id="userSettingName" name="ho_ten" autocomplete="name">
                                    </div>
                                    <div class="col-md-6">
                                        <label for="userSettingPhone" class="form-label">Số điện thoại</label>
                                        <input type="tel" class="form-control" id="userSettingPhone" name="sdt" autocomplete="tel">
                                    </div>
                                    <div class="col-md-6">
                                        <label for="userSettingEmail" class="form-label">Email</label>
                                        <input type="email" class="form-control" id="userSettingEmail" name="email" autocomplete="email">
                                    </div>
                                    <div class="col-md-6">
                                        <label for="userSettingCccd" class="form-label">Số CCCD</label>
                                        <input type="text" class="form-control" id="userSettingCccd" name="cccd" autocomplete="off">
                                    </div>
                                    <div class="col-md-6">
                                        <label for="userSettingBirthDate" class="form-label">Ngày sinh</label>
                                        <input type="date" class="form-control" id="userSettingBirthDate" name="ngay_sinh">
                                    </div>
                                    <div class="col-12">
                                        <label for="userSettingAddress" class="form-label">Địa chỉ</label>
                                        <textarea class="form-control" id="userSettingAddress" name="dia_chi" rows="3"></textarea>
                                    </div>
                                    <div class="col-12">
                                        <h6 class="fw-bold mb-0 mt-2">Ảnh hồ sơ và CCCD</h6>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="user-image-field">
                                            <label for="userSettingAvatarFile" class="form-label">Ảnh đại diện</label>
                                            <div class="user-image-preview user-avatar-preview" id="userSettingAvatarPreview">
                                                <img id="userSettingAvatarImg" alt="Ảnh đại diện">
                                                <div class="user-image-placeholder">
                                                    <i class="bi bi-person-circle"></i>
                                                    <span>Chưa có ảnh</span>
                                                </div>
                                            </div>
                                            <input type="hidden" id="userSettingAvatarPath" name="anh_cccd">
                                            <input type="file" class="form-control" id="userSettingAvatarFile" accept="image/*">
                                            <div class="user-image-note">Lưu vào trường Anh_cccd</div>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="user-image-field">
                                            <label for="userSettingCccdFrontFile" class="form-label">CCCD mặt trước</label>
                                            <div class="user-image-preview" id="userSettingCccdFrontPreview">
                                                <img id="userSettingCccdFrontImg" alt="Ảnh CCCD mặt trước">
                                                <div class="user-image-placeholder">
                                                    <i class="bi bi-card-image"></i>
                                                    <span>Chưa có ảnh</span>
                                                </div>
                                            </div>
                                            <input type="hidden" id="userSettingCccdFrontPath" name="anh_cccd_mat_truoc">
                                            <input type="file" class="form-control" id="userSettingCccdFrontFile" accept="image/*">
                                            <div class="user-image-note">Lưu vào trường Anh_cccd_mat_truoc</div>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="user-image-field">
                                            <label for="userSettingCccdBackFile" class="form-label">CCCD mặt sau</label>
                                            <div class="user-image-preview" id="userSettingCccdBackPreview">
                                                <img id="userSettingCccdBackImg" alt="Ảnh CCCD mặt sau">
                                                <div class="user-image-placeholder">
                                                    <i class="bi bi-card-image"></i>
                                                    <span>Chưa có ảnh</span>
                                                </div>
                                            </div>
                                            <input type="hidden" id="userSettingCccdBackPath" name="anh_cccd_mat_sau">
                                            <input type="file" class="form-control" id="userSettingCccdBackFile" accept="image/*">
                                            <div class="user-image-note">Lưu vào trường Anh_cccd_mat_sau</div>
                                        </div>
                                    </div>
                                        </div>
                                        <div id="userSettingMessage" class="small mt-3"></div>
                                    </div>
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Đóng</button>
                                        <button type="submit" class="btn btn-primary" id="userSettingSaveBtn">Lưu thay đổi</button>
                                    </div>
                                </div>
                            </form>
                            <form id="formDoiMatKhau" class="tab-pane fade" role="tabpanel"
                                  aria-labelledby="tabDoiMatKhau" novalidate>
                                <div id="khuVucDoiMatKhau" class="khu-vuc-doi-mat-khau">
                                    <div class="modal-body">
                                        <div class="mb-3">
                                            <label for="matKhauHienTai" class="form-label">Mật khẩu hiện tại</label>
                                            <input type="password" class="form-control" id="matKhauHienTai"
                                                   name="mat_khau_hien_tai" autocomplete="current-password" required>
                                        </div>
                                        <div class="mb-3">
                                            <label for="matKhauMoi" class="form-label">Mật khẩu mới</label>
                                            <input type="password" class="form-control" id="matKhauMoi"
                                                   name="mat_khau_moi" autocomplete="new-password" minlength="6" required>
                                        </div>
                                        <div class="mb-3">
                                            <label for="xacNhanMatKhauMoi" class="form-label">Nhập lại mật khẩu mới</label>
                                            <input type="password" class="form-control" id="xacNhanMatKhauMoi"
                                                   name="xac_nhan_mat_khau_moi" autocomplete="new-password" minlength="6" required>
                                        </div>
                                        <div id="thongBaoDoiMatKhau" class="thong-bao-doi-mat-khau"
                                             role="status" aria-live="polite"></div>
                                    </div>
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Đóng</button>
                                        <button type="submit" class="btn btn-primary" id="nutCapNhatMatKhau">
                                            Cập nhật mật khẩu
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    function ensureSettingsModal() {
        if (!document.getElementById('userSettingsModal')) {
            document.body.insertAdjacentHTML('beforeend', settingsModalMarkup());
        }
    }

    function complaintsModalMarkup() {
        return `
            <div class="modal fade user-complaints-modal" id="userComplaintsModal" tabindex="-1" aria-labelledby="userComplaintsModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered modal-lg">
                    <div class="modal-content border-0">
                        <div class="modal-header">
                            <div>
                                <h5 class="modal-title fw-bold" id="userComplaintsModalLabel">Quản lý khiếu nại</h5>
                                <div class="user-complaints-subtitle">Theo dõi các khiếu nại bạn đã gửi.</div>
                            </div>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="user-complaints-view" id="userComplaintsListView">
                                <div class="user-complaints-toolbar">
                                    <button type="button" class="btn btn-primary btn-sm" data-user-complaint-new>
                                        Gửi khiếu nại mới
                                    </button>
                                </div>
                                <div id="userComplaintsMessage" class="small"></div>
                                <div class="user-complaints-list" id="userComplaintsList"></div>
                            </div>
                            <div class="user-complaints-view d-none" id="userComplaintDetailView">
                                <button type="button" class="btn btn-link px-0 mb-3 user-complaint-back" data-user-complaint-back>
                                    Quay lại danh sách
                                </button>
                                <div class="user-complaint-detail-card" id="userComplaintDetail"></div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Đóng</button>
                            <button type="button" class="btn btn-primary" data-user-complaint-new>Gửi khiếu nại mới</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    function ensureComplaintsModal() {
        if (!document.getElementById('userComplaintsModal')) {
            document.body.insertAdjacentHTML('beforeend', complaintsModalMarkup());
        }
    }

    function setComplaintsMessage(message, type) {
        const messageEl = document.getElementById('userComplaintsMessage');
        if (!messageEl) return;

        messageEl.textContent = message || '';
        messageEl.className = `small mb-3 ${type === 'error' ? 'text-danger fw-semibold' : 'text-muted'}`;
    }

    function complaintId(complaint) {
        return complaint.Id_khieu_nai || complaint.id_khieu_nai || complaint.id || '';
    }

    function complaintCode(complaint) {
        const id = complaintId(complaint);
        return id ? `KN${String(id).padStart(4, '0')}` : '-';
    }

    function orderCodeFromComplaint(complaint) {
        if (complaint.ma_don) return complaint.ma_don;
        return complaint.id_don_thue ? `DH${String(complaint.id_don_thue).padStart(4, '0')}` : '-';
    }

    function formatComplaintProducts(value) {
        if (!value) return '-';
        if (Array.isArray(value)) return value.join(', ');

        try {
            const parsed = JSON.parse(value);
            if (Array.isArray(parsed)) return parsed.join(', ');
        } catch (error) {
            console.warn(error.message || error);
        }

        return String(value);
    }

    function formatComplaintDate(value) {
        if (!value) return '-';
        const date = new Date(String(value).replace(' ', 'T'));
        if (Number.isNaN(date.getTime())) return String(value);
        return date.toLocaleString('vi-VN');
    }

    function complaintStatusLabel(status) {
        const raw = String(status || 'Chờ xử lý').trim();
        const aliases = {
            'Cho xu ly': 'Chờ xử lý',
            'Dang xu ly': 'Đang xử lý',
            'Da tiep nhan': 'Đã tiếp nhận',
            'Cho phan hoi': 'Chờ phản hồi',
            'Da xu ly': 'Đã xử lý',
        };
        return aliases[raw] || raw;
    }

    function getComplaintStatusBadge(status) {
        const normalized = complaintStatusLabel(status);
        const statusClasses = {
            'Chờ xử lý': 'is-pending',
            'Đang xử lý': 'is-processing',
            'Đã tiếp nhận': 'is-accepted',
            'Chờ phản hồi': 'is-waiting',
            'Đã xử lý': 'is-resolved',
        };
        const className = statusClasses[normalized] || 'is-pending';
        return `<span class="user-complaint-status ${className}">${escapeHtml(normalized)}</span>`;
    }

    function complaintSummary(text, maxLength) {
        const value = String(text || '-').trim();
        if (value.length <= maxLength) return value;
        return `${value.slice(0, maxLength).trim()}...`;
    }

    function renderMyComplaints(items) {
        const list = document.getElementById('userComplaintsList');
        if (!list) return;

        myComplaints = Array.isArray(items) ? items : [];

        if (!myComplaints.length) {
            list.innerHTML = `
                <div class="user-complaints-empty">
                    <div class="user-complaints-empty-icon"><i class="bi bi-inbox"></i></div>
                    <h6>Bạn chưa gửi khiếu nại nào</h6>
                    <p>Vui lòng chọn đơn hàng cần khiếu nại trong mục Đơn hàng đã thuê.</p>
                    <button type="button" class="btn btn-primary btn-sm" data-user-complaint-new>Gửi khiếu nại mới</button>
                </div>
            `;
            return;
        }

        list.innerHTML = myComplaints.map(function (complaint) {
            const id = complaintId(complaint);
            const products = formatComplaintProducts(complaint.san_pham_khieu_nai);
            return `
                <article class="user-complaint-card">
                    <div class="user-complaint-card-header">
                        <div>
                            <div class="user-complaint-code">${escapeHtml(complaintCode(complaint))}</div>
                            <div class="user-complaint-order">Đơn thuê: ${escapeHtml(orderCodeFromComplaint(complaint))}</div>
                        </div>
                        ${getComplaintStatusBadge(complaint.trang_thai)}
                    </div>
                    <div class="user-complaint-grid">
                        <div>
                            <span>Sản phẩm khiếu nại</span>
                            <strong>${escapeHtml(products)}</strong>
                        </div>
                        <div>
                            <span>Ngày khiếu nại</span>
                            <strong>${escapeHtml(formatComplaintDate(complaint.ngay_khieu_nai))}</strong>
                        </div>
                    </div>
                    <div class="user-complaint-title">${escapeHtml(complaint.tieu_de || '-')}</div>
                    <p class="user-complaint-content">${escapeHtml(complaintSummary(complaint.noi_dung, 150))}</p>
                    <button type="button" class="btn btn-outline-primary btn-sm" data-user-complaint-detail="${escapeHtml(id)}">
                        Xem chi tiết
                    </button>
                </article>
            `;
        }).join('');
    }

    async function loadMyComplaints() {
        const list = document.getElementById('userComplaintsList');
        if (list) {
            list.innerHTML = '<div class="user-complaints-loading">Đang tải khiếu nại...</div>';
        }
        setComplaintsMessage('', 'info');

        try {
            const data = await userApiFetch('/complaints/my-complaints');
            renderMyComplaints(Array.isArray(data) ? data : (data.danh_sach || data.items || []));
        } catch (error) {
            console.error(error);
            if (error.status === 401 || error.status === 403) {
                clearAuthStorage();
                setLoggedOut();
                window.location.href = LOGIN_URL;
                return;
            }
            renderMyComplaints([]);
            setComplaintsMessage(error.message || 'Không tải được danh sách khiếu nại.', 'error');
        }
    }

    function showComplaintsListView() {
        const listView = document.getElementById('userComplaintsListView');
        const detailView = document.getElementById('userComplaintDetailView');
        if (listView) listView.classList.remove('d-none');
        if (detailView) detailView.classList.add('d-none');
    }

    function openComplaintDetail(id) {
        const complaint = myComplaints.find(function (item) {
            return String(complaintId(item)) === String(id);
        });
        const detail = document.getElementById('userComplaintDetail');
        const listView = document.getElementById('userComplaintsListView');
        const detailView = document.getElementById('userComplaintDetailView');

        if (!complaint || !detail) return;

        detail.innerHTML = `
            <div class="user-complaint-detail-head">
                <div>
                    <div class="user-complaint-code">${escapeHtml(complaintCode(complaint))}</div>
                    <div class="user-complaint-order">Đơn thuê: ${escapeHtml(orderCodeFromComplaint(complaint))}</div>
                </div>
                ${getComplaintStatusBadge(complaint.trang_thai)}
            </div>
            <dl class="user-complaint-detail-list">
                <div>
                    <dt>Sản phẩm khiếu nại</dt>
                    <dd>${escapeHtml(formatComplaintProducts(complaint.san_pham_khieu_nai))}</dd>
                </div>
                <div>
                    <dt>Tiêu đề</dt>
                    <dd>${escapeHtml(complaint.tieu_de || '-')}</dd>
                </div>
                <div>
                    <dt>Nội dung</dt>
                    <dd>${escapeHtml(complaint.noi_dung || '-')}</dd>
                </div>
                <div>
                    <dt>Ngày gửi</dt>
                    <dd>${escapeHtml(formatComplaintDate(complaint.ngay_khieu_nai))}</dd>
                </div>
            </dl>
        `;

        if (listView) listView.classList.add('d-none');
        if (detailView) detailView.classList.remove('d-none');
    }

    function closeComplaintsModal() {
        const modalElement = document.getElementById('userComplaintsModal');
        if (!modalElement || !window.bootstrap || !window.bootstrap.Modal) return;
        window.bootstrap.Modal.getOrCreateInstance(modalElement).hide();
    }

    function openComplaintsModal() {
        if (!isUserLoggedIn || !nguoiDungHienTai) {
            window.location.href = LOGIN_URL;
            return;
        }

        ensureComplaintsModal();
        closeUserMenus();
        showComplaintsListView();

        const modalElement = document.getElementById('userComplaintsModal');
        if (!modalElement || !window.bootstrap || !window.bootstrap.Modal) return;

        window.bootstrap.Modal.getOrCreateInstance(modalElement).show();
        loadMyComplaints();
    }

    function setUserImagePreview(type, path) {
        const config = USER_IMAGE_FIELDS[type];
        if (!config) return;

        const preview = document.getElementById(config.previewId);
        const img = document.getElementById(config.imgId);
        const pathInput = document.getElementById(config.pathId);
        const source = imageSource(path);

        if (pathInput) {
            pathInput.value = path || '';
        }
        if (preview) {
            preview.classList.toggle('has-image', Boolean(source));
        }
        if (img) {
            if (source) {
                img.src = source;
            } else {
                img.removeAttribute('src');
            }
        }
    }

    function previewSelectedUserImage(type, file) {
        const config = USER_IMAGE_FIELDS[type];
        const preview = document.getElementById(config.previewId);
        const img = document.getElementById(config.imgId);

        if (!file || !preview || !img) return;

        img.src = URL.createObjectURL(file);
        preview.classList.add('has-image');
    }

    function resetSelectedUserImages() {
        Object.keys(selectedUserImages).forEach(function (type) {
            selectedUserImages[type] = null;
            const input = document.getElementById(USER_IMAGE_FIELDS[type].fileId);
            if (input) {
                input.value = '';
            }
        });
    }

    function selectedImagePath(type) {
        const config = USER_IMAGE_FIELDS[type];
        const input = document.getElementById(config.pathId);
        return input ? input.value.trim() : '';
    }

    function userIdForUpload() {
        const user = nguoiDungHienTai || {};
        const id = user.id_khach_hang
            || user.id_tai_khoan
            || user.id
            || user.user_id
            || 'me';

        return String(id);
    }

    function customerIdFromUser(user) {
        const targetUser = user || nguoiDungHienTai || {};
        const cached = getCachedUser() || {};

        return targetUser.id_khach_hang
            || targetUser.customer_id
            || cached.id_khach_hang
            || cached.customer_id
            || '';
    }

    function fileToDataUrl(file) {
        return new Promise(function (resolve, reject) {
            const reader = new FileReader();
            reader.onload = function () {
                resolve(reader.result);
            };
            reader.onerror = function () {
                reject(reader.error || new Error('Không đọc được file ảnh.'));
            };
            reader.readAsDataURL(file);
        });
    }

    async function readApiResponse(response) {
        if (response.status === 204) return null;

        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            return response.json();
        }

        return response.text();
    }

    function apiError(data, status) {
        if (isPlainObject(data)) {
            const detail = data.detail || data.message || data.error;
            if (Array.isArray(detail)) {
                return detail.map(function (item) {
                    return item.msg || item.message || JSON.stringify(item);
                }).join('\n');
            }
            if (detail) return detail;
        }
        if (typeof data === 'string' && data.trim()) return data.trim();
        return `API lỗi ${status}`;
    }

    async function userApiFetch(path, options) {
        const token = getToken();
        if (!token) {
            const error = new Error('Bạn cần đăng nhập để tiếp tục.');
            error.status = 401;
            throw error;
        }

        let lastError = null;

        for (const baseUrl of USER_API_BASES) {
            const headers = new Headers((options && options.headers) || {});
            headers.set('Authorization', `Bearer ${token}`);

            let body = options && options.body;
            if (body && !(body instanceof FormData) && typeof body !== 'string') {
                headers.set('Content-Type', 'application/json');
                body = JSON.stringify(body);
            }

            let response;
            try {
                response = await fetch(`${baseUrl}${path}`, {
                    ...(options || {}),
                    headers,
                    body,
                });
            } catch (error) {
                lastError = error;
                continue;
            }

            const data = await readApiResponse(response);

            if (response.ok) {
                return data;
            }

            if (response.status === 404) {
                lastError = new Error(apiError(data, response.status));
                lastError.status = response.status;
                continue;
            }

            const error = new Error(apiError(data, response.status));
            error.status = response.status;
            throw error;
        }

        throw lastError || new Error('Không gọi được API người dùng.');
    }

    function isNotFoundError(error) {
        const message = String((error && error.message) || '').toLowerCase();
        return (error && error.status === 404)
            || message.includes('not found')
            || message.includes('404')
            || message.includes('không tìm thấy');
    }

    async function fetchUserProfileData() {
        let lastError = null;

        try {
            return await userApiFetch('/nguoi-dung/me');
        } catch (error) {
            if (!isNotFoundError(error)) throw error;
            lastError = error;
        }

        try {
            return await userApiFetch('/xac-thuc/me');
        } catch (error) {
            if (!isNotFoundError(error)) throw error;
            lastError = error;
        }

        try {
            return await userApiFetch('/users/me');
        } catch (error) {
            if (!isNotFoundError(error)) throw error;
            lastError = error;
        }

        try {
            return await userApiFetch('/auth/me');
        } catch (error) {
            if (!isNotFoundError(error)) throw error;
            lastError = error;
        }

        const customerId = customerIdFromUser(getCachedUser());
        if (customerId) {
            try {
                return await userApiFetch(`/khach-hang/${customerId}`);
            } catch (error) {
                if (!isNotFoundError(error)) throw error;
                lastError = error;
            }

            try {
                return await userApiFetch(`/customers/${customerId}`);
            } catch (error) {
                if (!isNotFoundError(error)) throw error;
                lastError = error;
            }
        }

        throw lastError || new Error('Không lấy được thông tin người dùng.');
    }

    function fillSettingsForm(user) {
        const fields = {
            userSettingName: user.ho_ten || user.fullName || user.name || '',
            userSettingPhone: user.sdt || user.phone || user.so_dien_thoai || '',
            userSettingEmail: user.thu_dien_tu || user.email || '',
            userSettingCccd: user.cccd || user.so_cccd || user.So_CCCD || user.identityNumber || '',
            userSettingBirthDate: toDateInput(user.ngay_sinh || user.birthDate || user.date_of_birth),
            userSettingAddress: user.dia_chi || user.address || '',
        };

        Object.keys(fields).forEach(function (id) {
            const field = document.getElementById(id);
            if (field) {
                field.value = fields[id];
            }
        });

        resetSelectedUserImages();
        setUserImagePreview('avatar', userImagePath(user, 'avatar'));
        setUserImagePreview('front', userImagePath(user, 'front'));
        setUserImagePreview('back', userImagePath(user, 'back'));
    }

    function setImagePayloadFields(payload, type, value) {
        const config = USER_IMAGE_FIELDS[type];
        const normalizedValue = value || null;

        (config.payloadFields || [config.field]).forEach(function (fieldName) {
            payload[fieldName] = normalizedValue;
        });
    }

    function collectSettingsPayload() {
        const payload = {
            ho_ten: document.getElementById('userSettingName').value.trim(),
            sdt: document.getElementById('userSettingPhone').value.trim(),
            email: document.getElementById('userSettingEmail').value.trim(),
            cccd: document.getElementById('userSettingCccd').value.trim(),
            dia_chi: document.getElementById('userSettingAddress').value.trim(),
            ngay_sinh: document.getElementById('userSettingBirthDate').value || null,
        };

        setImagePayloadFields(payload, 'avatar', selectedImagePath('avatar'));
        setImagePayloadFields(payload, 'front', selectedImagePath('front'));
        setImagePayloadFields(payload, 'back', selectedImagePath('back'));

        return payload;
    }

    function customerUpdatePayload(payload) {
        return {
            ho_ten: payload.ho_ten,
            sdt: payload.sdt || null,
            email: payload.email || null,
            cccd: payload.cccd || null,
            dia_chi: payload.dia_chi || null,
            ngay_sinh: payload.ngay_sinh || null,
            anh_cccd: payload.anh_cccd || payload.Anh_cccd || payload.Anh_CCCD || null,
            anh_cccd_mat_truoc: payload.anh_cccd_mat_truoc || payload.Anh_cccd_mat_truoc || payload.Anh_CCCD_mat_truoc || null,
            anh_cccd_mat_sau: payload.anh_cccd_mat_sau || payload.Anh_cccd_mat_sau || payload.Anh_CCCD_mat_sau || null,
        };
    }

    async function updateUserProfileData(payload) {
        let lastError = null;

        try {
            return await userApiFetch('/nguoi-dung/me', {
                method: 'PUT',
                body: customerUpdatePayload(payload),
            });
        } catch (error) {
            if (!isNotFoundError(error)) throw error;
            lastError = error;
        }

        try {
            return await userApiFetch('/users/me', {
                method: 'PUT',
                body: customerUpdatePayload(payload),
            });
        } catch (error) {
            if (!isNotFoundError(error)) throw error;
            lastError = error;
        }

        const customerId = customerIdFromUser();
        if (customerId) {
            try {
                return await userApiFetch(`/khach-hang/${customerId}`, {
                    method: 'PUT',
                    body: customerUpdatePayload(payload),
                });
            } catch (error) {
                if (!isNotFoundError(error)) throw error;
                lastError = error;
            }

            try {
                return await userApiFetch(`/customers/${customerId}`, {
                    method: 'PUT',
                    body: customerUpdatePayload(payload),
                });
            } catch (error) {
                if (!isNotFoundError(error)) throw error;
                lastError = error;
            }
        }

        throw lastError || new Error('Không cập nhật được thông tin người dùng.');
    }

    function setSettingsMessage(message, type) {
        const messageEl = document.getElementById('userSettingMessage');
        if (!messageEl) return;

        messageEl.textContent = message || '';
        messageEl.className = `small mt-3 ${type === 'success' ? 'text-success fw-semibold' : 'text-danger fw-semibold'}`;
    }

    function hienThiThongBaoDoiMatKhau(thongBao, loai = 'error') {
        const khuVucThongBao = document.getElementById('thongBaoDoiMatKhau');
        if (!khuVucThongBao) return;

        khuVucThongBao.textContent = thongBao || '';
        khuVucThongBao.className = 'thong-bao-doi-mat-khau';
        if (thongBao) {
            khuVucThongBao.classList.add(loai === 'success' ? 'thanh-cong' : 'loi');
        }
    }

    function xoaTrangThaiLoiDoiMatKhau() {
        ['matKhauHienTai', 'matKhauMoi', 'xacNhanMatKhauMoi'].forEach(function (id) {
            const oNhap = document.getElementById(id);
            if (!oNhap) return;
            oNhap.classList.remove('is-invalid');
            oNhap.removeAttribute('aria-invalid');
        });
    }

    function danhDauLoiDoiMatKhau(oNhap) {
        if (!oNhap) return;
        oNhap.classList.add('is-invalid');
        oNhap.setAttribute('aria-invalid', 'true');
    }

    function kiemTraDuLieuDoiMatKhau() {
        const matKhauHienTai = document.getElementById('matKhauHienTai');
        const matKhauMoi = document.getElementById('matKhauMoi');
        const xacNhanMatKhauMoi = document.getElementById('xacNhanMatKhauMoi');
        const cacONhap = [matKhauHienTai, matKhauMoi, xacNhanMatKhauMoi];

        xoaTrangThaiLoiDoiMatKhau();

        const oNhapBiTrong = cacONhap.filter(function (oNhap) {
            return !oNhap || oNhap.value.trim().length === 0;
        });
        if (oNhapBiTrong.length) {
            oNhapBiTrong.forEach(danhDauLoiDoiMatKhau);
            hienThiThongBaoDoiMatKhau('Vui lòng nhập đầy đủ thông tin đổi mật khẩu.');
            if (oNhapBiTrong[0]) oNhapBiTrong[0].focus();
            return null;
        }

        if (matKhauMoi.value.length < 6) {
            danhDauLoiDoiMatKhau(matKhauMoi);
            hienThiThongBaoDoiMatKhau('Mật khẩu mới phải có tối thiểu 6 ký tự.');
            matKhauMoi.focus();
            return null;
        }

        if (xacNhanMatKhauMoi.value !== matKhauMoi.value) {
            danhDauLoiDoiMatKhau(xacNhanMatKhauMoi);
            hienThiThongBaoDoiMatKhau('Nhập lại mật khẩu mới không khớp.');
            xacNhanMatKhauMoi.focus();
            return null;
        }

        if (matKhauMoi.value === matKhauHienTai.value) {
            danhDauLoiDoiMatKhau(matKhauMoi);
            hienThiThongBaoDoiMatKhau('Mật khẩu mới không được trùng mật khẩu hiện tại.');
            matKhauMoi.focus();
            return null;
        }

        return {
            mat_khau_hien_tai: matKhauHienTai.value,
            mat_khau_moi: matKhauMoi.value,
        };
    }

    async function goiApiDoiMatKhau(duLieuDoiMatKhau) {
        const token = getToken();
        if (!token) {
            const loiKhongCoToken = new Error('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
            loiKhongCoToken.status = 401;
            throw loiKhongCoToken;
        }

        const phanHoi = await fetch(API_DOI_MAT_KHAU, {
            method: 'PUT',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(duLieuDoiMatKhau),
        });
        const duLieuPhanHoi = await readApiResponse(phanHoi);

        if (!phanHoi.ok) {
            const loiApi = new Error(apiError(duLieuPhanHoi, phanHoi.status));
            loiApi.status = phanHoi.status;
            throw loiApi;
        }

        return duLieuPhanHoi;
    }

    function thongBaoLoiDoiMatKhau(loi) {
        if (loi && loi.status === 401) {
            return 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.';
        }

        const noiDungLoi = String((loi && loi.message) || '').trim();
        const noiDungThuong = noiDungLoi.toLocaleLowerCase('vi-VN');
        if (noiDungThuong.includes('mật khẩu hiện tại') && noiDungThuong.includes('không đúng')) {
            return 'Mật khẩu hiện tại không đúng.';
        }
        if (noiDungThuong.includes('mật khẩu mới') && noiDungThuong.includes('trùng')) {
            return 'Mật khẩu mới không được trùng mật khẩu hiện tại.';
        }

        return noiDungLoi || 'Không thể đổi mật khẩu.';
    }

    function datLaiFormDoiMatKhau(xoaThongBao = true) {
        const formDoiMatKhau = document.getElementById('formDoiMatKhau');
        if (formDoiMatKhau) formDoiMatKhau.reset();
        xoaTrangThaiLoiDoiMatKhau();
        if (xoaThongBao) hienThiThongBaoDoiMatKhau('');
    }

    async function doiMatKhauNguoiDung(event) {
        event.preventDefault();

        const duLieuDoiMatKhau = kiemTraDuLieuDoiMatKhau();
        if (!duLieuDoiMatKhau) return;

        const nutCapNhatMatKhau = document.getElementById('nutCapNhatMatKhau');
        hienThiThongBaoDoiMatKhau('');
        if (nutCapNhatMatKhau) {
            nutCapNhatMatKhau.disabled = true;
            nutCapNhatMatKhau.textContent = 'Đang cập nhật...';
        }

        try {
            await goiApiDoiMatKhau(duLieuDoiMatKhau);
            datLaiFormDoiMatKhau(false);
            hienThiThongBaoDoiMatKhau('Đổi mật khẩu thành công.', 'success');
        } catch (loi) {
            hienThiThongBaoDoiMatKhau(thongBaoLoiDoiMatKhau(loi));
        } finally {
            if (nutCapNhatMatKhau) {
                nutCapNhatMatKhau.disabled = false;
                nutCapNhatMatKhau.textContent = 'Cập nhật mật khẩu';
            }
        }
    }

    function uploadPathFromResponse(data, type) {
        if (!data || typeof data !== 'object') return '';

        const config = USER_IMAGE_FIELDS[type];
        const candidateObjects = [
            data,
            data.account,
            data.customer,
            data.khach_hang,
            data.user,
            data.profile,
        ].filter(isPlainObject);

        const candidateKeys = type === 'avatar'
            ? ['path', 'url', 'image_url', 'anh_dai_dien', 'avatar', config.field, ...config.aliases]
            : ['path', 'url', 'image_url', config.field, ...config.aliases];

        for (const item of candidateObjects) {
            for (const key of candidateKeys) {
                if (item[key]) return item[key];
            }
        }

        return data.filename ? `assets/images/user/${data.filename}` : '';
    }

    async function postUserImage(path, type, file, side) {
        const formData = new FormData();
        formData.append('file', file);
        if (side) {
            formData.append('side', side);
        }
        formData.append('user_id', userIdForUpload());

        const data = await userApiFetch(path, {
            method: 'POST',
            body: formData,
        });
        const uploadedPath = uploadPathFromResponse(data, type);

        if (!uploadedPath) {
            throw new Error('API upload chưa trả về đường dẫn ảnh.');
        }

        return uploadedPath;
    }

    async function postCustomerCccdImage(type, file) {
        const customerId = customerIdFromUser();
        if (!customerId) {
            const error = new Error('Không xác định được khách hàng để upload ảnh CCCD.');
            error.status = 404;
            throw error;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('side', USER_IMAGE_FIELDS[type].uploadSide);

        const data = await userApiFetch(`/khach-hang/${customerId}/cccd-image`, {
            method: 'POST',
            body: formData,
        });
        const uploadedPath = uploadPathFromResponse(data, type);

        if (!uploadedPath) {
            throw new Error('API upload chưa trả về đường dẫn ảnh.');
        }

        return uploadedPath;
    }

    function shouldUseInlineImageFallback(error, type) {
        const message = String((error && error.message) || '').toLowerCase();
        return isNotFoundError(error)
            || (type === 'avatar' && (message.includes('side') || message.includes('avatar')));
    }

    async function tryUploadImage(path, type, file, side) {
        try {
            return await postUserImage(path, type, file, side);
        } catch (error) {
            if (isNotFoundError(error)) return '';
            throw error;
        }
    }

    async function uploadUserImage(type, file) {
        const config = USER_IMAGE_FIELDS[type];

        if (type !== 'avatar') {
            try {
                return await postCustomerCccdImage(type, file);
            } catch (error) {
                if (!shouldUseInlineImageFallback(error, type)) {
                    throw error;
                }
            }
        }

        if (type === 'avatar') {
            try {
                const duongDanAnhDaiDien = await tryUploadImage('/nguoi-dung/upload-anh_dai_dien', type, file);
                if (duongDanAnhDaiDien) {
                    return duongDanAnhDaiDien;
                }
                const duongDanCu = await tryUploadImage('/users/upload-avatar', type, file, config.uploadSide);
                if (duongDanCu) {
                    return duongDanCu;
                }
            } catch (error) {
                if (!shouldUseInlineImageFallback(error, type)) {
                    console.warn(error.message || error);
                }
            }
        }

        try {
            const duongDanCccdNguoiDung = await tryUploadImage('/nguoi-dung/upload-cccd', type, file, config.uploadSide);
            if (duongDanCccdNguoiDung) {
                return duongDanCccdNguoiDung;
            }
            const duongDanCccdCu = await tryUploadImage('/users/upload-cccd', type, file, config.uploadSide);
            if (duongDanCccdCu) {
                return duongDanCccdCu;
            }
            return fileToDataUrl(file);
        } catch (error) {
            if (shouldUseInlineImageFallback(error, type)) {
                return fileToDataUrl(file);
            }
            throw error;
        }
    }

    async function uploadSelectedUserImages(payload) {
        for (const type of Object.keys(USER_IMAGE_FIELDS)) {
            const file = selectedUserImages[type];
            if (!file) continue;

            const uploadedPath = await uploadUserImage(type, file);
            setImagePayloadFields(payload, type, uploadedPath);
            setUserImagePreview(type, uploadedPath);
        }
    }

    async function taiThongTinTaiKhoan() {
        const token = getToken();
        const cachedUser = getCachedUser();

        if (!token) {
            setLoggedOut();
            return;
        }

        if (cachedUser && isStaffAccount(cachedUser)) {
            clearAuthStorage();
            setLoggedOut();
            return;
        }

        if (cachedUser) {
            setLoggedIn(cachedUser);
        } else {
            setLoggedIn({});
        }

        try {
            const data = await fetchUserProfileData();
            const user = normalizeUser(data);

            if (!Object.keys(user).length) {
                throw new Error('Không có dữ liệu người dùng.');
            }
            if (isStaffAccount(user)) {
                clearAuthStorage();
                setLoggedOut();
                return;
            }

            nguoiDungHienTai = {
                ...(cachedUser || {}),
                ...user,
            };
            saveUserToStorage(nguoiDungHienTai);
            setLoggedIn(nguoiDungHienTai);
        } catch (error) {
            console.warn(error.message || error);
            if ((error.status === 401 || error.status === 403) || !cachedUser) {
                clearAuthStorage();
                setLoggedOut();
            }
        }
    }

    async function refreshSettingsProfile() {
        try {
            const data = await fetchUserProfileData();
            const user = normalizeUser(data);

            if (!Object.keys(user).length) return;
            if (isStaffAccount(user)) {
                clearAuthStorage();
                setLoggedOut();
                return;
            }

            nguoiDungHienTai = {
                ...(nguoiDungHienTai || {}),
                ...user,
            };
            saveUserToStorage(nguoiDungHienTai);
            setLoggedIn(nguoiDungHienTai);
            fillSettingsForm(nguoiDungHienTai);
        } catch (error) {
            console.warn(error.message || error);
            if (error.status === 401 || error.status === 403) {
                clearAuthStorage();
                setLoggedOut();
            }
        }
    }

    function openSettingsModal() {
        if (!isUserLoggedIn || !nguoiDungHienTai) {
            window.location.href = LOGIN_URL;
            return;
        }

        ensureSettingsModal();
        closeUserMenus();
        fillSettingsForm(nguoiDungHienTai);
        setSettingsMessage('', 'success');
        datLaiFormDoiMatKhau();

        const modalElement = document.getElementById('userSettingsModal');
        if (!modalElement || !window.bootstrap || !window.bootstrap.Modal) return;

        const modal = window.bootstrap.Modal.getOrCreateInstance(modalElement);
        modal.show();
        refreshSettingsProfile();
    }

    async function handleSettingsSubmit(event) {
        event.preventDefault();

        const submitButton = document.getElementById('userSettingSaveBtn');
        const payload = collectSettingsPayload();

        setSettingsMessage('', 'success');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Đang lưu...';
        }

        try {
            await uploadSelectedUserImages(payload);

            const data = await updateUserProfileData(payload);
            const updatedUser = normalizeUser(data);
            let refreshedUser = {};

            try {
                refreshedUser = normalizeUser(await fetchUserProfileData());
            } catch (refreshError) {
                console.warn(refreshError.message || refreshError);
            }

            nguoiDungHienTai = {
                ...(nguoiDungHienTai || {}),
                ...payload,
                ...updatedUser,
                ...refreshedUser,
            };
            saveUserToStorage(nguoiDungHienTai);
            setLoggedIn(nguoiDungHienTai);
            fillSettingsForm(nguoiDungHienTai);
            setSettingsMessage('Cập nhật thông tin thành công', 'success');
        } catch (error) {
            console.error(error);
            setSettingsMessage(error.message || 'Không thể cập nhật thông tin.', 'error');
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = 'Lưu thay đổi';
            }
        }
    }

    function logoutUser(event) {
        if (event) {
            event.preventDefault();
        }

        clearAuthStorage();
        setLoggedOut();
        window.location.href = LOGIN_URL;
    }

    function handleDocumentClick(event) {
        const trigger = event.target.closest('[data-user-trigger]');
        const settingsButton = event.target.closest('[data-user-settings]');
        const complaintsButton = event.target.closest('[data-user-complaints]');
        const complaintDetailButton = event.target.closest('[data-user-complaint-detail]');
        const complaintBackButton = event.target.closest('[data-user-complaint-back]');
        const newComplaintButton = event.target.closest('[data-user-complaint-new]');
        const logoutButton = event.target.closest('[data-user-logout]');

        if (complaintDetailButton) {
            event.preventDefault();
            openComplaintDetail(complaintDetailButton.dataset.userComplaintDetail);
            return;
        }

        if (complaintBackButton) {
            event.preventDefault();
            showComplaintsListView();
            return;
        }

        if (newComplaintButton) {
            event.preventDefault();
            closeComplaintsModal();
            window.location.href = USER_LINKS.orders;
            return;
        }

        if (complaintsButton) {
            event.preventDefault();
            openComplaintsModal();
            return;
        }

        if (settingsButton) {
            event.preventDefault();
            openSettingsModal();
            return;
        }

        if (logoutButton) {
            logoutUser(event);
            return;
        }

        if (trigger) {
            const menu = trigger.closest('[data-user-menu]');
            if (!menu || !isUserLoggedIn) return;

            event.preventDefault();
            const isOpen = menu.classList.contains('open');
            closeUserMenus();
            menu.classList.toggle('open', !isOpen);
            trigger.setAttribute('aria-expanded', String(!isOpen));
            return;
        }

        if (!event.target.closest('[data-user-menu]')) {
            closeUserMenus();
        }
    }

    function bindSettingsImageInputs() {
        Object.keys(USER_IMAGE_FIELDS).forEach(function (type) {
            const input = document.getElementById(USER_IMAGE_FIELDS[type].fileId);
            if (!input || input.dataset.userAccountBound === 'true') return;

            input.dataset.userAccountBound = 'true';
            input.addEventListener('change', function () {
                const file = input.files && input.files[0];
                selectedUserImages[type] = null;

                if (!file) {
                    setUserImagePreview(type, selectedImagePath(type));
                    return;
                }

                if (!file.type.startsWith('image/')) {
                    input.value = '';
                    alert('Vui lòng chọn đúng file ảnh.');
                    return;
                }

                selectedUserImages[type] = file;
                previewSelectedUserImage(type, file);
            });
        });
    }

    function init() {
        loadUserAccountStyles();
        ensureAccountMenus();
        ensureSettingsModal();
        ensureComplaintsModal();

        const settingsForm = document.getElementById('userSettingsForm');
        if (settingsForm && settingsForm.dataset.userAccountBound !== 'true') {
            settingsForm.dataset.userAccountBound = 'true';
            settingsForm.addEventListener('submit', handleSettingsSubmit);
        }

        const formDoiMatKhau = document.getElementById('formDoiMatKhau');
        if (formDoiMatKhau && formDoiMatKhau.dataset.userAccountBound !== 'true') {
            formDoiMatKhau.dataset.userAccountBound = 'true';
            formDoiMatKhau.addEventListener('submit', doiMatKhauNguoiDung);
            formDoiMatKhau.addEventListener('input', function (event) {
                const oNhap = event.target.closest('input');
                if (oNhap) {
                    oNhap.classList.remove('is-invalid');
                    oNhap.removeAttribute('aria-invalid');
                }
                hienThiThongBaoDoiMatKhau('');
            });
        }

        bindSettingsImageInputs();
        document.addEventListener('click', handleDocumentClick);
        taiThongTinTaiKhoan();
        loadNotificationsWidget();
    }

    window.SunlensUserAccount = {
        refresh: taiThongTinTaiKhoan,
        openSettingsModal,
        openComplaintsModal,
        closeComplaintsModal,
        loadMyComplaints,
        renderMyComplaints,
        formatComplaintProducts,
        getComplaintStatusBadge,
        openComplaintDetail,
        logout: logoutUser,
    };

    ready(init);
})();
