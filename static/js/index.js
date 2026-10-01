document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('cardsGrid');
    const searchInput = document.getElementById('searchInput');
    const searchStatus = document.getElementById('searchStatus');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const loadMoreStatus = document.getElementById('loadMoreStatus');

    if (!grid || !searchInput || !loadMoreBtn || !loadMoreStatus) {
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

        const imageWrap = document.createElement('div');
        imageWrap.className = 'item-image-wrap';

        if (item.imagem) {
            const img = document.createElement('img');
            img.src = item.imagem;
            img.alt = item.nome;
            img.className = 'item-image';
            imageWrap.appendChild(img);
        } else {
            const placeholder = document.createElement('div');
            placeholder.className = 'item-image placeholder-image';
            placeholder.textContent = 'imagem do item';
            imageWrap.appendChild(placeholder);
        }

        const body = document.createElement('div');
        body.className = 'item-body';

        const title = document.createElement('h3');
        title.textContent = item.nome;

        if (item.local) {
            const local = document.createElement('p');
            local.className = 'meta-item';
            local.innerHTML = `<strong>Local:</strong> ${item.local}`;
            body.appendChild(local);
        }

        if (item.data_registro) {
            const data = document.createElement('p');
            data.className = 'meta-item';
            data.innerHTML = `<strong>Data:</strong> ${item.data_registro}`;
            body.appendChild(data);
        }

        const link = document.createElement('a');
        link.href = item.url_detalhe || '#';
        link.className = 'btn btn-primary';
        link.textContent = 'Detalhar';

        body.appendChild(title);
        body.appendChild(link);

        card.appendChild(imageWrap);
        card.appendChild(body);
        return card;
    }

    function renderItems(items) {
        grid.innerHTML = '';

        if (!items.length) {
            grid.innerHTML = `
                <div class="empty-state">
                    <span class="empty-state-icon">🔎</span>
                    <p>Nenhum item encontrado.</p>
                </div>
            `;
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
