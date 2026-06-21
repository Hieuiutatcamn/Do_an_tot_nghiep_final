// Time Display
function updateTime() {

    const now = new Date();

    const timeString = now.toLocaleTimeString('en-GB', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit'
    });

    const timeDisplay = document.getElementById('timeDisplay');

    if (timeDisplay) {
        timeDisplay.textContent = timeString;
    }
}

updateTime();
setInterval(updateTime, 1000);

// Navbar Scroll Effect
window.addEventListener('scroll', function () {

    const nav = document.querySelector('.modern-nav');

    if (!nav) return;

    if (window.scrollY > 50) {
        nav.classList.add('scrolled');
    } else {
        nav.classList.remove('scrolled');
    }
});

// Cart Count
function updateCartCount() {
    // Giỏ hàng đã chuyển sang API thật; bộ đếm được lấy qua SunlensCart thay cho localStorage.
    if (window.SunlensCart && typeof window.SunlensCart.updateCartCount === 'function') {
        window.SunlensCart.updateCartCount();
        return;
    }

    const count = 0;

    const cartBadge = document.getElementById('cartCount');
    const cartBadgeMobile = document.getElementById('cartCountMobile');

    if (cartBadge) {
        cartBadge.textContent = count;
        cartBadge.style.display = count > 0 ? 'flex' : 'none';
    }

    if (cartBadgeMobile) {
        cartBadgeMobile.textContent = count;
        cartBadgeMobile.style.display = count > 0 ? 'inline' : 'none';
    }
}

document.addEventListener('DOMContentLoaded', function () {

    updateCartCount();
});
