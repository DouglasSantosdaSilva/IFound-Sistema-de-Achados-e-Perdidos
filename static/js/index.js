document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('cardsGrid');
    const searchInput = document.getElementById('heroSearchInput');
    const searchStatus = document.getElementById('heroSearchStatus');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const loadMoreStatus = document.getElementById('loadMoreStatus');
    const searchForm = document.getElementById('heroSearchForm');

    if (!grid || !searchInput || !searchStatus || !loadMoreBtn || !loadMoreStatus) {
        return;
    }

    const pageState = window.ifoundPageState || {};
    const initialQuery = (pageState.initialQuery || searchInput.value || '').trim();
    let nextPage = pageState.nextPage ?? null;
    let debounceTimer = null;

    function showLoading(target, message) {
        target.textContent = message;
    }

    function clearStatus(target) {
        target.textContent = '';
    }

    function renderItemCard(item) {
        const card = document.createElement('article');
        card.className = 'item-card';

        // Image wrapper
        const imageWrapper = document.createElement('div');
        imageWrapper.className = 'item-card-image-wrapper';

        if (item.imagem) {
            const img = document.createElement('img');
            img.src = item.imagem;
            img.alt = item.titulo;
            img.className = 'item-card-image';
            imageWrapper.appendChild(img);
        } else {
            const placeholder = document.createElement('div');
            placeholder.className = 'item-card-image-placeholder';
            placeholder.innerHTML = '<i class="bi bi-image"></i><span>Sem imagem</span>';
            imageWrapper.appendChild(placeholder);
        }

        // Status badge
        const statusDiv = document.createElement('div');
        statusDiv.className = 'item-card-status';
        const statusBadge = document.createElement('span');
        const statusClass = item.status_key === 'perdi' ? 'status-perdi' : 
                           item.status_key === 'achei' ? 'status-achei' : 'status-analise';
        statusBadge.className = `status-badge ${statusClass}`;
        statusBadge.textContent = item.status;
        statusDiv.appendChild(statusBadge);
        imageWrapper.appendChild(statusDiv);

        card.appendChild(imageWrapper);

        // Content wrapper
        const content = document.createElement('div');
        content.className = 'item-card-content';

        // Title
        const title = document.createElement('h3');
        title.className = 'item-card-title';
        title.textContent = item.titulo;
        content.appendChild(title);

        // Location
        if (item.local) {
            const localDiv = document.createElement('div');
            localDiv.className = 'item-card-meta';
            localDiv.innerHTML = `<i class="bi bi-geo-alt-fill"></i><span>${item.local}</span>`;
            content.appendChild(localDiv);
        }

        // Date
        if (item.data) {
            const dateDiv = document.createElement('div');
            dateDiv.className = 'item-card-meta';
            dateDiv.innerHTML = `<i class="bi bi-calendar3"></i><span>${item.data}</span>`;
            content.appendChild(dateDiv);
        }

        // Button
        const button = document.createElement('a');
        button.href = item.url_detalhe || '#';
        button.className = 'item-card-button';
        button.innerHTML = '<span>Detalhar</span><i class="bi bi-arrow-right"></i>';
        content.appendChild(button);

        card.appendChild(content);
        return card;
    }

    function renderItems(items) {
        grid.innerHTML = '';

        if (!items.length) {
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.innerHTML = `
                <div class="empty-state-icon">😔</div>
                <h3>Nenhum item encontrado</h3>
                <p>Tente pesquisar novamente ou navegue pela página.</p>
            `;
            grid.appendChild(emptyState);
            return;
        }

        items.forEach((item) => {
            grid.appendChild(renderItemCard(item));
        });
    }

    function updateLoadMore(hasNextPage, message) {
        if (!hasNextPage) {
            loadMoreBtn.style.display = 'none';
            loadMoreStatus.textContent = message || 'Você já visualizou todos os itens.';
            return;
        }

        loadMoreBtn.style.display = 'inline-flex';
        loadMoreStatus.textContent = message || 'Mais itens disponíveis.';
    }

    function getItemRequestUrl(params) {
        const url = new URL(window.location.origin + window.location.pathname);
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                url.searchParams.set(key, value);
            }
        });
        return url.toString();
    }

    function makeFetchRequest(url) {
        return fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || '',
            }
        }).then((response) => {
            if (!response.ok) {
                throw new Error('Request failed');
            }
            return response.json();
        });
    }

    async function searchItems() {
        const query = searchInput.value.trim();
        showLoading(searchStatus, 'Carregando itens...');

        try {
            const url = getItemRequestUrl({ q: query, ajax: 1 });
            const data = await makeFetchRequest(url);

            if (!data.items || !data.items.length) {
                renderItems([]);
                updateLoadMore(false, 'Nenhum item encontrado.');
                clearStatus(searchStatus);
                return;
            }

            renderItems(data.items);
            clearStatus(searchStatus);
            nextPage = data.next_page || null;
            updateLoadMore(Boolean(data.has_next_page), data.has_next_page ? 'Mais itens disponíveis.' : 'Você já visualizou todos os itens.');
        } catch (error) {
            renderItems([]);
            loadMoreBtn.style.display = 'none';
            searchStatus.textContent = 'Não foi possível carregar os itens. Tente novamente.';
            loadMoreStatus.textContent = 'Não foi possível carregar os itens. Tente novamente.';
        }
    }

    async function loadMoreItems() {
        if (!nextPage) {
            updateLoadMore(false, 'Você já visualizou todos os itens.');
            return;
        }

        loadMoreBtn.disabled = true;
        showLoading(loadMoreStatus, 'Carregando itens...');

        try {
            const query = searchInput.value.trim();
            const url = getItemRequestUrl({ q: query, page: nextPage, ajax: 1 });
            const data = await makeFetchRequest(url);

            if (data.items && data.items.length) {
                const items = data.items;
                items.forEach((item) => grid.appendChild(renderItemCard(item)));
                nextPage = data.next_page || null;
                updateLoadMore(Boolean(data.has_next_page), data.has_next_page ? 'Mais itens disponíveis.' : 'Você já visualizou todos os itens.');
            } else {
                updateLoadMore(false, 'Você já visualizou todos os itens.');
            }
        } catch (error) {
            loadMoreStatus.textContent = 'Não foi possível carregar os itens. Tente novamente.';
        } finally {
            loadMoreBtn.disabled = false;
            clearStatus(loadMoreStatus);
        }
    }

    // Event listeners
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            searchItems();
        }, 400);
    });

    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        searchItems();
    });

    loadMoreBtn.addEventListener('click', loadMoreItems);

    if (initialQuery) {
        searchInput.value = initialQuery;
        searchItems();
    }
});

        }

        loadMoreBtn.style.display = 'inline-flex';
        loadMoreStatus.textContent = message || 'Mais itens disponíveis.';
    }

    function getItemRequestUrl(params) {
        const url = new URL(window.location.origin + window.location.pathname);
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                url.searchParams.set(key, value);
            }
        });
        return url.toString();
    }

    function makeFetchRequest(url) {
        return fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || '',
            }
        }).then((response) => {
            if (!response.ok) {
                throw new Error('Request failed');
            }
            return response.json();
        });
    }

    async function searchItems() {
        const query = searchInput.value.trim();
        showLoading(searchStatus, 'Carregando itens...');

        try {
            const url = getItemRequestUrl({ q: query, ajax: 1 });
            const data = await makeFetchRequest(url);

            if (!data.items || !data.items.length) {
                renderItems([]);
                updateLoadMore(false, 'Nenhum item encontrado.');
                clearStatus(searchStatus);
                return;
            }

            renderItems(data.items);
            clearStatus(searchStatus);
            nextPage = data.next_page || null;
            updateLoadMore(Boolean(data.has_next_page), data.has_next_page ? 'Mais itens disponíveis.' : 'Você já visualizou todos os itens.');
        } catch (error) {
            renderItems([]);
            loadMoreBtn.style.display = 'none';
            searchStatus.textContent = 'Não foi possível carregar os itens. Tente novamente.';
            loadMoreStatus.textContent = 'Não foi possível carregar os itens. Tente novamente.';
        }
    }

    async function loadMoreItems() {
        if (!nextPage) {
            updateLoadMore(false, 'Você já visualizou todos os itens.');
            return;
        }

        loadMoreBtn.disabled = true;
        showLoading(loadMoreStatus, 'Carregando itens...');

        try {
            const query = searchInput.value.trim();
            const url = getItemRequestUrl({ q: query, page: nextPage, ajax: 1 });
            const data = await makeFetchRequest(url);

            if (data.items && data.items.length) {
                const items = data.items;
                items.forEach((item) => grid.appendChild(renderItemCard(item)));
                nextPage = data.next_page || null;
                updateLoadMore(Boolean(data.has_next_page), data.has_next_page ? 'Mais itens disponíveis.' : 'Você já visualizou todos os itens.');
            } else {
                updateLoadMore(false, 'Você já visualizou todos os itens.');
            }
        } catch (error) {
            loadMoreStatus.textContent = 'Não foi possível carregar os itens. Tente novamente.';
        } finally {
            loadMoreBtn.disabled = false;
            clearStatus(loadMoreStatus);
        }
    }

    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            searchItems();
        }, 400);
    });

    loadMoreBtn.addEventListener('click', loadMoreItems);

    if (initialQuery) {
        searchInput.value = initialQuery;
        searchItems();
    }
});
