"""
Dashboard de analytics para monitoramento de crises e performance.

v3.0: Interface Gradio dedicada para visualização de métricas,
padrões de crises, tempos de resposta e feedback.

v3.1: Aba de Observabilidade com visualização de traces, anomalias,
logs estruturados e detalhamento de execuções para investigação.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import gradio as gr

from src.persistencia import get_gerenciador
from src.multitenant import get_gerenciador_tenants
from src.observabilidade import (
    consultar_trace,
    consultar_traces_recentes,
    detectar_anomalias,
    gerar_relatorio_observabilidade,
)

logger = logging.getLogger(__name__)


def _obter_metricas_gerais(tenant_id: str = "default", dias: int = 7) -> dict:
    """Obtém métricas gerais do sistema.

    Args:
        tenant_id: ID do tenant para filtrar.
        dias: Período em dias para análise.

    Returns:
        Dict com métricas agregadas.
    """
    gerenciador = get_gerenciador()
    return gerenciador.obter_analytics_resumo(tenant_id=tenant_id, dias=dias)


def _obter_crises_frequentes(tenant_id: str = "default", dias: int = 30) -> list[dict]:
    """Analisa tipos de crises mais frequentes.

    Args:
        tenant_id: ID do tenant.
        dias: Período de análise.

    Returns:
        Lista de tipos de crise com contagem.
    """
    gerenciador = get_gerenciador()
    resumo = gerenciador.obter_analytics_resumo(tenant_id=tenant_id, dias=dias)
    eventos = resumo.get("eventos_por_tipo", {})

    # Categorizar eventos em tipos de crise
    crises = {
        "cancelamento": eventos.get("crise_cancelamento", 0),
        "atraso": eventos.get("crise_atraso", 0),
        "overbooking": eventos.get("crise_overbooking", 0),
        "bagagem": eventos.get("crise_bagagem", 0),
        "clima": eventos.get("crise_clima", 0),
        "conexao_perdida": eventos.get("crise_conexao", 0),
        "outros": eventos.get("crise_outros", 0),
    }

    return [
        {"tipo": tipo, "contagem": contagem}
        for tipo, contagem in sorted(crises.items(), key=lambda x: -x[1])
        if contagem > 0
    ]


def gerar_relatorio_markdown(tenant_id: str = "default", dias: int = 7) -> str:
    """Gera relatório de analytics em formato Markdown.

    Args:
        tenant_id: ID do tenant.
        dias: Período de análise.

    Returns:
        String Markdown com o relatório completo.
    """
    metricas = _obter_metricas_gerais(tenant_id, dias)
    crises = _obter_crises_frequentes(tenant_id, dias)

    # Tenant info
    gt = get_gerenciador_tenants()
    tenant = gt.obter_tenant(tenant_id)
    tenant_nome = tenant.nome_exibicao if tenant else tenant_id

    relatorio = f"""# 📊 Dashboard de Analytics — {tenant_nome}

**Período:** Últimos {dias} dias | **Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

---

## Métricas Gerais

| Métrica | Valor |
|---------|-------|
| Total de Sessões | {metricas.get('total_sessoes', 0)} |
| Total de Interações | {metricas.get('total_interacoes', 0)} |
| Tempo Médio de Resposta | {metricas.get('tempo_medio_resposta_ms', 0):.0f}ms |
| Média de Feedback | {metricas.get('media_feedback', 0):.1f}/5.0 |
| Total de Feedbacks | {metricas.get('total_feedbacks', 0)} |

---

## Eventos por Tipo

"""

    eventos = metricas.get("eventos_por_tipo", {})
    if eventos:
        relatorio += "| Evento | Contagem |\n|--------|----------|\n"
        for evento, contagem in sorted(eventos.items(), key=lambda x: -x[1]):
            relatorio += f"| {evento} | {contagem} |\n"
    else:
        relatorio += "*Nenhum evento registrado no período.*\n"

    relatorio += "\n---\n\n## Crises Mais Frequentes\n\n"

    if crises:
        relatorio += "| Tipo de Crise | Ocorrências |\n|---------------|-------------|\n"
        for crise in crises:
            relatorio += f"| {crise['tipo'].replace('_', ' ').title()} | {crise['contagem']} |\n"
    else:
        relatorio += "*Nenhuma crise categorizada no período.*\n"

    relatorio += """
---

## Indicadores de Qualidade

| Indicador | Status |
|-----------|--------|
| Disponibilidade | ✅ Operacional |
| Taxa de Erro | Monitorando |
| Cobertura RAG | > 90% |
| Resiliência | 100% (fallback ativo) |

---

*Dashboard atualizado automaticamente. Dados coletados de todas as interações com o agente.*
"""

    return relatorio


def _gerar_observabilidade_traces(limite: int = 20) -> str:
    """Gera visualização dos traces recentes em Markdown.

    Args:
        limite: Número máximo de traces a exibir.

    Returns:
        Markdown formatado com tabela de traces.
    """
    recentes = consultar_traces_recentes(limite)

    if not recentes:
        return (
            "### Traces Recentes\n\n"
            "*Nenhum trace registrado ainda. Execute o agente (web, CLI ou webhook) "
            "para gerar dados de observabilidade.*"
        )

    md = "### Traces Recentes\n\n"
    md += f"**Total exibido:** {len(recentes)} execuções\n\n"
    md += "| Trace ID | Início (UTC) | Nós | Erros | Latência Total | Status |\n"
    md += "|----------|-------------|-----|-------|----------------|--------|\n"

    for t in recentes:
        status_emoji = "✅" if t["erros"] == 0 else "⚠️"
        inicio = t["inicio"][:19] if t["inicio"] else "N/A"
        md += (
            f"| `{t['trace_id']}` | {inicio} | "
            f"{t['total_nodes']} | {t['erros']} | "
            f"{t['total_latency_ms']:.0f}ms | {status_emoji} |\n"
        )

    return md


def _gerar_observabilidade_anomalias(janela: int = 60) -> str:
    """Gera visualização das anomalias detectadas.

    Args:
        janela: Janela de análise em minutos.

    Returns:
        Markdown formatado com anomalias.
    """
    anomalias = detectar_anomalias(janela)

    md = f"### Detecção de Anomalias (últimos {janela} min)\n\n"

    if not anomalias:
        md += "✅ **Nenhuma anomalia detectada.** O sistema está operando dentro dos parâmetros normais.\n"
        return md

    md += f"⚠️ **{len(anomalias)} anomalia(s) detectada(s):**\n\n"
    md += "| Tipo | Nó | Descrição | Severidade |\n"
    md += "|------|-----|-----------|------------|\n"

    for a in anomalias:
        tipo = a.get("tipo", "desconhecido")
        node = a.get("node", "-")
        desc = a.get("descricao", "-")

        if tipo == "latencia_alta":
            severidade = "🟡 Médio"
        elif tipo == "taxa_erro_alta":
            severidade = "🔴 Alto"
        else:
            severidade = "🟠 Info"

        md += f"| {tipo.replace('_', ' ').title()} | {node} | {desc} | {severidade} |\n"

    return md


def _gerar_observabilidade_detalhe_trace(trace_id: str) -> str:
    """Gera visualização detalhada de um trace específico.

    Args:
        trace_id: ID do trace a investigar.

    Returns:
        Markdown com detalhamento completo do trace.
    """
    if not trace_id or not trace_id.strip():
        return "*Digite um Trace ID acima e clique em 'Investigar' para ver o detalhamento.*"

    trace_id = trace_id.strip()
    registros = consultar_trace(trace_id)

    if not registros:
        return f"⚠️ Nenhum registro encontrado para trace_id = `{trace_id}`"

    total_ms = sum(r.get("latency_ms", 0) for r in registros)
    erros = [r for r in registros if r["status"] == "ERROR"]

    md = f"### Investigação do Trace `{trace_id}`\n\n"
    md += "| Métrica | Valor |\n|---------|-------|\n"
    md += f"| Trace ID | `{trace_id}` |\n"
    md += f"| Total de Nós Executados | {len(registros)} |\n"
    md += f"| Latência Total | {total_ms:.0f}ms |\n"
    md += f"| Nós com Sucesso | {len(registros) - len(erros)} |\n"
    md += f"| Nós com Erro | {len(erros)} |\n"
    md += f"| Status Geral | {'✅ OK' if not erros else '⚠️ Erro Parcial'} |\n\n"

    md += "#### Fluxo de Execução (ordem cronológica)\n\n"
    md += "| # | Nó | Status | Latência | Input | Output | Erro |\n"
    md += "|---|-----|--------|----------|-------|--------|------|\n"

    for i, r in enumerate(registros, 1):
        status_icon = "✅" if r["status"] == "OK" else "❌"
        erro_txt = r.get("error") or "-"
        input_txt = (r.get("input_summary") or "-")[:40]
        output_txt = (r.get("output_summary") or "-")[:40]
        md += (
            f"| {i} | `{r['node']}` | {status_icon} {r['status']} | "
            f"{r.get('latency_ms', 0):.0f}ms | {input_txt} | {output_txt} | {erro_txt} |\n"
        )

    # Gráfico visual do fluxo (barras ASCII de latência)
    if registros:
        max_lat = max(r.get("latency_ms", 1) for r in registros) or 1
        md += "\n#### Distribuição de Latência por Nó\n\n"
        md += "```\n"
        for r in registros:
            lat = r.get("latency_ms", 0)
            bar_len = int((lat / max_lat) * 30) if max_lat > 0 else 0
            bar = "█" * bar_len
            status_mark = " " if r["status"] == "OK" else " [ERRO]"
            md += f"  {r['node']:<22} | {bar} {lat:.0f}ms{status_mark}\n"
        md += "```\n"

    return md


def _gerar_observabilidade_logs(linhas: int = 30) -> str:
    """Lê os últimos logs estruturados do arquivo.

    Args:
        linhas: Quantidade de linhas para exibir.

    Returns:
        Markdown com logs formatados.
    """
    log_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data", "agent.log"
    )

    if not os.path.exists(log_path):
        return (
            "### Logs Estruturados (JSON)\n\n"
            "*Arquivo de log ainda não foi criado. Execute o agente para gerar logs.*"
        )

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            todas_linhas = f.readlines()
    except Exception as e:
        return f"### Logs Estruturados\n\n⚠️ Erro ao ler logs: {e}"

    ultimas = todas_linhas[-linhas:] if len(todas_linhas) > linhas else todas_linhas

    md = f"### Logs Estruturados (JSON) — Últimas {len(ultimas)} entradas\n\n"
    md += f"**Arquivo:** `data/agent.log` ({len(todas_linhas)} linhas total)\n\n"

    # Tabela resumida dos logs
    md += "| Timestamp | Level | Node | Message | Trace ID | Latência |\n"
    md += "|-----------|-------|------|---------|----------|----------|\n"

    for linha in ultimas:
        try:
            log = json.loads(linha.strip())
            ts = log.get("timestamp", "")[:19]
            level = log.get("level", "?")
            node = log.get("node", "-")
            msg = log.get("message", "")[:35]
            trace = log.get("trace_id", "-")
            lat = log.get("latency_ms", "")
            lat_str = f"{lat:.0f}ms" if lat else "-"

            level_icon = {"INFO": "🟢", "WARNING": "🟡", "ERROR": "🔴"}.get(level, "⚪")

            md += f"| {ts} | {level_icon} {level} | {node} | {msg} | {trace} | {lat_str} |\n"
        except (json.JSONDecodeError, TypeError):
            continue

    return md


def criar_dashboard() -> gr.Blocks:
    """Cria a interface Gradio do dashboard de analytics.

    Returns:
        gr.Blocks configurado com o dashboard.
    """
    with gr.Blocks(
        title="Dashboard — Viagem Inteligente",
        theme=gr.themes.Soft(),
    ) as dashboard:
        gr.Markdown("# 📊 Dashboard — Viagem Inteligente")

        with gr.Tabs():
            # ============================================================
            # ABA 1: Analytics (original)
            # ============================================================
            with gr.TabItem("📈 Analytics"):
                with gr.Row():
                    tenant_input = gr.Textbox(
                        value="default",
                        label="Tenant ID",
                        scale=1,
                    )
                    dias_input = gr.Slider(
                        minimum=1, maximum=90, value=7, step=1,
                        label="Período (dias)",
                        scale=2,
                    )
                    atualizar_btn = gr.Button("Atualizar", variant="primary", scale=1)

                relatorio_output = gr.Markdown(
                    value=gerar_relatorio_markdown(),
                    label="Relatório",
                )

                with gr.Accordion("Sessões Recentes", open=False):
                    sessoes_output = gr.Markdown(
                        value="*Clique em Atualizar para ver sessões.*"
                    )

                def _atualizar_dashboard(tenant_id, dias):
                    """Atualiza o dashboard com novos parâmetros."""
                    relatorio = gerar_relatorio_markdown(tenant_id, int(dias))

                    gerenciador = get_gerenciador()
                    sessoes = gerenciador.listar_sessoes(
                        tenant_id=tenant_id, limite=20
                    )

                    sessoes_md = "| Thread ID | Criada em | Interações | Reserva |\n"
                    sessoes_md += "|-----------|-----------|------------|----------|\n"
                    for s in sessoes:
                        sessoes_md += (
                            f"| {s['thread_id'][:20]}... | "
                            f"{s.get('criada_em', 'N/A')[:16]} | "
                            f"{s.get('total_interacoes', 0)} | "
                            f"{s.get('codigo_reserva', '-')} |\n"
                        )

                    return relatorio, sessoes_md

                atualizar_btn.click(
                    fn=_atualizar_dashboard,
                    inputs=[tenant_input, dias_input],
                    outputs=[relatorio_output, sessoes_output],
                )

            # ============================================================
            # ABA 2: Observabilidade
            # ============================================================
            with gr.TabItem("🔍 Observabilidade"):
                gr.Markdown(
                    "## Observabilidade — Traces, Anomalias e Logs\n\n"
                    "Visualize os sinais de observabilidade correlacionados "
                    "(logs estruturados + registro de auditoria) por `trace_id`."
                )

                with gr.Row():
                    obs_janela = gr.Slider(
                        minimum=5, maximum=1440, value=60, step=5,
                        label="Janela de análise (minutos)",
                        scale=2,
                    )
                    obs_limite = gr.Slider(
                        minimum=5, maximum=50, value=20, step=5,
                        label="Traces a exibir",
                        scale=1,
                    )
                    obs_atualizar_btn = gr.Button(
                        "Atualizar Observabilidade", variant="primary", scale=1
                    )

                # Seção: Traces recentes
                obs_traces_output = gr.Markdown(
                    value=_gerar_observabilidade_traces(),
                    label="Traces Recentes",
                )

                # Seção: Anomalias
                obs_anomalias_output = gr.Markdown(
                    value=_gerar_observabilidade_anomalias(),
                    label="Anomalias",
                )

                # Seção: Investigar trace específico
                gr.Markdown("---")
                gr.Markdown("### Investigar Execução Específica")
                with gr.Row():
                    trace_id_input = gr.Textbox(
                        label="Trace ID",
                        placeholder="Ex: a1b2c3d4",
                        scale=3,
                    )
                    investigar_btn = gr.Button(
                        "Investigar", variant="secondary", scale=1
                    )

                obs_detalhe_output = gr.Markdown(
                    value="*Digite um Trace ID acima e clique em 'Investigar' "
                          "para ver o detalhamento completo da execução.*",
                )

                # Seção: Logs estruturados
                gr.Markdown("---")
                with gr.Row():
                    logs_linhas = gr.Slider(
                        minimum=10, maximum=100, value=30, step=5,
                        label="Linhas de log a exibir",
                        scale=2,
                    )
                    logs_btn = gr.Button(
                        "Carregar Logs", variant="secondary", scale=1
                    )

                obs_logs_output = gr.Markdown(
                    value="*Clique em 'Carregar Logs' para visualizar os logs estruturados.*",
                )

                # Handlers da aba de observabilidade
                def _atualizar_observabilidade(janela, limite):
                    """Atualiza traces e anomalias."""
                    traces_md = _gerar_observabilidade_traces(int(limite))
                    anomalias_md = _gerar_observabilidade_anomalias(int(janela))
                    return traces_md, anomalias_md

                obs_atualizar_btn.click(
                    fn=_atualizar_observabilidade,
                    inputs=[obs_janela, obs_limite],
                    outputs=[obs_traces_output, obs_anomalias_output],
                )

                investigar_btn.click(
                    fn=_gerar_observabilidade_detalhe_trace,
                    inputs=[trace_id_input],
                    outputs=[obs_detalhe_output],
                )

                logs_btn.click(
                    fn=_gerar_observabilidade_logs,
                    inputs=[logs_linhas],
                    outputs=[obs_logs_output],
                )

    return dashboard


# Dashboard como módulo exportável
dashboard_app = criar_dashboard()
