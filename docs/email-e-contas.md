# Cadastro, confirmação e recuperação por email

O login foi redesenhado para desktop e celular. Cadastro, confirmação, reenvio e recuperação usam o mesmo visual, formulários Django com CSRF, mensagens de erro inline e controle para mostrar/ocultar senha. Nenhuma biblioteca nova é necessária para enviar emails.

## Configurar o remetente

As opções já foram acrescentadas ao `.env` e ao `.env.example`. Os valores anteriores do banco, Ollama e chave do Django foram preservados. **O endereço de email sozinho não autentica um envio SMTP**: é necessário configurar o servidor e, quando exigido, uma credencial de envio.

Para Gmail, mantenha as opções de porta/TLS que já estão no arquivo e preencha:

```dotenv
EMAIL_PROVIDER=gmail
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=seu-remetente@gmail.com
EMAIL_HOST_PASSWORD='sua-senha-de-aplicativo'
DEFAULT_FROM_EMAIL=
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
PUBLIC_SITE_URL=http://127.0.0.1:8000
```

Com `EMAIL_PROVIDER=gmail` e host vazio, o código usa `smtp.gmail.com`. Com remetente padrão vazio, os emails saem de `EMAIL_HOST_USER`, com o nome amigável `SITE_NAME`. Assim, o endereço é preenchido uma única vez. A configuração usa STARTTLS na porta 587, conforme a [documentação do Gmail](https://developers.google.com/workspace/gmail/imap/imap-smtp).

Use **senha de aplicativo**, quando disponível para sua conta, não a senha normal de login do Google. Esse recurso exige verificação em duas etapas e pode ser restringido pelo administrador da organização. Veja as [instruções oficiais do Google](https://support.google.com/mail/answer/185833). Cole a senha sem os espaços de agrupamento exibidos pelo provedor.

Para outro serviço SMTP:

```dotenv
EMAIL_PROVIDER=smtp
EMAIL_HOST=smtp.seu-provedor.example
EMAIL_PORT=587
EMAIL_HOST_USER=seu-remetente@seu-dominio.example
EMAIL_HOST_PASSWORD='credencial-smtp-do-provedor'
DEFAULT_FROM_EMAIL=
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
```

Se o provedor usar SSL direto na porta 465, configure `EMAIL_PORT=465`, `EMAIL_USE_SSL=true` e `EMAIL_USE_TLS=false`. TLS e SSL não podem estar habilitados simultaneamente. O backend implementado usa SMTP com usuário/senha ou um relay autorizado sem autenticação; provedores que aceitem somente OAuth exigem integração adicional ou um relay compatível. A configuração segue o [backend de email do Django 5.2](https://docs.djangoproject.com/en/5.2/topics/email/).

`DEFAULT_FROM_EMAIL` pode ser preenchido quando o provedor autorizar outro remetente, por exemplo `Sistema de Chat <notificacoes@seu-dominio.example>`. Para um relay sem usuário/senha, esse campo é obrigatório. Não use um remetente que o servidor não autorize.

## Endereço dos links

`PUBLIC_SITE_URL` é a origem do **site Django**, não do Ollama ou do servidor SMTP. Não inclua caminho, query ou credenciais. Para uso local no mesmo computador, o valor atual `http://127.0.0.1:8000` funciona. Para destinatários em outro dispositivo, configure um endereço acessível por eles, normalmente uma origem HTTPS própria. Um link para `127.0.0.1` aberto no celular aponta para o próprio celular.

Os emails usam essa origem fixa, evitando construir links com o Host arbitrário de uma requisição. A chave `DJANGO_SECRET_KEY` deve ser aleatória e privada, pois protege os tokens; o README principal inclui o comando para gerá-la. Reinicie o `runserver` depois de editar `.env`.

## Testar seu serviço de envio

Depois de preencher a configuração:

```powershell
.\.venv-tcc\Scripts\python.exe manage.py check
.\.venv-tcc\Scripts\python.exe manage.py testar_email seu-destinatario@exemplo.com
.\.venv-tcc\Scripts\python.exe manage.py runserver
```

O comando envia **uma mensagem real** para o endereço informado, sem senha ou token de recuperação, e não imprime credenciais. A resposta de sucesso confirma que o serviço aceitou a mensagem; confira a caixa de entrada e o spam para confirmar o recebimento. Em caso de erro, o comando mostra uma mensagem pública e, quando disponível, apenas o código SMTP. Credenciais, política de envio, DNS, bloqueios de rede e entrega na caixa real dependem do provedor.

## Fluxos disponíveis

| Caminho | Função |
|---|---|
| `/login/` | Entrar com usuário e senha; contas antigas continuam funcionando |
| `/login/cadastro/` | Criar uma conta com nome, usuário, email e senha |
| `/login/confirmar-email/<uid>/<token>/` | Conferir o link e confirmar via POST |
| `/login/reenviar-confirmacao/` | Pedir outro link para uma conta pendente |
| `/login/recuperar-senha/` | Pedir link de recuperação por email |
| `/login/redefinir-senha/<uid>/<token>/` | Escolher uma nova senha |

Novas contas ficam inativas até confirmar o email. A confirmação envia boas-vindas; nenhum email contém a senha escolhida. Aberturas automáticas do link por scanners de email não ativam a conta: a página exige o botão “Confirmar meu email”. Depois da ativação, o token não pode ser reutilizado. Uma conta confirmada e posteriormente desativada por um administrador não é reativada por um link antigo.

A recuperação usa os tokens do Django, valida a senha com as regras existentes e invalida o link após trocar a senha. Recuperação e confirmação expiram por padrão em **3600 segundos**, configuráveis com `PASSWORD_RESET_TIMEOUT`. Contas inativas ou sem senha utilizável não recebem recuperação. Os caminhos antigos de `/accounts/` passam pelos mesmos controles; o endpoint `/api-login/` foi preservado.

Emails de novos cadastros são normalizados e reservados de forma única em `AccountEmail`; há também uma conferência dos emails nas contas antigas. A migration `login.0001_initial` já foi aplicada no PostgreSQL 17 do projeto, sem alterar as contas, categorias, chats ou outputs anteriores. As contas antigas não precisam confirmar novamente, mas precisam ter um email correto salvo em `User.email` para receber recuperação. A conta `tcc` já possui um email preenchido; seu valor não foi exibido nem alterado.

Pedidos para emails inexistentes e existentes recebem a mesma resposta pública na recuperação/reenvio. Falhas SMTP durante recuperação também não revelam se a conta existe: geram um evento técnico sem endereço, corpo ou credenciais e a mesma tela genérica. Use `testar_email` para diagnosticar o envio. No cadastro, falha de envio desfaz a criação, libera usuário/email para uma nova tentativa e mostra erro útil.

Há cooldown por email de 60 segundos e limite de 10 pedidos por IP/ação por hora (`AUTH_EMAIL_COOLDOWN` e `AUTH_EMAIL_MAX_PER_IP`). Usa o cache do Django; o cache padrão é local ao processo. Se futuramente usar vários workers, configure um cache compartilhado para que os limites sejam comuns. Não foi criado editor de perfis, coleta de pesquisa ou avaliação de aprendizagem.

## Evidências de verificação

- **25 testes de regressão passaram** em banco PostgreSQL temporário separado: os 12 existentes e 13 novos de autenticação/email.
- `check` e `makemigrations --check --dry-run` passaram; a nova migration foi aplicada também no PostgreSQL 17 configurado pelo usuário.
- Chrome headless verificou desktop/celular, ausência de rolagem horizontal, mostrar senha, cadastro, bloqueio antes da confirmação, confirmação, boas-vindas, recuperação, troca, rejeição de senha antiga/token usado e login final.
- O teste de navegador usou o **backend SMTP real contra um servidor local que apenas captura mensagens**. Foram conferidas as partes texto e HTML. Nenhum email externo foi enviado e não foram usadas contas reais nos testes de cadastro/troca de senha.
- A primeira execução de navegador revelou `Origin: null` causado por `Referrer-Policy: no-referrer`. A política foi corrigida para `same-origin`, mantendo a proteção CSRF; a execução final passou.
- Não foram testados autenticação ou entrega de um provedor externo, pois as credenciais de envio ainda não foram fornecidas.

Veja [log dos testes](auth-evidencias/backend.txt), [fluxo navegador/SMTP](auth-evidencias/browser-smtp.txt), [login desktop](auth-evidencias/login-desktop.png), [login celular](auth-evidencias/login-mobile.png), [cadastro](auth-evidencias/cadastro-desktop.png) e [recuperação](auth-evidencias/recuperacao-desktop.png).

Para repetir a verificação isolada no Windows, instale Playwright apenas como ferramenta de teste e execute:

```powershell
npm install --prefix .test-artifacts --no-audit --no-fund playwright@1.64.0
.\.venv-tcc\Scripts\python.exe tools/verify_auth_smtp.py
```

O helper usa PostgreSQL 18 instalado no caminho padrão, ou `TCC_TEST_PG_BIN` apontando para os binários desejados; cria um cluster próprio em `.test-artifacts/auth-pgdata`, banco `auth_browser`, porta 55432, SMTP capturador em 55437 e Django em 55436. Nunca usa `tcc` como fallback. Precisa de Chrome no caminho padrão e portas livres; encerra os processos iniciados ao terminar. Os emails de teste com tokens ficam somente em `.test-artifacts`, ignorado pelo Git, e não são servidos como arquivos públicos.
