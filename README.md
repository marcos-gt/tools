# Projeto Django — análise documental de representações Mermaid

Interface Django, templates, JavaScript e Bootstrap; PostgreSQL; Ollama local ou remoto com `qwen3.5:9b-q4_K_M`; Mermaid **11.12.0**. A análise é feita pelo pesquisador, com conferência humana externa. Não há avaliação de aprendizagem, recrutamento ou editor de curadoria.

Login, cadastro com confirmação por email e recuperação de senha estão implementados. Configure o remetente e a credencial SMTP no `.env`; consulte o [guia de email e contas](docs/email-e-contas.md), com exemplos de Gmail, outros servidores e o comando `manage.py testar_email`.

## Windows / PowerShell / VS Code

Use Python 3.12 e uma instalação própria de PostgreSQL. Não reutilize `.venv` ou `.venv1` empacotados. No terminal, em `C:\App\web`:

```powershell
py -3.12 -m venv .venv-tcc
.\.venv-tcc\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv-tcc\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Edite `.env`: coloque a chave gerada em `DJANGO_SECRET_KEY`, entre aspas simples; configure usuário, senha e nome do **banco novo**. O carregamento de `.env` é explícito e variáveis já definidas no processo têm precedência. No VS Code selecione `.venv-tcc\Scripts\python.exe` em “Python: Select Interpreter”. Os comandos abaixo dispensam ativação do ambiente.

Para criar um usuário e banco novos, execute separadamente no `psql` com um administrador (não execute se os nomes já existirem):

```sql
CREATE ROLE tcc LOGIN;
\password tcc
CREATE DATABASE tcc OWNER tcc;
```

Nenhum comando desta entrega recria fisicamente seu banco existente. Depois de configurar `.env` para o banco vazio:

```powershell
.\.venv-tcc\Scripts\python.exe manage.py check
.\.venv-tcc\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv-tcc\Scripts\python.exe manage.py migrate
.\.venv-tcc\Scripts\python.exe manage.py createsuperuser
.\.venv-tcc\Scripts\python.exe manage.py runserver
```

Abra `http://127.0.0.1:8000/login/`. Cadastre categorias e mensagens; selecione a categoria e a modalidade no formulário de geração. Duas contas podem ter categorias de mesmo nome. O frontend usa IDs de categoria. O botão “Deletar” existente inativa a categoria, sem apagar a evidência de geração.

## Testes

Use **outro banco de desenvolvimento**, com nome, usuário e senha próprios. O teste Django cria e remove apenas seu banco `test_<DB_NAME>`; o usuário de teste precisa de `CREATEDB`. Nunca use credenciais de produção para testes.

```powershell
$env:DB_NAME='tcc_dev'
$env:DB_USER='tcc_dev'
$env:DB_PASSWORD='sua-senha-local'
.\.venv-tcc\Scripts\python.exe manage.py check
.\.venv-tcc\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv-tcc\Scripts\python.exe manage.py migrate
.\.venv-tcc\Scripts\python.exe manage.py test
```

Crie antes `tcc_dev` e seu proprietário; conceda `CREATEDB` apenas ao usuário de teste. As chamadas Ollama da suíte são simuladas. Não se usa `db.sqlite3` como banco ou fonte de dados.

## Ollama e limites

Local: `OLLAMA_BASE_URL=http://127.0.0.1:11434`; instale/carregue o modelo com `ollama pull qwen3.5:9b-q4_K_M` no servidor. Remoto: prefira proxy HTTPS com certificado válido ou túnel SSH, por exemplo `ssh -N -L 11434:127.0.0.1:11434 usuario@servidor`, usando então a URL local. Não publique Ollama sem proteção. `OLLAMA_TOKEN` configura Bearer no backend; não chega ao navegador ou às exportações.

Timeouts de conexão e leitura são independentes. `OLLAMA_MAX_INPUT_CHARS=0` desativa o limite da aplicação; um valor positivo rejeita a entrada inteira quando excedido, sem truncá-la. O limite considera a representação JSON do material. `OLLAMA_NUM_CTX` configura a janela do modelo; caracteres não equivalem a tokens. O servidor/modelo ainda pode limitar o contexto: use casos compatíveis com a janela e confira os registros reais. Nenhum prompt garante fidelidade conceitual.

O modelo atual usa `OLLAMA_THINK=false` no `.env`, solicitando resposta direta para gerar Mermaid. `true` habilita o raciocínio; deixe vazio para usar o padrão do modelo. O payload exportado registra a escolha. Reinicie o Django após editar o `.env`. A primeira tentativa do Qwen com o padrão do modelo atingiu o timeout de 120 segundos; a rodada completa usa resposta direta. O controle é documentado na [API oficial do Ollama](https://docs.ollama.com/api/chat).

## Evidências e exportações

`/output/` lista os registros da conta autenticada, incluindo falhas. Cada tentativa válida tem novo ID, data, proprietário, categoria e modalidade, snapshots dos IDs/textos integrais/timestamps, payload efetivo com modelo e opções, resposta original, Mermaid normalizado, duração e status. Entradas rejeitadas antes da inferência não geram registro. `pending` indica execução interrompida ainda sem conclusão registrada.

No modal, exporte JSON, `.mmd` ou PNG (quando o renderer funcionar). Também é possível acessar `/output/<id>/export/json/` e `/output/<id>/export/mmd/`. Falhas de inferência mostram o ID de registro; recupere JSON pela listagem. A resposta original pode incluir `<think>` e fica disponível ao pesquisador no JSON; esse trecho não entra no diagrama. Não são armazenados URL do servidor ou headers de autenticação. Textos fornecidos pelo próprio pesquisador são preservados integralmente: não inclua segredos nos materiais analisados.

`status=success` significa resposta estruturalmente aproveitável; **não** confirma sintaxe Mermaid ou correção conceitual. `render_status` registra o resultado informado pelo navegador e não altera o snapshot da geração. Mermaid usa configuração estrita, sem HTML nos rótulos de fluxograma; código inválido permanece como texto. CDN de Mermaid e Bootstrap requer conexão à internet.

Categorias antigas sem proprietário ficam isoladas (`usuario=NULL`) e não aparecem nas rotas da aplicação. Esta entrega é preparada para banco vazio; atribuição ou divisão de categorias de bancos antigos exige migração de dados específica. As migrations históricas foram preservadas. Defaults históricos de usuário 1 não povoam tabelas vazias; o modelo atual não depende desse usuário.

Veja [registro das correções](docs/correcoes-tcc.md), [casos planejados](docs/casos-documentais.md) e [modelo externo de curadoria](docs/modelo-curadoria.md).

## Teste real com o ambiente configurado

O [comparativo Qwen 3.5 e DeepSeek](docs/testes-qwen35-2026-10-12/relatorio.md) registra a nova rodada no mesmo conjunto de categorias e os tempos reais de inferência.

O [relatório de 12/10/2026](docs/testes-reais-2026-10-12/relatorio.md) registra 15 categorias preenchidas, 54 mensagens ativas e 60 chamadas reais ao `deepseek-r1:7b` no PostgreSQL 17. A primeira categoria usa a referência `diagrama-1.png`. Foram preservados resultados válidos e falhas; renderizar não confirma correção conceitual.

As categorias SIM01–SIM15 e os registros continuam na conta `tcc`. A categoria SIM16 é um controle vazio. Para repetir os testes funcionais, o script abaixo cria novos outputs, não apaga dados e exige Ollama disponível; ele também cria uma conta adicional para testar isolamento. As dependências Node são somente de verificação:

```powershell
npm install --prefix .test-artifacts --no-audit --no-fund playwright@1.64.0
$senhaTeste = Read-Host 'Senha da conta Django tcc' -AsSecureString
$env:TCC_LOGIN_PASSWORD = [System.Net.NetworkCredential]::new('', $senhaTeste).Password
$env:TCC_TEST_PHASE = 'nova_rodada'
$env:TCC_REAL_REPORT = 'docs/testes-qwen35-2026-10-12'
.\.venv-tcc\Scripts\python.exe tools/testar_categorias_reais.py
Remove-Item Env:TCC_LOGIN_PASSWORD
```

O script usa Chrome instalado no caminho padrão do Windows e a porta local 55435. Entradas, snapshots, Mermaid, PNGs e resultados ficam na pasta definida por `TCC_REAL_REPORT`. Copie `categorias.json` para essa pasta ao criar um relatório novo. Não executa a suíte Django contra o banco existente nem muda permissões do PostgreSQL.
