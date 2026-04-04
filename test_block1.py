
import os
import sys
import time

# Adiciona o diretório atual ao path para garantir que imports funcionem
sys.path.append(os.getcwd())

import config
import utils
from main import CoreSight

def test_run():
    print("--- INICIANDO TESTE DO BLOCO 1 ---")
    try:
        # Inicializa o CoreSight
        app = CoreSight()
        print("[OK] CoreSight inicializado com sucesso.")
        
        # Testa a largura do terminal padrão
        width = 80
        
        # Executa a construção do dashboard uma vez
        print("[...] Gerando o dashboard pela primeira vez...")
        dashboard = app.build_dashboard(width)
        
        # Verifica se o dashboard contém elementos essenciais
        if "CoreSight Dashboard" in dashboard:
            print("[OK] Dashboard gerado corretamente.")
            print("-" * 30)
            # Imprime apenas o cabeçalho e a primeira seção para validar a estética
            print("\n".join(dashboard.split("\n")[:10]))
            print("-" * 30)
        else:
            print("[ERRO] O dashboard gerado parece estar vazio ou corrompido.")
            sys.exit(1)
            
        print("[OK] Teste de integração do Bloco 1 concluído com sucesso!")
        
    except Exception as e:
        print(f"[FALHA] Ocorreu um erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_run()
