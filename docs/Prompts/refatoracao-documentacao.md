# Documentação de Prompts — Refatoração de Documentação

---

## 1. Prompt Utilizado

Este é o prompt enviado ao Kiro para refatoração e atualização da documentação do projeto:

```text
Adicione ou substitua o link do repositório do projeto do Github

https://github.com/wiltonssp/mini-projeto-t2-crise-viagem

Em seguida analise do projeto e verifique todos os requisitos, 

atualize todos a documentação .md (README.md, product.md, PRD.md, INSTALLATION.md) ao final adicione novo md. com este promts na pasta doc/Prompts com nome refatoracao-documentacao.md
```

---

## 2. Objetivo da Refatoração

Atualizar toda a documentação do projeto para:

1. Incluir o link do repositório GitHub em todos os documentos `.md`
2. Verificar se todos os requisitos do PRD estão implementados no código
3. Atualizar informações para refletir o estado atual do projeto
4. Registrar o prompt utilizado para rastreabilidade

---

## 3. Alterações Realizadas

### 3.1 README.md

| Alteração | Descrição |
|-----------|-----------|
| Link do repositório | Adicionado no topo como destaque (blockquote) |
| Quick Start | Atualizado com `git clone` do repositório GitHub |
| Seção CI/CD | Menção ao pipeline GitHub Actions nas decisões de design |
| Estrutura do projeto | Adicionada pasta `.github/workflows/` |
| Seção Autor | Adicionada com link para perfil GitHub |
| Exemplos de teste | Adicionada consulta de clima sem código |

### 3.2 product.md

| Alteração | Descrição |
|-----------|-----------|
| Link do repositório | Adicionado no topo e na tabela de identidade |
| Diferenciais técnicos | Adicionado CI/CD com GitHub Actions |
| Roadmap v1.0 | Adicionados itens de CI/CD e documentação completa |
| Métricas | Adicionada métrica de cobertura de testes (≥70%) |
| Glossário | Adicionado termo CI/CD |

### 3.3 PRD.md

| Alteração | Descrição |
|-----------|-----------|
| Link do repositório | Adicionado no topo e na tabela de resumo executivo |
| Coluna Status | Adicionada em todos os requisitos funcionais (todos ✅) |
| RF-10 | Novo grupo de requisitos: CI/CD (lint, testes, docs) |
| RNF-05 | Novo grupo: Qualidade de Código |
| Métricas de Sucesso | Adicionada coluna de status com checkmarks |
| Dependências externas | Adicionado GitHub Actions |
| Cronograma Fase 8 | Atualizada para incluir CI/CD |

### 3.4 INSTALLATION.md

| Alteração | Descrição |
|-----------|-----------|
| Link do repositório | Adicionado no topo como destaque |
| Pré-requisitos | Adicionado Git 2.0+ |
| Passo 1 | Substituído por `git clone` do repositório + opção ZIP |
| Passo 6 | Nova seção para execução de testes |
| Troubleshooting | Adicionada seção para erros ao clonar |
| Dependências | Adicionados pytest e pytest-cov na tabela |

---

## 4. Verificação de Requisitos

Todos os requisitos do PRD foram verificados contra o código-fonte:

| Grupo | Total | Implementados | Cobertura |
|-------|-------|---------------|-----------|
| RF-01: Validação de Entrada | 5 | 5 | 100% |
| RF-02: Consulta de Voo | 3 | 3 | 100% |
| RF-03: Consulta Climática | 5 | 5 | 100% |
| RF-04: Transporte Alternativo | 3 | 3 | 100% |
| RF-05: RAG | 5 | 5 | 100% |
| RF-06: Plano de Contingência | 4 | 4 | 100% |
| RF-07: Detecção de Intenção | 4 | 4 | 100% |
| RF-08: Memória de Sessão | 3 | 3 | 100% |
| RF-09: Interfaces | 3 | 3 | 100% |
| RF-10: CI/CD | 3 | 3 | 100% |
| **Total** | **38** | **38** | **100%** |

### Evidências no Código

| Requisito | Arquivo | Função/Classe |
|-----------|---------|---------------|
| RF-01 (validação) | `src/validacao.py` | `validar_codigo_reserva`, `validar_mensagem`, `verificar_dominio` |
| RF-02 (voo) | `src/ferramentas/voo.py` | `consultar_status_voo`, `VOOS_DB` (6 voos) |
| RF-03 (clima) | `src/ferramentas/clima.py` | `consultar_clima`, `COORDENADAS` (8 aeroportos) |
| RF-04 (transporte) | `src/ferramentas/transporte.py` | `consultar_transporte_alternativo`, `ROTAS_DB` (8 rotas) |
| RF-05 (RAG) | `src/rag/busca.py`, `src/rag/documentos.py` | `BuscaSemantica`, `DOCUMENTOS_POLITICAS` (10 docs) |
| RF-06 (plano) | `src/agente.py` | `gerar_plano_node` (5 seções obrigatórias) |
| RF-07 (intenção) | `src/agente.py` | `_eh_pergunta_simples`, `_eh_consulta_clima_direta` |
| RF-08 (memória) | `src/agente.py` | `validacao_node` (reutiliza `codigo_reserva` do state) |
| RF-09 (interfaces) | `src/interface/gradio_app.py`, `src/interface/cli.py` | `demo`, `executar_cli` |
| RF-10 (CI/CD) | `.github/workflows/ci.yml` | jobs: lint, test, documentation |

---

## 5. Ferramentas Utilizadas

| Ferramenta | Uso |
|-----------|-----|
| **Kiro IDE** | Ambiente de desenvolvimento com IA |
| **Análise de código** | Leitura e verificação de todos os módulos Python |
| **Verificação de requisitos** | Cruzamento PRD vs. código-fonte |

---

## 6. Notas

- Todos os 38 requisitos funcionais do PRD estão implementados e verificados
- Os 4 documentos `.md` foram atualizados com o link do repositório GitHub
- A documentação reflete fielmente o estado atual do código-fonte
- O pipeline CI/CD no GitHub Actions valida lint, testes (≥70% cobertura) e documentação
- Este arquivo serve como registro de rastreabilidade da refatoração de documentação
