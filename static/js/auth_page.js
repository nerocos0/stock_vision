import { loginUser } from './api.js';
import { showToast } from './utils.js';


const urlParams = new URLSearchParams(window.location.search);
if (urlParams.has('verified')) {
    showToast('Почта успешно подтверждена! Теперь вы можете войти.', 'success');
    window.history.replaceState({}, document.title, "/auth/");
} else if (urlParams.has('error')) {
    showToast('Ссылка подтверждения недействительна или устарела.', 'error');
    window.history.replaceState({}, document.title, "/auth/");
}

const tabLogin = document.getElementById('tab-login');
const tabRegister = document.getElementById('tab-register');
const formLogin = document.getElementById('form-login');
const formRegister = document.getElementById('form-register');

tabLogin.addEventListener('click', () => {
    tabLogin.classList.add('active');
    tabRegister.classList.remove('active');
    formLogin.style.display = 'block';
    formRegister.style.display = 'none';
});

tabRegister.addEventListener('click', () => {
    tabRegister.classList.add('active');
    tabLogin.classList.remove('active');
    formRegister.style.display = 'block';
    formLogin.style.display = 'none';
});

formLogin.addEventListener('submit', async (event) => {
    event.preventDefault();
    const errorMsg = document.getElementById('error-login');
    errorMsg.style.display = 'none';

    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const tokens = await loginUser(username, password);
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
        window.location.href = '/';
    } catch (error) {
        errorMsg.textContent = "Неверный логин или пароль, либо аккаунт не подтвержден. Проверьте почту.";
        errorMsg.style.display = 'block';
        showToast('Ошибка входа. Проверьте данные или подтвердите почту.', 'error');
    }
});

formRegister.addEventListener('submit', async (event) => {
    event.preventDefault();
    const errorMsg = document.getElementById('error-register');
    errorMsg.style.display = 'none';

    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const password2 = document.getElementById('reg-password2').value;

    try {
        const response = await fetch('/api/auth/register/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, password2 })
        });

        const data = await response.json();

        if (!response.ok) {
            const errorText = Object.values(data).flat()[0] || 'Ошибка регистрации';
            throw new Error(errorText);
        }

        showToast('Регистрация успешна! Проверьте почту для подтверждения.', 'success');
        
        tabLogin.click(); 
        formRegister.reset();

    } catch (error) {
        errorMsg.textContent = error.message;
        errorMsg.style.display = 'block';
        showToast(error.message, 'error');
    }
});

// --- Логика восстановления пароля ---
const btnForgot = document.getElementById('btn-forgot-password');
const modalForgot = document.getElementById('forgot-password-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const formForgot = document.getElementById('forgot-password-form');

// Открыть окно
btnForgot.addEventListener('click', (e) => {
    e.preventDefault();
    modalForgot.style.display = 'flex';
});

// Закрыть окно
btnCloseModal.addEventListener('click', () => {
    modalForgot.style.display = 'none';
    formForgot.reset();
});

// Отправка формы
formForgot.addEventListener('submit', async (event) => {
    event.preventDefault();
    const email = document.getElementById('reset-email').value;

    try {
        const response = await fetch('/api/auth/password-reset/', { // Убедись, что URL совпадает
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email })
        });

        const data = await response.json();

        if (!response.ok) {
            // Если пользователь не найден или другая ошибка
            const errorText = Object.values(data).flat()[0] || 'Ошибка';
            throw new Error(errorText);
        }

        // Успех
        showToast('Ссылка для сброса пароля отправлена на почту!', 'success');
        modalForgot.style.display = 'none';
        formForgot.reset();

    } catch (error) {
        showToast(error.message, 'error');
    }
});