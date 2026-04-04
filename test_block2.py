
import os
import sys

# Adiciona o diretório atual ao path para garantir que imports funcionem
sys.path.append(os.getcwd())

import config
import utils
from main import CoreSight

def test_pipeline():
    print("--- INICIANDO TESTE DO PIPELINE (BLOCO 2) ---")
    try:
        # Inicializa o CoreSight
        app = CoreSight()
        print("[OK] CoreSight inicializado com sucesso.")
        
        # Simula o novo pipeline do CoreSight
        print("[...] Executando o pipeline estruturado...")
        
        # 1. Coletar
        app.collect_data()
        print("[OK] Coleta de dados (collect_data) realizada.")
        
        # 2. Processar
        app.process_data()
        print("[OK] Processamento de alertas (process_data) realizado.")
        
        # 3. Formatar
        app.format_output()
        dashboard_str = "\n".join(app.formatted_output)
        print("[OK] Formatação do dashboard (format_output) concluída.")
        
        # Verifica se o dashboard contém elementos essenciais
        if "CoreSight Dashboard" in dashboard_str:
            print("[OK] Dashboard gerado corretamente via pipeline.")
            print("-" * 30)
            # Imprime apenas as primeiras 5 linhas para validar o layout
            print("\n".join(dashboard_str.split("\n")[:5]))
            print("-" * 30)
        else:
            print("[ERRO] O dashboard gerado parece estar vazio ou corrompido.")
            sys.exit(1)
            
        print("[OK] Teste do Bloco 2 concluído com sucesso!")
        
    except Exception as e:
        print(f"[FALHA] Ocorreu um erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_pipeline()
