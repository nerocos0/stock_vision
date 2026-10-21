export function initAuthUI() {
    const authContainer = document.getElementById('auth-buttons');
    if (!authContainer) return;

    const token = localStorage.getItem('access_token');

    if (token) {
        authContainer.innerHTML = `
            <button id="logout-btn" class="auth-btn logout">Выйти</button>
        `;
        
        document.getElementById('logout-btn').addEventListener('click', () => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.reload();
        });
    } else {
        authContainer.innerHTML = `
            <a href="/auth/" class="auth-btn">Войти</a>
        `;
    }
}