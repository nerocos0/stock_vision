import { showToast } from './utils.js';

const form = document.getElementById('reset-password-form');
const errorMsg = document.getElementById('error-message');

// Достаем uid и token из URL
const urlParams = new URLSearchParams(window.location.search);
const uid = urlParams.get('uid');
const token = urlParams.get('token');

// Если в URL нет uid или token - ссылка битая
if (!uid || !token) {
    showToast('Неверная ссылка для сброса пароля', 'error');
    form.style.display = 'none'; // Скрываем форму
} else {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        errorMsg.style.display = 'none';

        const newPassword = document.getElementById('new_password').value;
        const newPassword2 = document.getElementById('new_password2').value;

        try {
            const response = await fetch('/api/auth/reset-password/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    new_password: newPassword,
                    new_password2: newPassword2,
                    uid: uid,
                    token: token
                })
            });

            const data = await response.json();

            if (!response.ok) {
                const errorText = Object.values(data).flat()[0] || 'Ошибка сброса пароля';
                throw new Error(errorText);
            }

            // Успех!
            showToast('Пароль успешно изменен! Теперь вы можете войти.', 'success');
            
            // Перенаправляем на логин через 2 секунды
            setTimeout(() => {
                window.location.href = '/auth/';
            }, 2000);

        } catch (error) {
            errorMsg.textContent = error.message;
            errorMsg.style.display = 'block';
            showToast(error.message, 'error');
        }
    });
}