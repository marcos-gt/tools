# Correções para análise documental — 12/10/2026

**Atualização posterior à primeira entrega:** o ambiente fornecido pelo usuário foi testado com PostgreSQL 17.0 e Ollama 0.32.3. Foram preenchidas 15 categorias com 54 mensagens e executadas 60 gerações reais. Digest e quantização do modelo foram obtidos. Os resultados, falhas e ajustes adicionais de prompt e renderer estão no [relatório de testes reais](testes-reais-2026-10-12/relatorio.md). As pendências descritas abaixo registram a situação da verificação inicial, anterior a essa configuração.

## Escopo e inspeção

Preservados Django, templates HTML, JavaScript, Bootstrap, PostgreSQL, Ollama e o modelo padrão `deepseek-r1:7b`. Foram inspecionados views, models, migrations, autenticação, URLs, template e script do fluxo. Não foram encontrados arquivos AGENTS.md aplicáveis. Havia alterações locais em `home/views.py`, `web/settings.py`, `login/views.py`, arquivos da IDE e bytecode. As mudanças funcionais foram feitas sobre os arquivos existentes; arquivos da IDE não foram editados. Os ambientes empacotados não foram usados.

A inspeção confirmou QuerySet enviado ao modelo, mensagens truncadas pela representação textual, seleção por nome com fallback parcial, corte em dez mensagens, modalidade sem efeito no prompt, ausência de proprietário de categoria, listagem de chats compartilhada, inativação com CSRF desativado, credenciais/configuração fixas e possibilidade de sucesso com saída nula. **Chat.ativo já tinha a migration 0004 neste checkout**: não foi criada uma migration redundante.

## Alterações e arquivos

| Problema | Correção | Arquivos |
|---|---|---|
| Conteúdo parcial e categorias misturadas | Seleção por ID e proprietário; somente mensagens ativas/não vazias, ordem timestamp/ID, sem corte; contagem real | `home/views.py`, `home/inference.py` |
| Modalidade apenas visual | Escolha no formulário de geração e payload, validação de dois valores, prompts distintos para mindmap/flowchart TD | `templates/index.html`, `static/app/scripts.js`, `home/inference.py` |
| Instrução de complementar criativamente | Fidelidade, português, preservação técnica, sem invenção ou conhecimento externo, entrada tratada como material | `home/inference.py` |
| Falhas retornando sucesso/nulo | Erros específicos de validação, conexão, timeout, HTTP, JSON, estrutura, vazio/incompleto; status 400/502/504 | `home/inference.py`, `home/views.py`, `web/api.py` |
| Confusão entre estrutura e sintaxe | Backend avalia estrutura; parser Mermaid no navegador avalia sintaxe; render_status independente | `home/inference.py`, `output/views.py`, template/scripts |
| HTML do modelo e mensagens inseridos sem proteção | Mermaid strict; texto escapado ou textContent; fallback textual seguro e código preservado | template/scripts |
| Dados compartilhados | Proprietário de categoria, unicidade por usuário/nome, filtros e validação de propriedade em consultas/mutações/exports | apps `chat`, `categoria`, `output`; `web/api.py` |
| CSRF/autenticação | Sessão com CSRF também no login; cookie inicial; operações protegidas; retirada do token DRF desnecessário | `web/auth.py`, `login/views.py`, `web/api.py`, scripts |
| Ausência de evidência persistente | Novo Output para cada tentativa; snapshots integrais, payload, opções, resposta, Mermaid, status e duração; JSON/.mmd | `output/models.py`, views/urls, `home/views.py` |
| Configuração fixa e dependências extras | `.env` explícito e variáveis; remoção de CORS/DRF/Extensions/WhiteNoise sem uso necessário no fluxo; quatro dependências diretas | settings, requirements, `.env.example`, `.gitignore` |
| Schema novo | Acrescentadas migrations de proprietário/unicidade e campos de evidência; removido default atual de Output.usuario; histórico preservado | `categoria/migrations/0002*`, `output/migrations/0003*` |

`Categoria.usuario` aceita NULL para manter categorias históricas sem atribuição arbitrária. Rotas da aplicação excluem essas categorias. A criação normal sempre atribui o usuário autenticado. Bancos antigos com categorias compartilhadas não foram convertidos ou povoados. Defaults históricos `usuario=1` permanecem nas migrations antigas, mas não exigem usuário 1 em tabelas vazias; confirmado pela aplicação integral das migrations antes da criação de contas.

O payload exportado é o mesmo objeto JSON enviado ao Ollama e não contém URL ou headers. Credenciais do proxy ficam apenas no header backend. Resposta de conteúdo preserva o texto original, inclusive think; a normalização retira think apenas do diagrama e rejeita blocos incompletos. Corpos de JSON inválido/estrutura inesperada têm configuração privada conhecida removida antes do registro. Falhas de transporte não têm resposta textual a preservar; corpos HTTP de erro não são expostos. Logs normais contêm somente IDs e códigos técnicos.

## Evidências de verificação

Verificações executadas com ambiente novo `.venv-tcc` e **PostgreSQL temporário separado**, usuário `tcc_test`, porta 55432, banco `tcc_schema`. O servidor existente na porta 5432 não recebeu migrations, alteração de dados, DROP ou flush. O teste Django criou seu próprio `test_tcc_schema` e o removeu ao concluir. A instância temporária foi encerrada após os comandos.

| Comando/verificação | Evidência |
|---|---|
| `python manage.py check` | Passou: nenhum problema |
| `python manage.py makemigrations --check --dry-run` | Passou: nenhuma mudança detectada |
| `python manage.py migrate --noinput` | Passou em banco PostgreSQL vazio, incluindo admin/auth/sessions e apps do projeto |
| `python manage.py test --verbosity 2` | **12 testes passaram**; resultado em `docs/evidencias/backend.txt` |
| `node --check static/app/scripts.js` | Passou |
| Mermaid 11.12.0 no Chrome headless | mindmap e flowchart TD produziram SVG; sintaxe inválida foi rejeitada pelo parser real |
| Percurso completo da interface | Login, duas modalidades, SVG, JSON/.mmd/PNG, falha de sintaxe com código preservado, HTTP 502 para vazio, botão restaurado e proteção de HTML passaram; `docs/evidencias/frontend.txt` |

O teste de navegador usou Chrome headless via Playwright, um servidor HTTP Ollama simulado na porta 55434 e Django na porta 55433. A CDN foi interceptada no teste com os pacotes npm exatos Mermaid 11.12.0 e Bootstrap 5.3.0; portanto não comprova disponibilidade da CDN no ambiente do pesquisador. As respostas eram fixtures técnicas sintéticas, distintas de resultados documentais BD01–BD03. JSON e .mmd foram comparados; os PNGs das duas modalidades foram baixados e tiveram sua assinatura verificada, e o PNG de mapa mental foi aberto para inspeção visual.

Os scripts desse teste e de sua fixture foram arquivados como texto em `docs/evidencias/frontend-script.cjs.txt` e `frontend-fixture.py.txt` para permitir inspeção das verificações. São evidências da execução em ambiente temporário, com credenciais sintéticas exclusivas da fixture. Não configuram a instalação normal; para execução do projeto e validação real, seguir o README. Versões instaladas e hash do módulo Mermaid executado estão em `docs/evidencias/versoes.json`.

Durante as verificações, iniciar PostgreSQL dentro do sandbox falhou, exigindo execução autorizada fora dele. O coletor inicial precisou de correção de codificação cp1252/UTF-8 e do lançamento de subprocessos no Windows; o teste de navegador precisou corrigir uma URL relativa no próprio teste. Nenhuma execução interrompida foi tratada como aprovada. O teste também revelou falhas reais na conversão PNG e no contêiner dos controles de zoom, que foram corrigidas na aplicação antes da execução final.

## Versões e pendências

| Componente | Situação verificável |
|---|---|
| Python | 3.12.5, executado no ambiente novo |
| Django | 5.2.18, instalado e executado |
| PostgreSQL | 18.0, cliente e servidor temporário confirmados |
| Mermaid | 11.12.0, versão exata no template e pacote executado no navegador |
| Ollama | Cliente 0.32.3; comando informou ausência de serviço local em execução |
| Modelo | `deepseek-r1:7b` mantido; versão/digest/quantização pendentes |

Não foi chamada a antiga URL pública hardcoded. Nenhuma configuração remota protegida foi fornecida em `.env`. Inferência real, versão do servidor remoto, disponibilidade do modelo, digest e quantização **não foram verificados**. Mocks e diagramas de teste não são resultados reais dos casos BD01–BD03.

Para verificar localmente: iniciar Ollama no servidor escolhido, conferir `/api/version` e `/api/tags`, consultar `/api/show` para o modelo e registrar digest/detalhes de quantização quando disponíveis. Configurar URL e token no `.env`, iniciar Django, criar as entradas efetivamente consultadas dos três casos, gerar as duas modalidades e exportar os registros. Conferir conteúdo na fonte e sintaxe/renderização no navegador. A exportação PNG passou com fixtures no Chrome, mas depende do suporte do navegador ao SVG/canvas e deve ser conferida também nas saídas reais.

## Atualizações necessárias no TCC

**Recursos anteriores:** cadastro de mensagens e categorias, autenticação, interface Bootstrap, solicitação de representação via Ollama remoto, apresentação Mermaid e exportação de imagem. A modalidade de cadastro não diferenciava semanticamente o prompt de geração e o mapa usava flowchart. Descrições de envio integral, isolamento completo ou tratamento robusto de falhas não correspondiam ao fluxo anterior.

**Recursos implementados nesta entrega:** seleção de modalidade na geração; mindmap hierárquico e flowchart TD com prompts distintos; payload de mensagens integrais determinístico; isolamento por usuário/categoria; CSRF; configuração externa; erros explícitos; registros persistentes com snapshots; exportação JSON/.mmd; renderer com versão exata e fallback textual seguro. Atualizar arquitetura operacional, modelo de dados, sequência de geração, autenticação, modalidades e método de coleta documental para refletir essas mudanças.

**Limitações restantes:** fidelidade conceitual exige conferência humana; sem garantia de aprendizagem; sintaxe só é confirmada pelo parser no navegador; parâmetros/contexto do modelo podem limitar a entrada no servidor; nenhuma inferência real realizada nesta verificação; dependência de CDN na interface; registros antigos não têm snapshots retrospectivos; categorias antigas sem proprietário exigem decisão de migração própria; curadoria externa, sem editor nativo ou histórico de revisões.

Os casos planejados e o formulário externo constam de `casos-documentais.md` e `modelo-curadoria.md`. Referências e páginas serão preenchidas somente quando efetivamente consultadas pelo pesquisador. O TCC não foi reescrito e o sistema não foi publicado.

Documentação técnica consultada: [sintaxe de mindmap](https://mermaid.js.org/syntax/mindmap.html), [sintaxe de flowchart](https://mermaid.js.org/syntax/flowchart.html), [versões Django](https://www.djangoproject.com/download/). Essas fontes verificam aspectos técnicos da implementação, não substituem as referências de bancos de dados do TCC.
