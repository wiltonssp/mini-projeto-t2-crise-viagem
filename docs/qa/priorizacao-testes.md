# Priorização de Testes por Risco e Impacto

## Metodologia

A priorização foi realizada com apoio de IA (Kiro), avaliando cada cenário de teste
em duas dimensões:
- **Probabilidade de falha:** Quão provável é que este cenário apresente bugs.
- **Impacto no usuário:** Qual o impacto se este cenário falhar em produção.

## Matriz de Priorização

| # | Cenário de Teste | Probabilidade | Impacto | Prioridade | Justificativa |
|---|------------------|---------------|---------|------------|---------------|
| 1 | E2E Fluxo de Crise | Média | Crítico | **ALTA** | Cenário principal do produto. Falha = usuário sem orientação em crise |
| 2 | E2E Prompt Injection | Alta | Crítico | **ALTA** | Entrada adversarial é frequente em chatbots. Falha = comprometimento de segurança |
| 3 | E2E Resiliência (API falha) | Alta | Alto | **ALTA** | APIs externas falham frequentemente. Falha = sistema silencioso em crise |
| 4 | Validação de Código de Reserva | Baixa | Médio | **MÉDIA** | Lógica consolidada com 107 testes. Risco de regressão baixo |
| 5 | E2E Consulta de Clima | Média | Baixo | **MÉDIA** | Funcionalidade complementar, API real pode ter instabilidade |
| 6 | Formatação do Plano | Baixa | Baixo | **BAIXA** | Apresentação visual, não impacta funcionalidade core |

## Testes E2E Gerados com Priorização

### Prioridade ALTA — Implementados em `tests/test_e2e.py`

1. **TestE2EFluxoCrise** — Exercita o fluxo completo de cancelamento e atraso
2. **TestE2ECenarioAdversarial** — Verifica bloqueio de prompt injection no fluxo E2E
3. **TestE2EResiliencia** — Confirma que falha de API não impede resposta ao usuário

### Prioridade MÉDIA — Implementados em `tests/test_e2e.py`

4. **TestE2EConsultaSimples** — Verifica consulta de clima e status sem crise

## Decisão de Priorização

O teste E2E de **prompt injection** foi priorizado acima do teste de consulta simples
porque:
- Chatbots públicos recebem tentativas de injection frequentemente
- Uma falha de segurança tem impacto regulatório (LGPD, exposição de dados)
- O cenário de crise é mais frequente que consultas simples no domínio

---

*Análise e priorização realizadas com apoio de IA (Kiro) — Agosto/2026*
