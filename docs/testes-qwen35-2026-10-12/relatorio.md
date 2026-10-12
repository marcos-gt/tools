# Qwen 3.5 versus DeepSeek — 12/10/2026

Teste funcional real no PostgreSQL e Ollama, com as 15 categorias SIM01–SIM15, 54 mensagens ativas e duas modalidades por categoria. A primeira chamada de cada rodada usa a transcricao de `diagrama-1.png`. Chats, outputs e evidencias anteriores foram preservados.

## Desempenho observado

| Modelo / rodada | Tentativas | Renderizados | Falhas de sintaxe | Rejeitados pelo backend | Mediana (s) | Media (s) |
|---|---:|---:|---:|---:|---:|---:|
| deepseek-r1:7b / sintaxe_explicita | 30 | 19 | 9 | 2 | 9.27 | 9.95 |
| qwen3.5:9b-q4_K_M / qwen35_mesmo_prompt | 1 | 0 | 0 | 1 | 120.02 | 120.02 |
| qwen3.5:9b-q4_K_M / qwen35_resposta_direta | 30 | 26 | 3 | 1 | 3.85 | 4.23 |

Os tempos medem a chamada de inferencia no backend (incluem carregamento, raciocinio quando habilitado e eventuais timeouts), sem o tempo de exportacao PNG. A primeira chamada nao foi descartada. Media/mediana consideram todas as tentativas com tempo medido, inclusive falhas. Tempos por modalidade e por resultado renderizado estao no JSON.

A referencia usa somente a ultima rodada do DeepSeek, com instrucoes explicitas de sintaxe. A comparacao e descritiva: houve uma chamada por caso/modalidade, em horarios distintos, sem controlar cache, aquecimento ou outras cargas. Nao comprova superioridade geral do modelo.

## Ambiente

- Modelo: `qwen3.5:9b-q4_K_M`.
- Parametros: `{"temperature": 0.0, "num_ctx": 8192, "read_timeout": 120.0, "think": false}`.
- Ollama: `0.32.3`.
- Mermaid 11.12.0 no Chrome real, com exportacao JSON/Mermaid/PNG.
- Metadados do modelo: `[{"name": "qwen3.5:9b-q4_K_M", "digest": "56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90", "details": {"parent_model": "model.gguf", "format": "gguf", "family": "qwen35", "families": ["qwen35"], "parameter_size": "9.0B", "quantization_level": "Q4_K_M", "context_length": 262144, "embedding_length": 4096}}]`.

## Resultados por categoria

| Rodada | Caso | Modalidade | Output | Resultado | Inferencia (s) |
|---|---|---|---:|---|---:|
| qwen35_mesmo_prompt | SIM01 | mapa-mental | 62 | HTTP 504 / timeout | 120.02 |
| qwen35_resposta_direta | SIM01 | mapa-mental | 64 | renderizado | 2.75 |
| qwen35_resposta_direta | SIM01 | fluxograma | 65 | renderizado | 3.17 |
| qwen35_resposta_direta | SIM02 | mapa-mental | 66 | renderizado | 4.97 |
| qwen35_resposta_direta | SIM02 | fluxograma | 67 | renderizado | 3.81 |
| qwen35_resposta_direta | SIM03 | mapa-mental | 68 | renderizado | 4.50 |
| qwen35_resposta_direta | SIM03 | fluxograma | 69 | renderizado | 3.78 |
| qwen35_resposta_direta | SIM04 | mapa-mental | 70 | sintaxe rejeitada | 3.66 |
| qwen35_resposta_direta | SIM04 | fluxograma | 71 | renderizado | 3.69 |
| qwen35_resposta_direta | SIM05 | mapa-mental | 72 | renderizado | 4.22 |
| qwen35_resposta_direta | SIM05 | fluxograma | 73 | sintaxe rejeitada | 3.31 |
| qwen35_resposta_direta | SIM06 | mapa-mental | 74 | renderizado | 3.47 |
| qwen35_resposta_direta | SIM06 | fluxograma | 75 | renderizado | 3.86 |
| qwen35_resposta_direta | SIM07 | mapa-mental | 76 | sintaxe rejeitada | 4.22 |
| qwen35_resposta_direta | SIM07 | fluxograma | 77 | renderizado | 3.52 |
| qwen35_resposta_direta | SIM08 | mapa-mental | 78 | renderizado | 3.95 |
| qwen35_resposta_direta | SIM08 | fluxograma | 79 | renderizado | 2.86 |
| qwen35_resposta_direta | SIM09 | mapa-mental | 80 | renderizado | 3.98 |
| qwen35_resposta_direta | SIM09 | fluxograma | 81 | renderizado | 3.95 |
| qwen35_resposta_direta | SIM10 | mapa-mental | 82 | renderizado | 4.61 |
| qwen35_resposta_direta | SIM10 | fluxograma | 83 | renderizado | 3.48 |
| qwen35_resposta_direta | SIM11 | mapa-mental | 84 | renderizado | 3.84 |
| qwen35_resposta_direta | SIM11 | fluxograma | 85 | renderizado | 3.27 |
| qwen35_resposta_direta | SIM12 | mapa-mental | 86 | renderizado | 3.92 |
| qwen35_resposta_direta | SIM12 | fluxograma | 87 | renderizado | 2.67 |
| qwen35_resposta_direta | SIM13 | mapa-mental | 88 | renderizado | 9.05 |
| qwen35_resposta_direta | SIM13 | fluxograma | 89 | renderizado | 10.38 |
| qwen35_resposta_direta | SIM14 | mapa-mental | 90 | renderizado | 4.02 |
| qwen35_resposta_direta | SIM14 | fluxograma | 91 | renderizado | 4.28 |
| qwen35_resposta_direta | SIM15 | mapa-mental | 92 | HTTP 502 / unsafe_structure | 6.92 |
| qwen35_resposta_direta | SIM15 | fluxograma | 93 | renderizado | 2.73 |

## Integridade e controles

- Mesmas mensagens e prompt da referencia: 31/31.
- Mesmas options (contexto e temperatura): 31/31.
- Payload integral: 31/31.
- Mensagem inativa excluida: 31/31.
- Botao restaurado: 31/31.
- Controles HTTP/CSRF/isolamento: 9/9.
- Falhas do verificador: 0.

Renderizar confirma sintaxe utilizavel, nao fidelidade conceitual. Confira os arquivos Mermaid e as mensagens de origem antes de usar qualquer diagrama como resultado do TCC. Nenhuma resposta foi corrigida manualmente para forcar um sucesso.

## Primeiro caso e evidencias

- [qwen35_mesmo_prompt / mapa-mental / arquivo_json](SIM01-mapa-mental-geracao-62.json)
- [qwen35_resposta_direta / mapa-mental / arquivo_json](SIM01-mapa-mental-geracao-64.json)
- [qwen35_resposta_direta / mapa-mental / arquivo_mmd](SIM01-mapa-mental-geracao-64.mmd)
- [qwen35_resposta_direta / mapa-mental / arquivo_png](SIM01-mapa-mental-geracao-64.png)
- [qwen35_resposta_direta / fluxograma / arquivo_json](SIM01-fluxograma-geracao-65.json)
- [qwen35_resposta_direta / fluxograma / arquivo_mmd](SIM01-fluxograma-geracao-65.mmd)
- [qwen35_resposta_direta / fluxograma / arquivo_png](SIM01-fluxograma-geracao-65.png)

[Observacoes e limites da comparacao](observacoes.md)

[Metricas detalhadas](comparacao.json) · [Tentativas](resultados.json) · [Manifesto e controles](manifesto.json)
