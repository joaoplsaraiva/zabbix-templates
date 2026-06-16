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

### `template_mikrotik_snmp.yaml`

Template completo para monitoramento de roteadores MikroTik via **SNMP v2c**.
Desenvolvido com base em certificação SENAI/CEDAM — MikroTik Mod I (60h, 2019) e experiência prática na SEFA/PA.

**Compatibilidade:** Zabbix 6.0 LTS e 7.0 LTS | RouterOS 6.x e 7.x

#### Pré-requisito: habilitar SNMP no MikroTik

```bash
# No terminal do RouterOS (Winbox ou SSH)
/snmp set enabled=yes community=PUBLIC contact="" location=""
/snmp print
```

#### Como usar

1. Crie um **host** para cada roteador MikroTik no Zabbix
2. Defina o **IP do host** como o IP de gerência do roteador
3. Em **Host interfaces**, adicione interface **SNMP** com a community configurada
4. Aplique este template ao host
5. Ajuste as macros `{$SNMP.COMMUNITY}` e `{$TEMP.MAX.WARN}` conforme o modelo

#### Items monitorados

| Categoria | Item | Intervalo |
|---|---|---|
| Sistema | Uptime, nome, modelo, número de série | 60s / 1h |
| Sistema | Versão do RouterOS | 1h |
| CPU | Uso total (%), frequência (MHz) | 60s / 5m |
| Memória | Total, em uso (bytes), percentual (%) | 60s / 1h |
| Disco | Espaço total e em uso no flash | 1h / 5m |
| Temperatura | CPU (°C), placa mãe (°C) | 2m |
| Energia | Tensão de entrada (V) | 5m |
| Wireless | Clientes conectados, frequência (MHz), sinal (dBm) | 60s / 5m |
| VPN | Sessões L2TP ativas | 60s |
| Roteamento | Número de rotas na tabela | 5m |
| Rede | Descoberta automática de interfaces (LLD) | 1h |
| SNMP | Disponibilidade do agente | 60s |

#### Triggers configuradas

| Trigger | Severidade | Condição padrão |
|---|---|---|
| SNMP indisponível | HIGH | Sem resposta SNMP |
| Dispositivo reiniciado | WARNING | Uptime < 10 min |
| CPU crítica | HIGH | > 95% por 5 min |
| CPU elevada | WARNING | > 80% por 5 min |
| Memória crítica | HIGH | > 95% |
| Memória elevada | WARNING | > 80% |
| Temperatura CPU crítica | HIGH | > 75°C |
| Temperatura CPU elevada | WARNING | > 60°C |
| Sessões VPN no limite | WARNING | ≥ 50 sessões |

#### Macros configuráveis

| Macro | Valor padrão | Descrição |
|---|---|---|
| `{$SNMP.COMMUNITY}` | PUBLIC | Community SNMP v2c do MikroTik |
| `{$CPU.UTIL.CRIT}` | 95 | Limite crítico de CPU (%) |
| `{$CPU.UTIL.WARN}` | 80 | Limite de alerta de CPU (%) |
| `{$MEMORY.UTIL.CRIT}` | 95 | Limite crítico de memória (%) |
| `{$MEMORY.UTIL.WARN}` | 80 | Limite de alerta de memória (%) |
| `{$TEMP.MAX.CRIT}` | 75 | Temperatura crítica (°C) |
| `{$TEMP.MAX.WARN}` | 60 | Temperatura de alerta (°C) |
| `{$VPN.SESSIONS.MAX}` | 50 | Máximo de sessões VPN ativas |
| `{$UPTIME.MIN.WARN}` | 600 | Uptime mínimo antes de alertar reboot |

#### Gráficos incluídos

- CPU e Memória (%)
- Temperatura CPU e placa mãe (°C)
- Clientes Wireless e Sessões VPN ativas

> **Observação sobre temperatura:** nem todos os modelos MikroTik possuem sensor de temperatura.
> Modelos suportados: RB4011, CCR1xxx, CCR2xxx, CRS3xx, RB1100.
> Em modelos sem sensor, os items retornarão sem valor (unsupported) — não impacta as outras métricas.

---

### `template_switch_datacom.yaml`

Monitoramento completo para switches **DATACOM linha DM1200E** via SNMP v2c.
Baseado no treinamento: *Configuração e Operação da Linha DM1200E — DATACOM/SEFA (24h, 2015)*.

**Compatibilidade:** Zabbix 6.0 LTS e 7.0 LTS
**Testado em:** DM1200E-4S, DM1200E-28S, DM1200E-52P

#### Pré-requisito

```
switch(config)# snmp-server community PUBLIC ro
switch(config)# snmp-server enable traps
```

#### Items monitorados

| Categoria | Item | Intervalo |
|---|---|---|
| Sistema | Uptime, hostname, firmware, localização | 60s / 1h |
| CPU | Uso total (%) | 60s |
| Memória | Total, em uso (bytes), percentual (%) | 60s / 1h |
| Temperatura | Temperatura interna (°C) | 2m |
| Interfaces | Descoberta automática de portas (LLD) | 1h |
| Spanning-Tree | Modo STP, mudanças de topologia, tempo desde última mudança | 60s / 5m |
| LACP | Número de grupos Port-Channel ativos | 5m |
| MAC Table | Total de endereços aprendidos | 5m |
| SNMP | Disponibilidade do agente | 60s |

#### Triggers configuradas

| Trigger | Severidade | Condição padrão |
|---|---|---|
| SNMP indisponível | HIGH | Sem resposta |
| Switch reiniciado | WARNING | Uptime < 10 min |
| CPU crítica | HIGH | > 95% por 5 min |
| CPU elevada | WARNING | > 80% por 5 min |
| Memória crítica | HIGH | > 95% |
| Memória elevada | WARNING | > 80% |
| Temperatura crítica | HIGH | > 70°C |
| Temperatura elevada | WARNING | > 55°C |
| Instabilidade STP | WARNING | > 5 mudanças de topologia |

#### Macros configuráveis

| Macro | Padrão | Descrição |
|---|---|---|
| `{$SNMP.COMMUNITY}` | PUBLIC | Community SNMP v2c |
| `{$CPU.UTIL.CRIT}` | 95 | Limite crítico de CPU (%) |
| `{$CPU.UTIL.WARN}` | 80 | Limite de alerta de CPU (%) |
| `{$TEMP.MAX.CRIT}` | 70 | Temperatura crítica (°C) |
| `{$TEMP.MAX.WARN}` | 55 | Temperatura de alerta (°C) |

#### Gráficos incluídos
- CPU e Memória (%)
- Temperatura (°C)
- Mudanças de Topologia STP

