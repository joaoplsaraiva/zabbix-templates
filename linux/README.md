# 🐧 Linux Templates

Templates para monitoramento de servidores Linux via Zabbix Agent.

## Templates Disponíveis

### `template_linux_by_agent.yaml`

Template completo para monitoramento de servidores Linux em produção.

**Testado em:**
- Oracle Linux 8 e 9
- CentOS 7 e 8
- Ubuntu 20.04 e 22.04
- Debian 11 e 12

**Compatibilidade:** Zabbix 6.0 LTS e 7.0 LTS

#### Items monitorados

| Categoria | Item | Intervalo |
|---|---|---|
| CPU | Uso total (%) | 60s |
| CPU | Uso user / system / iowait (%) | 60s |
| CPU | Load average (1 e 5 min) | 60s |
| CPU | Número de CPUs lógicas | 1h |
| Memória | Total instalado / disponível | 60s |
| Memória | Percentual de uso (%) | 60s |
| Swap | Espaço livre (%) | 60s |
| Disco | Espaço total / usado / % na raiz (/) | 60s |
| Disco | IOPS: leitura e escrita por segundo | 60s |
| Rede | Tráfego in/out em bps (eth0) | 60s |
| Sistema | Uptime, hostname, versão do OS | 60s/1h |
| Sistema | Número de processos | 60s |
| Zabbix | Disponibilidade do agente | 60s |

#### Triggers configuradas

| Trigger | Severidade | Condição padrão |
|---|---|---|
| CPU uso crítico | HIGH | > 90% por 5 min |
| CPU uso elevado | WARNING | > 80% por 5 min |
| Memória crítica | HIGH | > 90% |
| Memória elevada | WARNING | > 80% |
| Disco crítico (/) | HIGH | > 95% |
| Disco elevado (/) | WARNING | > 85% |
| Swap baixo | WARNING | < 20% livre |
| Host reiniciado | WARNING | uptime < 10 min |
| Agente indisponível | HIGH | sem resposta |

#### Macros configuráveis

| Macro | Valor padrão | Descrição |
|---|---|---|
| `{$CPU.UTIL.CRIT}` | 90 | Limite crítico de CPU em % |
| `{$CPU.UTIL.WARN}` | 80 | Limite de alerta de CPU em % |
| `{$MEMORY.UTIL.MAX}` | 90 | Limite crítico de memória em % |
| `{$MEMORY.UTIL.WARN}` | 80 | Limite de alerta de memória em % |
| `{$SWAP.PFREE.MIN.WARN}` | 20 | Swap livre mínimo em % |
| `{$VFS.FS.PUSED.MAX.CRIT}` | 95 | Limite crítico de disco em % |
| `{$VFS.FS.PUSED.MAX.WARN}` | 85 | Limite de alerta de disco em % |

#### Gráficos incluídos

- CPU: uso geral (total, user, system, iowait)
- Memória: uso e disponibilidade
- Disco /: uso de espaço
- Rede: tráfego eth0 (in/out)

## Como importar

1. Acesse **Data collection → Templates → Import**
2. Selecione o arquivo `.yaml`
3. Clique em **Import**
4. Associe o template ao host desejado

> **Atenção:** O item de rede usa `eth0` por padrão. Ajuste a chave para o nome correto da sua interface (ex: `ens3`, `ens192`, `bond0`) nas propriedades do item após importar, ou use descoberta automática de interfaces.
