# Guia de Instalação — Viagem Inteligente

> **Repositório:** [https://github.com/wiltonssp/mini-projeto-t2-crise-viagem](https://github.com/wiltonssp/mini-projeto-t2-crise-viagem)

## Pré-requisitos

| Requisito | Versão Mínima | Verificação |
|-----------|---------------|-------------|
| Python | 3.10+ | `python --version` |
| pip | 21.0+ | `pip --version` |
| Git | 2.0+ | `git --version` |
| Conexão Internet | — | Necessário para API Open-Meteo e Groq |
| GROQ_API_KEY | — | Obtida em [console.groq.com](https://console.groq.com/) |

## Passo 1: Clonar o Repositório

```bash
git clone https://github.com/wiltonssp/mini-projeto-t2-crise-viagem.git
cd mini-projeto-t2-crise-viagem
```

Ou baixe o ZIP diretamente:

```
https://github.com/wiltonssp/mini-projeto-t2-crise-viagem/archive/refs/heads/main.zip
```

## Passo 2: Criar Ambiente Virtual

Recomendado para isolar as dependências do projeto.

### Windows (CMD)

```cmd
python -m venv venv
venv\Scripts\activate
```

### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

> Ao ativar o ambiente virtual, o prompt do terminal exibirá `(venv)` no início.

## Passo 3: Instalar Dependências

```bash
pip install -r requirements.txt
```

### Dependências do Projeto

| Pacote | Versão | Função |
|--------|--------|--------|
| `langgraph` | ≥0.2 | Orquestração do grafo do agente |
| `langchain-groq` | ≥0.2 | Integração com LLM Groq |
| `langchain-core` | ≥0.3 | Tools e tipos de mensagem |
| `gradio` | ≥4.0 | Interface web conversacional + dashboard |
| `python-dotenv` | ≥1.0 | Carregamento de variáveis .env |
| `requests` | ≥2.31 | Chamadas HTTP (Open-Meteo, FlightAware, Amadeus) |
| `scikit-learn` | ≥1.3 | TF-IDF e similaridade cosseno |
| `numpy` | ≥1.24 | Operações vetoriais |
| `pytest` | ≥7.0 | Testes unitários |
| `pytest-cov` | ≥4.0 | Cobertura de testes |

### Dependências Opcionais (v2.0+)

| Pacote | Função | Fallback |
|--------|--------|----------|
| `sentence-transformers` | Embeddings semânticos para RAG | TF-IDF (automático) |
| `twilio` | Integração WhatsApp | Canal indisponível |

```bash
# Para instalar dependências opcionais:
pip install sentence-transformers twilio
```

### Verificar Instalação

```bash
python -c "import langgraph, langchain_groq, gradio, sklearn; print('Todas as dependências instaladas com sucesso!')"
```

## Passo 4: Configurar Variáveis de Ambiente

### 4.1. Criar arquivo `.env`

```bash
# Copie o template
cp .env.example .env
```

Ou no Windows CMD:

```cmd
copy .env.example .env
```

### 4.2. Obter GROQ_API_KEY (Obrigatório)

1. Acesse [console.groq.com](https://console.groq.com/)
2. Crie uma conta gratuita (se ainda não tiver)
3. Navegue até **API Keys**
4. Clique em **Create API Key**
5. Copie a chave gerada

### 4.3. Configurar a chave

Edite o arquivo `.env`:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 4.4. Configurações Opcionais (v2.0+)

Para habilitar integrações reais, adicione ao `.env`:

```env
# APIs de Aviação (sem estas, usa base simulada automaticamente)
FLIGHTAWARE_API_KEY=sua_chave_flightaware
AMADEUS_CLIENT_ID=seu_client_id
AMADEUS_CLIENT_SECRET=seu_client_secret

# WhatsApp via Twilio
TWILIO_ACCOUNT_SID=seu_account_sid
TWILIO_AUTH_TOKEN=seu_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Telegram Bot
TELEGRAM_BOT_TOKEN=seu_bot_token
```

> **Segurança:** Nunca versione o arquivo `.env`. Ele já está no `.gitignore`.

## Passo 5: Executar o Agente

### Interface Web (Gradio) — Recomendado

```bash
python main.py web
```

Acesse: **http://localhost:7860**

A interface mostra:
- Chat conversacional com memória
- Painel lateral com arquitetura do grafo
- Exemplos de uso
- Botão "Nova Sessão" para reiniciar conversa

### Interface CLI (Terminal)

```bash
python main.py cli ABC123 "Meu voo foi cancelado por mau tempo e vou perder minha conexão"
```

Formato: `python main.py cli <CODIGO_RESERVA> <MENSAGEM>`

### Dashboard de Analytics (v3.0)

```bash
python main.py dashboard
```

Acesse: **http://localhost:7861**

O dashboard mostra: sessões, interações, tempo de resposta, feedback e eventos por tipo.

## Passo 6: Executar Testes

```bash
# Todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=src --cov-report=term-missing -v

# Teste específico
pytest tests/test_validacao.py -v
```

## Verificação da Instalação

Execute o seguinte para validar que tudo está configurado:

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

# Verificar Python
import sys
print(f'Python: {sys.version}')

# Verificar dependências
import langgraph, langchain_groq, gradio, sklearn, requests
print('Dependências: OK')

# Verificar API key
key = os.getenv('GROQ_API_KEY', '')
if key and key != 'sua_chave_groq_aqui':
    print(f'GROQ_API_KEY: Configurada ({key[:10]}...)')
else:
    print('GROQ_API_KEY: NÃO CONFIGURADA')
    print('  Configure no arquivo .env')

print('\nInstalação concluída!')
"
```

## Solução de Problemas

### `ModuleNotFoundError: No module named 'langgraph'`

O ambiente virtual não está ativado ou as dependências não foram instaladas.

```bash
# Ativar ambiente virtual
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac

# Reinstalar dependências
pip install -r requirements.txt
```

### `ERRO: Variável de ambiente GROQ_API_KEY não definida ou vazia`

A chave da API Groq não está configurada.

```bash
# Verificar se .env existe
type .env                      # Windows CMD
cat .env                       # Linux/Mac

# Deve conter: GROQ_API_KEY=gsk_xxxxx
```

### `Connection refused` ao acessar http://localhost:7860

O servidor Gradio não está rodando ou a porta está ocupada.

```bash
# Verificar se a porta está em uso
netstat -an | findstr 7860     # Windows
lsof -i :7860                  # Linux/Mac

# Se a porta estiver ocupada, finalize o processo ou use outra porta
```

### `requests.exceptions.ConnectionError` (consulta de clima)

Sem conexão com a internet. A API Open-Meteo requer acesso à internet.
O agente continuará funcionando, mas a seção de clima ficará indisponível.

### Erro de encoding (Windows)

Se encontrar erros de encoding ao executar, configure:

```cmd
set PYTHONIOENCODING=utf-8
python main.py web
```

### Erro ao clonar o repositório

Se receber erro de autenticação:

```bash
# Verifique se o Git está configurado
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"

# Clone via HTTPS (não requer SSH key)
git clone https://github.com/wiltonssp/mini-projeto-t2-crise-viagem.git
```

## Estrutura de Configuração

```
.env.example     ← Template (versionado)
.env             ← Suas configurações (NÃO versionado)
.gitignore       ← Protege .env, __pycache__, venv/
```

## Portas Utilizadas

| Serviço | Porta | Protocolo |
|---------|-------|-----------|
| Interface Gradio (web) | 7860 | HTTP |
| Dashboard Analytics | 7861 | HTTP |
| API Open-Meteo | 443 | HTTPS (externo) |
| API Groq | 443 | HTTPS (externo) |
| API FlightAware (v2.0) | 443 | HTTPS (externo, opcional) |
| API Amadeus (v2.0) | 443 | HTTPS (externo, opcional) |
| API Twilio (v2.0) | 443 | HTTPS (externo, opcional) |
| API Telegram (v2.0) | 443 | HTTPS (externo, opcional) |

## Requisitos de Sistema

- **RAM:** ~512 MB (sem modelos locais — LLM é remoto). ~2 GB se usar Sentence Transformers local
- **Disco:** ~200 MB (dependências base). ~500 MB com sentence-transformers
- **CPU:** Qualquer processador moderno
- **SO:** Windows 10+, Linux, macOS

## Estrutura de Dados Local

O sistema cria automaticamente um diretório `data/` com bancos SQLite:

```
data/
├── sessoes.db        # Histórico de sessões e mensagens (v1.1)
├── usuarios.db       # Autenticação e perfis (v2.0)
├── tenants.db        # Configurações multi-tenant (v3.0)
└── feedback.db       # Feedback e datasets de fine-tuning (v3.0)
```

Estes arquivos são criados na primeira execução e estão no `.gitignore`.
