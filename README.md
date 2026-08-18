# ✈️ Viagem Inteligente — Gestão Automatizada de Crises em Itinerários

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-StateGraph-green.svg)](https://github.com/langchain-ai/langgraph)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-orange.svg)](https://console.groq.com/)
[![License: Academic](https://img.shields.io/badge/license-Academic-lightgrey.svg)](#licença)

> **Repositório:** [https://github.com/wiltonssp/mini-projeto-t2-crise-viagem](https://github.com/wiltonssp/mini-projeto-t2-crise-viagem)

## Visão Geral

Agente inteligente que automatiza a gestão de crises em itinerários de viagem, oferecendo respostas em segundos ao consolidar informações de múltiplas fontes e gerar planos de contingência personalizados.

Desenvolvido como Mini-Projeto do **Módulo 2 — Curso de IA SCTEC**.

## O Problema

Milhões de viajantes enfrentam diariamente atrasos, cancelamentos de voos, condições climáticas extremas e perdas de conexão. O atendimento tradicional das companhias aéreas pode levar horas em filas ou ao telefone, deixando o passageiro sem orientação clara sobre seus direitos, opções de reembolso e rotas alternativas.

## A Solução

Um agente conversacional que:

1. **Detecta** a situação do viajante a partir de linguagem natural
2. **Consulta APIs** para status de voo, clima e transporte alternativo
3. **Recupera políticas** e legislação via RAG (Resolução ANAC 400/2016 + regulamentações internacionais)
4. **Gera planos de contingência** personalizados em Markdown
5. **Responde perguntas simples** (data, hora, clima) diretamente sem plano completo
6. **Mantém memória** da conversa para interações contínuas
7. **Notifica proativamente** sobre mudanças de status (v2.0)
8. **Suporta múltiplos canais** — Web, CLI, WhatsApp, Telegram (v2.0)

## Quick Start

```bash
# 1. Clone o repositório
git clone https://github.com/wiltonssp/mini-projeto-t2-crise-viagem.git
cd mini-projeto-t2-crise-viagem

# 2. Crie ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure a API key
cp .env.example .env
# Edite .env com sua GROQ_API_KEY

# 5. Execute
python main.py web           # Interface Gradio → http://localhost:7860
python main.py cli ABC123 "Meu voo foi cancelado"  # Via terminal
python main.py dashboard     # Dashboard analytics → http://localhost:7861
```

> Para instruções detalhadas de instalação, veja [INSTALLATION.md](INSTALLATION.md).

## Arquitetura do Agente

### Fluxo LangGraph (StateGraph com 8 nós)

```mermaid
graph TD
    START([START]) --> validacao_node
    validacao_node --> check_valido{Entrada válida?}
    check_valido -->|Não| erro_node
    check_valido -->|Sim| consulta_voo_node
    erro_node --> END_ERR([END])
    consulta_voo_node --> consulta_clima_node
    consulta_clima_node --> consulta_transporte_node
    consulta_transporte_node --> rag_node
    rag_node --> analise_llm_node
    analise_llm_node --> gerar_plano_node
    gerar_plano_node --> END_OK([END])
```

### Nós do Grafo

| # | Nó | Função |
|---|-----|--------|
| 1 | `validacao` | Extrai código de reserva, valida formato/domínio, gerencia memória de sessão |
| 2 | `consulta_voo` | Consulta status via adapter (API real ou simulada com fallback) |
| 3 | `consulta_clima` | Consulta API Open-Meteo (temperatura, condição, vento, visibilidade, alertas) |
| 4 | `consulta_transporte` | Busca alternativas (voos, ônibus, trens) ordenadas por duração |
| 5 | `rag` | Recupera políticas e legislação via TF-IDF ou Sentence Transformers |
| 6 | `analise_llm` | Síntese contextual com LLM (identificação de pontos críticos) |
| 7 | `gerar_plano` | Gera plano de contingência ou resposta direta conforme tipo de pergunta |
| 8 | `erro` | Retorna mensagem amigável com orientação ao usuário |

### Estado Compartilhado (TypedDict)

```python
class EstadoCrise(TypedDict):
    messages: Annotated[list, add_messages]  # Histórico do chat
    codigo_reserva: str          # Código validado (6 chars A-Z0-9)
    mensagem_usuario: str        # Descrição da situação
    status_voo: dict             # Dados do voo
    info_clima: dict             # Condições climáticas
    alternativas_transporte: list # Opções de transporte
    politicas_recuperadas: list  # Documentos RAG - políticas
    direitos_passageiro: list    # Documentos RAG - direitos
    relatorio_final: str         # Plano gerado em Markdown
    erros: list                  # Erros registrados
    validacao_ok: bool           # Flag de validação
```

## Stack Tecnológica

| Tecnologia | Função |
|-----------|--------|
| **LangGraph** (StateGraph) | Orquestração do fluxo com controle de nós e arestas |
| **ChatGroq** (Llama 3.3 70B) | LLM para análise e geração de planos |
| **Open-Meteo API** | Clima em tempo real (gratuita, sem API key) |
| **Gradio** | Interface web conversacional + dashboard analytics |
| **scikit-learn** (TF-IDF) | Busca semântica RAG com similaridade cosseno |
| **Sentence Transformers** | Embeddings semânticos multilíngues (v2.0, opcional) |
| **SQLite** | Persistência de sessões, histórico e analytics (v1.1) |
| **LangChain Core** | Tools (@tool) e tipos de mensagem |
| **python-dotenv** | Gerenciamento de variáveis de ambiente |

## Versões

### v1.0 — MVP (Base)
- Fluxo completo com 8 nós LangGraph
- Ferramentas: voo (simulado), clima (real), transporte (simulado)
- RAG com TF-IDF sobre 10 documentos ANAC
- Interface web (Gradio) + CLI
- Memória de sessão (MemorySaver)

### v1.1 — Melhorias de UX
- Suporte a múltiplas sessões simultâneas (thread_id por usuário)
- Histórico persistente em SQLite
- Confirmação pós-atendimento ("Precisa de mais ajuda?")
- Visualização da arquitetura do grafo na interface

### v2.0 — Integração Real
- APIs de aviação (FlightAware, Amadeus) com fallback simulado
- Embeddings semânticos (Sentence Transformers) com fallback TF-IDF
- Base multilíngue (PT/EN/ES) com 19+ documentos
- Notificações proativas de mudança de status
- Integração WhatsApp (Twilio) e Telegram
- Autenticação e perfil de usuário

### v3.0 — Plataforma
- Multi-tenant B2B (planos: Básico, Profissional, Enterprise)
- Dashboard de analytics (`python main.py dashboard`)
- Feedback loop com export para fine-tuning (JSONL)
- Cobertura IATA internacional (35+ aeroportos)
- Integração com sistemas PNR (Passenger Name Record)

## Uso

### Modos de Execução

```bash
python main.py web           # Interface Gradio (padrão)
python main.py cli ABC123 "mensagem"  # Linha de comando
python main.py dashboard     # Dashboard de analytics
```

### Entrada

```
ABC123 Meu voo foi cancelado por mau tempo e vou perder minha conexão para o Rio.
```

- `ABC123` — código de reserva (6 caracteres alfanuméricos)
- Restante — descrição da situação em linguagem natural

### Modos de Resposta

| Tipo de Pergunta | Exemplo | Resposta |
|-----------------|---------|----------|
| **Crise** | "Meu voo foi cancelado" | Plano completo (5 seções) |
| **Pergunta simples** | "Qual a hora do meu voo?" | Resposta direta e concisa |
| **Clima por cidade** | "Previsão do tempo em Curitiba" | Clima direto (sem código) |
| **Clima do destino** | "Tempo no destino?" | Usa destino da memória |

### Exemplo de Plano de Contingência

```markdown
## 1. Diagnóstico da Situação
- Voo LA3456 (GRU → GIG) cancelado por condições meteorológicas adversas.
- Horário original: 14h30. Conexão para o Rio comprometida.

## 2. Direitos do Passageiro
- Resolução ANAC 400 garante assistência material imediata.
- Comunicação gratuita, alimentação após 2h, hospedagem se pernoite.

## 3. Opções de Reembolso
- Reembolso integral em até 7 dias úteis.
- Reacomodação no próximo voo sem custo.

## 4. Rotas Alternativas
- [VOO] Partida: 18:00 | Duração: 1h15min
- [ÔNIBUS] Partida: 16:30 | Duração: 6h00min

## 5. Recomendações Imediatas
- Dirija-se ao balcão para reacomodação.
- Guarde comprovantes para reembolso posterior.
```

## Estrutura do Projeto

```
mini-projeto-t2-crise-viagem/
├── src/
│   ├── __init__.py
│   ├── agente.py                  # Agente principal com StateGraph (8 nós)
│   ├── estado.py                  # TypedDict do estado compartilhado
│   ├── validacao.py               # Validação de entrada
│   ├── persistencia.py            # Gerenciador de sessões SQLite (v1.1)
│   ├── autenticacao.py            # Autenticação e perfis (v2.0)
│   ├── notificacoes.py            # Notificações proativas (v2.0)
│   ├── multitenant.py             # Arquitetura multi-tenant B2B (v3.0)
│   ├── feedback.py                # Feedback loop para LLM (v3.0)
│   ├── ferramentas/
│   │   ├── __init__.py
│   │   ├── voo.py                 # Status de voo (base simulada)
│   │   ├── voo_api.py             # Adapters FlightAware/Amadeus (v2.0)
│   │   ├── clima.py               # Clima via Open-Meteo API
│   │   ├── transporte.py          # Transporte alternativo (base simulada)
│   │   ├── aeroportos.py          # Base IATA internacional (v3.0)
│   │   └── pnr.py                 # Integração PNR (v3.0)
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── documentos.py          # Base de políticas (10 docs PT)
│   │   ├── documentos_multilingual.py  # Base expandida PT/EN/ES (v2.0)
│   │   ├── busca.py               # Busca TF-IDF + cosseno
│   │   └── embeddings.py          # Sentence Transformers (v2.0)
│   └── interface/
│       ├── __init__.py
│       ├── gradio_app.py          # Interface web (multi-sessão, v1.1)
│       ├── cli.py                 # Interface CLI
│       ├── dashboard.py           # Dashboard analytics (v3.0)
│       └── messaging.py           # WhatsApp/Telegram (v2.0)
├── tests/                          # 107 testes unitários
├── data/                           # Bancos SQLite (auto-criados, gitignored)
├── docs/
│   └── Prompts/                   # Prompts documentados
├── .github/workflows/ci.yml       # Pipeline CI
├── .env.example                   # Template de variáveis
├── requirements.txt               # Dependências
├── main.py                         # Entry point (web/cli/dashboard)
├── INSTALLATION.md                # Guia de instalação
├── PRD.md                         # Product Requirements Document
└── product.md                     # Visão do produto e roadmap
```

## Decisões de Design

### Adapter Pattern com Fallback
- Todos os providers (aviação, PNR, mensageria) implementam interfaces abstratas
- Se nenhuma API key real estiver configurada, usa dados simulados automaticamente
- Zero breaking changes ao adicionar novos providers

### Persistência SQLite (v1.1)
- Thread-safe com `threading.Lock()`
- Criação automática de tabelas na primeira execução
- Diretório `data/` no `.gitignore`

### Embeddings com Fallback (v2.0)
- Se `sentence-transformers` não instalado, usa TF-IDF transparentemente
- Modelo multilíngue pré-selecionado para cobertura PT/EN/ES
- Reutilização global do modelo carregado (singleton)

### Multi-tenant (v3.0)
- Planos com funcionalidades escalonadas
- Isolamento por `tenant_id` em todas as tabelas
- Tracking de uso (mensagens, tokens) para cobrança futura

## Códigos de Reserva para Testes

| Código | Voo | Origem | Destino | Status | Motivo |
|--------|-----|--------|---------|--------|--------|
| `ABC123` | LA3456 | GRU | GIG | Cancelado | Condições meteorológicas adversas |
| `DEF456` | G3 1020 | BSB | SSA | Atrasado | Manutenção não programada (2h) |
| `GHI789` | AD4512 | CNF | GRU | Confirmado | N/A |
| `JKL012` | LA1234 | GIG | BSB | Embarcando | N/A |
| `MNO345` | G3 2078 | CWB | POA | Cancelado | Neblina intensa no destino |
| `XYZ789` | LA5678 | GRU | GIG | Atrasado | Conexão perdida em BSB |

### Exemplos de teste rápido

```
ABC123 Meu voo foi cancelado por mau tempo e vou perder minha conexão para o Rio.
DEF456 Estou no aeroporto de Brasília e meu voo atrasou mais de 4 horas.
MNO345 Meu voo está cancelado por neblina e preciso chegar a Porto Alegre urgente.
GHI789 qual a data e hora do meu voo?
XYZ789 quais meus direitos por atraso?
Previsão do tempo em Curitiba
```

## Testes

```bash
# Executar todos os testes (107 testes)
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=src --cov-report=term-missing -v

# Teste específico
pytest tests/test_validacao.py -v
```

## Configuração de APIs (Opcional)

Para habilitar integrações reais, configure no `.env`:

```env
# Obrigatório
GROQ_API_KEY=sua_chave_groq

# APIs de Aviação (opcional — fallback: dados simulados)
FLIGHTAWARE_API_KEY=sua_chave
AMADEUS_CLIENT_ID=seu_id
AMADEUS_CLIENT_SECRET=seu_secret

# Mensageria (opcional)
TWILIO_ACCOUNT_SID=sid
TWILIO_AUTH_TOKEN=token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
TELEGRAM_BOT_TOKEN=token_do_bot
```

## Documentação Adicional

- [INSTALLATION.md](INSTALLATION.md) — Guia completo de instalação e configuração
- [PRD.md](PRD.md) — Product Requirements Document
- [product.md](product.md) — Visão do produto e roadmap
- [docs/Prompts/](docs/Prompts/) — Prompts e decisões técnicas documentadas

## Autor

**Wilton Pereira** — [GitHub](https://github.com/wiltonssp/mini-projeto-t2-crise-viagem)

## Licença

Projeto acadêmico desenvolvido para o Módulo 2 (Projeto Avaliativo) do curso de IA SCTEC.
