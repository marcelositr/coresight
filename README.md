# CoreSight Industrial Toolkit & Dashboard

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-134%20passed-green.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Plataforma híbrida de **monitoramento de sistema** e **diagnóstico de hardware ARM CoreSight** com interface TUI profissional, CLI técnica e pipeline de análise de trace. Projeto refatorado com **Clean Code**, **POO** e **SOLID**, seguindo o Blueprint CoreSight.

---

## 🏗️ Arquitetura

```
coresight/
├── app/                    # Camada de aplicação (Coordinator Pattern)
│   ├── orchestrator.py     #   DataOrchestrator – coleta e processamento
│   ├── renderer.py         #   DashboardRenderer – formatação e renderização UI
│   └── input_handler.py    #   InputHandler – input terminal + command dispatch
├── core/                   # Motor CoreSight (hardware trace)
│   ├── topology_manager.py #   Grafo de hardware (Source → Link → Sink)
│   ├── trace_capture.py    #   Captura com ordem mandatória de ativação
│   ├── trace_decode.py     #   Decodificação de pacotes ETMv4
│   ├── trace_analyzer.py   #   Análise estatística de eventos
│   ├── hardware_interface.py # I/O sysfs com retry e safety
│   └── ...
├── system/                 # Monitores de sistema (Template Method Pattern)
│   ├── base_monitor.py     #   Classe base abstrata [T]
│   ├── cpu.py              #   CpuMonitor extends BaseMonitor[CpuMetrics]
│   ├── ram.py              #   RamMonitor extends BaseMonitor[MemoryMetrics]
│   ├── disk.py             #   DiskMonitor extends BaseMonitor[DiskMetrics]
│   ├── network.py          #   NetworkMonitor extends BaseMonitor[NetworkMetrics]
│   ├── logs.py             #   LogsMonitor extends BaseMonitor[LogsMetrics]
│   └── alerts.py           #   AlertsMonitor extends BaseMonitor[AlertMetrics]
├── infra/                  # Infraestrutura
│   ├── config.py           #   Configuração tipada (_Thresholds, _Colors)
│   ├── utils.py            #   TerminalFormatter, FileLogger, utilitários
│   └── exceptions.py       #   SysfsError, TopologyError, CaptureError
├── cli/
│   └── coresightctl.py     # CLI técnica estilo systemctl
├── i18n/                   # Internacionalização (en_US, pt_BR)
├── tests/                  # 134 testes unitários + integração
│   ├── unit/               #   13 arquivos de teste unitário
│   └── integration/        #   3 testes de integração (phases 1-3)
└── main.py                 # Entry point – Coordinator Pattern
```

### Design Patterns Aplicados

| Pattern | Onde | Propósito |
|---------|------|-----------|
| **Coordinator** | `main.py` + `app/` | Separar orquestração de execução |
| **Template Method** | `system/base_monitor.py` | Unificar contrato de monitores |
| **Strategy** | Monitores individuais | Coleta específica por métrica |
| **Factory Method** | `InputHandler.create_default_input_handler()` | Wiring de comandos |
| **Value Object** | `*Metrics` dataclasses | Objetos imutáveis de métricas |
| **Singleton** | `TopologyManager` | Único grafo de hardware |

---

## 🚀 Quick Start

### Instalação

```bash
git clone https://github.com/usuario/coresight.git
cd coresight
pip install psutil
```

### Dashboard TUI

```bash
python3 main.py
```

| Tecla | Ação |
|-------|------|
| `1` | View: Monitor de Sistema |
| `2` | View: CoreSight Toolkit |
| `S` | Start trace capture |
| `T` | Stop trace capture |
| `A` | Analyze trace data |
| `ESC` / `Ctrl+C` | Sair |

### CLI Técnica

```bash
python3 cli/coresightctl.py list        # Listar dispositivos CoreSight
python3 cli/coresightctl.py topology    # Exibir grafo em árvore ASCII
python3 cli/coresightctl.py path etm0 tmc_etr0  # Validar caminho físico
python3 cli/coresightctl.py capture start --source etm0 --sink tmc_etr0
python3 cli/coresightctl.py capture status
python3 cli/coresightctl.py capture stop
```

---

## 📊 Features

### Monitoramento de Sistema
- **CPU**: Por core e total, com barras de progresso coloridas
- **RAM**: RAM + Swap com detalhes de used/total
- **Disco**: Todas as partições físicas (filtra loop/snap)
- **Rede**: Throughput upload/download por interface
- **Logs**: Entradas críticas do journalctl desde o start
- **Alertas**: Thresholds configuráveis com notificação visual + sonora

### CoreSight Toolkit
- **Topologia dinâmica**: Descoberta automática via sysfs
- **Captura de trace**: Ativação segura Sink → Links → Source
- **Decodificação**: Parsing de pacotes ETMv4 (sync markers, branches)
- **Análise**: Densidade de branches, ciclo total, distribuição de pacotes

### UI Responsiva
- Layout adapta-se ao tamanho do terminal (60+ colunas)
- Bordas ANSI alinhadas sem line-wrap
- Conteúdo truncado inteligentemente quando necessário
- Detalhes opcionais em terminais estreitos

---

## 🧪 Testes

```bash
# Suite completa
python3 -m pytest tests/ -v

# Com cobertura
python3 -m pytest tests/ --cov=. --cov-report=term-missing
```

**Resultado atual**: 134 passed, 0 failed

| Categoria | Testes | Cobertura |
|-----------|--------|-----------|
| Unitários | 131 | config, utils, base_monitor, monitors, orchestrator, renderer, input_handler, topology, exceptions |
| Integração | 3 | Phase 1 (capture), Phase 2 (pipeline), Phase 3 (analysis) |

---

## 📋 Requisitos

| Item | Mínimo |
|------|--------|
| Python | 3.8+ |
| OS | Linux |
| Hardware | ARM64 com CoreSight **ou** x86 (modo simulação) |
| Dependências | `psutil` |

---

## 🏅 Refatoração Clean Code / POO

O projeto passou por **6 fases de refatoração** aplicando princípios de Robert C. Martin:

| Fase | Escopo | Mudança |
|------|--------|---------|
| **1** | `infra/config.py` | Classes tipadas `_Thresholds`, `_Colors` com acesso duplo |
| **2** | `infra/utils.py` | SRP: `TerminalFormatter` + `FileLogger` separados |
| **3** | `main.py` + `app/` | Coordinator Pattern: 3 orchestrators especializados |
| **4** | `system/*.py` | Template Method: `BaseMonitor[T]` elimina duplicação |
| **5** | Revisão completa | 22 issues corrigidos (syntax, type hints, imports) |
| **6** | Testes | +13 arquivos de teste, 134 testes passing |

### Princípios SOLID Aplicados

- **S**RP: Cada classe tem uma responsabilidade
- **O**CP: Extensível sem modificar código existente
- **L**SP: Qualquer monitor substitui `BaseMonitor`
- **I**SP: Contratos mínimos e focados
- **D**IP: Dependência de abstrações, não concretos

---

## 📄 Licença

MIT License. Projeto destinado a engenheiros de sistemas embarcados e profissionais de performance.
