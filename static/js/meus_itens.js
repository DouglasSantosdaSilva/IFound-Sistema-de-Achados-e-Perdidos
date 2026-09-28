document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('itens-table-body');

    if (!tbody) {
        return;
    }

    const statusClassMap = {
        'Perdido': 'perdido',
        'Encontrado': 'encontrado',
        'Em análise': 'analise'
    };

    function getCookie(name) {
        const cookies = document.cookie ? document.cookie.split('; ') : [];
        for (const cookie of cookies) {
            const [key, value] = cookie.split('=');
            if (key === name) {
                return decodeURIComponent(value);
            }
        }
        return '';
    }

    function getCsrfHeaders() {
        const token = getCookie('csrftoken');
        return {
            'X-CSRFToken': token,
            'X-Requested-With': 'XMLHttpRequest'
        };
    }

    function renderizarItens() {
        tbody.innerHTML = '';

        const dados = Array.isArray(window.itens) ? window.itens : [];

        dados.forEach((item) => {
            const row = document.createElement('tr');
            const status = item.status || 'Em análise';
            const statusClass = statusClassMap[status] || 'analise';

            row.innerHTML = `
                <td>${item.id || '#'}</td>
                <td>${item.titulo || ''}</td>
                <td>${item.data || ''}</td>
                <td>${item.detalhes || ''}</td>
                <td>
                    <span class="status-badge status-${statusClass}">${status}</span>
                </td>
            `;

            tbody.appendChild(row);
        });
    }

    renderizarItens();

    if (window.fetch) {
        const csrfHeader = getCsrfHeaders();
        if (!csrfHeader['X-CSRFToken']) {
            return;
        }
    }
});
