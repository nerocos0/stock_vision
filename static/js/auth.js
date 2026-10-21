export async function initAuthUI() {
    const authContainer = document.getElementById('auth-buttons');
    if (!authContainer) return;

    const token = localStorage.getItem('access_token');

    if (!token) {
        renderLoginButton(authContainer);
        return;
    }

    try {
        const response = await fetch('/api/auth/favorites/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            renderLoginButton(authContainer);
        } else {
            renderLogoutButton(authContainer);
        }
    } catch (error) {
        console.error("Ошибка проверки токена:", error);
        renderLogoutButton(authContainer);
    }
}

function renderLoginButton(container) {
    container.innerHTML = `<a href="/auth/" class="auth-btn">Войти</a>`;
}

function renderLogoutButton(container) {
    container.innerHTML = `<button id="logout-btn" class="auth-btn logout">Выйти</button>`;
    document.getElementById('logout-btn').addEventListener('click', () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.reload();
    });
}