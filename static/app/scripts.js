class ChatApp {
    constructor() {
        this.chats = [];
        this.categories = [];
        this.activeTab = 'all';
        this.output = '';
        this.init();
    }
    
    async init() {
        this.bindEvents();
        await this.loadInitialData();
    }
    
    bindEvents() {
        document.getElementById('chatForm').addEventListener('submit', this.handleAddChat.bind(this));
        document.getElementById('categoryForm').addEventListener('submit', this.handleAddCategory.bind(this));
        document.getElementById('generatorForm').addEventListener('submit', this.handleGenerate.bind(this));
        document.getElementById('categories-container').addEventListener('click', this.handleDeleteCategory.bind(this));
        document.getElementById('categoryTabs').addEventListener('click', this.handleTabChange.bind(this));
    }
    
    async loadInitialData() {
        this.setLoading(true);
        try {
        const chatsResp = await fetch('/chat/meus/');
        if (!chatsResp.ok)
            throw new Error('Erro ao carregar conversas');
        const chatsData = await chatsResp.json();

        this.chats = chatsData.chats.map(chat => ({
            ...chat,
             category: (chat.category || chat.categoria || "").trim().toUpperCase()
        }));

        const categoriesResp = await fetch('/categoria/lista');
        if (!categoriesResp.ok)
            throw new Error('Erro ao carregar categorias');
        const categoriesData = await categoriesResp.json();

         this.categories = categoriesData.categorias.map(cat => cat.nome.trim().toUpperCase());


        this.renderCategories();
        this.renderCategoryTabs();
        this.renderChats();
        this.updateCategoriesSelect();
         this.updateGeneratorSelect();
    } catch (error) {
        this.showError('Erro ao carregar dados');
        console.error('Erro:', error);
    } finally {
        this.setLoading(false);
    }

    }

    async handleGerarMap() {
    try {
        if (!this.output) {
            console.error('Nenhum output encontrado');
            return;
        }

        console.log('Gerando mapa com conteúdo:', this.output);

        if (window.renderMermaid) {
            await window.renderMermaid('cardmap', this.output);
        } else {
            console.error('Função renderMermaid não disponível');

            const mapElement = document.getElementById('cardmap');
            if (mapElement) {
                mapElement.innerHTML = this.output;
            }
        }

    } catch (error) {
        console.error('Erro ao gerar mapa:', error);
        this.showError('Erro ao renderizar o mapa mental');
    }
    }




    async handleAddChat(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        const message = formData.get('message');
        const category = formData.get('category');
        const visualizationType = formData.get('visualizationType');
        
        if (!message || !category || !visualizationType) {
            this.showError('Todos os campos são obrigatórios');
            return;
        }
        
        const submitBtn = form.querySelector('#submitBtn');
        this.setButtonLoading(submitBtn, true);
        
        try {
            console.log('Adicionando chat:', { message, category, visualizationType });
            // Simular API call
            const response = await fetch('/chat/novo/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin',
        });

        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Erro ao adicionar chat');
        }


            const newChat = {
                id: Date.now().toString(),
                message,
                 category: category.toUpperCase(),
                visualizationType,
                timestamp: new Date().toISOString()
            };
            
            this.chats.unshift(newChat);
            this.renderChats();
            this.renderCategoryTabs();
            
            // Limpar formulário
            form.reset();

            window.location.reload();
            
        } catch (error) {
            this.showError('Erro ao adicionar chat');
            console.error('Erro:', error);
        } finally {
            this.setButtonLoading(submitBtn, false);
        }
    }
    
    async handleAddCategory(e) {
    e.preventDefault();
    console.log('ADICIONANDO CATEGORIA DEBUG inicio');
    
    const form = e.target;
    const formData = new FormData(form);
    
    // ✅ Buscar tanto pelo name quanto pelo ID
    let category = formData.get('newCategory');
    if (!category) {
        // Fallback: buscar pelo ID se não encontrar pelo name
        const input = document.getElementById('newCategoryInput');
        category = input ? input.value : null;
    }
    
    console.log('Categoria encontrada:', category);
    
    if (!category || !category.trim()) {
        this.showError('Nome da categoria é obrigatório');
        return;
    }
    
    category = category.trim().toUpperCase();
    
    if (this.categories.includes(category)) {
        this.showError('Esta categoria já existe');
        return;
    }
    
    const submitBtn = form.querySelector('#addCategoryBtn');
    this.setButtonLoading(submitBtn, true);
    
    console.log('ADICIONANDO CATEGORIA DEBUG:', category);
    
    try {
        // ✅ Usar a URL correta para adicionar categoria
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        const response = await fetch('/categoria/receberCategorias/', {
            method: 'POST',
            body: JSON.stringify({
                nome: category
            }),
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            },
            credentials: 'same-origin',
        });

        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Erro ao adicionar categoria');
        }

        const result = await response.json();
        console.log('Categoria adicionada:', result);

        // Adicionar à lista local
        this.categories.push(category);
        this.renderCategories();
        this.renderCategoryTabs();
        this.updateCategoriesSelect();
        this.updateGeneratorSelect();
        
        // Limpar formulário
        form.reset();
        
        this.showSuccess('Categoria adicionada com sucesso!');
        
    } catch (error) {
        this.showError('Erro ao adicionar categoria: ' + error.message);
        console.error('Erro:', error);
    } finally {
        this.setButtonLoading(submitBtn, false);
    }
}
    async handleInactivateCategory(e) {
    const form = e.target;
    const formData = new FormData(form);
    const category = formData.get('generatorCategory');

    if (!category) {
        this.showError('Selecione uma categoria para inativar');
        return;
    }

    if (!confirm(`Tem certeza que deseja inativar a categoria "${category}"?\n\nTodos os chats desta categoria ficarão ocultos.`)) {
        return;
    }

    const deleteBtn = form.querySelector('#deleteBtn');
    this.setButtonLoading(deleteBtn, true);
    console.log('DELETE DEBUG:');
    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        const response = await fetch('/categoria/inativar/', {
            method: 'POST',
            body: JSON.stringify({
                category: category,
                action: 'inactivate'
            }),
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            },
            credentials: 'same-origin',
        });
        console.log('DELETE passou aqui');
        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Erro ao inativar categoria');
        }

        const result = await response.json();
        console.log(result)
        this.showSuccess(`Categoria "${category}" foi inativada com sucesso!`);

        // Recarregar os dados para refletir as mudanças
        await this.loadInitialData();

        // Limpar o formulário
        form.reset();

    } catch (error) {
        this.showError('Erro ao inativar categoria');
        console.error('Erro:', error);
    } finally {
        this.setButtonLoading(deleteBtn, false);
    }
    }

    async handleGenerate(e) {
    e.preventDefault();
    const isDeleteAction = e.submitter && e.submitter.id === 'deleteBtn';

    if (isDeleteAction) {
        await this.handleInactivateCategory(e);
        return;
    }

    document.getElementById('cardmap').classList.remove('d-none');
    const form = e.target;
    const formData = new FormData(form);
    const category = formData.get('generatorCategory');

    if (!category) {
        this.showError('Selecione uma categoria');
        return;
    }

    const submitBtn = form.querySelector('#generateBtn');
    this.setButtonLoading(submitBtn, true);

    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        const response = await fetch('/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            },
            credentials: 'same-origin',
        });

        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Erro ao gerar conteúdo');
        }

        const result = await response.json();
        this.output = result.output;

        await this.handleGerarMap();
        await this.loadInitialData();

    } catch (error) {
        this.showError('Erro ao gerar conteúdo');
        console.error('Erro:', error);
    } finally {
        this.setButtonLoading(submitBtn, false);
    }
}
    async handleDeleteChats(e) {
    const form = e.target;
    const formData = new FormData(form);
    const category = formData.get('generatorCategory');

    if (!category) {
        this.showError('Selecione uma categoria para inativar');
        return;
    }

    if (!confirm(`Tem certeza que deseja inativar a categoria "${category}"?\n\nTodos os chats desta categoria não aparecerão mais na interface.`)) {
        return;
    }

    const deleteBtn = form.querySelector('#deleteBtn');
    this.setButtonLoading(deleteBtn, true);

    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        const response = await fetch('/chat/inativar/', {
            method: 'POST',
            body: JSON.stringify({
                category: category,
                action: 'inactivate'
            }),
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            },
            credentials: 'same-origin',
        });

        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Erro ao inativar chats');
        }

        const result = await response.json();

        this.showSuccess(`${result.count || 0} chats foram inativados com sucesso!`);

        // Recarregar os dados para refletir as mudanças
        await this.loadInitialData();

        // Limpar o formulário
        form.reset();

    } catch (error) {
        this.showError('Erro ao inativar chats');
        console.error('Erro:', error);
    } finally {
        this.setButtonLoading(deleteBtn, false);
    }
    }

    async handleDeleteCategory(e) {
        if (!e.target.classList.contains('btn-close')) return;
        
        const category = e.target.dataset.category;
        
        if (!confirm(`Tem certeza que deseja deletar a categoria "${category}"?`)) {
            return;
        }
        
        const button = e.target;
        this.setButtonLoading(button, true);
        
        try {
            // Simular API call
            const response = await fetch('/categoria/deletar/', {
                method: 'POST',
                body: JSON.stringify({ category: category }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
            });
            
            this.categories = this.categories.filter(c => c !== category);
            
            // Se a aba ativa foi deletada, voltar para "all"
            if (this.activeTab === category) {
                this.activeTab = 'all';
            }
            
            this.renderCategories();
            this.renderCategoryTabs();
            this.renderChats();
            this.updateCategoriesSelect();
            this.updateGeneratorSelect();
            this.showSuccess('Categoria deletada com sucesso!');
            
        } catch (error) {
            this.showError('Erro ao deletar categoria');
            console.error('Erro:', error);
        } finally {
            this.setButtonLoading(button, false);
        }
    }
    
    handleTabChange(e) {
    e.preventDefault();
    e.stopPropagation(); // Impede que o Bootstrap interfira

    if (!e.target.classList.contains('nav-link')) return;

    // Remove classe active de todas as abas
    const allTabs = document.querySelectorAll('#categoryTabs .nav-link');
    allTabs.forEach(tab => tab.classList.remove('active'));

    // Adiciona active na aba clicada
    e.target.classList.add('active');

    // Pega a categoria do data attribute
    const category = e.target.getAttribute('data-category');

    console.log('🎯 TAB CHANGE DEBUG:');
    console.log('Tab clicada:', e.target.textContent);
    console.log('Categoria:', category);

    this.activeTab = category;
    console.log('Nova aba ativa:', this.activeTab);

    // Renderizar imediatamente
    this.renderChats();
}

    renderChats() {
        const container = document.getElementById('chats-container');
        const emptyState = document.getElementById('empty-state');

        const filteredChats = this.activeTab === 'all'
            ? this.chats
            : this.chats.filter(chat => {
                const chatCategory = (chat.category || '').trim().toUpperCase();
                return chatCategory === this.activeTab;
            });

        if (filteredChats.length === 0) {
            container.classList.add('d-none');
            emptyState.classList.remove('d-none');
            return;
        }

        container.classList.remove('d-none');
        emptyState.classList.add('d-none');

        container.innerHTML = filteredChats.map(chat => this.createChatCard(chat)).join('');
    }
    
    createChatCard(chat) {
        const category = chat.category || 'Sem Categoria';
    const visualizationType = chat.visualizationType || '';
    const visualizationIcon = visualizationType === 'mapa-mental'
        ? 'bi-diagram-3'
        : 'bi-diagram-2';
    const visualizationText = visualizationType === 'mapa-mental'
        ? 'Mapa Mental'
        : 'Fluxograma';
    const timestamp = chat.timestamp ? this.formatTimestamp(chat.timestamp) : '';
    const message = chat.message || '';
    const id = chat.id || '';

        
        return `
        <div class="card chat-card mb-3">
            <div class="card-header bg-white border-0 pb-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex gap-2">
                        <span class="badge bg-outline-primary category-badge text-capitalize">${category}</span>
                        <span class="badge bg-secondary visualization-badge d-flex align-items-center gap-1">
                            <i class="bi ${visualizationIcon}"></i>
                            <span>${visualizationText}</span>
                        </span>
                    </div>
                    <small class="text-muted">${timestamp}</small>
                </div>
            </div>
            <div class="card-body pt-0">
                <p class="card-text">${message}</p>
            </div>
            <div class="card-footer bg-transparent border-0 pt-0">
                <small class="text-muted">ID: ${id}</small>
            </div>
        </div>
    `;


    }
    
    renderCategories() {
        const container = document.getElementById('categories-container');

        if (this.categories.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">Nenhuma categoria criada</p>';
            return;
        }

        container.innerHTML = this.categories.map(category => `
            <span class="badge bg-secondary me-2 mb-2 d-inline-flex align-items-center">
                ${category.charAt(0).toUpperCase() + category.slice(1)}
                <button type="button" class="btn-close btn-close-white ms-2 delete-category" 
                        data-category="${category}"></button>
            </span>
        `).join('');
    }

        renderCategoryTabs() {
        const tabsContainer = document.getElementById('categoryTabs');

        if (!tabsContainer) {
            console.error('Container de tabs não encontrado');
            return;
        }

        let tabsHTML = `
            <li class="nav-item" role="presentation">
                <button class="nav-link ${this.activeTab === 'all' ? 'active' : ''}" 
                        data-category="all" type="button" role="tab">
                    Todos (<span id="all-count">${this.chats.length}</span>)
                </button>
            </li>
        `;

        this.categories.forEach(category => {
            const count = this.chats.filter(chat => {
                const chatCategory = (chat.category || chat.categoria || '').trim().toUpperCase();
                return chatCategory === category.toUpperCase();
            }).length;

            const categoryDisplay = category.charAt(0).toUpperCase() + category.slice(1).toLowerCase();

            tabsHTML += `
                <li class="nav-item" role="presentation">
                    <button class="nav-link ${this.activeTab === category.toUpperCase() ? 'active' : ''}" 
                            data-category="${category.toUpperCase()}" type="button" role="tab">
                        ${categoryDisplay} (${count})
                    </button>
                </li>
            `;
        });

        tabsContainer.innerHTML = tabsHTML;

        }

    updateCategoriesSelect() {
        const select = document.getElementById('category');
        
        select.innerHTML = '<option value="">Selecione uma categoria</option>';
        
        this.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category.charAt(0).toUpperCase() + category.slice(1);
            select.appendChild(option);
        });
    }
    updateGeneratorSelect() {
        const select = document.getElementById('generatorCategory');

        select.innerHTML = '<option value="">Selecione uma categoria</option>';

        this.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category.charAt(0).toUpperCase() + category.slice(1).toLowerCase();
            select.appendChild(option);
        });
    }
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'agora';
        if (minutes < 60) return `${minutes}m atrás`;
        if (hours < 24) return `${hours}h atrás`;
        return `${days}d atrás`;
    }
    
    setLoading(loading) {
        const loadingEl = document.getElementById('loading');
        const chatsContainer = document.getElementById('chats-container');
        const emptyState = document.getElementById('empty-state');
        
        if (loading) {
            loadingEl.classList.remove('d-none');
            chatsContainer.classList.add('d-none');
            emptyState.classList.add('d-none');
        } else {
            loadingEl.classList.add('d-none');
        }
    }
    
    setButtonLoading(button, loading) {
    if (loading) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Carregando...';
    } else {
        button.disabled = false;
        // Restaurar texto original baseado no ID do botão
        if (button.id === 'submitBtn') {
            button.innerHTML = '<i class="bi bi-send me-2"></i>Enviar';
        } else if (button.id === 'addCategoryBtn') {
            button.innerHTML = '<i class="bi bi-plus"></i>';
        } else if (button.id === 'generateBtn') {
            button.innerHTML = '<i class="bi bi-magic me-2"></i>Gerar';
        } else if (button.id === 'deleteBtn') {
            button.innerHTML = '<i class="bi bi-trash me-2"></i>Deletar';
        } else {
            button.innerHTML = '<i class="bi bi-trash"></i>';
        }
    }
    }

    
    showError(message) {
        const toast = document.getElementById('errorToast');
        const messageEl = document.getElementById('errorMessage');
        
        messageEl.textContent = message;
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
    
    showSuccess(message) {
        // Criar toast de sucesso dinamicamente
        const toastContainer = document.querySelector('.toast-container');
        
        const successToast = document.createElement('div');
        successToast.className = 'toast';
        successToast.innerHTML = `
            <div class="toast-header bg-success text-white">
                <i class="bi bi-check-circle me-2"></i>
                <strong class="me-auto">Sucesso</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        `;
        
        toastContainer.appendChild(successToast);
        
        const bsToast = new bootstrap.Toast(successToast);
        bsToast.show();
        
        // Remover toast após ser ocultado
        successToast.addEventListener('hidden.bs.toast', () => {
            successToast.remove();
        });
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

async function logout() {
    if (confirm('Tem certeza que deseja sair?')) {
        try {
            const response = await fetch('/login/logout/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });
            if (response.ok) {
                localStorage.clear();
                sessionStorage.clear();

                window.location.href = '/login/?next=/';
            } else {
                throw new Error('Erro no logout');
            }
        } catch (error) {
            console.error('Erro no logout:', error);
            alert('Erro ao fazer logout. Tente novamente.');
        }
    }
}


document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});