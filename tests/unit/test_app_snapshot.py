
from main import CoreSightUnified


def run_snapshot():
    print("--- INICIANDO SNAPSHOT DA APLICAÇÃO (MODO INDUSTRIAL) ---")

    # Forçamos o modo de simulação para o ambiente atual
    app = CoreSightUnified(simulation=True)
    app._view_mode["mode"] = 2  # Mudança para a Sessão 2

    # Simulamos uma captura ativa para ver o dashboard populado
    print("[TEST] Simulando início de captura...")
    app._capture.capture_start("etm0", "tmc_etr0")

    # Executamos o pipeline oficial
    app.collect_data()
    app.process_data()
    app.format_output()

    # Exibimos o resultado formatado (limpando códigos ANSI para leitura clara aqui)
    print("\n--- RENDERIZAÇÃO DO DASHBOARD ---")
    for line in app.formatted_output:
        # Removemos cores ANSI apenas para visualização no log de teste
        clean_line = (
            line.replace("\033[92m", "")
            .replace("\033[94m", "")
            .replace("\033[96m", "")
            .replace("\033[0m", "")
            .replace("\033[91m", "")
            .replace("\033[5m", "")
            .replace("\033[93m", "")
        )
        print(clean_line)
    print("--- FIM DO SNAPSHOT ---\n")


if __name__ == "__main__":
    run_snapshot()
