import { authFetch } from './api.js';

export async function initAuthUI() {
    const authContainer = document.getElementById('auth-buttons');
    if (!authContainer) return;

    if (!localStorage.getItem('access_token')) {
        renderLoginButton(authContainer);
        return;
    }

    try {
        const response = await authFetch('/api/auth/favorites/');

        if (response.status === 401) {
            renderLoginButton(authContainer);
        } else {
            renderLogoutButton(authContainer);
        }
    } catch (error) {
        console.error("Ошибка проверки токена:", error);
        renderLogoutButton(authContainer);
    }
}

window.addEventListener('auth:logout', () => {
    const authContainer = document.getElementById('auth-buttons');
    if (authContainer) renderLoginButton(authContainer);
    location.reload();
});

function renderLoginButton(container) {
    container.innerHTML = `<a href="/auth/" class="auth-btn">Войти</a>`;
}

function renderLogoutButton(container) {
    container.innerHTML = `
        <a href="/profile/" class="auth-btn" style="margin-right: 10px;">Профиль</a>
        <button id="logout-btn" class="auth-btn logout">Выйти</button>
    `;
    document.getElementById('logout-btn').addEventListener('click', () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.reload();
    });
}