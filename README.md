# CoreSight: Dashboard Híbrido de Sistema e Toolkit de Trace ARM

O **CoreSight** é uma solução profissional e modular para Linux, projetada para unir o monitoramento de métricas de sistema em tempo real com um toolkit avançado de captura e análise de trace de hardware ARM CoreSight. 

Desenvolvido sob padrões de engenharia sênior, o projeto oferece uma interface de terminal (TUI) responsiva, de alta fidelidade e com suporte a internacionalização, permitindo desde a gestão de recursos de CPU/RAM até o debug de baixo nível de fluxos de instrução (ETM).

## 🚀 Funcionalidades Principais

### 1. Monitoramento de Sistema (Visualização 1)
*   **Métricas de Hardware**: Acompanhamento em tempo real de CPU (por núcleo), RAM, Swap e utilização de Disco.
*   **Análise de Rede**: Velocidades de upload e download com conversão automática de unidades.
*   **Logs Críticos**: Integração direta com o `journalctl` para exibição de erros do sistema em tempo real.
*   **Sistema de Alertas**: Gerenciamento de limites (thresholds) com alertas visuais e sonoros.

### 2. CoreSight Toolkit (Visualização 2)
*   **Hardware Interface**: Abstração completa do `sysfs` para controle de dispositivos CoreSight (ETM, Funnel, Sink).
*   **Orquestração de Captura**: Gerenciamento de sessões de captura, configuração de buffers e roteamento de trace.
*   **Motor de Decode (Fase 2)**: Parsing experimental de pacotes ETMv4, identificando eventos como `BRANCH`, `TIMESTAMP` e `CYCLE_COUNT`.
*   **Análise de Performance (Fase 3)**: Geração de estatísticas de densidade de saltos, contagem de ciclos e throughput de dados.
*   **Integração Perf (Fase 4)**: Suporte ao subsistema `perf` do Linux para capturas robustas e extração de dados `cs_etm`.
*   **Modo de Simulação**: Ambiente de simulação integrado que permite testes e desenvolvimento em plataformas não-ARM.

## 🏗️ Arquitetura do Projeto

O projeto segue uma separação rigorosa de responsabilidades em módulos independentes:

*   **Core (`main.py`)**: Orquestrador central e motor de layout responsivo ANSI.
*   **Modules (`modules/`)**:
    *   `hardware_interface.py`: Camada de abstração de hardware.
    *   `trace_capture.py`: Lógica de controle de sessões de trace.
    *   `trace_decode.py`: Decoder de stream binário CoreSight.
    *   `trace_analyzer.py`: Motor de análise estatística.
    *   `perf_integration.py`: Interface com o comando `perf` do Linux.
    *   `cpu.py`, `ram.py`, etc.: Módulos de monitoramento de recursos.
*   **Utilities (`utils.py`)**: Funções de formatação, logging profissional e detecção de terminal.

## 🛠️ Requisitos e Instalação

### Pré-requisitos
*   Python 3.8+
*   Linux com suporte a `sysfs` (CoreSight drivers recomendados para uso real)
*   Dependências Python: `psutil`
*   Dependências de Sistema: `perf`, `mypy` (para validação de tipos)

### Instalação
```bash
git clone https://github.com/usuario/coresight.git
cd coresight
pip install psutil
```

## 🎮 Como Usar

Para iniciar o dashboard unificado:
```bash
python3 main.py
```

### Controles de Navegação
*   `1`: Alternar para o **Monitor de Sistema**.
*   `2`: Alternar para o **CoreSight Toolkit**.
*   `ESC` / `Ctrl+C`: Encerramento seguro da aplicação.

### Controles de Trace (Modo CoreSight)
*   `S`: **Iniciar** captura de trace (Start).
*   `T`: **Parar** captura de trace (Stop).
*   `A`: **Analisar** dados capturados e gerar relatório (Analyze).

## 📈 Roadmap de Evolução Concluído

O projeto completou com sucesso as 4 fases de desenvolvimento planejadas no blueprint:
- [x] **Fase 1**: Implementação da infraestrutura básica de captura e hardware.
- [x] **Fase 2**: Desenvolvimento do motor de decodificação de pacotes.
- [x] **Fase 3**: Implementação de métricas e análise estatística de trace.
- [x] **Fase 4**: Integração profissional com o subsistema `perf` do Linux.

## 📄 Licença

Este projeto é uma ferramenta de engenharia avançada destinada a desenvolvedores de sistemas embarcados e administradores de performance. Todos os direitos reservados.
