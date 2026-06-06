# 🌐 Network Templates

Templates para monitoramento de rede, links de internet e equipamentos de rede.

## Templates Disponíveis

### `template_link_internet.yaml`

Template completo para monitoramento de links de internet e gateways via ICMP.  
Desenvolvido com base em anos de monitoramento de links corporativos na **SEFA/PA**.

**Compatibilidade:** Zabbix 6.0 LTS e 7.0 LTS

#### Como usar

1. Crie um **host** para cada link ou roteador a ser monitorado
2. Defina o **IP do host** como o gateway ou IP externo do link
3. Aplique este template ao host
4. Configure as macros `{$LINK.NAME}` e `{$LINK.PROVIDER}` no host

**Exemplo de hosts que você pode criar:**
```
Host: Gateway-Vivo       | IP: 192.168.1.1    | Macro LINK.NAME: "Link Vivo Fibra"
Host: Gateway-Claro      | IP: 10.0.0.1       | Macro LINK.NAME: "Link Claro Backup"
Host: DNS-Google         | IP: 8.8.8.8        | Macro LINK.NAME: "Verificacao DNS Google"
Host: DNS-Cloudflare     | IP: 1.1.1.1        | Macro LINK.NAME: "Verificacao DNS Cloudflare"
```

#### Items monitorados

| Item | Tipo | Intervalo | Descrição |
|---|---|---|---|
| Status ICMP (UP/DOWN) | SIMPLE | 60s | Disponibilidade básica do link |
| Perda de pacotes (%) | SIMPLE | 60s | Percentual de pacotes perdidos |
| Latência mínima (ms) | SIMPLE | 60s | Menor RTT entre os pacotes |
| Latência média (ms) | SIMPLE | 60s | RTT médio — principal métrica |
| Latência máxima (ms) | SIMPLE | 60s | Maior RTT entre os pacotes |
| Jitter (ms) | CALCULATED | 60s | Variação de latência (max - min) |
| Disponibilidade 24h (%) | CALCULATED | 5m | SLA diário |
| Disponibilidade 7 dias (%) | CALCULATED | 30m | SLA semanal |
| Disponibilidade 30 dias (%) | CALCULATED | 1h | SLA mensal |

#### Triggers configuradas

| Trigger | Severidade | Condição padrão |
|---|---|---|
| Link INDISPONÍVEL | DISASTER | Sem resposta ICMP por 5 min |
| Perdeu resposta ICMP | HIGH | Down detectado agora |
| Perda crítica de pacotes | HIGH | > 50% de perda |
| Perda elevada de pacotes | WARNING | > 20% de perda |
| Latência crítica | HIGH | > 500ms por 5 min |
| Latência elevada | WARNING | > 150ms por 5 min |
| Jitter alto | WARNING | > 50ms |
| SLA mensal abaixo | WARNING | < 99.5% em 30 dias |

#### Macros configuráveis

| Macro | Valor padrão | Descrição |
|---|---|---|
| `{$ICMP.LOSS.WARN}` | 20 | Perda de pacotes para alerta (%) |
| `{$ICMP.LOSS.CRIT}` | 50 | Perda de pacotes crítica (%) |
| `{$ICMP.RESPONSE_TIME.WARN}` | 0.15 | Latência para alerta (150ms) |
| `{$ICMP.RESPONSE_TIME.CRIT}` | 0.5 | Latência crítica (500ms) |
| `{$ICMP.JITTER.WARN}` | 0.05 | Jitter para alerta (50ms) |
| `{$ICMP.COUNT}` | 5 | Pacotes ICMP por verificação |
| `{$LINK.NAME}` | Link Principal | Nome descritivo do link |
| `{$LINK.PROVIDER}` | Provedor | Nome da operadora |
| `{$DOWNTIME.MINUTES.CRIT}` | 5 | Minutos DOWN para trigger DISASTER |

#### Gráficos incluídos

- Latência ICMP: mínimo, médio e máximo
- Perda de pacotes e jitter
- Disponibilidade acumulada: 24h, 7 dias e 30 dias

---

## Em Breve

| Template | Descrição |
|---|---|
| `template_mikrotik_snmp.yaml` | Monitoramento completo de roteadores MikroTik via SNMP v2c |
| `template_switch_datacom.yaml` | Monitoramento de switches DATACOM DM1200E via SNMP |

> Os templates MikroTik e DATACOM estão em desenvolvimento e serão baseados em experiência real com esses equipamentos.
