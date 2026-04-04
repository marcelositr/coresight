# CoreSight

O CoreSight é um dashboard de terminal modular e profissional, projetado para o monitoramento de sistemas em tempo real em ambientes Linux. Ele fornece uma interface unificada de alta fidelidade para rastreamento de métricas de hardware, tráfego de rede e logs críticos do sistema com um motor de layout responsivo.

## Visão Geral

O sistema é construído sobre uma arquitetura modular onde cada componente de monitoramento (CPU, RAM, Disco, Rede, Logs) opera de forma independente. A camada de integração gerencia a renderização responsiva e o sistema de gerenciamento de alertas, garantindo que a interface mantenha sua integridade estrutural em diversas dimensões de terminal.

## Funcionalidades Principais

- **Rastreamento Avançado de Hardware**: Monitoramento em tempo real da utilização da CPU (por núcleo e média total), consumo de memória (RAM e Swap) e utilização de espaço em disco em todos os pontos de montagem do sistema.
- **Análise de Tráfego de Rede**: Cálculo em tempo real das velocidades de upload e download por interface, com conversão automática de unidades (B/s, KB/s, MB/s) e alinhamento de largura fixa.
- **Integração de Logs em Tempo Real**: Monitoramento direto de erros críticos do sistema via journalctl, filtrados especificamente para exibir eventos ocorridos após o início da sessão de monitoramento.
- **Layout ANSI Responsivo**: Motor de renderização customizado que considera códigos de escape ANSI para garantir o alinhamento perfeito das bordas e o redimensionamento proporcional (suporte para terminais Ultrawide e telas pequenas).
- **Sistema de Alertas Inteligente**: Gerenciamento centralizado de limites (thresholds) que aciona efeitos visuais intermitentes e alertas sonoros do sistema quando os limites críticos são excedidos.
- **Internacionalização (i18n)**: Detecção automática do idioma do sistema com suporte nativo para Inglês e Português (Brasil).
- **Manipulação de Entrada de Baixo Nível**: Implementação nativa de captura de teclado não bloqueante, permitindo a saída via ESC ou Ctrl+C sem a necessidade da tecla Enter.

## Arquitetura

O projeto segue uma separação rigorosa de responsabilidades:
- **Core (main.py)**: Orquestra o ciclo de vida, entradas de teclado e a montagem do layout responsivo.
- **Módulos (modules/)**: Contém a lógica de coleta de dados e formatação especializada para cada subsistema.
- **Utilitários (utils.py)**: Fornece o motor de formatação compatível com ANSI, geração de barras de progresso e detecção de tamanho de terminal.
- **Configuração (config.py)**: Centraliza limites, definições de cores e intervalos de atualização.

## Pré-requisitos

- Python 3.x
- Biblioteca psutil
- Distribuição Linux baseada em Systemd (para integração com journalctl)

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seuusuario/CoreSight.git
   cd CoreSight
   ```

2. Instale as dependências necessárias:
   ```bash
   pip install psutil
   ```

## Uso

Para iniciar o dashboard, execute o ponto de entrada principal:

```bash
python3 main.py
```

### Controles
- **ESC**: Encerramento seguro da aplicação.
- **Ctrl+C**: Interrupção imediata e saída.

## Configuração

A personalização pode ser realizada no arquivo `config.py`:
- **REFRESH_INTERVAL**: Ajuste a frequência de atualização (padrão é 1.0 segundo).
- **THRESHOLDS**: Defina os limites percentuais para alertas de CPU, RAM e Disco.
- **DEBUG**: Alterna o log interno para cada módulo.

## Estrutura do Projeto

```text
CoreSight/
├── main.py              # Ponto de entrada e motor de layout
├── config.py            # Configurações globais e limites
├── utils.py             # Utilitários de interface e formatação
├── modules/             # Submódulos de monitoramento
│   ├── cpu.py
│   ├── ram.py
│   ├── disk.py
│   ├── network.py
│   ├── logs.py
│   ├── alerts.py
│   └── extras.py        # Template para expansões futuras
├── i18n/                # Arquivos de internacionalização
│   ├── __init__.py      # Carregador de idioma
│   ├── en_US.py
│   └── pt_BR.py
└── blueprint/           # Especificações de design do projeto
```

## Logs Internos

O CoreSight mantém arquivos de log individuais para cada módulo para facilitar a depuração e auditoria de desempenho. Os logs são armazenados no diretório de cache do usuário:
`~/.cache/CoreSight/`

## Licença

Este projeto é destinado a administradores de sistema e usuários avançados que necessitam de uma solução de monitoramento leve e robusta. Todos os direitos reservados.
