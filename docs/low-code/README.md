# Automação Low-Code — n8n + Viagem Inteligente

## Visão Geral

Fluxo no n8n que integra o agente Viagem Inteligente para notificações automáticas
de crises em itinerários de viagem via Discord.

## Arquitetura do Fluxo

```
┌──────────────┐     ┌───────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Webhook    │ ──> │ Chamar Agente │ ──> │ Verificar       │ ──> │  Notificar   │
│   Trigger    │     │ (HTTP POST)   │     │ Sucesso (IF)    │     │  Discord     │
└──────────────┘     └───────────────┘     └─────────────────┘     └──────────────┘
                                                    │
                                                    └── (erro) ──> Responder Erro
```

## Componentes

| Nó | Tipo | Função |
|----|------|--------|
| Webhook Trigger | `n8n-nodes-base.webhook` | Gatilho: recebe POST com dados da crise |
| Chamar Agente | `n8n-nodes-base.httpRequest` | Integração: chama webhook da aplicação |
| Verificar Sucesso | `n8n-nodes-base.if` | Decisão: verifica se processamento foi OK |
| Notificar Discord | `n8n-nodes-base.httpRequest` | Saída: envia plano no Discord |
| Responder OK | `n8n-nodes-base.respondToWebhook` | Responde ao chamador com sucesso |
| Responder Erro | `n8n-nodes-base.respondToWebhook` | Responde ao chamador com erro |

## Trigger (Gatilho)

O fluxo é acionado por um **POST HTTP** no endpoint do n8n:

```
POST http://localhost:5678/webhook/alerta-crise-viagem
Content-Type: application/json

{
    "codigo_reserva": "ABC123",
    "mensagem": "Meu voo foi cancelado por mau tempo"
}
```

## Integração com a Aplicação

O nó "Chamar Agente" faz um POST para o webhook da aplicação:

```
POST http://127.0.0.1:5000/webhook/alerta-voo
```

A aplicação processa a mensagem pelo grafo LangGraph completo e retorna
o plano de contingência.

## Saída Observável

O plano de contingência é enviado automaticamente para um **canal Discord**
via webhook, contendo:
- Código da reserva
- Trace ID (para rastreabilidade)
- Latência de processamento
- Plano de contingência completo

## Instruções de Reprodução

### Pré-requisitos

1. [n8n](https://n8n.io/) instalado (Docker ou npm)
2. Aplicação Viagem Inteligente rodando com webhook ativo
3. Webhook de Discord configurado (opcional para teste local)

### Passo a Passo

```bash
# 1. Iniciar a aplicação com webhook
python main.py webhook

# 2. Instalar e iniciar o n8n
npx n8n start
# Acesse http://localhost:5678

# 3. Importar o workflow
# No n8n: Menu → Import from file → selecione docs/low-code/n8n-workflow.json

# 4. Configurar variável de ambiente no n8n
# Settings → Variables → Adicionar: DISCORD_WEBHOOK_URL = <url_do_seu_webhook_discord>

# 5. Ativar o workflow no n8n

# 6. Testar com curl
curl -X POST http://localhost:5678/webhook/alerta-crise-viagem \
  -H "Content-Type: application/json" \
  -d '{"codigo_reserva": "ABC123", "mensagem": "Meu voo foi cancelado por mau tempo"}'
```

### Teste Local (sem Discord)

Para testar sem Discord, altere `canal_resposta` para `"log"`:

```bash
# Testar diretamente no webhook da aplicação
curl -X POST http://127.0.0.1:5000/webhook/alerta-voo \
  -H "Content-Type: application/json" \
  -d '{"codigo_reserva": "ABC123", "mensagem": "Meu voo foi cancelado", "canal_resposta": "log"}'
```

A resposta incluirá o plano de contingência e o trace_id para rastreabilidade.

### Verificar Saída

```bash
# Health check
curl http://127.0.0.1:5000/webhook/health

# Métricas de observabilidade
curl http://127.0.0.1:5000/webhook/metricas
```

## Alternativas de Ferramentas Low-Code

O webhook da aplicação (`/webhook/alerta-voo`) é compatível com qualquer
ferramenta low-code que suporte HTTP POST:

| Ferramenta | Como integrar |
|-----------|---------------|
| **n8n** | Importar `n8n-workflow.json` (fornecido) |
| **Make.com** | HTTP module → POST para `/webhook/alerta-voo` |
| **Zapier** | Webhooks by Zapier → POST |
| **Power Automate** | HTTP action → POST |

---

*Documentação da automação low-code — Agosto/2026*
