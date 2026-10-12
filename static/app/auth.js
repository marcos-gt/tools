document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-password-toggle]').forEach(button => {
        button.addEventListener('click', () => {
            const input = document.getElementById(button.dataset.passwordToggle);
            const visible = input.type === 'password';
            input.type = visible ? 'text' : 'password';
            button.textContent = visible ? 'Ocultar' : 'Mostrar';
            button.setAttribute('aria-pressed', String(visible));
            button.setAttribute('aria-label', visible ? 'Ocultar senha' : 'Mostrar senha');
        });
    });
    document.querySelectorAll('.auth-form').forEach(form => {
        form.addEventListener('submit', () => {
            const button = form.querySelector('button[type=submit]');
            if (!button) return;
            button.dataset.defaultHtml = button.innerHTML;
            button.disabled = true;
            button.textContent = form.dataset.submitLabel || 'Aguarde…';
        });
    });
});
window.addEventListener('pageshow', () => {
    document.querySelectorAll('.auth-form button[type=submit]').forEach(button => {
        button.disabled = false;
        if (button.dataset.defaultHtml) button.innerHTML = button.dataset.defaultHtml;
    });
});
