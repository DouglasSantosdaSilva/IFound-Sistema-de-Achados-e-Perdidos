document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('itensTableBody');
    const table = document.getElementById('itemsTable');
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const dateFilter = document.getElementById('dateFilter');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const tableLoading = document.getElementById('tableLoading');
    const emptyState = document.getElementById('emptyState');
    const errorState = document.getElementById('errorState');
    const retryBtn = document.getElementById('retryItemsBtn');
    const paginationControls = document.getElementById('paginationControls');
    const paginationInfo = document.getElementById('paginationInfo');
    const modal = document.getElementById('deleteModal');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    const toastContainer = document.getElementById('toastContainer');

    if (!tbody) {
        return;
    }

    const summaryMap = {
        total: document.getElementById('totalItemsCount'),
        perdido: document.getElementById('lostItemsCount'),
        encontrado: document.getElementById('foundItemsCount'),
        'em-analise': document.getElementById('reviewItemsCount')
    };

    const statusLabels = {
        perdido: 'Perdido',
        encontrado: 'Encontrado',
        'em-analise': 'Em análise'
    };

    const statusConfig = {
        perdido: { className: 'status-perdido', icon: 'bi-exclamation-triangle' },
        encontrado: { className: 'status-encontrado', icon: 'bi-check-circle' },
        'em-analise': { className: 'status-analise', icon: 'bi-hourglass-split' }
    };

    let debounceTimer = null;

    function setLoadingState() {
        if (tableLoading) tableLoading.hidden = false;
        if (table) table.hidden = true;
        if (emptyState) emptyState.hidden = true;
        if (errorState) errorState.hidden = true;
    }

    function setSuccessState() {
        if (tableLoading) tableLoading.hidden = true;
        if (table) table.hidden = false;
        if (emptyState) emptyState.hidden = true;
        if (errorState) errorState.hidden = true;
    }

    function setEmptyState() {
        if (tableLoading) tableLoading.hidden = true;
        if (table) table.hidden = true;
        if (emptyState) emptyState.hidden = false;
        if (errorState) errorState.hidden = true;
    }

    function setErrorState() {
        if (tableLoading) tableLoading.hidden = true;
        if (table) table.hidden = true;
        if (emptyState) emptyState.hidden = true;
        if (errorState) errorState.hidden = false;
    }

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

    function showToast({ title, message, type = 'info' }) {
        if (!toastContainer) return;

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

    function openModal(itemId) {
        if (!modal) return;
        window.itensState.deleteId = itemId;
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
    }

    function closeModal() {
        if (!modal) return;
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
        window.itensState.deleteId = null;
    }

    function renderBadge(status) {
        const normalizedStatus = status === 'Perdido' ? 'perdido' : status === 'Encontrado' ? 'encontrado' : 'em-analise';
        const config = statusConfig[normalizedStatus] || statusConfig['em-analise'];
        const label = statusLabels[normalizedStatus] || status;

        return `
            <span class="status-badge ${config.className}">
                <i class="bi ${config.icon}"></i>
                ${label}
            </span>
        `;
    }

    function renderTable(items) {
        tbody.innerHTML = '';

        if (!Array.isArray(items) || !items.length) {
            setEmptyState();
            return;
        }

        setSuccessState();

        items.forEach((item) => {
            const row = document.createElement('tr');
            row.className = 'data-row';
            row.dataset.id = item.id;

            const statusText = item.status || 'Em análise';
            const detailText = item.detalhes || '—';

            row.innerHTML = `
                <td>#${String(item.id).padStart(4, '0')}</td>
                <td>
                    <div class="item-cell">
                        <div class="item-thumb">${item.titulo ? item.titulo.charAt(0).toUpperCase() : 'I'}</div>
                        <span>${item.titulo || 'Item sem nome'}</span>
                    </div>
                </td>
                <td>${item.data || '—'}</td>
                <td>${detailText}</td>
                <td>${renderBadge(statusText)}</td>
                <td>
                    <div class="action-group">
                        <button type="button" class="action-btn view-btn" aria-label="Visualizar item ${item.titulo || item.id}" title="Visualizar">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button type="button" class="action-btn edit-btn" aria-label="Editar item ${item.titulo || item.id}" title="Editar">
                            <i class="bi bi-pencil-square"></i>
                        </button>
                        <button type="button" class="action-btn delete-btn" aria-label="Excluir item ${item.titulo || item.id}" title="Excluir">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            `;

            const deleteBtn = row.querySelector('.delete-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', () => openModal(item.id));
            }

            const editBtn = row.querySelector('.edit-btn');
            if (editBtn) {
                editBtn.addEventListener('click', () => {
                    window.location.href = `/cadastrar/?edit=${item.id}`;
                });
            }

            const viewBtn = row.querySelector('.view-btn');
            if (viewBtn) {
                viewBtn.addEventListener('click', () => {
                    window.location.href = `/item/${item.id}/`;
                });
            }

            tbody.appendChild(row);
        });
    }

    function updateSummary(data) {
        if (!data || !summaryMap.total) return;

        const total = Number(data.total || data.totalItems || 0);
        const perdido = Number(data.perdidos || 0);
        const encontrado = Number(data.encontrados || 0);
        const analise = Number(data.em_analise ?? data.emAnalise ?? 0);

        summaryMap.total.textContent = total;
        summaryMap.perdido.textContent = perdido;
        summaryMap.encontrado.textContent = encontrado;
        summaryMap['em-analise'].textContent = analise;
    }

    function renderPagination(meta) {
        if (!paginationControls || !paginationInfo) return;

        paginationControls.innerHTML = '';
        paginationInfo.textContent = meta ? `Página ${meta.page} de ${meta.totalPages}` : '';

        if (!meta || meta.totalPages <= 1) {
            paginationControls.innerHTML = '';
            return;
        }

        const prev = document.createElement('button');
        prev.type = 'button';
        prev.className = 'page-btn';
        prev.disabled = meta.page <= 1;
        prev.textContent = 'Anterior';
        prev.addEventListener('click', () => {
            if (meta.page > 1) {
                window.itensState.currentPage = meta.page - 1;
                fetchItems();
            }
        });
        paginationControls.appendChild(prev);

        for (let page = 1; page <= meta.totalPages; page += 1) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `page-btn ${page === meta.page ? 'active' : ''}`;
            btn.textContent = page;
            btn.disabled = page === meta.page;
            btn.addEventListener('click', () => {
                window.itensState.currentPage = page;
                fetchItems();
            });
            paginationControls.appendChild(btn);
        }

        const next = document.createElement('button');
        next.type = 'button';
        next.className = 'page-btn';
        next.disabled = meta.page >= meta.totalPages;
        next.textContent = 'Próximo';
        next.addEventListener('click', () => {
            if (meta.page < meta.totalPages) {
                window.itensState.currentPage = meta.page + 1;
                fetchItems();
            }
        });
        paginationControls.appendChild(next);
    }

    async function fetchItems() {
        if (window.itensState.loading) return;

        window.itensState.loading = true;
        setLoadingState();

        const params = new URLSearchParams({
            page: String(window.itensState.currentPage),
            q: searchInput ? searchInput.value.trim() : '',
            status: statusFilter ? statusFilter.value : 'todos',
            data: dateFilter ? dateFilter.value : ''
        });

        try {
            const url = `${window.location.origin}${window.location.pathname}?${params.toString()}`;
            const response = await fetch(url, {
                headers: {
                    ...getCsrfHeaders(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error('Erro ao carregar itens');
            }

            const data = await response.json();

            if (!data || data.success === false) {
                throw new Error(data?.message || 'Não foi possível carregar seus itens.');
            }

            const items = Array.isArray(data.items) ? data.items : [];
            const summary = data.stats || data.summary || {};
            const pagination = data.pagination || null;

            renderTable(items);
            updateSummary(summary);
            renderPagination(pagination);

            if (!items.length) {
                setEmptyState();
                return;
            }

            setSuccessState();
        } catch (error) {
            setErrorState();
            showToast({
                title: 'Erro',
                message: 'Não foi possível carregar seus itens.',
                type: 'error'
            });
        } finally {
            window.itensState.loading = false;
            if (tableLoading) tableLoading.hidden = true;
        }
    }

    async function deleteItem(itemId) {
        const url = window.location.href.split('?')[0];

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: getCsrfHeaders({
                    'Content-Type': 'application/json'
                }),
                body: JSON.stringify({
                    action: 'delete_item',
                    item_id: itemId
                })
            });

            if (!response.ok) {
                throw new Error('Erro ao excluir item');
            }

            const data = await response.json();
            if (data.success) {
                showToast({
                    title: 'Sucesso',
                    message: 'Item excluído com sucesso.',
                    type: 'success'
                });
                closeModal();
                window.itensState.currentPage = 1;
                fetchItems();
            } else {
                throw new Error(data.message || 'Não foi possível excluir o item.');
            }
        } catch (error) {
            showToast({
                title: 'Erro',
                message: 'Não foi possível excluir o item.',
                type: 'error'
            });
        }
    }

    function applyFilters() {
        window.itensState.currentPage = 1;
        fetchItems();
    }

    searchInput?.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => applyFilters(), 350);
    });

    statusFilter?.addEventListener('change', applyFilters);
    dateFilter?.addEventListener('change', applyFilters);

    clearFiltersBtn?.addEventListener('click', () => {
        if (searchInput) searchInput.value = '';
        if (statusFilter) statusFilter.value = 'todos';
        if (dateFilter) dateFilter.value = '';
        window.itensState.currentPage = 1;
        showToast({ title: 'Info', message: 'Filtros limpos.', type: 'info' });
        fetchItems();
    });

    retryBtn?.addEventListener('click', () => {
        setLoadingState();
        fetchItems();
    });

    modal?.addEventListener('click', (event) => {
        const closeAction = event.target.dataset.close;
        if (closeAction === 'true') {
            closeModal();
        }
    });

    confirmDeleteBtn?.addEventListener('click', () => {
        if (window.itensState.deleteId) {
            deleteItem(window.itensState.deleteId);
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal && modal.classList.contains('is-open')) {
            closeModal();
        }
    });

    fetchItems();
});
