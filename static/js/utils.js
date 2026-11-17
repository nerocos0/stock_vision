export function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        toast.addEventListener('animationend', () => toast.remove());
    }, 3000);
}

export function toUnixSeconds(t) {
    if (typeof t === 'number') return t;
    if (/^\d+$/.test(t)) return Number(t);
    const s = t.includes('T') ? t : t.replace(' ', 'T');
    const hasZone = /[zZ]$|[+-]\d\d:?\d\d$/.test(s);
    return Math.floor(Date.parse(hasZone ? s : s + 'Z') / 1000);
}