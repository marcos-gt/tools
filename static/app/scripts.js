

class ChatApp {
    constructor() {
        this.chats = [];
        this.categories = [];
        this.activeTab = 'all';
        this.loading = false;
        console.log("entrei construtor")
        this.init();
    }
    
    async init() {
        console.log("entrei init")
        this.bindEvents();
        await this.loadInitialData();
    }
    
    bindEvents() {
        // Form de adicionar chat
        document.getElementById('chatForm').addEventListener('submit', this.handleAddChat.bind(this));
        
        // Form de adicionar categoria
        document.getElementById('categoryForm').addEventListener('submit', this.handleAddCategory.bind(this));
        
        // Delegação de eventos para deletar categorias
        document.getElementById('categories-container').addEventListener('click', this.handleDeleteCategory.bind(this));
        
        // Delegação de eventos para tabs
        document.getElementById('categoryTabs').addEventListener('click', this.handleTabChange.bind(this));
    }
    
    async loadInitialData() {
        this.setLoading(true);
        console.log("Iniciando o carregamento.")
        try {
        // 1. Buscar conversas da API
        const chatsResp = await fetch('/chat/meus/');
        if (!chatsResp.ok)
            throw new Error('Erro ao carregar conversas');
        const chatsData = await chatsResp.json();

        this.chats = chatsData.chats;
        console.log(this.chats);

        const categoriesResp = await fetch('/categoria/lista');
        if (!categoriesResp.ok)
            throw new Error('Erro ao carregar categorias');
        const categoriesData = await categoriesResp.json();
        console.log(categoriesData);

        // Ajuste conforme sua resposta real da API!
        this.categories = categoriesData.categorias.map(cat => cat.nome);

        this.renderCategories();
        this.renderCategoryTabs();
        this.renderChats();
        this.updateCategoriesSelect();
        console.log("carregado");
    } catch (error) {
        this.showError('Erro ao carregar dados');
        console.error('Erro:', error);
    } finally {
        this.setLoading(false);
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
                category,
                visualizationType,
                timestamp: new Date().toISOString()
            };
            
            this.chats.unshift(newChat);
            this.renderChats();
            this.renderCategoryTabs();
            
            // Limpar formulário
            form.reset();
            
            this.showSuccess('Chat adicionado com sucesso!');
            
        } catch (error) {
            this.showError('Erro ao adicionar chat');
            console.error('Erro:', error);
        } finally {
            this.setButtonLoading(submitBtn, false);
        }
    }
    
    async handleAddCategory(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        const category = formData.get('newCategory').trim().toLowerCase();
        
        if (!category) {
            this.showError('Nome da categoria é obrigatório');
            return;
        }
        
        if (this.categories.includes(category)) {
            this.showError('Esta categoria já existe');
            return;
        }
        
        const submitBtn = form.querySelector('#addCategoryBtn');
        this.setButtonLoading(submitBtn, true);
        
        try {
            // Simular API call
            await this.delay(1000);
            
            this.categories.push(category);
            this.renderCategories();
            this.renderCategoryTabs();
            this.updateCategoriesSelect();
            
            // Limpar formulário
            form.reset();
            
            this.showSuccess('Categoria adicionada com sucesso!');
            
        } catch (error) {
            this.showError('Erro ao adicionar categoria');
            console.error('Erro:', error);
        } finally {
            this.setButtonLoading(submitBtn, false);
        }
    }
    
    async handleDeleteCategory(e) {
        if (!e.target.classList.contains('delete-category')) return;
        
        const category = e.target.dataset.category;
        
        if (!confirm(`Tem certeza que deseja deletar a categoria "${category}"?`)) {
            return;
        }
        
        const button = e.target;
        this.setButtonLoading(button, true);
        
        try {
            // Simular API call
            await this.delay(1000);
            
            this.categories = this.categories.filter(c => c !== category);
            
            // Se a aba ativa foi deletada, voltar para "all"
            if (this.activeTab === category) {
                this.activeTab = 'all';
            }
            
            this.renderCategories();
            this.renderCategoryTabs();
            this.renderChats();
            this.updateCategoriesSelect();
            
            this.showSuccess('Categoria deletada com sucesso!');
            
        } catch (error) {
            this.showError('Erro ao deletar categoria');
            console.error('Erro:', error);
        } finally {
            this.setButtonLoading(button, false);
        }
    }
    
    handleTabChange(e) {
        if (!e.target.classList.contains('nav-link')) return;
        
        const tabId = e.target.getAttribute('data-bs-target');
        if (tabId === '#all') {
            this.activeTab = 'all';
        } else {
            this.activeTab = tabId.replace('#', '');
        }
        
        this.renderChats();
    }
    
    renderChats() {
        const container = document.getElementById('chats-container');
        const emptyState = document.getElementById('empty-state');
        
        const filteredChats = this.activeTab === 'all' 
            ? this.chats 
            : this.chats.filter(chat => chat.category === this.activeTab);
        
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
        const visualizationIcon = chat.visualizationType === 'mapa-mental' 
            ? 'bi-diagram-3' 
            : 'bi-diagram-2';
        
        const visualizationText = chat.visualizationType === 'mapa-mental' 
            ? 'Mapa Mental' 
            : 'Fluxograma';
        
        return `
            <div class="card chat-card mb-3">
                <div class="card-header bg-white border-0 pb-2">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="d-flex gap-2">
                            <span class="badge bg-outline-primary category-badge text-capitalize">${chat.category}</span>
                            <span class="badge bg-secondary visualization-badge d-flex align-items-center gap-1">
                                <i class="bi ${visualizationIcon}"></i>
                                <span>${visualizationText}</span>
                            </span>
                        </div>
                        <small class="text-muted">${this.formatTimestamp(chat.timestamp)}</small>
                    </div>
                </div>
                <div class="card-body pt-0">
                    <p class="card-text">${chat.message}</p>
                </div>
                <div class="card-footer bg-transparent border-0 pt-0">
                    <small class="text-muted">ID: ${chat.id}</small>
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
        
        let tabsHTML = `
            <li class="nav-item" role="presentation">
                <button class="nav-link ${this.activeTab === 'all' ? 'active' : ''}" 
                        data-bs-toggle="pill" data-bs-target="#all" type="button" role="tab">
                    Todos (<span id="all-count">${this.chats.length}</span>)
                </button>
            </li>
        `;
        
        this.categories.forEach(category => {
            const count = this.chats.filter(chat => chat.category === category).length;
            tabsHTML += `
                <li class="nav-item" role="presentation">
                    <button class="nav-link ${this.activeTab === category ? 'active' : ''}" 
                            data-bs-toggle="pill" data-bs-target="#${category}" type="button" role="tab">
                        ${category.charAt(0).toUpperCase() + category.slice(1)} (${count})
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

// Função de logout
function logout() {
    if (confirm('Tem certeza que deseja sair?')) {
        // Limpar dados de autenticação
        localStorage.removeItem('authToken');
        
        // Redirecionar para login (se existir)
        window.location.href = 'login.html';
    }
}

// Inicializar aplicação quando DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
