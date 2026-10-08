document.addEventListener('DOMContentLoaded', () => {
    const requestButton = document.getElementById('requestItemButton');
    const claimForm = document.getElementById('claimForm');
    const fotoInput = document.getElementById('fotoComprovante');
    const claimLabel = document.querySelector('.claim-form-label');
    const selectedFileName = document.getElementById('selectedFileName');

    function getCsrfHeaders(extraHeaders = {}) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
        return {
            ...extraHeaders,
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
        };
    }

    function showToast({ title, message, type = 'info' }) {
        const toastContainer = document.getElementById('toast-container') || document.getElementById('toastContainer');
        if (!toastContainer) {
            return;
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-header">
                <div class="toast-icon ${type}">
                    <i class="bi ${type === 'success' ? 'bi-check-circle-fill' : type === 'error' ? 'bi-x-circle-fill' : type === 'warning' ? 'bi-exclamation-triangle-fill' : 'bi-info-circle-fill'}"></i>
                </div>
                <div class="toast-text">
                    <strong>${title}</strong>
                    <span>${message}</span>
                </div>
                <button type="button" class="toast-close" aria-label="Fechar notificação">&times;</button>
            </div>
        `;

        const closeButton = toast.querySelector('.toast-close');
        closeButton?.addEventListener('click', () => {
            toast.classList.add('toast-closing');
            setTimeout(() => toast.remove(), 220);
        });

        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('toast-closing');
            setTimeout(() => toast.remove(), 220);
        }, 3400);
    }

    if (requestButton) {
        requestButton.addEventListener('click', async () => {
            const itemId = requestButton.dataset.itemId;
            if (!itemId) {
                return;
            }

            try {
                const response = await fetch(`/item/${itemId}/verificar-solicitacao/`, {
                    method: 'GET',
                    headers: getCsrfHeaders(),
                });
                const data = await response.json();

                if (data.exists) {
                    showToast({
                        title: 'Aviso',
                        message: data.message || 'Você já possui uma solicitação para este item.',
                        type: 'warning',
                    });
                    if (data.redirect_url) {
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 700);
                    }
                    return;
                }

                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                }
            } catch (error) {
                showToast({
                    title: 'Erro',
                    message: 'Não foi possível enviar a solicitação.',
                    type: 'error',
                });
            }
        });
    }

    if (!claimForm || !fotoInput) {
        return;
    }

    function updateClaimLabelWithFile(file) {
        const fileText = file && file.name ? file.name : 'Enviar foto de comprovação';
        if (selectedFileName) {
            selectedFileName.textContent = fileText;
        }

        if (claimLabel) {
            claimLabel.innerHTML = `
                <i class="bi bi-check-circle"></i>
                <span id="selectedFileName">${fileText}</span>
            `;
        }

        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (event) => {
                const preview = document.getElementById('claimImagePreview');
                if (!preview) {
                    const wrapper = document.createElement('div');
                    wrapper.className = 'claim-image-preview';
                    wrapper.id = 'claimImagePreview';
                    const img = document.createElement('img');
                    img.src = event.target.result;
                    img.alt = 'Prévia do comprovante';
                    wrapper.appendChild(img);
                    claimForm.insertBefore(wrapper, claimForm.querySelector('.claim-form-actions'));
                    return;
                }
                preview.querySelector('img').src = event.target.result;
            };
            reader.readAsDataURL(file);
        }
    }

    fotoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) {
            return;
        }

        if (!file.type.startsWith('image/')) {
            showToast({
                title: 'Erro',
                message: 'Selecione um arquivo de imagem válido.',
                type: 'error',
            });
            fotoInput.value = '';
            updateClaimLabelWithFile(null);
            return;
        }

        updateClaimLabelWithFile(file);
    });

    claimForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const file = fotoInput.files[0];
        if (!file) {
            showToast({
                title: 'Erro',
                message: 'Envie um comprovante para continuar.',
                type: 'error',
            });
            return;
        }

        const formData = new FormData(claimForm);

        try {
            const response = await fetch(claimForm.action || window.location.href, {
                method: 'POST',
                headers: getCsrfHeaders(),
                body: formData,
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                showToast({
                    title: 'Erro',
                    message: data.message || 'Não foi possível enviar a solicitação.',
                    type: 'error',
                });
                return;
            }

            showToast({
                title: 'Sucesso',
                message: data.message || 'Solicitação enviada com sucesso!',
                type: 'success',
            });

            if (data.redirect_url) {
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 900);
            }
        } catch (error) {
            showToast({
                title: 'Erro',
                message: 'Não foi possível enviar a solicitação.',
                type: 'error',
            });
        }
    });
});
