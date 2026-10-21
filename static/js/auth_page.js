import { loginUser } from './api.js';


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
        errorMsg.textContent = error.message;
        errorMsg.style.display = 'block';
    }
});


formRegister.addEventListener('submit', async (event) => {
    event.preventDefault();
    const errorMsg = document.getElementById('error-register');
    errorMsg.style.display = 'none';

    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    const password2 = document.getElementById('reg-password2').value;

    try {
        const response = await fetch('/api/auth/register/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, password2 })
        });

        const data = await response.json();

        if (!response.ok) {
            const errorText = Object.values(data)[0] || 'Ошибка регистрации';
            throw new Error(errorText);
        }

        const tokens = await loginUser(username, password);
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
        window.location.href = '/';
        
    } catch (error) {
        errorMsg.textContent = error.message;
        errorMsg.style.display = 'block';
    }
});