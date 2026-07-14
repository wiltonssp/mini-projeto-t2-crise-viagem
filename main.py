"""
Entry point do Agente de Gestão de Crises em Itinerários de Viagem.

Responsável por:
- Carregar variáveis de ambiente via dotenv
- Validar presença de GROQ_API_KEY antes de qualquer chamada a API
- Selecionar interface (web ou cli) com base em argumento de linha de comando
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


def main():
    """Função principal que valida ambiente e inicia a interface selecionada."""
    # Validar variáveis de ambiente antes de qualquer operação
    validar_variaveis_ambiente()

    # Determinar modo de execução: 'cli' ou 'web' (default)
    modo = sys.argv[1] if len(sys.argv) > 1 else "web"

    if modo == "cli":
        from src.interface.cli import executar_cli
        executar_cli()
    elif modo == "web":
        from src.interface.gradio_app import demo
        print("\n✈️ Agente de Gestão de Crises — Itinerários de Viagem")
        print("   Acesse: http://localhost:7860\n")
        demo.launch(server_name="127.0.0.1", server_port=7860)
    else:
        print(f"ERRO: Modo '{modo}' não reconhecido.")
        print("Uso: python main.py [web|cli]")
        print("  web  - Inicia interface Gradio (padrão)")
        print("  cli  - Executa via linha de comando")
        sys.exit(1)


if __name__ == "__main__":
    main()
