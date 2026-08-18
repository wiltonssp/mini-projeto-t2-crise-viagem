"""
Entry point do Agente de Gestão de Crises em Itinerários de Viagem.

Responsável por:
- Carregar variáveis de ambiente via dotenv
- Validar presença de GROQ_API_KEY antes de qualquer chamada a API
- Selecionar interface (web, cli, dashboard) com base em argumento de linha de comando
- Iniciar monitoramento proativo (v2.0)
"""

import sys
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()


def validar_variaveis_ambiente():
    """
    Valida a presença de variáveis de ambiente obrigatórias.
    Encerra com sys.exit(1) e mensagem clara se alguma estiver ausente.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key or groq_api_key.strip() == "":
        print("ERRO: Variável de ambiente GROQ_API_KEY não definida ou vazia.")
        print("Configure no arquivo .env ou exporte a variável:")
        print("  export GROQ_API_KEY=sua_chave_aqui")
        sys.exit(1)


def _mostrar_info_inicializacao():
    """Exibe informações sobre providers e configurações ativas."""
    print("\n✈️  Viagem Inteligente — Gestão de Crises em Itinerários")
    print("=" * 60)

    # Verificar providers de aviação
    from src.ferramentas.voo_api import get_aviation_service
    aviation = get_aviation_service()
    print(f"   Providers de voo: {', '.join(aviation.providers_ativos)}")

    # Verificar messaging
    from src.interface.messaging import get_servico_mensageria
    msg = get_servico_mensageria()
    canais = msg.canais_disponiveis
    if canais:
        print(f"   Canais de mensageria: {', '.join(canais)}")
    else:
        print("   Canais de mensageria: nenhum configurado")

    # Verificar embeddings
    try:
        from src.rag.embeddings import _SENTENCE_TRANSFORMERS_DISPONIVEL
        if _SENTENCE_TRANSFORMERS_DISPONIVEL:
            print("   RAG: Sentence Transformers (embeddings densos)")
        else:
            print("   RAG: TF-IDF (fallback)")
    except ImportError:
        print("   RAG: TF-IDF (padrão)")

    # Verificar aeroportos
    from src.ferramentas.aeroportos import total_aeroportos
    print(f"   Aeroportos IATA: {total_aeroportos()} cadastrados")

    print("=" * 60)


def main():
    """Função principal que valida ambiente e inicia a interface selecionada."""
    # Validar variáveis de ambiente antes de qualquer operação
    validar_variaveis_ambiente()

    # Determinar modo de execução: 'cli', 'web' (default), 'dashboard'
    modo = sys.argv[1] if len(sys.argv) > 1 else "web"

    if modo == "cli":
        from src.interface.cli import executar_cli
        executar_cli()

    elif modo == "web":
        _mostrar_info_inicializacao()

        # Iniciar monitoramento proativo em background (v2.0)
        try:
            from src.notificacoes import iniciar_monitoramento
            iniciar_monitoramento()
            print("   Monitor de voos: ativo (verificação a cada 5min)")
        except Exception as e:
            print(f"   Monitor de voos: desativado ({e})")

        from src.interface.gradio_app import demo
        print(f"\n   Acesse: http://localhost:7860\n")
        demo.launch(server_name="127.0.0.1", server_port=7860)

    elif modo == "dashboard":
        _mostrar_info_inicializacao()
        from src.interface.dashboard import dashboard_app
        print(f"\n   Dashboard: http://localhost:7861\n")
        dashboard_app.launch(server_name="127.0.0.1", server_port=7861)

    else:
        print(f"ERRO: Modo '{modo}' não reconhecido.")
        print("Uso: python main.py [web|cli|dashboard]")
        print("  web       - Inicia interface Gradio (padrão)")
        print("  cli       - Executa via linha de comando")
        print("  dashboard - Inicia dashboard de analytics")
        sys.exit(1)


if __name__ == "__main__":
    main()
