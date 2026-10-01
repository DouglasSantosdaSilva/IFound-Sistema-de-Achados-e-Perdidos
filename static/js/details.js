document.addEventListener('DOMContentLoaded', () => {
    const claimForm = document.getElementById('claimForm');
    const fotoInput = document.getElementById('fotoComprovante');
    const claimLabel = document.querySelector('.claim-form-label');

    if (!claimForm || !fotoInput) {
        return;
    }

    /* ========================================
       FILE INPUT HANDLING
       ======================================== */

    fotoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            updateClaimLabelWithFile(file);
        }
    });

    function updateClaimLabelWithFile(file) {
        if (claimLabel) {
            claimLabel.innerHTML = `
                <i class="bi bi-check-circle"></i>
                <div style="text-align: left; font-size: 14px;">
                    <strong>Arquivo selecionado:</strong>
                    <p style="margin: 4px 0 0; font-size: 13px; opacity: 0.8;">${file.name}</p>
                </div>
            `;
        }
    }

    /* ========================================
       FORM SUBMISSION
       ======================================== */

    claimForm.addEventListener('submit', function(e) {
        // Deixar o formulário submeter normalmente (POST)
        // Django irá redirecionar após sucesso
    });
});
