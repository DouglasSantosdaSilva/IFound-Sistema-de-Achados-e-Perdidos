const mockItems = [
  { id: 1, nome: 'Carteira', imagem: 'https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=900&q=80' },
  { id: 2, nome: 'Óculos', imagem: 'https://images.unsplash.com/photo-1577803947579-9f6d0d3be6f5?auto=format&fit=crop&w=900&q=80' },
  { id: 3, nome: 'Garrafa', imagem: 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=900&q=80' },
  { id: 4, nome: 'Chaveiro', imagem: 'https://images.unsplash.com/photo-1555529777-2f4f3a5d2a95?auto=format&fit=crop&w=900&q=80' },
  { id: 5, nome: 'Notebook', imagem: 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80' },
  { id: 6, nome: 'Moletom', imagem: 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80' },
  { id: 7, nome: 'Celular', imagem: 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=80' },
  { id: 8, nome: 'Bola', imagem: 'https://images.unsplash.com/photo-1547347298-4074fc3086f0?auto=format&fit=crop&w=900&q=80' },
  { id: 9, nome: 'Livro', imagem: 'https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=900&q=80' },
  { id: 10, nome: 'Mochila', imagem: 'https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=900&q=80' },
  { id: 11, nome: 'Relógio', imagem: 'https://images.unsplash.com/photo-1523170335258-f5ed11844a49?auto=format&fit=crop&w=900&q=80' },
  { id: 12, nome: 'Caneta', imagem: 'https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&w=900&q=80' }
];

const state = {
  visibleCount: 0,
  filteredItems: [...mockItems]
};

const grid = document.getElementById('itemGrid');
const searchInput = document.getElementById('searchInput');
const loadMoreBtn = document.getElementById('loadMoreBtn');

function fakeFetch(data, delay = 350) {
  return new Promise((resolve) => {
    setTimeout(() => resolve(data), delay);
  });
}

function renderCards(items) {
  grid.innerHTML = '';

  items.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'card';

    const imageWrap = document.createElement('div');
    imageWrap.className = 'item-image';

    if (item.imagem) {
      const img = document.createElement('img');
      img.src = item.imagem;
      img.alt = `Imagem de ${item.nome}`;
      img.loading = 'lazy';
      imageWrap.appendChild(img);
    } else {
      imageWrap.textContent = 'imagem do item';
    }

    const title = document.createElement('div');
    title.className = 'item-name';
    title.textContent = item.nome;

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn btn-primary';
    button.textContent = 'Detalhar';

    card.appendChild(imageWrap);
    card.appendChild(title);
    card.appendChild(button);
    grid.appendChild(card);
  });
}

async function loadInitialItems() {
  // Simulação de requisição AJAX inicial com fetch/fakeFetch.
  const response = await fakeFetch(mockItems.slice(0, 3));
  state.filteredItems = [...mockItems];
  state.visibleCount = response.length;
  renderCards(response);
}

async function loadMoreItems() {
  loadMoreBtn.disabled = true;
  loadMoreBtn.textContent = 'Carregando...';

  // Simula uma nova requisição AJAX ao clicar em "Mais Itens".
  const currentVisible = state.visibleCount;
  const nextItems = state.filteredItems.slice(currentVisible, currentVisible + 3);

  const response = await fakeFetch(nextItems);

  const existing = [...grid.children].length;
  const newItems = [...response];

  if (newItems.length > 0) {
    renderCards([...state.filteredItems.slice(0, currentVisible + newItems.length)]);
    state.visibleCount = currentVisible + newItems.length;
  }

  if (state.visibleCount >= state.filteredItems.length) {
    loadMoreBtn.style.display = 'none';
  }

  loadMoreBtn.disabled = false;
  loadMoreBtn.textContent = 'Mais Itens';
}

function handleSearch(event) {
  const query = event.target.value.trim().toLowerCase();

  loadMoreBtn.disabled = true;
  loadMoreBtn.textContent = 'Buscando...';

  // Simulação de busca via AJAX, filtrando no front-end para este exemplo.
  fakeFetch().then(() => {
    const filtered = mockItems.filter((item) => item.nome.toLowerCase().includes(query));
    state.filteredItems = filtered;
    state.visibleCount = Math.min(filtered.length, 3);

    renderCards(filtered.slice(0, state.visibleCount));

    if (filtered.length > 3) {
      loadMoreBtn.style.display = 'inline-flex';
      loadMoreBtn.disabled = false;
      loadMoreBtn.textContent = 'Mais Itens';
    } else {
      loadMoreBtn.style.display = 'none';
    }
  });
}

searchInput.addEventListener('input', handleSearch);
loadMoreBtn.addEventListener('click', loadMoreItems);

loadInitialItems();
