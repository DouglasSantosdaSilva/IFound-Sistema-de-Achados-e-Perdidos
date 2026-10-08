document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('claimForm');
    const fileInput = document.getElementById('fotoComprovante');
    const fileName = document.getElementById('selectedFileName');
    const toastContainer = document.getElementById('toast-container');
    if (!form || !fileInput) return;

    function showToast(message, type = 'info') {
        if (!toastContainer) return;
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        const content = document.createElement('div');
        content.className = 'toast-header';
        const text = document.createElement('div');
        text.className = 'toast-text';
        const heading = document.createElement('strong');
        heading.textContent = type === 'success' ? 'Sucesso' : type === 'warning' ? 'Aviso' : 'Erro';
        const detail = document.createElement('span');
        detail.textContent = message;
        text.append(heading, detail);
        content.appendChild(text);
        toast.appendChild(content);
        toastContainer.appendChild(toast);
        window.setTimeout(() => toast.remove(), 4000);
    }

    fileInput.addEventListener('change', () => {
        const file = fileInput.files?.[0];
        if (!file) {
            fileName.textContent = 'Escolher foto de comprovação';
            return;
        }

        const extension = file.name.split('.').pop().toLowerCase();
        if (!['jpg', 'jpeg', 'png', 'webp'].includes(extension)) {
            showToast('Selecione uma imagem JPG, JPEG, PNG ou WEBP.', 'error');
            fileInput.value = '';
            fileName.textContent = 'Escolher foto de comprovação';
            return;
        }
        fileName.textContent = file.name;
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const file = fileInput.files?.[0];
        if (!file) {
            showToast('Selecione uma foto de comprovação antes de continuar.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('foto_comprovante', file);
        const submitButton = form.querySelector('[type="submit"]');
        if (submitButton) submitButton.disabled = true;

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: window.getCsrfHeaders(),
                body: formData,
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                if (data.exists && data.redirect_url) {
                    showToast(data.message || 'Você já possui uma solicitação para este item.', 'warning');
                    window.setTimeout(() => { window.location.href = data.redirect_url; }, 800);
                    return;
                }
                throw new Error(data.message || 'Não foi possível enviar sua solicitação.');
            }

            showToast(data.message || 'Solicitação enviada com sucesso!', 'success');
            if (data.redirect_url) {
                window.setTimeout(() => { window.location.href = data.redirect_url; }, 800);
            }
        } catch (error) {
            showToast(error.message || 'Erro no servidor ao enviar a solicitação.', 'error');
        } finally {
            if (submitButton) submitButton.disabled = false;
        }
    });
});
