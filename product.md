# Visão do Produto — Viagem Inteligente

> **Repositório:** [https://github.com/wiltonssp/mini-projeto-t2-crise-viagem](https://github.com/wiltonssp/mini-projeto-t2-crise-viagem)

## Identidade

| Campo | Valor |
|-------|-------|
| **Nome** | Viagem Inteligente |
| **Subtítulo** | Gestão Automatizada de Crises em Itinerários com IA |
| **Tipo** | Agente Conversacional (AI Agent) |
| **Domínio** | Aviação / Turismo / Atendimento ao Passageiro |
| **Plataforma** | Web (Gradio) + CLI |
| **Idioma** | Português do Brasil |
| **Repositório** | [github.com/wiltonssp/mini-projeto-t2-crise-viagem](https://github.com/wiltonssp/mini-projeto-t2-crise-viagem) |

## Proposta de Valor

> Em segundos, o Viagem Inteligente consolida status de voo, clima, transporte alternativo, políticas e legislação para gerar um plano de ação personalizado — o que levaria horas no atendimento tradicional.

## Visão de Longo Prazo

Tornar-se a referência em assistência automatizada ao viajante em crise, integrando fontes de dados reais e oferecendo suporte proativo antes mesmo que o passageiro saiba que há um problema.

## Princípios do Produto

1. **Resposta imediata** — O viajante em crise precisa de ação, não de espera
2. **Informação consolidada** — Uma única interface reúne voo + clima + direitos + alternativas
3. **Personalização** — Cada plano referencia dados específicos do passageiro
4. **Resiliência** — Funciona com dados parciais; nunca deixa o usuário sem resposta
5. **Transparência** — Indica claramente quando uma informação não está disponível

## Arquitetura Conceitual

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACE (Gradio / CLI)                   │
├─────────────────────────────────────────────────────────────┤
│                     AGENTE (LangGraph)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Validação │→│  Consultas│→│    RAG   │→│   LLM    │    │
│  │           │  │ (Voo,    │  │ (TF-IDF) │  │ (Groq)   │   │
│  │           │  │  Clima,  │  │          │  │          │    │
│  │           │  │  Transp) │  │          │  │          │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    ESTADO (TypedDict + MemorySaver)           │
└─────────────────────────────────────────────────────────────┘
```

## Diferenciais Técnicos

| Aspecto | Implementação |
|---------|--------------|
| **Orquestração** | LangGraph StateGraph com fluxo explícito (não prompt-chain) |
| **Controle de fluxo** | Arestas condicionais baseadas em validação |
| **Memória** | MemorySaver + SQLite persistente com thread_id por sessão (v1.1) |
| **Detecção inteligente** | Regex determina resposta direta vs. plano completo (sem custo LLM) |
| **RAG** | TF-IDF + Sentence Transformers (fallback automático) — multilíngue |
| **Resiliência** | Try/except por nó — falha parcial nunca bloqueia o fluxo |
| **CI/CD** | GitHub Actions com lint, testes e validação de documentação |
| **Integrações** | Adapter pattern com FlightAware, Amadeus, Twilio, Telegram |
| **Multi-tenant** | Planos B2B com isolamento, branding e tracking de uso |
| **Feedback loop** | Coleta, categorização e export JSONL para fine-tuning |

## Fluxos de Uso

### Fluxo Principal — Situação de Crise

```
Usuário: "ABC123 Meu voo foi cancelado por mau tempo e vou perder minha conexão"
         ↓
   [Validação] → [Consulta Voo] → [Clima] → [Transporte] → [RAG] → [LLM] → [Plano]
         ↓
Agente: Plano de contingência com 5 seções personalizadas
```

### Fluxo Alternativo — Pergunta Simples

```
Usuário: "ABC123 qual a hora do meu voo?"
         ↓
   [Validação] → [Consulta Voo] → [Clima] → [Transporte] → [RAG] → [LLM] → [Resposta Direta]
         ↓
Agente: "Seu voo LA3456 tem partida às 14h30 de GRU para GIG."
```

### Fluxo Alternativo — Clima sem Código

```
Usuário: "Previsão do tempo em Curitiba"
         ↓
   [Validação: detecta clima direto] → [Consulta Clima CWB] → [Resposta Direta]
         ↓
Agente: "Clima em CWB: 18°C, parcialmente nublado, vento 12 km/h..."
```

### Fluxo com Memória

```
Mensagem 1: "ABC123 meu voo foi cancelado" → armazena ABC123 + destino GIG
Mensagem 2: "qual a previsão do tempo no destino?" → usa GIG da memória
Mensagem 3: "quais meus direitos?" → usa ABC123 da memória
```

## Fontes de Dados

| Fonte | Tipo | Cobertura |
|-------|------|-----------|
| Base de voos (VOOS_DB) | Simulada (fallback) | 6 reservas com 4 status |
| FlightAware AeroAPI | Real (v2.0, opcional) | Voos globais em tempo real |
| Amadeus Flight Status | Real (v2.0, opcional) | Voos globais em tempo real |
| Open-Meteo API | Real (externa) | Clima global, 35+ aeroportos |
| Base de rotas (ROTAS_DB) | Simulada | 8 pares origem-destino |
| Documentos de políticas (PT) | Estática | 14 docs (ANAC 400/2016, CDC, Montreal) |
| Documentos de políticas (EN) | Estática (v2.0) | 3 docs (EU 261, US DOT, Montreal) |
| Documentos de políticas (ES) | Estática (v2.0) | 2 docs (Mercosur, Argentina) |
| Base PNR | Simulada (v3.0) | 4 reservas com itinerário completo |
| Base IATA | Estática (v3.0) | 35+ aeroportos internacionais |

## Modelo de Inteligência

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| Detecção de intenção | Regex (Python re) | Classificar crise vs. pergunta simples |
| Extração de entidades | Regex + heurísticas | Extrair código de reserva e cidades |
| Detecção de idioma | Heurística (v2.0) | Classificar input em PT/EN/ES |
| Busca semântica | TF-IDF + Sentence Transformers | Recuperar políticas relevantes (fallback automático) |
| Geração de linguagem | Llama 3.3 70B (via Groq) | Análise contextual + plano de contingência |
| Orquestração | LangGraph StateGraph | Controle de fluxo entre nós |
| Persistência | SQLite (v1.1) | Sessões, histórico, feedback, analytics |
| Monitoramento | Thread daemon (v2.0) | Notificações proativas de mudança |

## Roadmap

### v1.0 — MVP (Atual)

- [x] Fluxo completo com 8 nós LangGraph
- [x] Ferramentas: voo (simulado), clima (real), transporte (simulado)
- [x] RAG com TF-IDF sobre 10 documentos ANAC
- [x] Geração de plano com LLM (Groq/Llama 3.3)
- [x] Detecção de intenção (crise vs. pergunta simples)
- [x] Memória de sessão (MemorySaver)
- [x] Interface web (Gradio) + CLI
- [x] Consulta de clima por cidade sem código
- [x] Pipeline CI/CD com GitHub Actions
- [x] Documentação completa (README, PRD, product, INSTALLATION)

### v1.1 — Melhorias de UX (Implementado)

- [x] Suporte a múltiplas sessões simultâneas
- [x] Histórico persistente (SQLite)
- [x] Confirmação de ação antes de encerrar (ex: "precisa de mais ajuda?")
- [x] Interface com visualização do grafo em tempo real

### v2.0 — Integração Real (Implementado)

- [x] APIs reais de aviação (FlightAware, Amadeus) com fallback simulado
- [x] Embeddings semânticos (Sentence Transformers) com fallback TF-IDF
- [x] Base de documentos expandida (multilíngue PT/EN/ES)
- [x] Notificações proativas (push quando voo muda de status)
- [x] Integração com WhatsApp / Telegram
- [x] Autenticação e perfil de usuário

### v3.0 — Plataforma (Implementado)

- [x] Multi-tenant (B2B para companhias aéreas)
- [x] Dashboard de analytics (crises mais comuns, tempos de resposta)
- [x] Feedback loop para melhoria contínua do LLM
- [x] Cobertura internacional (IATA — 35+ aeroportos)
- [x] Integração com sistemas de reserva (PNR)

## Métricas do Produto

| Métrica | Definição | Meta v1.0 | Meta v3.0 |
|---------|-----------|-----------|-----------|
| Tempo até resposta | Intervalo entre envio e plano completo | < 15s | < 10s |
| Taxa de validação | % de inputs que passam na validação | > 80% | > 90% |
| Cobertura RAG | % de cenários com documentos relevantes recuperados | > 90% | > 95% |
| Resiliência | % de execuções que entregam resposta mesmo com falha parcial | 100% | 100% |
| Cobertura de testes | % do código-fonte coberto por testes unitários | ≥ 70% | ≥ 80% |
| Satisfação (qualitativa) | Plano gerado é acionável e personalizado | Avaliação manual | Feedback loop ativo |
| Aeroportos cobertos | Total de aeroportos na base IATA | 8 | 35+ |
| Documentos RAG | Total de documentos na base de conhecimento | 10 | 19+ |
| Idiomas suportados | Idiomas dos documentos e detecção | 1 (PT) | 3 (PT/EN/ES) |

## Glossário

| Termo | Definição |
|-------|-----------|
| **ANAC 400** | Resolução nº 400/2016 da Agência Nacional de Aviação Civil |
| **IATA** | International Air Transport Association (códigos de aeroporto) |
| **RAG** | Retrieval-Augmented Generation — geração aumentada por recuperação |
| **TF-IDF** | Term Frequency–Inverse Document Frequency |
| **StateGraph** | Grafo de estados do LangGraph para orquestração de agentes |
| **MemorySaver** | Checkpointer in-memory do LangGraph |
| **DES** | Direitos Especiais de Saque (unidade monetária do FMI) |
| **CI/CD** | Integração Contínua / Entrega Contínua |
| **PNR** | Passenger Name Record — registro de reserva no sistema da companhia |
| **Multi-tenant** | Arquitetura onde múltiplos clientes (companhias) compartilham a plataforma |
| **Adapter Pattern** | Padrão de projeto que permite integração com múltiplos providers |
| **Sentence Transformers** | Modelos de embeddings densos para busca semântica |
| **Webhook** | Callback HTTP acionado por evento externo (mensagem recebida) |
