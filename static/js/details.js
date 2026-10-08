function initializeDetailsPage() {
    const button = document.getElementById('requestItemButton');
    const toastContainer = document.getElementById('toast-container');
    if (!button) return;

    function showToast(message, type = 'warning') {
        if (!toastContainer) return;
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        const content = document.createElement('div');
        content.className = 'toast-header';
        const text = document.createElement('div');
        text.className = 'toast-text';
        const heading = document.createElement('strong');
        heading.textContent = type === 'error' ? 'Erro' : 'Aviso';
        const detail = document.createElement('span');
        detail.textContent = message;
        text.append(heading, detail);
        content.appendChild(text);
        toast.appendChild(content);
        toastContainer.appendChild(toast);
        window.setTimeout(() => toast.remove(), 4000);
    }

    button.addEventListener('click', async (event) => {
        event.preventDefault();
        const checkUrl = button.dataset.checkUrl;
        if (!checkUrl) {
            showToast('Não foi possível verificar sua solicitação.', 'error');
            return;
        }

        button.disabled = true;
        try {
            const response = await fetch(checkUrl, {
                method: 'GET',
                headers: window.getCsrfHeaders(),
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Não foi possível verificar sua solicitação.');
            }

            if (data.exists) {
                showToast(data.message || 'Você já possui uma solicitação para este item.');
                if (data.redirect_url) {
                    window.setTimeout(() => { window.location.href = data.redirect_url; }, 800);
                }
                return;
            }

            if (!data.redirect_url) throw new Error('A página de confirmação não foi encontrada.');
            window.location.href = data.redirect_url;
        } catch (error) {
            showToast(error.message || 'Erro ao verificar a solicitação.', 'error');
        } finally {
            button.disabled = false;
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDetailsPage, { once: true });
} else {
    initializeDetailsPage();
}
