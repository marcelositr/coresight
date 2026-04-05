# CoreSight Industrial Toolkit & Dashboard

O **CoreSight** evoluiu de um simples monitor de sistema para uma plataforma de engenharia robusta voltada ao diagnóstico, captura e análise de hardware trace ARM em ambientes Linux. O projeto integra o monitoramento clássico de recursos com um motor avançado de topologia de hardware, seguindo rigorosamente os padrões de ativação e segurança do Kernel Linux.

## 🛠️ Arquitetura e Capacidades Técnicas

O sistema é construído sobre uma arquitetura de camadas independentes, garantindo estabilidade e extensibilidade:

### 1. Camada de Topologia (Graph-Based)
*   **TopologyManager**: Motor Singleton que constrói um grafo real do hardware (`Source → Link → Sink`).
*   **Descoberta Dinâmica**: Mapeamento recursivo de conexões via `sysfs`, detectando Funnels, Replicators e TMCs (ETR/ETF).
*   **Cálculo de Caminho**: Algoritmo de busca para encontrar rotas físicas válidas entre fontes de trace (CPU/ETM) e destinos (RAM/Sink).

### 2. Motor de Captura Industrial
*   **Ordem de Ativação Segura**: Implementa a sequência mandatória do Kernel:
    1.  **Sink** (Habilitação e alocação de buffer).
    2.  **Links** (Configuração de roteamento downstream → upstream).
    3.  **Source** (Ativação do fluxo de dados).
*   **CaptureValidator**: Validação pré-voo de integridade de caminho e disponibilidade de registradores.

### 3. I/O de Baixo Nível Robusto
*   **Stateless Hardware Interface**: Operações de leitura/escrita com lógica de retentativa automática (Retry on EBUSY) para lidar com estados transitórios de hardware.
*   **Logger Técnico**: Logs estruturados e categorizados por subsistema para facilitar o debug de campo.

## 🚀 Interfaces de Controle

### 📊 Dashboard Unificado (TUI)
Interface interativa de alta fidelidade com dois modos de visualização:
*   **Tecla 1**: Monitoramento de Sistema (CPU, RAM, Disco, Rede e Logs).
*   **Tecla 2**: CoreSight Toolkit (Status da topologia, estado da captura e análise de performance).

### 💻 CLI Técnica (`coresightctl`)
Ferramenta de linha de comando estilo `systemctl` para automação e diagnóstico profundo:
```bash
python3 cli/coresightctl.py list        # Lista dispositivos detectados
python3 cli/coresightctl.py topology    # Exibe o grafo em árvore ASCII
python3 cli/coresightctl.py path        # Valida caminho físico Source -> Sink
python3 cli/coresightctl.py capture     # Controle direto de ativação
```

## 🛠️ Requisitos e Instalação

*   **OS**: Linux (Kernel com drivers CoreSight habilitados).
*   **Hardware**: Plataformas ARM64 ou ambiente de simulação integrado.
*   **Dependências**: Python 3.8+, `psutil`.

```bash
git clone https://github.com/usuario/coresight.git
pip install psutil
```

## 🛡️ Segurança e Design
*   **Hierarquia de Exceções**: Erros granulares (`TopologyError`, `SysfsError`, etc) para identificação precisa de falhas de hardware.
*   **Modo Simulação**: Suporte total para desenvolvimento e testes em ambientes x86 através de mock estruturado do `sysfs`.
*   **Padrões Industriais**: Código com tipagem estática completa, documentação técnica e separação clara de responsabilidades.

## 📄 Licença
Projeto destinado a engenheiros de sistemas embarcados e profissionais de performance. Todos os direitos reservados.
