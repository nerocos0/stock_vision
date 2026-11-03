import { initAuthUI } from './auth.js';

const token = localStorage.getItem('access_token');

if (!token) {
    window.location.href = '/auth/';
}

async function loadProfileData() {
    try {
        const response = await fetch('/api/auth/profile/', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
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

const btnShowPassword = document.getElementById('btn-show-password');
const btnCancelPassword = document.getElementById('btn-cancel-password');
const passwordFormContainer = document.getElementById('password-form-container');

btnShowPassword.addEventListener('click', () => {
    passwordFormContainer.style.display = 'block';
    btnShowPassword.style.display = 'none';
});

btnCancelPassword.addEventListener('click', () => {
    passwordFormContainer.style.display = 'none';
    btnShowPassword.style.display = 'block';
    document.getElementById('change-password-form').reset();
    document.getElementById('error-message').style.display = 'none';
});

const form = document.getElementById('change-password-form');
const errorMsg = document.getElementById('error-message');

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorMsg.style.display = 'none';

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

        alert('Пароль успешно изменен!');
        btnCancelPassword.click();
        
    } catch (error) {
        errorMsg.textContent = error.message;
        errorMsg.style.display = 'block';
    }
});

initAuthUI();