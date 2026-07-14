# Documentação de Prompts — Geração de Documentação do Projeto

---

## 1. Prompt de Geração da Documentação

Este é o prompt utilizado para solicitar ao Kiro a criação e atualização dos documentos de projeto seguindo padrões profissionais.

```text
Analise a estrutura do Agente e atualize README.md, crie INSTALLATION.md, PRD.md e product.md conforme os padroes de projetos
```

---

## 2. Documentos Gerados

### 2.1 README.md (Atualizado)

**Propósito:** Documento principal do repositório com visão geral completa do projeto.

**Estrutura gerada:**
- Badges (Python, LangGraph, Groq, License)
- Visão Geral
- O Problema / A Solução
- Quick Start (instalação rápida em 5 passos)
- Arquitetura do Agente (diagrama Mermaid + tabela de nós)
- Estado Compartilhado (TypedDict)
- Stack Tecnológica
- Uso (entrada, modos de resposta, exemplo de plano)
- Funcionalidades Inteligentes
- Estrutura do Projeto (árvore de diretórios)
- Decisões de Design
- Limitações (com sugestão de evolução)
- Códigos de Reserva para Testes
- Testes
- Documentação Adicional (links)
- Licença

---

### 2.2 INSTALLATION.md (Criado)

**Propósito:** Guia detalhado de instalação e configuração para diferentes sistemas operacionais.

**Estrutura gerada:**
- Pré-requisitos (tabela com versões mínimas)
- Passo 1: Obter o Código
- Passo 2: Criar Ambiente Virtual (Windows CMD, PowerShell, Linux/Mac)
- Passo 3: Instalar Dependências (tabela de pacotes)
- Passo 4: Configurar Variáveis de Ambiente (obtenção da GROQ_API_KEY)
- Passo 5: Executar o Agente (web e CLI)
- Verificação da Instalação (script de validação)
- Solução de Problemas (troubleshooting dos erros mais comuns)
- Estrutura de Configuração
- Portas Utilizadas
- Requisitos de Sistema

---

### 2.3 PRD.md (Criado)

**Propósito:** Product Requirements Document formal com requisitos funcionais e não-funcionais.

**Estrutura gerada:**
- Resumo Executivo (tabela de metadados)
- Declaração do Problema (contexto e impacto)
- Objetivo do Produto
- Público-Alvo (personas)
- Requisitos Funcionais (RF-01 a RF-09 com IDs e prioridades Must/Should)
  - RF-01: Validação de Entrada
  - RF-02: Consulta de Status de Voo
  - RF-03: Consulta Climática
  - RF-04: Transporte Alternativo
  - RF-05: Recuperação de Políticas (RAG)
  - RF-06: Geração do Plano de Contingência
  - RF-07: Detecção de Intenção
  - RF-08: Memória de Sessão
  - RF-09: Interfaces
- Requisitos Não-Funcionais (RNF-01 a RNF-04)
  - RNF-01: Desempenho
  - RNF-02: Resiliência
  - RNF-03: Segurança
  - RNF-04: Usabilidade
- Escopo e Limitações Conhecidas
- Métricas de Sucesso
- Dependências Externas
- Cronograma (8 fases)

---

### 2.4 product.md (Criado)

**Propósito:** Visão do produto com roadmap e estratégia de evolução.

**Estrutura gerada:**
- Identidade (nome, tipo, domínio, plataforma)
- Proposta de Valor
- Visão de Longo Prazo
- Princípios do Produto (5 princípios)
- Arquitetura Conceitual (diagrama ASCII)
- Diferenciais Técnicos
- Fluxos de Uso (Principal, Pergunta Simples, Clima sem Código, Com Memória)
- Fontes de Dados
- Modelo de Inteligência (5 camadas)
- Roadmap (v1.0 MVP ✅, v1.1 UX, v2.0 Integração Real, v3.0 Plataforma)
- Métricas do Produto
- Glossário

---

## 3. Prompt de Adição de Códigos de Teste

```text
Coloque no README.md a relação de todos os numeros de voo para facilitar os testes.
```

**Resultado:** Seção "Códigos de Reserva para Testes" adicionada ao README.md com:
- Tabela completa dos 6 voos (código, número, origem, destino, status, motivo)
- Exemplos de mensagens prontas para copiar e testar

---

## 4. Padrões Seguidos

| Padrão | Aplicação |
|--------|-----------|
| Markdown com badges | README.md (shields.io) |
| Tabelas para dados estruturados | Todos os documentos |
| Diagramas Mermaid | Arquitetura no README.md |
| IDs únicos para requisitos | PRD.md (RF-XX.Y, RNF-XX.Y) |
| Priorização MoSCoW | PRD.md (Must/Should) |
| Roadmap versionado | product.md (v1.0 → v3.0) |
| Troubleshooting com soluções | INSTALLATION.md |
| Links cruzados entre docs | README.md → outros docs |

---

## 5. Notas Técnicas

- Os documentos foram gerados com base na análise completa do código-fonte (agente.py, estado.py, validacao.py, ferramentas/, rag/, interface/)
- A estrutura segue convenções de projetos open-source e documentação profissional
- Todos os documentos estão em português do Brasil
- O README.md serve como ponto de entrada com links para documentação detalhada
- O PRD.md pode ser usado como referência para avaliação acadêmica dos requisitos implementados
