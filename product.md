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
| **Memória** | MemorySaver com thread_id — estado persiste entre mensagens |
| **Detecção inteligente** | Regex determina resposta direta vs. plano completo (sem custo LLM) |
| **RAG leve** | TF-IDF + cosseno — zero dependência de embeddings externos |
| **Resiliência** | Try/except por nó — falha parcial nunca bloqueia o fluxo |
| **CI/CD** | GitHub Actions com lint, testes e validação de documentação |

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
| Base de voos (VOOS_DB) | Simulada | 6 reservas com 4 status |
| Open-Meteo API | Real (externa) | Clima global, foco em 8 aeroportos BR |
| Base de rotas (ROTAS_DB) | Simulada | 8 pares origem-destino |
| Documentos de políticas | Estática | 10 docs sobre ANAC 400/2016 |

## Modelo de Inteligência

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| Detecção de intenção | Regex (Python re) | Classificar crise vs. pergunta simples |
| Extração de entidades | Regex + heurísticas | Extrair código de reserva e cidades |
| Busca semântica | TF-IDF + cosseno (scikit-learn) | Recuperar políticas relevantes |
| Geração de linguagem | Llama 3.3 70B (via Groq) | Análise contextual + plano de contingência |
| Orquestração | LangGraph StateGraph | Controle de fluxo entre nós |

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

### v1.1 — Melhorias de UX (Planejado)

- [ ] Suporte a múltiplas sessões simultâneas
- [ ] Histórico persistente (SQLite/Redis)
- [ ] Confirmação de ação antes de encerrar (ex: "precisa de mais ajuda?")
- [ ] Interface com visualização do grafo em tempo real

### v2.0 — Integração Real (Futuro)

- [ ] APIs reais de aviação (FlightAware, Amadeus, Cirium)
- [ ] Embeddings semânticos (Sentence Transformers / OpenAI)
- [ ] Base de documentos expandida (multilíngue)
- [ ] Notificações proativas (push quando voo muda de status)
- [ ] Integração com WhatsApp / Telegram
- [ ] Autenticação e perfil de usuário

### v3.0 — Plataforma (Visão)

- [ ] Multi-tenant (B2B para companhias aéreas)
- [ ] Dashboard de analytics (crises mais comuns, tempos de resposta)
- [ ] Feedback loop para melhoria contínua do LLM
- [ ] Cobertura internacional (IATA completa)
- [ ] Integração com sistemas de reserva (PNR)

## Métricas do Produto

| Métrica | Definição | Meta v1.0 |
|---------|-----------|-----------|
| Tempo até resposta | Intervalo entre envio e plano completo | < 15s |
| Taxa de validação | % de inputs que passam na validação | > 80% (inputs válidos) |
| Cobertura RAG | % de cenários com documentos relevantes recuperados | > 90% |
| Resiliência | % de execuções que entregam resposta mesmo com falha parcial | 100% |
| Cobertura de testes | % do código-fonte coberto por testes unitários | ≥ 70% |
| Satisfação (qualitativa) | Plano gerado é acionável e personalizado | Avaliação manual |

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
