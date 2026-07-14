"""
Interface CLI do Agente de Gestão de Crises em Itinerários de Viagem.

Permite execução via linha de comando como alternativa à interface web Gradio.
Uso: python main.py cli <codigo_reserva> <mensagem>
"""

import sys

from langchain_core.messages import HumanMessage

from src.agente import build_graph


def executar_cli():
    """
    Executa o agente de crises via linha de comando.

    Aceita código de reserva e mensagem como argumentos CLI:
      - sys.argv[2] = codigo_reserva
      - sys.argv[3:] joined = mensagem do usuário

    Exibe o relatório final (plano de contingência) no terminal.
    Em caso de argumentos insuficientes, imprime instruções de uso e encerra.
    Em caso de erro durante o processamento, exibe mensagem indicando a falha.
    """
    # Verificar argumentos suficientes
    if len(sys.argv) < 4:
        print("Uso: python main.py cli <codigo_reserva> <mensagem>")
        print()
        print("Argumentos:")
        print("  codigo_reserva  Código de reserva alfanumérico de 6 caracteres (ex: ABC123)")
        print("  mensagem        Descrição da situação de crise (mínimo 10 caracteres)")
        print()
        print("Exemplos:")
        print('  python main.py cli ABC123 Meu voo foi cancelado por mau tempo')
        print('  python main.py cli XYZ789 Perdi minha conexão em Guarulhos e preciso chegar ao Rio')
        sys.exit(1)

    codigo_reserva = sys.argv[2]
    mensagem = " ".join(sys.argv[3:])

    try:
        # Construir o grafo do agente
        app = build_graph()

        # Configurar thread_id único para a sessão CLI
        config = {"configurable": {"thread_id": f"cli-{codigo_reserva}"}}

        # Invocar o grafo com a mensagem combinada (código + mensagem)
        entrada = {"messages": [HumanMessage(content=f"{codigo_reserva} {mensagem}")]}
        resultado = app.invoke(entrada, config)

        # Exibir o relatório final
        relatorio = resultado.get("relatorio_final", "")
        if relatorio:
            print(relatorio)
        else:
            print("Erro: Não foi possível gerar o plano de contingência.")
            print("Tente novamente ou verifique os dados fornecidos.")
            sys.exit(1)

    except Exception as e:
        print(f"Erro ao processar sua solicitação: {str(e)}")
        print("Verifique sua conexão e tente novamente.")
        sys.exit(1)
