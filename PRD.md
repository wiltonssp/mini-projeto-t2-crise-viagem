# Product Requirements Document (PRD)

## Viagem Inteligente — Gestão Automatizada de Crises em Itinerários

> **Repositório:** [https://github.com/wiltonssp/mini-projeto-t2-crise-viagem](https://github.com/wiltonssp/mini-projeto-t2-crise-viagem)

---

## 1. Resumo Executivo

| Campo | Descrição |
|-------|-----------|
| **Produto** | Agente de Gestão de Crises em Itinerários de Viagem |
| **Versão** | 3.0.0 |
| **Contexto** | Mini-Projeto — Módulo 2 do Curso de IA SCTEC |
| **Autor** | Wilton Pereira |
| **Data** | Agosto/2026 |
| **Status** | Implementado (v1.0 a v3.0) |
| **Repositório** | [github.com/wiltonssp/mini-projeto-t2-crise-viagem](https://github.com/wiltonssp/mini-projeto-t2-crise-viagem) |

## 2. Declaração do Problema

### Contexto

Viajantes enfrentam situações de crise (cancelamentos, atrasos, condições climáticas adversas, perda de conexões) com frequência. O atendimento tradicional das companhias aéreas envolve:

- Filas de horas em balcões de atendimento
- Espera prolongada em call centers
- Falta de informação consolidada sobre direitos e alternativas
- Desconhecimento da legislação aplicável (Resolução ANAC 400/2016)

### Impacto

- Passageiros ficam sem orientação em momentos críticos
- Desconhecem seus direitos legais
- Perdem oportunidades de reacomodação por falta de informação rápida
- Acumulam prejuízos financeiros e emocionais desnecessários

## 3. Objetivo do Produto

Desenvolver um agente conversacional inteligente que responde em segundos, consolidando automaticamente:

- Status do voo em tempo real
- Condições climáticas no destino
- Opções de transporte alternativo
- Políticas da companhia e legislação de direitos do passageiro
- Plano de contingência personalizado com ações imediatas

## 4. Público-Alvo

| Persona | Descrição | Necessidade Principal |
|---------|-----------|----------------------|
| **Viajante em crise** | Passageiro com voo cancelado/atrasado | Plano de ação rápido com direitos e alternativas |
| **Viajante informativo** | Passageiro verificando dados do voo | Resposta direta sobre horário, destino, clima |
| **Avaliador acadêmico** | Professor/avaliador do curso | Demonstração de competência em LangGraph e agentes IA |

## 5. Requisitos Funcionais

### RF-01: Validação de Entrada

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-01.1 | Extrair código de reserva (6 chars A-Z0-9) da mensagem | Must | ✅ Implementado |
| RF-01.2 | Validar tamanho da mensagem (10-2000 caracteres) | Must | ✅ Implementado |
| RF-01.3 | Verificar domínio (palavras-chave de viagem) | Must | ✅ Implementado |
| RF-01.4 | Rejeitar palavras comuns de 6 letras como código falso | Must | ✅ Implementado |
| RF-01.5 | Retornar mensagem amigável quando validação falha | Must | ✅ Implementado |

### RF-02: Consulta de Status de Voo

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-02.1 | Consultar voo por código de reserva | Must | ✅ Implementado |
| RF-02.2 | Retornar: número, origem, destino, horários, status, motivo | Must | ✅ Implementado |
| RF-02.3 | Informar quando reserva não é encontrada | Must | ✅ Implementado |

### RF-03: Consulta Climática

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-03.1 | Consultar clima no aeroporto de destino (API Open-Meteo) | Must | ✅ Implementado |
| RF-03.2 | Retornar: temperatura, condição, vento, visibilidade | Must | ✅ Implementado |
| RF-03.3 | Detectar e alertar condições adversas (tempestade, neblina, ventos fortes) | Must | ✅ Implementado |
| RF-03.4 | Permitir consulta por nome de cidade sem código de reserva | Should | ✅ Implementado |
| RF-03.5 | Usar destino da memória quando usuário menciona "destino" | Should | ✅ Implementado |

### RF-04: Transporte Alternativo

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-04.1 | Buscar opções entre origem e destino (voo, ônibus, trem) | Must | ✅ Implementado |
| RF-04.2 | Ordenar por duração de viagem | Must | ✅ Implementado |
| RF-04.3 | Limitar a 10 opções no máximo | Should | ✅ Implementado |

### RF-05: Recuperação de Políticas (RAG)

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-05.1 | Manter base de 10 documentos sobre ANAC 400/2016 | Must | ✅ Implementado |
| RF-05.2 | Busca semântica TF-IDF com similaridade cosseno | Must | ✅ Implementado |
| RF-05.3 | Retornar top-5 documentos mais relevantes | Must | ✅ Implementado |
| RF-05.4 | Separar políticas de empresa e direitos do passageiro | Should | ✅ Implementado |
| RF-05.5 | Limiar configurável de relevância (default: 0.1) | Should | ✅ Implementado |

### RF-06: Geração do Plano de Contingência

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-06.1 | Gerar plano com 5 seções obrigatórias em Markdown | Must | ✅ Implementado |
| RF-06.2 | Referenciar dados específicos do viajante em ≥3 seções | Must | ✅ Implementado |
| RF-06.3 | Indicar seções com dados indisponíveis | Must | ✅ Implementado |
| RF-06.4 | Usar linguagem clara, sem jargão (≤30 palavras/frase) | Should | ✅ Implementado |

### RF-07: Detecção de Intenção

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-07.1 | Distinguir pergunta simples de situação de crise | Must | ✅ Implementado |
| RF-07.2 | Responder direto para perguntas informativas (hora, data, clima) | Must | ✅ Implementado |
| RF-07.3 | Gerar plano completo apenas para crises | Must | ✅ Implementado |
| RF-07.4 | Solicitar código quando pergunta sobre voo sem código | Must | ✅ Implementado |

### RF-08: Memória de Sessão

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-08.1 | Persistir código de reserva entre interações da mesma sessão | Must | ✅ Implementado |
| RF-08.2 | Persistir destino para consultas de clima subsequentes | Must | ✅ Implementado |
| RF-08.3 | Usar MemorySaver com thread_id fixo por sessão | Must | ✅ Implementado |

### RF-09: Interfaces

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-09.1 | Interface web com Gradio (ChatInterface) | Must | ✅ Implementado |
| RF-09.2 | Interface CLI para execução via terminal | Must | ✅ Implementado |
| RF-09.3 | Exemplos de uso na interface web | Should | ✅ Implementado |

### RF-10: CI/CD

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-10.1 | Pipeline de lint automatizado (ruff) | Should | ✅ Implementado |
| RF-10.2 | Testes unitários com cobertura mínima de 70% | Should | ✅ Implementado |
| RF-10.3 | Validação de documentação no pipeline | Should | ✅ Implementado |

### RF-11: Multi-Sessão e Persistência (v1.1)

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-11.1 | Thread_id único por sessão de navegador | Must | ✅ Implementado |
| RF-11.2 | Histórico de mensagens persistido em SQLite | Must | ✅ Implementado |
| RF-11.3 | Isolamento de memória entre sessões simultâneas | Must | ✅ Implementado |
| RF-11.4 | Confirmação pós-atendimento em toda resposta | Should | ✅ Implementado |
| RF-11.5 | Visualização da arquitetura do grafo na interface | Should | ✅ Implementado |

### RF-12: Integrações Reais (v2.0)

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-12.1 | Adapter para FlightAware com fallback simulado | Should | ✅ Implementado |
| RF-12.2 | Adapter para Amadeus com fallback simulado | Should | ✅ Implementado |
| RF-12.3 | Embeddings semânticos (Sentence Transformers) | Should | ✅ Implementado |
| RF-12.4 | Base multilíngue PT/EN/ES | Should | ✅ Implementado |
| RF-12.5 | Notificações proativas de mudança de status | Should | ✅ Implementado |
| RF-12.6 | Integração WhatsApp via Twilio | Could | ✅ Implementado |
| RF-12.7 | Integração Telegram via Bot API | Could | ✅ Implementado |
| RF-12.8 | Autenticação com login/registro | Could | ✅ Implementado |

### RF-13: Plataforma (v3.0)

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-13.1 | Multi-tenant com planos escalonados | Could | ✅ Implementado |
| RF-13.2 | Dashboard de analytics com métricas | Could | ✅ Implementado |
| RF-13.3 | Feedback loop com categorização automática | Could | ✅ Implementado |
| RF-13.4 | Export de dataset para fine-tuning (JSONL) | Could | ✅ Implementado |
| RF-13.5 | Base IATA internacional (35+ aeroportos) | Could | ✅ Implementado |
| RF-13.6 | Integração PNR com dados de reserva | Could | ✅ Implementado |

## 6. Requisitos Não-Funcionais

### RNF-01: Desempenho

| ID | Requisito | Meta |
|----|-----------|------|
| RNF-01.1 | Tempo de resposta para perguntas simples | < 5s |
| RNF-01.2 | Tempo de resposta para plano completo | < 15s |
| RNF-01.3 | Timeout para API Open-Meteo | 10s |

### RNF-02: Resiliência

| ID | Requisito |
|----|-----------|
| RNF-02.1 | Cada nó com try/except individual — falha não interrompe fluxo |
| RNF-02.2 | Erros registrados no estado compartilhado |
| RNF-02.3 | Plano gerado com dados parciais quando fonte falha |
| RNF-02.4 | Indicação explícita de seções com dados indisponíveis |

### RNF-03: Segurança

| ID | Requisito |
|----|-----------|
| RNF-03.1 | API key protegida em .env (nunca versionada) |
| RNF-03.2 | Validação de variáveis obrigatórias antes de qualquer chamada |
| RNF-03.3 | Agente limitado a consultas (somente leitura) |
| RNF-03.4 | .gitignore protege .env, __pycache__, venv/ |

### RNF-04: Usabilidade

| ID | Requisito |
|----|-----------|
| RNF-04.1 | Mensagens de erro amigáveis com orientação de correção |
| RNF-04.2 | Exemplos de uso na interface |
| RNF-04.3 | Resposta em português do Brasil |

### RNF-05: Qualidade de Código

| ID | Requisito |
|----|-----------|
| RNF-05.1 | Linter ruff sem erros no código-fonte |
| RNF-05.2 | Testes unitários cobrindo ≥70% do código |
| RNF-05.3 | Documentação completa (README, PRD, product, INSTALLATION) |
| RNF-05.4 | Código modular com separação de responsabilidades |

## 7. Escopo e Limitações Conhecidas

### Dentro do Escopo (v1.0 — v3.0)

- 6 voos simulados com diferentes status + adapter para APIs reais
- 35+ aeroportos internacionais com coordenadas e fusos horários
- 8 rotas de transporte alternativo
- 19+ documentos de políticas/legislação (PT/EN/ES)
- Sessões persistentes com SQLite e histórico completo
- Interface web multi-sessão, CLI e Dashboard de analytics
- Integração com WhatsApp e Telegram
- Pipeline CI/CD com GitHub Actions
- Multi-tenant B2B com planos escalonados
- Feedback loop com export para fine-tuning
- Sistema PNR com dados completos de reserva

### Fora do Escopo Atual

- Deploy em produção com balanceamento de carga
- Fine-tuning real do modelo LLM (infraestrutura preparada, execução pendente)
- Integração com GDS (Sabre, Travelport) — apenas Amadeus implementado
- App mobile nativo
- Voz (speech-to-text/text-to-speech)

## 8. Métricas de Sucesso

| Métrica | Critério de Aceite | Status |
|---------|-------------------|--------|
| Validação de entrada | Rejeita inputs inválidos corretamente | ✅ |
| Detecção de intenção | Classifica crise vs. pergunta simples com acurácia | ✅ |
| Memória de sessão | Reutiliza código de reserva sem re-solicitar | ✅ |
| Resiliência | Gera plano mesmo com falha parcial de fontes | ✅ |
| Tempo de resposta | Plano completo em < 15s com LLM remoto | ✅ |
| Cobertura RAG | Recupera documentos relevantes para cenários de crise | ✅ |
| Cobertura de testes | ≥70% do código-fonte coberto | ✅ |

## 9. Dependências Externas

| Serviço | Tipo | SLA/Disponibilidade | Fallback |
|---------|------|---------------------|----------|
| Groq API | LLM remoto | Alta (free tier limitado) | Erro informado ao usuário |
| Open-Meteo | Clima | Alta (API pública) | Seção de clima marcada como indisponível |
| FlightAware (v2.0) | Status de voo | Alta (API paga) | Base simulada VOOS_DB |
| Amadeus (v2.0) | Status/PNR | Alta (API freemium) | Base simulada |
| Twilio (v2.0) | WhatsApp | Alta (API paga) | Canal não disponível |
| Telegram Bot (v2.0) | Messaging | Alta (API gratuita) | Canal não disponível |
| SQLite (v1.1) | Persistência | 100% (local) | MemorySaver in-memory |
| GitHub Actions | CI/CD | Alta | Execução local de lint e testes |

## 10. Cronograma

| Fase | Entregável | Status |
|------|-----------|--------|
| Fase 1 | Estrutura base + StateGraph | ✅ Concluído |
| Fase 2 | Ferramentas (voo, clima, transporte) | ✅ Concluído |
| Fase 3 | RAG (documentos + busca TF-IDF) | ✅ Concluído |
| Fase 4 | Geração de plano via LLM | ✅ Concluído |
| Fase 5 | Detecção de intenção + resposta direta | ✅ Concluído |
| Fase 6 | Memória de sessão | ✅ Concluído |
| Fase 7 | Interfaces (Gradio + CLI) | ✅ Concluído |
| Fase 8 | Testes, CI/CD e documentação | ✅ Concluído |
| Fase 9 | v1.1 — Multi-sessão, SQLite, UX | ✅ Concluído |
| Fase 10 | v2.0 — APIs reais, embeddings, messaging | ✅ Concluído |
| Fase 11 | v3.0 — Multi-tenant, analytics, PNR | ✅ Concluído |
