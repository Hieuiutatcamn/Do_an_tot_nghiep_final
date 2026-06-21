(function () {
    'use strict';

    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');

    if (!accessToken) return;

    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken || '');
    localStorage.setItem('token_type', 'bearer');

    params.delete('access_token');
    params.delete('refresh_token');
    const cleanQuery = params.toString();
    const cleanUrl = `${window.location.pathname}${cleanQuery ? `?${cleanQuery}` : ''}${window.location.hash}`;
    window.history.replaceState({}, document.title, cleanUrl);

    fetch('http://127.0.0.1:8000/api/v1/auth/me', {
        headers: {
            Authorization: `Bearer ${accessToken}`,
        },
    })
        .then((response) => {
            if (!response.ok) throw new Error('Không lấy được thông tin tài khoản.');
            return response.json();
        })
        .then((me) => {
            localStorage.setItem('user_account', JSON.stringify(me.tai_khoan || me.account || {}));
            localStorage.setItem('user_customer', JSON.stringify(me.khach_hang || me.customer || {}));
            if (window.SunlensUserAccount) {
                window.SunlensUserAccount.refresh();
            }
        })
        .catch(() => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('token_type');
            window.location.href = 'dang_nhap.html#oauth_error=Không%20lấy%20được%20thông%20tin%20tài%20khoản.';
        });
})();
