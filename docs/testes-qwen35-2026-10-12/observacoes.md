# Observações da comparação — 12/10/2026

A primeira chamada ao `qwen3.5:9b-q4_K_M`, com o comportamento padrão do modelo, atingiu o timeout de leitura de 120 segundos (output 62). A segunda chamada dessa exploração foi interrompida (output 63), registrada como `test_interrupted` e preservada no banco; ela não entra nas métricas de latência concluída. O [manifesto inicial](manifesto-padrao.json) e o [registro de interrupção](interrupcoes.json) preservam essa distinção.

A rodada completa usa `OLLAMA_THINK=false`, enviado como `think: false` na chamada Ollama. Prompt, mensagens, temperatura e contexto permanecem iguais aos da última rodada do DeepSeek. O modo de raciocínio é uma diferença entre as configurações comparadas; os números não devem ser apresentados como efeito exclusivo da troca de modelo. O primeiro carregamento e caches também não foram controlados.

O Ollama confirmou o modelo de 9 bilhões de parâmetros, quantização Q4_K_M e capacidade de raciocínio. Durante a exploração inicial, `ollama ps` mostrou contexto 8192 e execução 100% GPU na NVIDIA GeForce RTX 3060. A capacidade máxima declarada pelo tag não significa que o sistema esteja usando essa janela máxima.

## Conferência de conteúdo

- **SIM01, mapa mental, output 64:** renderiza e mantém os termos principais da transcrição. Porém, usa o nome da categoria como raiz e coloca “Nó central: Socrates” abaixo dela. A imagem de referência usa Socrates como centro. Os prefixos “Ramo Plato” e “Ramo contribuições” também diferem dos rótulos transcritos. Esse resultado não é uma reprodução fiel da referência.
- **SIM01, fluxograma, output 65:** renderiza as relações transcritas como ligações entre nós, sem acrescentar decisões. A entrada é conceitual e não descreve um processo; a renderização não converte essas relações em etapas reais.
- **SIM02, fluxograma, output 67:** renderiza, mas comprime o procedimento inteiro em um nó e deixa esse nó desconectado. A entrada descreve verificar a existência do cliente, inserir ou rejeitar; o diagrama não explicita esses caminhos de decisão.
- **SIM04, mapa mental, output 70:** o backend aceita a estrutura, mas o parser Mermaid rejeita a sintaxe. O código original foi preservado.
- **SIM05, fluxograma, output 73:** a definição do nó B começa com `{` e termina com `]`; o parser rejeita. Nenhuma correção foi aplicada ao código para contar essa tentativa como sucesso.
- **SIM07, mapa mental, output 76:** preserva expressões da entrada, mas o parser rejeita a sintaxe do mapa. A falha continua disponível como evidência.

Os exemplos acima são inspeções pontuais das saídas reais, sem revisão bibliográfica das entradas e sem aprovação conceitual dos demais diagramas. A contagem de diagramas renderizados mede sintaxe utilizável; a fidelidade dos termos e relações exige conferência humana.

A rodada completa entregou **26/30 diagramas renderizados**: 12/15 mapas mentais e 14/15 fluxogramas. Houve três falhas de sintaxe e uma rejeição pelo backend: o mapa de SIM15 (output 92) recebeu `unsafe_structure`. A mediana de inferência foi **3,85 s**, e a média **4,23 s**. Na última rodada do DeepSeek, foram 19/30 renderizados, mediana 9,27 s e média 9,95 s. A redução observada do tempo médio foi de aproximadamente **57,5%** nesta configuração.

Os **25 testes automatizados passaram** em PostgreSQL temporário separado, incluindo o envio das opções de raciocínio, autenticação, cadastro, recuperação de senha e isolamento. Os nove controles da rodada real passaram; o navegador não registrou exceções JavaScript nem diálogos executados pelo conteúdo das mensagens. Os 60 snapshots anteriores e os 31 registros concluídos do Qwen permaneceram inalterados nos campos de geração.

- [Log dos testes automatizados](backend-verification.txt)
- [Verificação dos snapshots](verificacao-snapshots.json)
- [Registros finais após o renderer](SIM01-mapa-mental-geracao-64-estado-final.json)

## Configuração e repetição

O `.env`, o `.env.example` e o modelo padrão do Django foram atualizados. A configuração ativa é:

```dotenv
OLLAMA_MODEL=qwen3.5:9b-q4_K_M
OLLAMA_THINK=false
```

Reinicie o Django se ele já estava aberto. `OLLAMA_THINK=true` solicita raciocínio, e o valor vazio preserva o padrão do modelo. O controle `think` é descrito na [API oficial do Ollama](https://docs.ollama.com/api/chat) e na [documentação de raciocínio](https://docs.ollama.com/capabilities/thinking).

Os novos outputs estão na conta `tcc`. Nenhuma categoria, chat ou geração anterior foi apagada. A alimentação da rodada evitou duplicar as 54 mensagens ativas existentes. Os testes de autenticação anteriores não foram refeitos com envio externo de email, pois esse serviço não depende do modelo Ollama.

Para regenerar somente a comparação a partir dos arquivos, sem novas inferências:

```powershell
.\.venv-tcc\Scripts\python.exe tools/comparar_modelos.py docs/testes-qwen35-2026-10-12
```

Consulte o [relatório com tempos e contagens](relatorio.md).
