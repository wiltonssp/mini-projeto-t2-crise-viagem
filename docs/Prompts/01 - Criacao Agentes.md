# Documentação de Prompts — Agente de Gestão de Crises em Itinerários

---

## 1. Prompt Principal de Criação do Agente

Este é o prompt completo utilizado para solicitar ao Kiro a criação do agente, contendo todos os requisitos funcionais e técnicos:

```text
Crie um agente inteligente em Python utilizando LangGraph para Gestão Automatizada de Crises em Itinerários de Viagem.

## Problema
Viajantes enfrentam atrasos, cancelamentos de voos, condições climáticas extremas e perdas de conexão. O atendimento tradicional pode levar horas. O agente deve resolver isso em segundos.

## Objetivo
Desenvolver um agente funcional, demonstrável e documentado que automatize a gestão de crises de viagem, capaz de:
- Detectar automaticamente a situação do viajante a partir de linguagem natural
- Consultar informações em tempo real (status de voos, clima via Open-Meteo API, transporte alternativo)
- Recuperar políticas internas e legislação aplicável via RAG (Resolução ANAC 400/2016)
- Gerar um plano de contingência personalizado em formato Markdown
- Responder perguntas simples diretamente (data/hora do voo, previsão do tempo) sem gerar plano completo

## Entrada
- Código da reserva: 6 caracteres alfanuméricos (ex: ABC123)
- Mensagem do usuário em linguagem natural (ex: "Meu voo foi cancelado por mau tempo e vou perder minha conexão")
- Consultas de previsão do tempo podem ser feitas por nome de cidade sem código de reserva

## Saída
- Para situações de CRISE: Relatório completo em Markdown com 5 seções:
  1. Diagnóstico da Situação
  2. Direitos do Passageiro
  3. Opções de Reembolso
  4. Rotas Alternativas
  5. Recomendações Imediatas
- Para PERGUNTAS SIMPLES: Resposta direta e concisa apenas com a informação solicitada

## Arquitetura com LangGraph (StateGraph)

### Fluxo do Grafo (8 nós):
START → validacao_node → [aresta condicional]
  ├─ inválido → erro_node → END
  └─ válido → consulta_voo_node → consulta_clima_node → consulta_transporte_node → rag_node → analise_llm_node → gerar_plano_node → END

### Estado Compartilhado (TypedDict):
- messages: Annotated[list, add_messages] — histórico de mensagens
- codigo_reserva: str — código de reserva validado
- mensagem_usuario: str — descrição da crise
- dados_cliente: dict — informações do cliente
- status_voo: dict — resultado da consulta de voo
- info_clima: dict — condições climáticas
- alternativas_transporte: list — opções de transporte
- politicas_recuperadas: list — documentos RAG de políticas
- direitos_passageiro: list — documentos RAG de direitos
- relatorio_final: str — plano de contingência gerado
- erros: list — erros registrados durante execução
- validacao_ok: bool — flag de validação aprovada

## Ferramentas (@tool)
1. consultar_status_voo(codigo_reserva) — base simulada com 6+ voos em diferentes status
2. consultar_clima(codigo_aeroporto) — API Open-Meteo real (gratuita, sem key), 8 aeroportos BR
3. consultar_transporte_alternativo(origem, destino) — base simulada com 8+ rotas

## RAG
- Base de 10 documentos sobre legislação brasileira (ANAC 400/2016): reembolso, reacomodação, assistência material, compensação, direitos em cancelamento, overbooking, bagagem, condições meteorológicas
- Busca semântica com TF-IDF (scikit-learn) + similaridade cosseno
- Limiar configurável de relevância

## Memória e Contexto
- MemorySaver como checkpointer para persistir estado entre interações
- Thread_id fixo por sessão para manter continuidade da conversa
- Se o usuário já informou o código de reserva, as mensagens seguintes devem reutilizar esse código automaticamente
- Consultas de clima que mencionam "no destino" devem usar o destino armazenado na memória

## Inteligência na Resposta
- Detectar se a mensagem é uma PERGUNTA SIMPLES (data, hora, destino, clima) → responder direto
- Detectar se a mensagem é uma SITUAÇÃO DE CRISE (cancelamento, atraso, perda de conexão) → gerar plano completo
- Se o usuário pergunta sobre voo sem informar código e não há código na memória → solicitar o código educadamente
- Consultas de previsão do tempo por nome de cidade/aeroporto não exigem código de reserva

## Validação de Entrada
- Código de reserva: exatamente 6 caracteres A-Z0-9
- Mensagem: 10-2000 caracteres não-espaço
- Domínio: verificar palavras-chave de viagem (voo, aeroporto, reserva, clima, etc.)
- Rejeitar palavras comuns de 6 letras que não são códigos (QUANDO, PORQUE, etc.)

## Segurança
- GROQ_API_KEY protegida em .env (nunca versionada)
- .gitignore com: .env, __pycache__/, *.pyc, .venv/, venv/
- .env.example com nomes de variáveis sem valores reais
- Validação de variáveis obrigatórias antes de qualquer chamada a API
- Agente limitado a consultas — não executa operações de escrita

## Resiliência
- Cada nó com try/except individual
- Erros registrados no estado sem interromper o fluxo
- Plano gerado com dados parciais quando alguma fonte falha
- Indicação explícita de seções com informações indisponíveis

## Interfaces
- Interface web com Gradio (ChatInterface) em http://localhost:7860
- Interface CLI: python main.py cli <codigo> <mensagem>
- Exemplos de uso na interface Gradio

## Estrutura de Diretórios
projeto/
├── src/
│   ├── agente.py (grafo principal)
│   ├── estado.py (TypedDict)
│   ├── validacao.py (validação de entrada)
│   ├── ferramentas/ (voo.py, clima.py, transporte.py)
│   ├── rag/ (documentos.py, busca.py)
│   └── interface/ (gradio_app.py, cli.py)
├── docs/prompts.md
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── main.py

## Stack Tecnológica
- Python 3.10+
- LangGraph (StateGraph, MemorySaver, conditional_edges)
- LangChain (ChatGroq com llama-3.3-70b-versatile, @tool, messages)
- Groq API (GROQ_API_KEY)
- Gradio 4+ (ChatInterface)
- scikit-learn (TfidfVectorizer, cosine_similarity)
- requests (Open-Meteo API)
- python-dotenv

## Requisitos de Documentação
- README.md completo com: problema, objetivo, fluxo, ferramentas, execução, entrada/saída, decisões, limitações
- docs/prompts.md com todos os system prompts documentados
- Commits semânticos (feat:, fix:, docs:, refactor:, chore:)
```

---

## 2. System Prompts Internos do Agente

### 2.1 `analise_llm_node` — Análise Contextual

**Arquivo:** `src/agente.py`

**Propósito:** Enviar todos os dados coletados (voo, clima, transporte, RAG) à LLM para preparar uma síntese analítica que fundamenta o plano de contingência.

**System Prompt:**

```text
Você é um assistente especializado em gestão de crises de itinerários de viagem. Analise os dados coletados sobre a situação do viajante e prepare uma síntese para a geração do plano de contingência. Identifique os pontos críticos, os direitos aplicáveis e as melhores alternativas. Responda em português do Brasil de forma clara e objetiva.
```

---

### 2.2 `gerar_plano_node` — Geração do Plano de Contingência (Modo Crise)

**Arquivo:** `src/agente.py`

**Propósito:** Gerar o plano de contingência completo com 5 seções obrigatórias quando a situação envolve uma crise real (cancelamento, atraso, perda de conexão).

**System Prompt:**

```text
Você é um assistente especializado em gestão de crises de itinerários de viagem. Gere um plano de contingência personalizado em formato Markdown. O plano DEVE conter exatamente estas 5 seções com os cabeçalhos abaixo:
## 1. Diagnóstico da Situação
## 2. Direitos do Passageiro
## 3. Opções de Reembolso
## 4. Rotas Alternativas
## 5. Recomendações Imediatas

REGRAS OBRIGATÓRIAS:
- Escreva em português do Brasil.
- Use linguagem clara, sem jargão técnico.
- Cada frase deve ter no máximo 30 palavras.
- Referencie dados específicos do viajante (número do voo, destino, horários, condições) em pelo menos 3 das 5 seções.
- Se alguma informação estiver indisponível, indique explicitamente na seção correspondente que os dados não puderam ser obtidos.
- Use bullet points para facilitar a leitura.
- NÃO inclua cabeçalho de nível 1 (# título). Comece direto com as seções ##.
```

---

### 2.3 `_gerar_resposta_direta` — Resposta Direta (Modo Pergunta Simples)

**Arquivo:** `src/agente.py`

**Propósito:** Responder de forma direta e concisa quando o usuário faz uma pergunta informativa simples (data do voo, previsão do tempo, destino), sem gerar o plano completo de 5 seções.

**System Prompt:**

```text
Você é um assistente de viagens. O usuário fez uma pergunta simples sobre seu voo ou itinerário. Responda APENAS o que foi perguntado, de forma direta e concisa. Use os dados disponíveis abaixo.

REGRAS:
- Responda em português do Brasil.
- Seja direto — responda SOMENTE o que foi perguntado.
- NÃO gere um plano de contingência completo.
- NÃO inclua seções ## ou cabeçalhos.
- Se a informação solicitada não estiver disponível, diga claramente.
- Formate de forma limpa e legível.
```

---

## 3. Prompts de Ferramentas (@tool)

### 3.1 `consultar_status_voo`

**Docstring (usada pelo LLM para decidir quando chamar):**

```text
Consulta o status de um voo pelo código de reserva.
Retorna informações completas do voo incluindo número, origem, destino,
horários de partida e chegada, status atual e motivo de alteração.
```

### 3.2 `consultar_clima`

**Docstring:**

```text
Consulta condições climáticas atuais e previsão 24h para um aeroporto.
Usa API gratuita Open-Meteo. Retorna: temperatura, condição, vento,
visibilidade e alertas de condições adversas.
```

### 3.3 `consultar_transporte_alternativo`

**Docstring:**

```text
Busca opções de transporte alternativo entre origem e destino.
Retorna opções ordenadas por tempo de viagem (voos, ônibus, trens).
```

---

## 4. Notas Técnicas sobre os Prompts

- Todos os system prompts são enviados como `SystemMessage` do LangChain, seguidos de `HumanMessage` com dados contextuais
- O modelo utilizado é `llama-3.3-70b-versatile` via ChatGroq com `temperature=0.3`
- A decisão entre resposta direta vs. plano completo é feita em código (regex) antes de chamar o LLM, otimizando o prompt enviado
- O `analise_llm_node` executa antes do `gerar_plano_node`, fornecendo análise adicional nos messages do estado
- Todos os dados contextuais são formatados como texto estruturado no `HumanMessage` para melhor compreensão pelo LLM
