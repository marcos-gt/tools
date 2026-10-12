# Teste real — PostgreSQL 17 e Ollama — 12/10/2026

Foram criadas **15 categorias preenchidas, com 54 mensagens ativas**, na conta `tcc`. Também ficaram uma mensagem inativa de controle, a categoria `SIM16 - CONTROLE SEM MENSAGENS` e duas contas sem privilégios administrativos para testar isolamento. Categorias, chats e outputs que já existiam foram preservados. Nenhum banco foi apagado e não se usou SQLite.

O primeiro caso usa a imagem `diagrama-1.png` fornecida pelo usuário. Os outros casos são exemplos sintéticos de bancos de dados, sem referências bibliográficas ou páginas inventadas. As **saídas são respostas reais de deepseek-r1:7b**, não mocks. Estes são testes funcionais exploratórios, não validação conceitual ou avaliação de aprendizagem.

## Resultado observado

| Rodada | Tentativas | HTTP 200 estrutural | Renderizados | Sintaxe rejeitada pelo renderer | Rejeitados pelo backend/Ollama |
|---|---:|---:|---:|---:|---:|
| baseline | 30 | 22 | 14 | 8 | 8 |
| sintaxe_explicita | 30 | 28 | 19 | 9 | 2 |

**Total: 60 tentativas, 33 renderizadas, 17 falhas de sintaxe e 10 rejeições do backend/serviço.** Todas as 15 categorias tiveram ao menos uma saída renderizada na segunda rodada. Renderização confirma sintaxe aproveitável, não fidelidade conceitual.

A primeira rodada usou o prompt anterior. A segunda acrescentou instruções explícitas de sintaxe, sem trocar modelo ou parâmetros. No caso SIM01, duas mensagens da transcrição foram revistas para explicitar `Socrates → Plato → discípulo`; as outras 14 entradas foram mantidas. Por isso, a comparação entre rodadas é descritiva e não comprova causalidade, melhoria de aprendizagem ou correção conceitual.

## Categorias e última rodada

| Caso | Categoria | Chats ativos | Mapa mental | Fluxograma |
|---|---|---:|---|---|
| SIM01 | SIM01 - DIAGRAMA-1 REFERÊNCIA VISUAL | 3 | ID 32: renderizado | ID 33: renderizado |
| SIM02 | SIM02 - CHAVES E INTEGRIDADE REFERENCIAL | 3 | ID 34: sintaxe rejeitada | ID 35: renderizado |
| SIM03 | SIM03 - RELACIONAMENTOS E CARDINALIDADE | 3 | ID 36: sintaxe rejeitada | ID 37: renderizado |
| SIM04 | SIM04 - PRIMEIRA FORMA NORMAL | 3 | ID 38: renderizado | ID 39: sintaxe rejeitada |
| SIM05 | SIM05 - SEGUNDA FORMA NORMAL | 3 | ID 40: renderizado | ID 41: renderizado |
| SIM06 | SIM06 - TERCEIRA FORMA NORMAL | 3 | ID 42: sintaxe rejeitada | ID 43: renderizado |
| SIM07 | SIM07 - DEPENDÊNCIAS FUNCIONAIS | 3 | ID 44: sintaxe rejeitada | ID 45: renderizado |
| SIM08 | SIM08 - TRANSAÇÕES COMMIT E ROLLBACK | 3 | ID 46: renderizado | ID 47: sintaxe rejeitada |
| SIM09 | SIM09 - CONSULTAS JOINS E VALORES NULOS | 3 | ID 48: renderizado | ID 49: renderizado |
| SIM10 | SIM10 - FILTROS COM ACENTOS E COMPARAÇÕES | 3 | ID 50: renderizado | ID 51: sintaxe rejeitada |
| SIM11 | SIM11 - ÍNDICES E PLANOS DE EXECUÇÃO | 3 | ID 52: sintaxe rejeitada | ID 53: renderizado |
| SIM12 | SIM12 - POLÍTICAS DE EXCLUSÃO REFERENCIAL | 3 | ID 54: renderizado | ID 55: sintaxe rejeitada |
| SIM13 | SIM13 - DOZE MENSAGENS SEM TRUNCAMENTO | 12 | ID 56: renderizado | ID 57: HTTP 502 / incomplete_content |
| SIM14 | SIM14 - LACUNAS E CONTEÚDO COMO DADO | 3 | ID 58: renderizado | ID 59: renderizado |
| SIM15 | SIM15 - TEXTO LONGO E CARACTERES ESPECIAIS | 3 | ID 60: HTTP 502 / unsafe_structure | ID 61: renderizado |

## Primeiro caso: diagrama-1.png

A primeira tentativa (ID 2) retornou `graph TD` em vez de `mindmap` e foi rejeitada com HTTP 502. O fluxograma inicial (ID 3) passou na checagem estrutural e falhou no parser real. Essas tentativas foram preservadas.

O mapa mental da segunda rodada, **ID 32**, renderizou os nove nós observados na transcrição revisada e preservou a hierarquia transcrita. O código permanece o retornado pelo modelo; não foi editado para forçar um sucesso. O layout, as cores e a forma circular da raiz diferem da imagem de referência. Não foi feita validação histórica/filosófica das afirmações da imagem.

- [PNG com alinhamento corrigido](SIM01-mapa-mental-geracao-32-alinhamento-corrigido.png)
- [Mermaid original normalizado](SIM01-mapa-mental-geracao-32.mmd)
- [Registro JSON final](SIM01-mapa-mental-geracao-32-estado-final.json)

O PNG inicial desse mesmo output tinha o texto da raiz circular deslocado para a direita. Foi corrigida uma regra de apresentação no Mermaid (`text-anchor: middle` para rótulos de nós circulares de mindmap). O PNG anterior foi mantido, e 19 outputs renderizados da segunda rodada receberam uma exportação adicional com sufixo `alinhamento-corrigido`. A geometria dos rótulos circulares foi verificada no navegador. Essa alteração é de apresentação, sem alteração do código Mermaid, entrada ou resposta original.

## Controles e limites observados

- 60/60 payloads conferidos com IDs, textos integrais e ordem das mensagens.
- 60/60 excluíram a mensagem inativa de controle.
- SIM13 enviou todas as 12 mensagens, inclusive M12, em ambas as rodadas e modalidades.
- 60/60 botões foram restaurados após sucesso ou falha.
- 60/60 snapshots permaneceram inalterados na exportação final, inclusive os outputs anteriores à revisão da transcrição.
- 9/9 controles finais passaram: modalidade inválida, categoria vazia/inexistente, CSRF e isolamento em listagem, geração, inativação e exportação.
- Nenhuma exceção JavaScript não tratada foi registrada nas duas rodadas. Na segunda, o único diálogo foi o aviso de login; o HTML literal da entrada não executou `alert(1)`.
- JSON/.mmd foram exportados por rotas autenticadas. As 33 renderizações tiveram PNG baixado e assinatura do arquivo verificada. Falhas de sintaxe tiveram texto preservado e captura do modal.

**Problemas de conteúdo continuam exigindo conferência humana.** Exemplos verificáveis: o ID 4 introduziu “Obter/Criar Cliente” apesar da entrada dizer para não criar cliente; o ID 33 trocou o rótulo “contribuições” por “Contrações” e omitiu seus dois sub-ramos; o ID 35 renderizou, mas omitiu o caminho de rejeição do pedido; o ID 34 copiou marcadores “Conceito/Detalhe” e produziu múltiplas raízes, causando falha de sintaxe. Nenhuma dessas saídas foi corrigida manualmente ou apresentada como conceitualmente aprovada.

## Ambiente e verificações

Também foi corrigido o badge dos chats de tipo `text`: eles agora aparecem como **Texto**, em vez de serem rotulados como fluxogramas. A modalidade efetiva continua sendo escolhida exclusivamente no formulário de geração.

- PostgreSQL real: **17.0**, consultado no banco `tcc`.
- Ollama real: **0.32.3**.
- Modelo solicitado: **deepseek-r1:7b**; metadados do tag informam **7.6B**, GGUF, família qwen2 e **Q4_K_M**.
- Digest consultado em `/api/tags`: `755ced02ce7befdb13b7ca74e1e4d08cddba4986afdb63a480f2c93d3140383f`.
- Mermaid: **11.12.0**, carregado pelo frontend no Chrome headless, sem substituir a inferência por mocks nas rodadas reais.
- Python **3.12.5**, Django **5.2.18**.
- `manage.py check`, `makemigrations --check --dry-run` e conferência de migrations passaram no ambiente configurado para PostgreSQL 17. Todas as migrations já estavam aplicadas.
- Após ajustar o prompt, os **12 testes de regressão** passaram em PostgreSQL 18 temporário separado. A conta `tcc` do PostgreSQL 17 não possui CREATEDB; não foram alteradas suas permissões nem executado `manage.py test` contra seu banco para contornar isso.
- O percurso com fixtures de navegador foi repetido após a correção de alinhamento e passou, incluindo a verificação de que o rótulo cabe no círculo.

## Como inspecionar e continuar

Inicie o sistema na raiz do projeto com `.\.venv-tcc\Scripts\python.exe manage.py runserver` (o comando PowerShell completo está no README principal) e entre na conta `tcc`. As categorias SIM01–SIM15 estão disponíveis com seus chats. Os servidores de teste nas portas 55433/55435 foram encerrados; PostgreSQL e Ollama existentes permaneceram em execução.

Os registros reais continuam no banco: `/output/` lista somente os outputs do proprietário; `/output/<id>/export/json/` e `/output/<id>/export/mmd/` exportam as evidências. O token ou endereço privado do Ollama não aparece nesses exports.

Arquivos de evidência: `categorias.json`/`manifesto.json` contêm entradas e IDs da segunda rodada; os correspondentes `*-baseline.json` preservam a primeira; `resultados.json` contém as 60 tentativas; `resumo.json` resume as contagens; `verificacao-snapshots.json` confirma a preservação; `exportacoes-alinhamento-corrigido.json` registra as imagens adicionais. Os JSONs iniciais foram coletados antes da confirmação do renderer e podem indicar `render_status=pending`; os arquivos `*-estado-final.json` registram o estado posterior, sem mudar os campos de geração.

Para repetir a alimentação e as chamadas reais, use `tools/testar_categorias_reais.py` com `TCC_LOGIN_PASSWORD` definido apenas no processo. O script não apaga mensagens, evita duplicar textos já ativos e cria novos outputs em cada repetição. Playwright deve estar instalado em `.test-artifacts/node_modules`. Cada repetição cria uma conta adicional para os controles de isolamento. Não copie credenciais para relatórios.
