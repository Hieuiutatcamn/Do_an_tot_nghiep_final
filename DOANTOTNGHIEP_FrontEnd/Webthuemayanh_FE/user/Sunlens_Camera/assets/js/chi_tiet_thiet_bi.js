(function () {
    'use strict';

    const API_BASE_URL = 'http://127.0.0.1:8000/api/v1/devices';
    const API_LIST_URL = `${API_BASE_URL}?page=1&page_size=100`;
    const API_ORIGIN = 'http://127.0.0.1:8000';
    const NO_IMAGE = './assets/images/no-image.png';

    let currentProduct = null;
    let detailMainSwiper = null;
    let detailThumbSwiper = null;
    let availabilityRequestId = 0;

    function ready(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
            return;
        }

        callback();
    }

    function byId(id) {
        return document.getElementById(id);
    }

    function text(id, value) {
        const element = byId(id);
        if (element) element.textContent = value;
    }

    function rentalDateInputs() {
        return {
            start: byId('rental-start'),
            end: byId('rental-end'),
        };
    }

    function selectedRentalDates() {
        const inputs = rentalDateInputs();
        return {
            ngay_nhan: inputs.start ? inputs.start.value : '',
            ngay_tra: inputs.end ? inputs.end.value : '',
        };
    }

    function todayValue() {
        return window.SunlensCart && window.SunlensCart.todayValue
            ? window.SunlensCart.todayValue()
            : new Date().toISOString().slice(0, 10);
    }

    function addDaysValue(value, days) {
        if (window.SunlensCart && window.SunlensCart.addDaysValue) {
            return window.SunlensCart.addDaysValue(value, days);
        }
        const date = new Date(`${value || todayValue()}T00:00:00`);
        if (Number.isNaN(date.getTime())) return todayValue();
        date.setDate(date.getDate() + days);
        return date.toISOString().slice(0, 10);
    }

    function rentalDateErrorMessage(dates) {
        if (window.SunlensCart && window.SunlensCart.dateErrorMessage) {
            return window.SunlensCart.dateErrorMessage(dates);
        }
        const start = new Date(`${dates.ngay_nhan}T00:00:00`);
        const end = new Date(`${dates.ngay_tra}T00:00:00`);
        const today = new Date(`${todayValue()}T00:00:00`);
        if (start < today) return 'Ngày nhận không được nhỏ hơn ngày hiện tại.';
        if (!Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime()) || end <= start) return 'Ngày trả phải lớn hơn ngày nhận.';
        return '';
    }

    function updateDateInputConstraints() {
        const inputs = rentalDateInputs();
        const minStart = todayValue();
        const minEnd = addDaysValue(inputs.start && inputs.start.value ? inputs.start.value : minStart, 1);
        if (inputs.start) inputs.start.min = minStart;
        if (inputs.end) inputs.end.min = minEnd;
    }

    function dateRangeIsValid(dates) {
        return !rentalDateErrorMessage(dates);
    }

    function requestedQuantity() {
        const input = byId('detail-quantity-input');
        return Math.max(1, Number(input && input.value) || 1);
    }

    function availabilityAvailable(data) {
        if (typeof data.available === 'boolean') return data.available;
        if (typeof data.kha_dung === 'boolean') return data.kha_dung;
        if (typeof data.con_hang === 'boolean') return data.con_hang;
        return Number(data.remaining_quantity ?? data.so_luong_kha_dung ?? data.so_luong ?? 0) >= requestedQuantity();
    }

    function availabilityRemaining(data) {
        return Number(data.remaining_quantity ?? data.so_luong_kha_dung ?? data.so_luong ?? 0) || 0;
    }

    function availabilityMessage(data, isAvailable) {
        if (data && data.message) return data.message;
        if (isAvailable) return 'Có thể thuê';
        if (availabilityRemaining(data || {}) <= 0) return 'Thiết bị hiện không còn số lượng khả dụng.';
        return 'Thiết bị này đã được đặt trong khoảng thời gian bạn chọn.';
    }

    function setAvailabilityMessage(message, type) {
        const element = byId('detail-availability-message');
        if (!element) return;

        element.textContent = message || '';
        element.className = `small mb-3 ${type === 'error' ? 'text-danger fw-semibold' : type === 'success' ? 'text-success fw-semibold' : 'text-muted'}`;
    }

    function setActionAvailability(isAvailable) {
        const addToCartButton = byId('add-to-cart-btn');
        const rentNowButton = byId('rent-now-btn');

        if (addToCartButton) {
            addToCartButton.disabled = !isAvailable;
            addToCartButton.classList.toggle('disabled', !isAvailable);
            addToCartButton.setAttribute('aria-disabled', isAvailable ? 'false' : 'true');
        }
        if (rentNowButton) {
            rentNowButton.classList.toggle('disabled', !isAvailable);
            rentNowButton.setAttribute('aria-disabled', isAvailable ? 'false' : 'true');
        }
    }

    function ensureRentalDateDefaults() {
        if (!window.SunlensCart || typeof window.SunlensCart.defaultRentalDates !== 'function') return;

        const inputs = rentalDateInputs();
        const defaults = window.SunlensCart.defaultRentalDates();
        if (inputs.start && !inputs.start.value) {
            inputs.start.value = defaults.ngay_nhan;
        }
        if (inputs.end && !inputs.end.value) {
            inputs.end.value = defaults.ngay_tra;
        }
        updateDateInputConstraints();
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

    function formatVND(value) {
        return `${Number(value || 0).toLocaleString('vi-VN')} VNĐ`;
    }

    function normalizeProducts(data) {
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

    function normalizeImagePath(path) {
        if (!path) return NO_IMAGE;

        const value = String(path).trim();
        if (!value) return NO_IMAGE;
        if (/^(https?:|data:|blob:)/i.test(value)) return value;
        if (value.startsWith('/')) return `${API_ORIGIN}${value}`;
        if (value.startsWith('./') || value.startsWith('../')) return value;
        if (value.startsWith('assets/')) return `./${value}`;
        return value;
    }

    function productImageValues(product) {
        const imageValue = product.hinh_anh
            || product.anh_thiet_bi
            || product.image
            || product.image_url
            || '';

        if (Array.isArray(imageValue)) {
            return imageValue;
        }

        if (typeof imageValue === 'string') {
            const trimmedValue = imageValue.trim();
            if (!trimmedValue) return [];

            if (trimmedValue.startsWith('[')) {
                try {
                    const images = JSON.parse(trimmedValue);
                    if (Array.isArray(images) && images.length) {
                        return images;
                    }
                } catch (error) {
                    console.warn('Không đọc được hinh_anh sản phẩm.', error);
                }
            }

            return [trimmedValue];
        }

        return [];
    }

    function productImages(product) {
        const images = productImageValues(product)
            .map(normalizeImagePath)
            .filter(Boolean);
        const uniqueImages = [...new Set(images)];

        return uniqueImages.length ? uniqueImages : [NO_IMAGE];
    }

    function firstProductImage(product) {
        return productImages(product)[0];
    }

    function destroyGallerySwipers() {
        if (detailMainSwiper) {
            detailMainSwiper.destroy(true, true);
            detailMainSwiper = null;
        }

        if (detailThumbSwiper) {
            detailThumbSwiper.destroy(true, true);
            detailThumbSwiper = null;
        }
    }

    function bindImageFallbacks(scope) {
        scope.querySelectorAll('img').forEach(function (image) {
            image.onerror = function () {
                image.onerror = null;
                image.src = NO_IMAGE;
            };
        });
    }

    function setGalleryVisibility(images) {
        const thumbSwiper = byId('detail-thumb-swiper');
        const prevButton = document.querySelector('.detail-gallery-prev');
        const nextButton = document.querySelector('.detail-gallery-next');
        const hasMultipleImages = images.length > 1;

        if (thumbSwiper) {
            thumbSwiper.style.display = hasMultipleImages ? '' : 'none';
        }

        if (prevButton) {
            prevButton.style.display = hasMultipleImages ? '' : 'none';
        }

        if (nextButton) {
            nextButton.style.display = hasMultipleImages ? '' : 'none';
        }
    }

    function renderImageGallery(images, productName) {
        const mainWrapper = byId('detail-main-wrapper');
        const thumbWrapper = byId('detail-thumb-wrapper');
        const mainSwiperElement = byId('detail-main-swiper');
        const thumbSwiperElement = byId('detail-thumb-swiper');

        if (!mainWrapper || !thumbWrapper || !mainSwiperElement || !thumbSwiperElement) return;

        destroyGallerySwipers();
        setGalleryVisibility(images);

        mainWrapper.innerHTML = images.map(function (imageUrl, index) {
            return `
                <div class="swiper-slide">
                    <img src="${escapeHTML(imageUrl)}" alt="${escapeHTML(productName)} - ảnh ${index + 1}">
                </div>
            `;
        }).join('');

        thumbWrapper.innerHTML = images.map(function (imageUrl, index) {
            return `
                <div class="swiper-slide">
                    <img src="${escapeHTML(imageUrl)}" alt="${escapeHTML(productName)} - thumbnail ${index + 1}">
                </div>
            `;
        }).join('');

        bindImageFallbacks(mainSwiperElement);
        bindImageFallbacks(thumbSwiperElement);

        if (!window.Swiper) {
            thumbSwiperElement.style.display = 'none';
            return;
        }

        detailThumbSwiper = new window.Swiper(thumbSwiperElement, {
            spaceBetween: 10,
            slidesPerView: 3,
            freeMode: true,
            watchSlidesProgress: true,
            breakpoints: {
                576: {
                    slidesPerView: 4,
                },
                992: {
                    slidesPerView: 5,
                },
            },
        });

        detailMainSwiper = new window.Swiper(mainSwiperElement, {
            spaceBetween: 10,
            navigation: {
                nextEl: '.detail-gallery-next',
                prevEl: '.detail-gallery-prev',
            },
            thumbs: {
                swiper: detailThumbSwiper,
            },
        });
    }

    async function readJson(response) {
        if (!response.ok) {
            const error = new Error(`API lỗi ${response.status}`);
            error.status = response.status;
            throw error;
        }

        return response.json();
    }

    async function fetchProductById(id) {
        try {
            return await fetch(`${API_BASE_URL}/${encodeURIComponent(id)}`).then(readJson);
        } catch (error) {
            if (error.status && error.status !== 404) {
                throw error;
            }
        }

        const data = await fetch(API_LIST_URL).then(readJson);
        const products = normalizeProducts(data);
        return products.find(function (product) {
            return String(product.id_thiet_bi) === String(id);
        }) || null;
    }

    async function checkAvailability() {
        if (!currentProduct) return;

        updateDateInputConstraints();
        const productId = currentProduct.id_thiet_bi || currentProduct.id || '';
        const dates = selectedRentalDates();
        if (!productId || !dates.ngay_nhan || !dates.ngay_tra) {
            setActionAvailability(false);
            setAvailabilityMessage('Vui lòng chọn ngày nhận và ngày trả.', 'error');
            return;
        }
        const dateMessage = rentalDateErrorMessage(dates);
        if (dateMessage) {
            setActionAvailability(false);
            setAvailabilityMessage(dateMessage, 'error');
            return;
        }

        const requestId = ++availabilityRequestId;
        setActionAvailability(false);
        setAvailabilityMessage('Đang kiểm tra lịch thuê...', 'info');

        try {
            const params = new URLSearchParams({
                ngay_nhan: dates.ngay_nhan,
                ngay_tra: dates.ngay_tra,
                so_luong: String(requestedQuantity()),
            });
            const data = await fetch(`${API_BASE_URL}/${encodeURIComponent(productId)}/availability?${params.toString()}`)
                .then(readJson);
            console.log('Availability Response', data);
            if (requestId !== availabilityRequestId) return;

            const isAvailable = availabilityAvailable(data);
            const remainingQuantity = availabilityRemaining(data);
            text('detail-quantity', String(remainingQuantity));

            if (!isAvailable) {
                setActionAvailability(false);
                setAvailabilityMessage(availabilityMessage(data, false), 'error');
                return;
            }

            setActionAvailability(true);
            setAvailabilityMessage(availabilityMessage(data, true), 'success');
        } catch (error) {
            if (requestId !== availabilityRequestId) return;
            console.error(error);
            setActionAvailability(false);
            setAvailabilityMessage('Không kiểm tra được lịch thuê. Vui lòng thử lại.', 'error');
        }
    }

    function setLoading() {
        text('detail-title', 'Đang tải sản phẩm...');
        text('detail-page-title', 'Đang tải sản phẩm...');
        text('detail-description', 'Đang tải mô tả thiết bị...');

        renderImageGallery([NO_IMAGE], 'Đang tải sản phẩm');
    }

    function setError(message) {
        text('detail-title', message);
        text('detail-page-title', message);
        text('detail-category', '-');
        text('detail-quantity', '-');
        text('detail-status', '-');
        text('detail-price', '-');
        text('detail-description', message);

        const addToCartButton = byId('add-to-cart-btn');
        const rentNowButton = byId('rent-now-btn');

        if (addToCartButton) addToCartButton.disabled = true;
        if (rentNowButton) {
            rentNowButton.classList.add('disabled');
            rentNowButton.removeAttribute('href');
        }

        renderImageGallery([NO_IMAGE], message);
    }

    function renderProduct(product) {
        currentProduct = product;

        const productId = product.id_thiet_bi || product.id || '';
        const productName = product.ten_thiet_bi || 'Thiết bị chưa đặt tên';
        const productCategory = categoryName(product);
        const productQuantity = product.so_luong ?? 0;
        const productStatus = product.tinh_trang || 'Chưa cập nhật';
        const productPrice = formatVND(product.gia_thue);
        const productDescription = product.mo_ta || 'Chưa có mô tả thiết bị.';
        const images = productImages(product);

        document.title = `${productName} - Sunlens Camera`;
        text('detail-page-title', productName);
        text('detail-title', productName);
        text('detail-id', productId || '-');
        text('detail-category', productCategory);
        text('detail-quantity', productQuantity);
        text('detail-status', productStatus);
        text('detail-price', `${productPrice} / ngày`);
        text('detail-description', productDescription);

        renderImageGallery(images, productName);

        const rentNowButton = byId('rent-now-btn');
        if (rentNowButton) {
            rentNowButton.href = `thanh_toan.html?id=${encodeURIComponent(productId)}`;
            rentNowButton.classList.add('disabled');
        }

        const addToCartButton = byId('add-to-cart-btn');
        if (addToCartButton) {
            addToCartButton.disabled = true;
            addToCartButton.dataset.productId = productId;
        }

        if (window.SunlensCart) {
            window.SunlensCart.setProducts([product]);
        }

        ensureRentalDateDefaults();
        checkAvailability();
    }

    async function addCurrentProductToCart() {
        if (!currentProduct) return;

        if (window.SunlensCart) {
            await window.SunlensCart.addProduct(currentProduct, {
                ...selectedRentalDates(),
                so_luong: requestedQuantity(),
            });
            const addToCartButton = byId('add-to-cart-btn');
            if (addToCartButton) {
                addToCartButton.textContent = 'Đã thêm vào giỏ';
                setTimeout(function () {
                    addToCartButton.textContent = 'Thêm vào giỏ';
                }, 1600);
            }
            return;
        }

        alert('Không thể kết nối API giỏ hàng.');
    }

    ready(function () {
        const params = new URLSearchParams(window.location.search);
        const productId = params.get('id');
        const addToCartButton = byId('add-to-cart-btn');
        const inputs = rentalDateInputs();

        if (addToCartButton && !window.SunlensCart) {
            addToCartButton.addEventListener('click', addCurrentProductToCart);
        }
        updateDateInputConstraints();
        if (inputs.start) {
            inputs.start.addEventListener('change', checkAvailability);
            inputs.start.addEventListener('input', checkAvailability);
        }
        if (inputs.end) {
            inputs.end.addEventListener('change', checkAvailability);
            inputs.end.addEventListener('input', checkAvailability);
        }
        const quantityInput = byId('detail-quantity-input');
        if (quantityInput) {
            quantityInput.addEventListener('change', checkAvailability);
            quantityInput.addEventListener('input', checkAvailability);
        }

        if (!productId) {
            setError('Không tìm thấy id sản phẩm trên URL.');
            return;
        }

        setLoading();

        fetchProductById(productId)
            .then(function (product) {
                if (!product) {
                    setError('Không tìm thấy sản phẩm.');
                    return;
                }

                renderProduct(product);
            })
            .catch(function (error) {
                console.error(error);
                setError('Không thể tải chi tiết sản phẩm.');
            });
    });
})();


