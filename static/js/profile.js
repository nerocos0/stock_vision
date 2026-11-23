import { initAuthUI } from './auth.js';
import { showToast } from './utils.js';

const token = localStorage.getItem('access_token');

if (!token) {
    window.location.href = '/auth/';
}

// ==========================================
// 1. ЗАГРУЗКА ПРОФИЛЯ
// ==========================================
async function loadProfileData() {
    try {
        const response = await fetch('/api/auth/profile/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/auth/';
            return;
        }

        const data = await response.json();
        document.getElementById('profile-username').textContent = data.username;
        document.getElementById('profile-email').textContent = data.email || 'Не указан';
    } catch (error) {
        console.error("Ошибка загрузки профиля:", error);
        document.getElementById('profile-username').textContent = 'Ошибка загрузки';
        document.getElementById('profile-email').textContent = '-';
    }
}

loadProfileData();

// ==========================================
// 2. ОБРАБОТКА URL-ПАРАМЕТРОВ (после смены email)
// ==========================================
const urlParams = new URLSearchParams(window.location.search);

if (urlParams.has('email_changed')) {
    showToast('Email успешно изменён!', 'success');
    window.history.replaceState({}, document.title, '/profile/');
    loadProfileData();
}

if (urlParams.has('email_error')) {
    const error = urlParams.get('email_error');
    if (error === 'invalid') {
        showToast('Ссылка недействительна или устарела', 'error');
    } else if (error === 'expired') {
        showToast('Ссылка истекла (прошло больше 24 часов)', 'error');
    }
    window.history.replaceState({}, document.title, '/profile/');
}

// ==========================================
// 3. УПРАВЛЕНИЕ ФОРМАМИ (ТАБЫ)
// ==========================================
const btnShowPassword = document.getElementById('btn-show-password');
const btnShowEmail = document.getElementById('btn-show-email');
const passwordFormContainer = document.getElementById('password-form-container');
const emailFormContainer = document.getElementById('email-form-container');
const btnCancelPassword = document.getElementById('btn-cancel-password');
const btnCancelEmail = document.getElementById('btn-cancel-email');

// Функция: показать форму пароля, скрыть форму email
function showPasswordForm() {
    passwordFormContainer.style.display = 'block';
    emailFormContainer.style.display = 'none';
    
    // Кнопки: пароль активна, email неактивна
    btnShowPassword.classList.add('btn-active');
    btnShowPassword.classList.remove('btn-inactive');
    btnShowEmail.classList.add('btn-inactive');
    btnShowEmail.classList.remove('btn-active');
}

// Функция: показать форму email, скрыть форму пароля
function showEmailForm() {
    emailFormContainer.style.display = 'block';
    passwordFormContainer.style.display = 'none';
    
    // Кнопки: email активна, пароль неактивна
    btnShowEmail.classList.add('btn-active');
    btnShowEmail.classList.remove('btn-inactive');
    btnShowPassword.classList.add('btn-inactive');
    btnShowPassword.classList.remove('btn-active');
}

// Функция: скрыть обе формы (вернуть в исходное состояние)
function hideAllForms() {
    passwordFormContainer.style.display = 'none';
    emailFormContainer.style.display = 'none';
    
    // Кнопки: обе неактивны (или можно сделать обе активными, как хочешь)
    btnShowPassword.classList.remove('btn-active');
    btnShowEmail.classList.remove('btn-active');
    btnShowPassword.classList.add('btn-inactive');
    btnShowEmail.classList.add('btn-inactive');
}

// Инициализация: обе кнопки неактивны, формы скрыты
hideAllForms();

// Обработчики кнопок
btnShowPassword.addEventListener('click', showPasswordForm);
btnShowEmail.addEventListener('click', showEmailForm);

btnCancelPassword.addEventListener('click', hideAllForms);
btnCancelEmail.addEventListener('click', hideAllForms);

// ==========================================
// 4. СМЕНА ПАРОЛЯ
// ==========================================
const passwordForm = document.getElementById('change-password-form');
const passwordErrorMsg = document.getElementById('error-message');

passwordForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    passwordErrorMsg.style.display = 'none';

    const oldPassword = document.getElementById('old_password').value;
    const newPassword = document.getElementById('new_password').value;
    const newPassword2 = document.getElementById('new_password2').value;

    try {
        const response = await fetch('/api/auth/profile/change-password/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                oldpassword: oldPassword,
                new_password: newPassword,
                new_password2: newPassword2
            })
        });

        const data = await response.json();

        if (!response.ok) {
            const errorText = Object.values(data).flat()[0] || 'Ошибка смены пароля';
            throw new Error(errorText);
        }

        // Обновляем токены
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);

        showToast('Пароль успешно изменен!', 'success');
        passwordForm.reset();
        hideAllForms();
        
    } catch (error) {
        passwordErrorMsg.textContent = error.message;
        passwordErrorMsg.style.display = 'block';
    }
});

// ==========================================
// 5. СМЕНА EMAIL
// ==========================================
const emailForm = document.getElementById('change-email-form');
const emailErrorMsg = document.getElementById('email-error-message');

emailForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    emailErrorMsg.style.display = 'none';

    const newEmail = document.getElementById('new_email').value;
    const password = document.getElementById('email_password').value;

    try {
        const response = await fetch('/api/auth/profile/change-email/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                new_email: newEmail,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            const errorText = Object.values(data).flat()[0] || 'Ошибка смены email';
            throw new Error(errorText);
        }

        showToast('Письмо отправлено! Проверьте новый email и перейдите по ссылке.', 'success');
        emailForm.reset();
        hideAllForms();
        
    } catch (error) {
        emailErrorMsg.textContent = error.message;
        emailErrorMsg.style.display = 'block';
    }
});

// ==========================================
// 6. ИНИЦИАЛИЗАЦИЯ
// ==========================================
initAuthUI();