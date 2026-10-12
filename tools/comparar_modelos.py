"""Compara evidencias reais existentes; nao faz chamadas nem altera o banco."""
import argparse
import json
import statistics
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def summarize(records):
    times = [r['duracao_inferencia_ms'] / 1000 for r in records
             if 'duracao_inferencia_ms' in r]
    successes = [r['duracao_inferencia_ms'] / 1000 for r in records
                 if r.get('render_status') == 'success' and 'duracao_inferencia_ms' in r]
    return {
        'tentativas': len(records),
        'renderizados': sum(r.get('render_status') == 'success' for r in records),
        'falhas_renderer': sum(r.get('render_status') == 'failure' for r in records),
        'rejeitados_backend': sum(r.get('http') != 200 for r in records),
        'timeouts': sum(r.get('codigo_erro') == 'timeout' for r in records),
        'falhas_verificacao': sum(bool(r.get('falha_verificacao')) for r in records),
        'tempos_medidos': len(times),
        'media_segundos': statistics.mean(times) if times else None,
        'mediana_segundos': statistics.median(times) if times else None,
        'minimo_segundos': min(times) if times else None,
        'maximo_segundos': max(times) if times else None,
        'tempo_total_segundos': sum(times),
        'mediana_renderizados_segundos': statistics.median(successes) if successes else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--previous', type=Path, default=Path('docs/testes-reais-2026-10-12'))
    args = parser.parse_args()
    current = read(args.report / 'resultados.json')
    previous = [r for r in read(args.previous / 'resultados.json')
                if r.get('fase') == 'sintaxe_explicita']
    manifest = read(args.report / 'manifesto.json')
    runs = sorted(set(r['run_id'] for r in current))
    summary = {'referencia_deepseek': summarize(previous), 'rodadas': {}, 'comparacao_payloads': []}
    by_case = {(r['caso'], r['modalidade']): r for r in previous}
    for run in runs:
        records = [r for r in current if r['run_id'] == run]
        summary['rodadas'][run] = {'fase': records[0].get('fase'), **summarize(records),
                                 'modalidades': {mode: summarize([r for r in records if r['modalidade'] == mode])
                                                for mode in ('mapa-mental', 'fluxograma')}}
        for record in records:
            old = by_case.get((record['caso'], record['modalidade']))
            if not old or not record.get('arquivo_json'):
                continue
            old_payload = read(args.previous / old['arquivo_json'])['payload']
            new_payload = read(args.report / record['arquivo_json'])['payload']
            summary['comparacao_payloads'].append({
                'run_id': run, 'caso': record['caso'], 'modalidade': record['modalidade'],
                'mesmas_mensagens_e_prompt': old_payload['messages'] == new_payload['messages'],
                'mesmas_options': old_payload['options'] == new_payload['options'],
                'think': new_payload.get('think', 'padrao_do_modelo'),
            })
    summary['controles'] = manifest['controles']
    (args.report / 'comparacao.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    lines = ['# Qwen 3.5 versus DeepSeek — 12/10/2026', '',
             'Teste funcional real no PostgreSQL e Ollama, com as 15 categorias SIM01–SIM15, '
             '54 mensagens ativas e duas modalidades por categoria. A primeira chamada de cada rodada '
             'usa a transcricao de `diagrama-1.png`. Chats, outputs e evidencias anteriores foram preservados.', '',
             '## Desempenho observado', '',
             '| Modelo / rodada | Tentativas | Renderizados | Falhas de sintaxe | Rejeitados pelo backend | Mediana (s) | Media (s) |',
             '|---|---:|---:|---:|---:|---:|---:|']

    def row(name, stat):
        median = f"{stat['mediana_segundos']:.2f}" if stat['mediana_segundos'] is not None else '—'
        mean = f"{stat['media_segundos']:.2f}" if stat['media_segundos'] is not None else '—'
        return (f"| {name} | {stat['tentativas']} | {stat['renderizados']} | {stat['falhas_renderer']} "
                f"| {stat['rejeitados_backend']} | {median} | {mean} |")

    lines.append(row('deepseek-r1:7b / sintaxe_explicita', summary['referencia_deepseek']))
    for run, stat in summary['rodadas'].items():
        lines.append(row(manifest['modelo'] + ' / ' + stat['fase'], stat))
    lines += ['', 'Os tempos medem a chamada de inferencia no backend (incluem carregamento, raciocinio '
              'quando habilitado e eventuais timeouts), sem o tempo de exportacao PNG. '
              'A primeira chamada nao foi descartada. Media/mediana consideram todas as tentativas com tempo '
              'medido, inclusive falhas. Tempos por modalidade e por resultado renderizado estao no JSON.', '',
              'A referencia usa somente a ultima rodada do DeepSeek, com instrucoes explicitas de sintaxe. '
              'A comparacao e descritiva: houve uma chamada por caso/modalidade, em horarios distintos, '
              'sem controlar cache, aquecimento ou outras cargas. Nao comprova superioridade geral do modelo.', '',
              '## Ambiente', '', f"- Modelo: `{manifest['modelo']}`.",
              f"- Parametros: `{json.dumps(manifest['parametros'], ensure_ascii=False)}`.",
              f"- Ollama: `{manifest['ollama_version'].get('version')}`.",
              '- Mermaid 11.12.0 no Chrome real, com exportacao JSON/Mermaid/PNG.',
              f"- Metadados do modelo: `{json.dumps(manifest['ollama_tags'], ensure_ascii=False)}`.", '',
              '## Resultados por categoria', '',
              '| Rodada | Caso | Modalidade | Output | Resultado | Inferencia (s) |',
              '|---|---|---|---:|---|---:|']
    for r in current:
        outcome = ('renderizado' if r.get('render_status') == 'success' else
                   'sintaxe rejeitada' if r.get('render_status') == 'failure' else
                   f"HTTP {r.get('http')} / {r.get('codigo_erro', '')}")
        duration = f"{r['duracao_inferencia_ms'] / 1000:.2f}" if 'duracao_inferencia_ms' in r else '—'
        lines.append(f"| {r.get('fase')} | {r['caso']} | {r['modalidade']} | {r.get('output_id', '—')} | {outcome} | {duration} |")
    equal_messages = sum(c['mesmas_mensagens_e_prompt'] for c in summary['comparacao_payloads'])
    equal_options = sum(c['mesmas_options'] for c in summary['comparacao_payloads'])
    lines += ['', '## Integridade e controles', '',
              f"- Mesmas mensagens e prompt da referencia: {equal_messages}/{len(summary['comparacao_payloads'])}.",
              f"- Mesmas options (contexto e temperatura): {equal_options}/{len(summary['comparacao_payloads'])}.",
              f"- Payload integral: {sum(r.get('payload_integral') is True for r in current)}/{len(current)}.",
              f"- Mensagem inativa excluida: {sum(r.get('inativo_excluido') is True for r in current)}/{len(current)}.",
              f"- Botao restaurado: {sum(r.get('botao_restaurado') is True for r in current)}/{len(current)}.",
              f"- Controles HTTP/CSRF/isolamento: {sum(c['passou'] for c in manifest['controles'])}/{len(manifest['controles'])}.",
              f"- Falhas do verificador: {sum(bool(r.get('falha_verificacao')) for r in current)}.", '',
              'Renderizar confirma sintaxe utilizavel, nao fidelidade conceitual. Confira os arquivos Mermaid '
              'e as mensagens de origem antes de usar qualquer diagrama como resultado do TCC. Nenhuma resposta '
              'foi corrigida manualmente para forcar um sucesso.', '',
              '## Primeiro caso e evidencias', '']
    for r in current:
        if r['caso'] == 'SIM01':
            for key in ('arquivo_json', 'arquivo_mmd', 'arquivo_png'):
                if r.get(key):
                    lines.append(f"- [{r['fase']} / {r['modalidade']} / {key}]({r[key]})")
    lines += ['', '[Observacoes e limites da comparacao](observacoes.md)', '',
              '[Metricas detalhadas](comparacao.json) · [Tentativas](resultados.json) · '
              '[Manifesto e controles](manifesto.json)', '']
    (args.report / 'relatorio.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'comparacao_payloads'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
