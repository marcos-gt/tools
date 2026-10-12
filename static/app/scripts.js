function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
}
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

        const categoriesResp = await fetch('/categoria/lista/');
        if (!categoriesResp.ok)
            throw new Error('Erro ao carregar categorias');
        const categoriesData = await categoriesResp.json();

         this.categoryRecords = categoriesData.categorias;
         this.categories = categoriesData.categorias.map(cat => cat.nome.trim().toUpperCase());


        this.renderCategories();
        this.renderCategoryTabs();
        this.renderChats();
        this.updateCategoriesSelect();
         this.updateGeneratorSelect();
    } catch (error) {
        this.showError('Erro ao carregar dados');

    } finally {
        this.setLoading(false);
    }

    }

    async handleGerarMap() {
    try {
        if (!this.output) {

            return;
        }

        if (window.renderMermaid) {
            await window.renderMermaid('cardmap', this.output);
        } else {

            const mapElement = document.getElementById('cardmap');
            if (mapElement) {
                mapElement.textContent = this.output;
            }
        }

    } catch (error) {

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

            // Simular API call
            const response = await fetch('/chat/novo/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(),
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

        } finally {
            this.setButtonLoading(submitBtn, false);
        }
    }
    
    async handleAddCategory(e) {
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);
    
    // ✅ Buscar tanto pelo name quanto pelo ID
    let category = formData.get('newCategory');
    if (!category) {
        // Fallback: buscar pelo ID se não encontrar pelo name
        const input = document.getElementById('newCategoryInput');
        category = input ? input.value : null;
    }

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
                'X-CSRFToken': getCsrfToken(),
                'X-CSRFToken': csrfToken,
            },
            credentials: 'same-origin',
        });

        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Erro ao adicionar categoria');
        }

        const result = await response.json();

        // Adicionar à lista local
        await this.loadInitialData();
        this.renderCategories();
        this.renderCategoryTabs();
        this.updateCategoriesSelect();
        this.updateGeneratorSelect();
        
        // Limpar formulário
        form.reset();
        
        this.showSuccess('Categoria adicionada com sucesso!');
        
    } catch (error) {
        this.showError('Erro ao adicionar categoria: ' + error.message);

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
                'X-CSRFToken': getCsrfToken(),
                'X-CSRFToken': csrfToken,
            },
            credentials: 'same-origin',
        });

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
// Obter informações da categoria
    const categorySelect = document.getElementById('generatorCategory');
    const categoryName = categorySelect.options[categorySelect.selectedIndex].text;

    // Obter tipo de visualização se disponível
    const visualizationType = formData.get('visualizationType') || 'mapa-mental';

    const submitBtn = form.querySelector('#generateBtn');
    this.setButtonLoading(submitBtn, true);

    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        const response = await fetch('/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(),
                'X-CSRFToken': csrfToken,
            },
            credentials: 'same-origin',
        });

        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Erro ao gerar conteúdo');
        }

        const result = await response.json();
        if (!result.output || !result.output.trim()) throw new Error('Serviço retornou saída vazia.');
        this.outputId = result.output_id;
        this.output = result.output;

        // Renderizar no card principal também
        await this.handleGerarMap();
        await this.loadInitialData();

        // ✅ Mostrar modal dinâmico
        const chatsCount = this.chats.filter(chat =>
            chat.category && chat.category.toUpperCase() === categoryName.toUpperCase()
        ).length;

        this.showGeneratedModal(categoryName, this.output, {
            chatsUsed: result.total_chats,
            visualizationType: visualizationType,
            generatedAt: new Date().toISOString()
        });

    } catch (error) {
        this.showError(error.message || 'Falha de inferência.');

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
                'X-CSRFToken': getCsrfToken(),
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
            const response = await fetch('/categoria/inativar/', {
                method: 'POST',
                body: JSON.stringify({ category: category }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(),
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



    this.activeTab = category;

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
        const category = escapeHtml(chat.category) || 'Sem Categoria';
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
                <p class="card-text">${escapeHtml(message)}</p>
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
                ${escapeHtml(category.charAt(0).toUpperCase() + category.slice(1))}
                <button type="button" class="btn-close btn-close-white ms-2 delete-category" 
                        data-category="${escapeHtml(category)}"></button>
            </span>
        `).join('');
    }

        renderCategoryTabs() {
        const tabsContainer = document.getElementById('categoryTabs');

        if (!tabsContainer) {

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
                            data-category="${escapeHtml(category.toUpperCase())}" type="button" role="tab">
                        ${escapeHtml(categoryDisplay)} (${count})
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
            option.value = this.categoryRecords.find(c => c.nome.trim().toUpperCase() === category).id;
            option.textContent = category.charAt(0).toUpperCase() + category.slice(1);
            select.appendChild(option);
        });
    }
    updateGeneratorSelect() {
        const select = document.getElementById('generatorCategory');

        select.innerHTML = '<option value="">Selecione uma categoria</option>';

        this.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = this.categoryRecords.find(c => c.nome.trim().toUpperCase() === category).id;
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
            <div class="toast-body">${escapeHtml(message)}</div>
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

createGeneratedModal() {
    // Verificar se já existe um modal
    const existingModal = document.getElementById('generatedContentModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Criar o modal HTML dinamicamente
    const modalHTML = `
        <div class="modal fade" id="generatedContentModal" tabindex="-1" aria-labelledby="generatedContentModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-xl modal-dialog-centered" style="max-width: 80vw; max-height: 80vh;">
                <div class="modal-content" style="height: 80vh;">
                    <div class="modal-header bg-gradient text-white" style="background: linear-gradient(45deg, #667eea, #764ba2);">
                        <h5 class="modal-title d-flex align-items-center" id="generatedContentModalLabel">
                            <i class="bi bi-diagram-3 me-2"></i>
                            Mapa Mental Gerado
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body p-0" style="height: calc(80vh - 120px); overflow: hidden;">
                        <!-- Cabeçalho com informações -->
                        <div class="p-3 border-bottom bg-light">
                            <div class="row align-items-center">
                                <div class="col-md-8">
                                    <h6 class="mb-1">
                                        <span class="badge bg-primary me-2" id="modalCategoryBadge">Categoria</span>
                                        <span class="text-success">✓ Gerado com sucesso</span>
                                    </h6>
                                    <p class="mb-0 text-muted" id="modalDescription">
                                        Mapa mental baseado nas suas conversas
                                    </p>
                                </div>
                                <div class="col-md-3 text-center">
                                    <!-- Controles de Zoom -->
                                    <div class="btn-group" role="group" aria-label="Controles de zoom">
                                        <button type="button" class="btn btn-outline-secondary btn-sm" id="zoomOutBtn" title="Diminuir zoom">
                                            <i class="bi bi-zoom-out"></i>
                                        </button>
                                        <button type="button" class="btn btn-outline-secondary btn-sm" id="resetZoomBtn" title="Resetar zoom">
                                            <span id="zoomLevel">100%</span>
                                        </button>
                                        <button type="button" class="btn btn-outline-secondary btn-sm" id="zoomInBtn" title="Aumentar zoom">
                                            <i class="bi bi-zoom-in"></i>
                                        </button>
                                    </div>
                                </div>

                                <div class="col-md-4 text-end">
                                    <small class="text-muted" id="modalTimestamp">
                                        Gerado agora
                                    </small>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Área do conteúdo gerado -->
                        <div class="h-100 d-flex align-items-center justify-content-center" style="min-height: 500px;">
                            <div id="modalMermaidContent" class="w-100 h-100 d-flex align-items-center justify-content-center">
                                <!-- Loading inicial -->
                                <div class="text-center">
                                    <div class="spinner-border text-primary mb-3" role="status">
                                        <span class="visually-hidden">Carregando...</span>
                                    </div>
                                    <p class="text-muted">Renderizando diagrama...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer bg-light">
                        <div class="row w-100 align-items-center">
                            <div class="col-md-6">
                                <small class="text-muted" id="modalStats">
                                    Baseado em 0 conversas
                                </small>
                            </div>
                            <div class="col-md-6 text-end">
<!--                                <button type="button" class="btn btn-outline-secondary me-2" onclick="downloadMermaid()">-->
<!--                                    <i class="bi bi-download me-1"></i>-->
<!--                                    Baixar-->
<!--                                </button>-->
                                <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
                                    <i class="bi bi-check-lg me-1"></i>
                                    Fechar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Adicionar o modal ao body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    this.setupZoomControls();

    // Adicionar event listener para limpar quando fechado
    const modal = document.getElementById('generatedContentModal');
    modal.addEventListener('hidden.bs.modal', () => {
        modal.remove(); // Remove completamente do DOM
    });
const style = document.createElement('style');
style.textContent = `
    @media (max-width: 768px) {
        #generatedContentModal .modal-dialog {
            max-width: 95vw !important;
            max-height: 90vh !important;
        }
        
        #generatedContentModal .modal-content {
            height: 90vh !important;
        }
        
        #modalMermaidContent .mermaid {
            font-size: 12px;
        }
    }
    
    #modalMermaidContent .mermaid {
        background: white !important;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
`;
document.head.appendChild(style);

    return modal;
}
setupZoomControls() {
    // ✅ Usar setTimeout para garantir que o DOM foi atualizado
    setTimeout(() => {
        let currentZoom = 1; // 100%
        const zoomStep = 0.2; // 20% por clique
        const minZoom = 0.2;  // 20% mínimo
        const maxZoom = 3;    // 300% máximo

        const zoomInBtn = document.getElementById('zoomInBtn');
        const zoomOutBtn = document.getElementById('zoomOutBtn');
        const resetZoomBtn = document.getElementById('resetZoomBtn');
        const zoomLevel = document.getElementById('zoomLevel');
        const mermaidContent = document.getElementById('modalMermaidContent');
        const container = document.getElementById('mermaidContainer');

        // Função para atualizar o zoom
        const updateZoom = (newZoom) => {
            currentZoom = Math.max(minZoom, Math.min(maxZoom, newZoom));

            // Aplicar transformação
            mermaidContent.style.transform = `scale(${currentZoom})`;

            // Atualizar display do nível de zoom
            zoomLevel.textContent = `${Math.round(currentZoom * 100)}%`;

            // Atualizar estado dos botões
            zoomInBtn.disabled = currentZoom >= maxZoom;
            zoomOutBtn.disabled = currentZoom <= minZoom;

            // Ajustar scroll do container se necessário
            if (currentZoom > 1) {
                container.style.overflow = 'auto';
            } else {
                container.style.overflow = 'hidden';
            }
        };

        // Event listeners dos botões
        zoomInBtn.addEventListener('click', () => {
            updateZoom(currentZoom + zoomStep);
        });

        zoomOutBtn.addEventListener('click', () => {
            updateZoom(currentZoom - zoomStep);
        });

        resetZoomBtn.addEventListener('click', () => {
            updateZoom(1);
            // Resetar posição do scroll
            container.scrollTop = 0;
            container.scrollLeft = 0;
        });

        // ✅ Suporte a zoom com scroll do mouse (opcional)
        container.addEventListener('wheel', (e) => {
            if (e.ctrlKey) {
                e.preventDefault();
                const delta = e.deltaY > 0 ? -zoomStep : zoomStep;
                updateZoom(currentZoom + delta);
            }
        });

        // ✅ Suporte a atalhos de teclado (opcional)
        const keydownHandler = (e) => {
            // Verificar se o modal está aberto
            const modal = document.getElementById('generatedContentModal');
            if (!modal || !modal.classList.contains('show')) return;

            if (e.ctrlKey) {
                switch(e.key) {
                    case '+':
                    case '=':
                        e.preventDefault();
                        updateZoom(currentZoom + zoomStep);
                        break;
                    case '-':
                        e.preventDefault();
                        updateZoom(currentZoom - zoomStep);
                        break;
                    case '0':
                        e.preventDefault();
                        updateZoom(1);
                        container.scrollTop = 0;
                        container.scrollLeft = 0;
                        break;
                }
            }
        };

        document.addEventListener('keydown', keydownHandler);

        // ✅ Limpar event listener quando modal for removido
        const modal = document.getElementById('generatedContentModal');
        modal.addEventListener('hidden.bs.modal', () => {
            document.removeEventListener('keydown', keydownHandler);
        });

        // Inicializar estado
        updateZoom(1);

    }, 150); // Aguardar 100ms para o DOM ser atualizado
}
showGeneratedModal(categoryName, output, details = null) {
    const modalElement = this.createGeneratedModal();

    document.getElementById('modalCategoryBadge').textContent = categoryName;

    const description = details?.visualizationType === 'fluxograma' 
        ? 'Fluxograma baseado nas suas conversas'
        : 'Mapa mental baseado nas suas conversas';
    document.getElementById('modalDescription').textContent = description;
    
    
    const now = new Date();
    document.getElementById('modalTimestamp').textContent = 
        `Gerado às ${now.toLocaleTimeString()}`;
    
    
    const chatsCount = details?.chatsUsed || 0;
    document.getElementById('modalStats').textContent = 
        `Baseado em ${chatsCount} conversa${chatsCount !== 1 ? 's' : ''}`;
    
    // Mostrar o modal
    const modal = new bootstrap.Modal(modalElement, {
        backdrop: 'static', // Não fecha clicando fora
        keyboard: true      // Permite fechar com ESC
    });
    
    modal.show();
    
    // Renderizar o conteúdo Mermaid após o modal estar visível
    modalElement.addEventListener('shown.bs.modal', () => {
        this.renderMermaidInModal(output);
    }, { once: true });
}

async renderMermaidInModal(content) {
    const container = document.getElementById('modalMermaidContent');
    let status = 'success';
    try {
        if (!window.renderMermaid) throw new Error('Renderer indisponível.');
        await window.renderMermaid('modalMermaidContent', content);
    } catch (error) {
        status = 'failure';
        container.replaceChildren();
        const warning = document.createElement('p');
        warning.textContent = 'Falha de renderização Mermaid. Código preservado abaixo; confira a sintaxe.';
        const pre = document.createElement('pre');
        pre.textContent = content;
        container.append(warning, pre);
    }
    if (this.outputId) {
        const links = document.createElement('div');
        for (const format of ['json', 'mmd']) {
            const link = document.createElement('a');
            link.href = `/output/${this.outputId}/export/${format}/`;
            link.textContent = `Exportar .${format} `;
            link.className = 'btn btn-outline-primary m-1';
            links.appendChild(link);
        }
        const image = document.createElement('button');
        image.textContent = 'Exportar PNG';
        image.className = 'btn btn-outline-primary m-1';
        image.disabled = status !== 'success';
        image.onclick = () => this.downloadMermaidAsImage();
        links.appendChild(image);
        container.appendChild(links);
        try {
            await fetch(`/output/${this.outputId}/render-status/`, {method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
                body: JSON.stringify({status})});
        } catch (_) { this.showError('Não foi possível registrar o status de renderização.'); }
    }
}

async downloadMermaidAsImage() {
    try {
        const mermaidContent = this.output;
        if (!mermaidContent) {
            this.showError('Nenhum conteúdo para baixar');
            return;
        }

        if (!window.mermaid) {
            this.showError('Mermaid não está disponível');
            return;
        }

        // Gerar SVG com Mermaid
        const { svg } = await window.mermaid.render('downloadSvg', mermaidContent);

        // Criar imagem a partir do SVG
        const img = new window.Image();
        const svgBlob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(svgBlob);

        img.onload = () => {
            // Criar canvas com resolução maior para alta qualidade
            const scale = 3; // Aumente para mais qualidade
            const canvas = document.createElement('canvas');
            canvas.width = img.width * scale;
            canvas.height = img.height * scale;
            const ctx = canvas.getContext('2d');
            ctx.setTransform(scale, 0, 0, scale, 0, 0);
            ctx.drawImage(img, 0, 0);

            // Baixar como PNG
            canvas.toBlob(blob => {
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = `mapa-mental-${new Date().toISOString().slice(0, 10)}.png`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                this.showSuccess('Imagem baixada com sucesso!');
            }, 'image/png');
        };
        img.onerror = () => {
            this.showError('Erro ao converter SVG para imagem');
            URL.revokeObjectURL(url);
        };
        img.src = url;
    } catch (error) {

        this.showError('Erro ao baixar a imagem');
    }
}
// Método para download (opcional)
downloadMermaid() {
    try {
        const mermaidContent = this.output;
        if (!mermaidContent) {
            this.showError('Nenhum conteúdo para baixar');
            return;
        }

        const blob = new Blob([mermaidContent], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mapa-mental-${new Date().toISOString().slice(0, 10)}.mmd`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        this.downloadMermaidAsImage();
        this.showSuccess('Arquivo baixado com sucesso!');
    } catch (error) {

        this.showError('Erro ao baixar o arquivo');
    }
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

            alert('Erro ao fazer logout. Tente novamente.');
        }
    }
}


document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});