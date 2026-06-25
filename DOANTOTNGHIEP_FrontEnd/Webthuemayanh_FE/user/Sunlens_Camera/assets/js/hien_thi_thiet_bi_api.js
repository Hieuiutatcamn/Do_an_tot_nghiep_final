(function () {
    'use strict';

    const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';
    const API_ORIGIN = 'http://127.0.0.1:8000';
    const DEVICE_API_URL = `${API_BASE_URL}/devices`;
    const CATEGORIES_API_URL = `${API_BASE_URL}/categories?page=1&page_size=100`;
    const API_URL = `${DEVICE_API_URL}?page=1&page_size=100`;
    const FALLBACK_IMAGE = './assets/images/product/1.png';
    const PRICE_MIN = 0;
    const PRICE_MAX = 5000000;
    const PRICE_STEP = 50000;

    const PRODUCT_SLIDER_OPTIONS = {
        responsiveClass: true,
        autoplay: true,
        dots: false,
        responsive: {
            0: {
                nav: true,
                items: 2,
            },
            600: {
                nav: true,
                items: 3,
            },
            1000: {
                nav: true,
                items: 3,
            },
            1200: {
                nav: true,
                items: 4,
            },
        },
    };

    let productRequest = null;
    let catalogRequestController = null;
    let filtersBound = false;

    function ready(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
            return;
        }

        callback();
    }

    function escapeHTML(value) {
        return String(value ?? '').replace(/[&<>"']/g, function (char) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;',
            }[char];
        });
    }

    function normalizeText(value) {
        return String(value ?? '')
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/đ/g, 'd')
            .replace(/Đ/g, 'D')
            .toLowerCase()
            .trim();
    }

    function formatCurrency(value) {
        const amount = Number(value || 0);
        return `${amount.toLocaleString('vi-VN')} VNĐ`;
    }

    function formatVND(value) {
        return formatCurrency(value);
    }

    function normalizeProducts(data) {
        if (Array.isArray(data)) return data;
        if (data && Array.isArray(data.danh_sach)) return data.danh_sach;
        if (data && Array.isArray(data.items)) return data.items;
        return [];
    }

    function normalizeCategories(data) {
        if (Array.isArray(data)) return data;
        if (data && Array.isArray(data.danh_sach)) return data.danh_sach;
        if (data && Array.isArray(data.items)) return data.items;
        return [];
    }

    function categoryName(product) {
        return product.ten_danh_muc
            || (product.danh_muc && product.danh_muc.ten_danh_muc)
            || (product.category && product.category.ten_danh_muc)
            || 'Chưa phân loại';
    }

    function statusBadgeClass(status) {
        const key = statusKey(status);
        if (key === 'ready') return 'status-ready';
        if (key === 'rented') return 'status-rented';
        return 'status-unknown';
    }

    function statusKey(status) {
        const normalizedStatus = normalizeText(status).replace(/\s+/g, ' ');

        if (
            normalizedStatus === 'san sang'
            || normalizedStatus.includes('san sang')
            || normalizedStatus.includes('available')
            || normalizedStatus.includes('ready')
        ) {
            return 'ready';
        }

        if (
            normalizedStatus === 'dang thue'
            || normalizedStatus.includes('dang thue')
            || normalizedStatus.includes('dang duoc thue')
            || normalizedStatus.includes('rented')
        ) {
            return 'rented';
        }

        return '';
    }

    function displayStatus(status) {
        const key = statusKey(status);
        if (key === 'ready') return 'Sẵn sàng';
        if (key === 'rented') return 'Đang thuê';
        return String(status || 'Chưa cập nhật').trim();
    }

    function statusBadge(status) {
        return `<span class="status-badge ${statusBadgeClass(status)}">${escapeHTML(displayStatus(status))}</span>`;
    }

    function normalizeImagePath(path) {
        if (!path) return FALLBACK_IMAGE;

        const value = String(path).trim();
        if (!value) return FALLBACK_IMAGE;
        if (/^(https?:|data:|blob:)/i.test(value)) return value;
        if (value.startsWith('/')) return `${API_ORIGIN}${value}`;
        if (/^(uploads|static)\//i.test(value)) return `${API_ORIGIN}/${value}`;
        if (value.startsWith('./') || value.startsWith('../')) return value;
        if (value.startsWith('assets/')) return `./${value}`;
        return value;
    }

    function firstProductImage(product) {
        const imageValue = product.hinh_anh
            || product.anh_thiet_bi
            || product.image
            || product.image_url
            || '';

        if (Array.isArray(imageValue)) {
            return normalizeImagePath(imageValue[0]);
        }

        if (typeof imageValue === 'string') {
            const trimmedValue = imageValue.trim();

            if (trimmedValue.startsWith('[')) {
                try {
                    const images = JSON.parse(trimmedValue);
                    if (Array.isArray(images) && images.length) {
                        return normalizeImagePath(images[0]);
                    }
                } catch (error) {
                    console.warn('Không đọc được hinh_anh sản phẩm.', error);
                }
            }

            return normalizeImagePath(trimmedValue);
        }

        return FALLBACK_IMAGE;
    }

    function detailUrl(product) {
        const id = productId(product);
        return id
            ? `chi_tiet_thiet_bi.html?id=${encodeURIComponent(id)}`
            : 'chi_tiet_thiet_bi.html';
    }

    function productId(product) {
        return product.id_thiet_bi || product.Id_thiet_bi || product.id || '';
    }

    function layDanhSachThietBiTuApi() {
        if (!productRequest) {
            productRequest = fetch(API_URL)
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error('Không thể tải danh sách sản phẩm');
                    }
                    return response.json();
                })
                .then(normalizeProducts);
        }

        return productRequest;
    }

    function catalogCard(product) {
        const name = escapeHTML(product.ten_thiet_bi || 'Thiết bị chưa đặt tên');
        const category = escapeHTML(categoryName(product));
        const hasAvailabilityQuantity = product.so_luong_kha_dung !== undefined && product.so_luong_kha_dung !== null;
        const quantity = escapeHTML(hasAvailabilityQuantity ? product.so_luong_kha_dung : (product.so_luong ?? 0));
        const quantityLabel = hasAvailabilityQuantity ? 'Số lượng khả dụng' : 'Số lượng còn lại';
        const image = escapeHTML(firstProductImage(product));
        const url = escapeHTML(detailUrl(product));
        const id = escapeHTML(productId(product));

        return `
            <div class="col">
                <div class="card h-100">
                    <img src="${image}" class="card-img-top" alt="${name}">

                    <div class="card-body d-flex flex-column">
                        <span class="badge bg-primary align-self-start mb-2">${category}</span>
                        <h5>${name}</h5>

                        <p class="mb-1 text-muted">${quantityLabel}: ${quantity}</p>
                        <p class="mb-2">
                            ${statusBadge(product.tinh_trang)}
                        </p>

                        <p class="mt-auto text-danger fw-bold">
                            ${formatCurrency(product.gia_thue)} / ngày
                        </p>

                        <div class="d-flex justify-content-between">
                            <a href="${url}" class="btn btn-outline-primary">
                                Chi tiết
                            </a>
                            <a href="#" class="btn btn-primary add-to-cart" data-product-id="${id}">
                                Thêm vào giỏ
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    function homeProductCard(product, isSliderCard) {
        const name = escapeHTML(product.ten_thiet_bi || 'Thiết bị chưa đặt tên');
        const category = escapeHTML(categoryName(product));
        const hasAvailabilityQuantity = product.so_luong_kha_dung !== undefined && product.so_luong_kha_dung !== null;
        const quantity = escapeHTML(hasAvailabilityQuantity ? product.so_luong_kha_dung : (product.so_luong ?? 0));
        const quantityLabel = hasAvailabilityQuantity ? 'Khả dụng' : 'Còn';
        const image = escapeHTML(firstProductImage(product));
        const url = escapeHTML(detailUrl(product));
        const id = escapeHTML(productId(product));
        const cardClass = isSliderCard
            ? 'card product-card mx-2 mb-3 h-100'
            : 'card product-card h-100';

        return `
            <div class="${cardClass}">
                <a href="${url}">
                    <img src="${image}" class="card-img-top image-first" alt="${name}">
                    <img src="${image}" class="card-img-top image-second" alt="${name}">
                </a>
                <div class="card-body pt-0">
                    <div class="icons">
                        <a href="#" data-bs-toggle="tooltip" data-bs-placement="top" title="Yêu thích">
                            <i class="bi bi-heart"></i>
                        </a>
                    </div>
                    <span class="discount-badge">${category}</span>
                </div>
                <div class="product-price px-3 pb-2">
                    <h5 class="card-title">
                        <a href="${url}">${name}</a>
                    </h5>
                    <div class="mb-2 d-flex flex-wrap gap-1">
                        ${statusBadge(product.tinh_trang)}
                        <span class="badge bg-light text-dark">${quantityLabel}: ${quantity}</span>
                    </div>
                    <div class="d-block">
                        <span class="sell-price">${formatCurrency(product.gia_thue)} / ngày</span>
                    </div>
                </div>
                <div class="product-card-actions px-2 mb-2">
                    <div class="d-flex gap-2">
                        <a href="${url}" class="btn btn-primary">Chi tiết</a>
                        <a href="#" class="btn btn-secondary add-to-cart" data-product-id="${id}">Thêm vào giỏ</a>
                    </div>
                </div>
            </div>
        `;
    }

    function wrappedHomeProductCard(product) {
        return `<div class="col">${homeProductCard(product, false)}</div>`;
    }

    function initTooltips(scope) {
        if (!window.bootstrap || !window.bootstrap.Tooltip) return;

        scope.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (element) {
            window.bootstrap.Tooltip.getOrCreateInstance(element);
        });
    }

    function setCatalogLoading() {
        const danhSachThietBi = document.getElementById('product-list');
        if (!danhSachThietBi) return;

        danhSachThietBi.innerHTML = '<div class="col"><p class="text-muted mb-0">Đang tải sản phẩm...</p></div>';
    }

    function showCatalogMessage(message, className) {
        const danhSachThietBi = document.getElementById('product-list');
        if (!danhSachThietBi) return;

        danhSachThietBi.innerHTML = `<div class="col"><p class="${escapeHTML(className || 'text-muted')} mb-0">${escapeHTML(message)}</p></div>`;
    }

    function hienThiThietBi(products) {
        const danhSachThietBi = document.getElementById('product-list');
        if (!danhSachThietBi) return;

        if (!products.length) {
            showCatalogMessage('Không tìm thấy thiết bị phù hợp.', 'text-muted');
            return;
        }

        danhSachThietBi.innerHTML = products.map(catalogCard).join('');
        if (window.SunlensCart) {
            window.SunlensCart.setProducts(products);
            window.SunlensCart.bindAddToCartButtons(danhSachThietBi);
        }
    }

    function hienThiDanhSachThietBi(products) {
        hienThiThietBi(products);
    }

    function getSearchInputs() {
        return Array.from(document.querySelectorAll('[data-device-search]'));
    }

    function getSearchValue() {
        const inputs = getSearchInputs();
        const activeSearch = inputs.find(function (input) {
            return input === document.activeElement && input.value.trim();
        });
        const filledSearch = activeSearch || inputs.find(function (input) {
            return input.value.trim();
        });

        return filledSearch ? filledSearch.value.trim() : '';
    }

    function setSearchValue(value, sourceInput) {
        getSearchInputs().forEach(function (input) {
            if (input !== sourceInput) {
                input.value = value;
            }
        });
    }

    function getPriceRangeValues() {
        const priceRange = document.getElementById('priceRange');
        if (priceRange && priceRange.noUiSlider) {
            const values = priceRange.noUiSlider.get();
            return {
                minPrice: Math.round(Number(values[0] || PRICE_MIN)),
                maxPrice: Math.round(Number(values[1] || PRICE_MAX)),
            };
        }

        return {
            minPrice: PRICE_MIN,
            maxPrice: PRICE_MAX,
        };
    }

    function getDateInputValue(id) {
        const input = document.getElementById(id);
        return input ? input.value : '';
    }

    function hasCompleteRentalDateFilter(filters) {
        return Boolean(filters.ngayNhan && filters.ngayTra);
    }

    function hasPartialRentalDateFilter(filters) {
        return Boolean(filters.ngayNhan || filters.ngayTra) && !hasCompleteRentalDateFilter(filters);
    }

    function isValidRentalDateFilter(filters) {
        if (!hasCompleteRentalDateFilter(filters)) return true;
        return new Date(filters.ngayTra).getTime() > new Date(filters.ngayNhan).getTime();
    }

    function setAvailabilityFilterMessage(message, className) {
        const messageElement = document.getElementById('availabilityFilterMessage');
        if (!messageElement) return;

        messageElement.className = `small mt-2 ${className || ''}`.trim();
        messageElement.textContent = message || '';
    }

    function getFilters() {
        const priceRange = getPriceRangeValues();
        const categories = Array.from(document.querySelectorAll('[data-filter-category]:checked'))
            .map(function (input) {
                return input.value.trim();
            })
            .filter(Boolean);
        const statuses = Array.from(document.querySelectorAll('[data-filter-status]:checked'))
            .map(function (input) {
                return input.value.trim();
            })
            .filter(Boolean);
        const sortSelect = document.getElementById('productSort');

        return {
            search: getSearchValue(),
            categories: categories,
            statuses: statuses,
            minPrice: priceRange.minPrice,
            maxPrice: priceRange.maxPrice,
            sort: sortSelect ? sortSelect.value : '',
            ngayNhan: getDateInputValue('filterNgayNhan'),
            ngayTra: getDateInputValue('filterNgayTra'),
        };
    }

    function buildQueryParams(filters, includeRentalDates) {
        const params = new URLSearchParams();
        params.set('page', '1');
        params.set('page_size', '100');

        if (filters.search) {
            params.set('search', filters.search);
        }

        if (filters.categories.length === 1) {
            params.set('category', filters.categories[0]);
        } else if (filters.categories.length > 1) {
            params.set('categories', filters.categories.join(','));
        }

        if (filters.statuses.length === 1) {
            params.set('status', filters.statuses[0]);
        } else if (filters.statuses.length > 1) {
            params.set('statuses', filters.statuses.join(','));
        }

        if (Number.isFinite(filters.minPrice)) {
            params.set('min_price', String(filters.minPrice));
        }

        if (Number.isFinite(filters.maxPrice)) {
            params.set('max_price', String(filters.maxPrice));
        }

        if (filters.sort) {
            params.set('sort', filters.sort);
        }

        if (includeRentalDates) {
            params.set('ngay_nhan', filters.ngayNhan);
            params.set('ngay_tra', filters.ngayTra);
        }

        return params;
    }

    async function taiDanhSachThietBi() {
        const danhSachThietBi = document.getElementById('product-list');
        if (!danhSachThietBi) return [];

        if (catalogRequestController) {
            catalogRequestController.abort();
        }

        catalogRequestController = new AbortController();
        setCatalogLoading();

        try {
            const filters = getFilters();
            const useAvailabilityApi = hasCompleteRentalDateFilter(filters);

            if (hasPartialRentalDateFilter(filters)) {
                setAvailabilityFilterMessage('Chọn đủ ngày nhận và ngày trả để kiểm tra thiết bị trống.', 'text-warning');
            } else if (useAvailabilityApi && !isValidRentalDateFilter(filters)) {
                setAvailabilityFilterMessage('Ngày trả phải lớn hơn ngày nhận.', 'text-danger');
                showCatalogMessage('Ngày trả phải lớn hơn ngày nhận.', 'text-danger');
                return [];
            } else if (useAvailabilityApi) {
                setAvailabilityFilterMessage('Đang lọc thiết bị còn trống theo lịch thuê.', 'text-muted');
            } else {
                setAvailabilityFilterMessage('', '');
            }

            const endpoint = useAvailabilityApi ? `${DEVICE_API_URL}/available` : DEVICE_API_URL;
            const queryParams = buildQueryParams(filters, useAvailabilityApi);
            const response = await fetch(`${endpoint}?${queryParams.toString()}`, {
                signal: catalogRequestController.signal,
            });

            if (!response.ok) {
                throw new Error('Không thể tải danh sách sản phẩm');
            }

            const products = normalizeProducts(await response.json());
            hienThiThietBi(products);
            if (useAvailabilityApi) {
                setAvailabilityFilterMessage(
                    `Đang hiển thị ${products.length} thiết bị còn trống trong khoảng ngày đã chọn.`,
                    products.length ? 'text-success' : 'text-muted',
                );
            }
            return products;
        } catch (error) {
            if (error.name === 'AbortError') return [];

            console.error(error);
            showCatalogMessage('Không thể tải danh sách sản phẩm.', 'text-danger');
            return [];
        }
    }

    function debounce(callback, delay) {
        let timer = null;

        return function debouncedCallback() {
            const context = this;
            const args = arguments;
            window.clearTimeout(timer);
            timer = window.setTimeout(function () {
                callback.apply(context, args);
            }, delay);
        };
    }

    function updatePriceRangeLabel(values) {
        const label = document.getElementById('priceRangeValue');
        if (!label) return;

        const minValue = Math.round(Number(values[0] || PRICE_MIN));
        const maxValue = Math.round(Number(values[1] || PRICE_MAX));
        label.textContent = `${formatCurrency(minValue)} - ${formatCurrency(maxValue)}`;
    }

    function initPriceFilter() {
        const priceRange = document.getElementById('priceRange');
        if (!priceRange || !window.noUiSlider) return;

        if (!priceRange.noUiSlider) {
            window.noUiSlider.create(priceRange, {
                start: [PRICE_MIN, PRICE_MAX],
                connect: true,
                step: PRICE_STEP,
                range: {
                    min: PRICE_MIN,
                    max: PRICE_MAX,
                },
                format: {
                    to: function (value) {
                        return Math.round(value);
                    },
                    from: function (value) {
                        return Number(value);
                    },
                },
            });
        }

        priceRange.noUiSlider.on('update', updatePriceRangeLabel);
        priceRange.noUiSlider.on('change', taiDanhSachThietBi);
        updatePriceRangeLabel(priceRange.noUiSlider.get());
    }

    function refreshNiceSelect(selectElement) {
        if (!selectElement || !window.jQuery || !window.jQuery.fn || !window.jQuery.fn.niceSelect) return;
        window.jQuery(selectElement).niceSelect('update');
    }

    function clearFilters() {
        setSearchValue('', null);

        document.querySelectorAll('[data-filter-category], [data-filter-status]').forEach(function (input) {
            input.checked = false;
        });

        const sortSelect = document.getElementById('productSort');
        if (sortSelect) {
            sortSelect.value = '';
            refreshNiceSelect(sortSelect);
        }

        const priceRange = document.getElementById('priceRange');
        if (priceRange && priceRange.noUiSlider) {
            priceRange.noUiSlider.set([PRICE_MIN, PRICE_MAX]);
        }

        ['filterNgayNhan', 'filterNgayTra'].forEach(function (id) {
            const input = document.getElementById(id);
            if (input) {
                input.value = '';
            }
        });
        setAvailabilityFilterMessage('', '');

        taiDanhSachThietBi();
    }

    function bindFilterEvents() {
        if (filtersBound) return;
        filtersBound = true;

        const debouncedLoadDevices = debounce(taiDanhSachThietBi, 300);

        getSearchInputs().forEach(function (input) {
            input.addEventListener('input', function () {
                setSearchValue(input.value, input);
                debouncedLoadDevices();
            });

            const form = input.closest('form');
            if (form && !form.dataset.deviceSearchBound) {
                form.dataset.deviceSearchBound = 'true';
                form.addEventListener('submit', function (event) {
                    event.preventDefault();
                    taiDanhSachThietBi();
                });
            }
        });

        document.addEventListener('change', function (event) {
            const target = event.target;
            if (!target.matches('[data-filter-category], [data-filter-status], #productSort')) return;
            taiDanhSachThietBi();
        });

        const clearButton = document.getElementById('clearFiltersBtn');
        if (clearButton) {
            clearButton.addEventListener('click', clearFilters);
        }

        const availabilityButton = document.getElementById('btnCheckAvailability');
        if (availabilityButton) {
            availabilityButton.addEventListener('click', taiDanhSachThietBi);
        }
    }

    function categoryFilterValue(category) {
        return category.id_danh_muc
            || category.Id_danh_muc
            || category.id
            || category.ten_danh_muc
            || category.name
            || '';
    }

    function categoryFilterLabel(category) {
        return category.ten_danh_muc || category.name || 'Danh mục';
    }

    function renderCategoryFilters(categories) {
        const container = document.getElementById('categoryFilterList');
        if (!container || !categories.length) return;

        container.innerHTML = categories.map(function (category) {
            const value = escapeHTML(categoryFilterValue(category));
            const label = escapeHTML(categoryFilterLabel(category));

            return `
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${value}" data-filter-category>
                    <label class="form-check-label">${label}</label>
                </div>
            `;
        }).join('');
    }

    async function loadCategories() {
        const container = document.getElementById('categoryFilterList');
        if (!container) return;

        try {
            const response = await fetch(CATEGORIES_API_URL);
            if (!response.ok) return;

            const categories = normalizeCategories(await response.json());
            renderCategoryFilters(categories);
        } catch (error) {
            console.warn('Không thể tải danh mục sản phẩm, dùng danh mục mặc định.', error);
        }
    }

    function prepareHomeGrid() {
        const tabContent = document.getElementById('pills-tabContent');
        if (!tabContent) return null;

        tabContent.innerHTML = `
            <div class="tab-pane fade show active" id="pills-lastest" role="tabpanel" aria-labelledby="pills-lastest-tab" tabindex="0">
                <div class="product">
                    <div id="home-product-grid" class="row g-4 row-cols-xl-4 row-cols-lg-3 row-cols-md-3 row-cols-sm-2 row-cols-2 mt-1">
                        <div class="col">
                            <p class="text-muted mb-0">Đang tải sản phẩm...</p>
                        </div>
                    </div>
                </div>
                <div class="text-center mt-5">
                    <a href="thiet_bi.html" class="btn btn-primary">Xem tất cả</a>
                </div>
            </div>
        `;

        return document.getElementById('home-product-grid');
    }

    function renderHomeGrid(products) {
        const grid = document.getElementById('home-product-grid') || prepareHomeGrid();
        if (!grid) return;

        if (!products.length) {
            grid.innerHTML = '<div class="col"><p class="text-muted mb-0">Chưa có sản phẩm.</p></div>';
            return;
        }

        grid.innerHTML = products.map(wrappedHomeProductCard).join('');
        initTooltips(grid);
        if (window.SunlensCart) {
            window.SunlensCart.setProducts(products);
            window.SunlensCart.bindAddToCartButtons(grid);
        }
    }

    function productSliderElement() {
        return document.querySelector('.product-slider');
    }

    function destroyProductSlider(slider) {
        if (!window.jQuery || !window.jQuery.fn || !window.jQuery.fn.owlCarousel) return;

        const sliderElement = window.jQuery(slider);
        if (sliderElement.hasClass('owl-loaded')) {
            sliderElement.trigger('destroy.owl.carousel');
            sliderElement.removeClass('owl-loaded owl-hidden owl-drag');
        }
    }

    function initProductSlider(slider) {
        if (!window.jQuery || !window.jQuery.fn || !window.jQuery.fn.owlCarousel) return;

        window.jQuery(slider).owlCarousel(PRODUCT_SLIDER_OPTIONS);
    }

    function setProductSliderContent(html, shouldInit) {
        const slider = productSliderElement();
        if (!slider) return;

        destroyProductSlider(slider);
        slider.innerHTML = html;

        if (shouldInit) {
            initProductSlider(slider);
            initTooltips(slider);
        }
    }

    function prepareProductSlider() {
        if (!productSliderElement()) return;
        setProductSliderContent('<div class="px-2 text-muted">Đang tải sản phẩm...</div>', false);
    }

    function renderProductSlider(products) {
        if (!productSliderElement()) return;

        if (!products.length) {
            setProductSliderContent('<div class="px-2 text-muted">Chưa có sản phẩm.</div>', false);
            return;
        }

        setProductSliderContent(products.map(function (product) {
            return homeProductCard(product, true);
        }).join(''), true);
        if (window.SunlensCart) {
            window.SunlensCart.setProducts(products);
            window.SunlensCart.bindAddToCartButtons(productSliderElement());
        }
    }

    function showError(error) {
        console.error(error);

        const danhSachThietBi = document.getElementById('product-list');
        if (danhSachThietBi) {
            danhSachThietBi.innerHTML = '<div class="col"><p class="text-danger mb-0">Không thể tải danh sách sản phẩm.</p></div>';
        }

        const homeGrid = document.getElementById('home-product-grid');
        if (homeGrid) {
            homeGrid.innerHTML = '<div class="col"><p class="text-danger mb-0">Không thể tải danh sách sản phẩm.</p></div>';
        }

        if (productSliderElement()) {
            setProductSliderContent('<div class="px-2 text-danger">Không thể tải danh sách sản phẩm.</div>', false);
        }
    }

    window.SunlensDeviceFilters = {
        getFilters: getFilters,
        buildQueryParams: buildQueryParams,
        taiDanhSachThietBi: taiDanhSachThietBi,
        hienThiThietBi: hienThiThietBi,
        debounce: debounce,
        formatCurrency: formatCurrency,
        bindFilterEvents: bindFilterEvents,
        clearFilters: clearFilters,
    };

    ready(function () {
        const hasCatalog = Boolean(document.getElementById('product-list'));
        const hasHomeGrid = Boolean(document.getElementById('pills-tabContent'));
        const hasHomeSlider = Boolean(productSliderElement());

        if (!hasCatalog && !hasHomeGrid && !hasHomeSlider) return;

        if (hasCatalog) {
            setCatalogLoading();
            initPriceFilter();
            bindFilterEvents();
            loadCategories().finally(taiDanhSachThietBi);
        }

        if (hasHomeGrid) {
            prepareHomeGrid();
        }

        if (hasHomeSlider) {
            prepareProductSlider();
        }

        if (hasHomeGrid || hasHomeSlider) {
            layDanhSachThietBiTuApi()
                .then(function (products) {
                    if (window.SunlensCart) {
                        window.SunlensCart.setProducts(products);
                    }
                    renderHomeGrid(products);
                    renderProductSlider(products);
                })
                .catch(showError);
        }
    });
})();
