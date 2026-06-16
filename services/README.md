# ⚙️ Services Templates

Templates para monitoramento de serviços de infraestrutura: balanceador de carga,
servidor web e orquestração de containers.

---

## Templates Disponíveis

### `template_haproxy.yaml`

Monitoramento completo do HAProxy via HTTP Stats API (CSV).
Baseado no uso real do HAProxy como load balancer na SEFA/PA em conjunto com Pacemaker.

**Compatibilidade:** Zabbix 6.0 LTS e 7.0 LTS | HAProxy 2.x e 3.x

#### Pré-requisito

```haproxy
frontend stats
    bind *:8404
    stats enable
    stats uri /haproxy?stats
    stats refresh 10s
```

#### Items monitorados

| Item | Tipo | Intervalo | Descrição |
|---|---|---|---|
| Processo em execução | Agent | 60s | Verifica se o HAProxy está rodando |
| CPU do processo (%) | Agent | 60s | CPU consumida pelo processo |
| Memória do processo (bytes) | Agent | 60s | RAM RSS utilizada |
| Stats CSV bruto | HTTP Agent | 60s | Dados completos da stats page |
| Conexões atuais | Agent | 60s | Total de conexões ativas |
| Sessões por segundo | Agent | 60s | Taxa de novas sessões |
| Máximo de sessões | Agent | 60s | Pico histórico de sessões simultâneas |
| Servidores UP | Agent | 30s | Backends com status UP |
| Servidores DOWN | Agent | 30s | Backends com status DOWN |
| Fila de requisições | Agent | 30s | Requisições aguardando servidor |
| Tempo de resposta backends (ms) | Agent | 60s | rtime médio dos backends |
| Bytes recebidos/s | Agent | 60s | Tráfego de entrada |
| Bytes enviados/s | Agent | 60s | Tráfego de saída |
| Erros HTTP 4xx/s | Agent | 60s | Taxa de erros do cliente |
| Erros HTTP 5xx/s | Agent | 60s | Taxa de erros do servidor |
| Health checks com falha/s | Agent | 30s | Falhas nos health checks |

#### Triggers configuradas

| Trigger | Severidade | Condição padrão |
|---|---|---|
| Processo parou | DISASTER | proc.num = 0 |
| Servidor(es) DOWN | HIGH | ≥ 1 servidor DOWN |
| Fila alta | WARNING | ≥ 10 requisições na fila |
| Resposta backend lenta | WARNING | > 500ms por 5 min |

#### Macros configuráveis

| Macro | Padrão | Descrição |
|---|---|---|
| `{$HAPROXY.STATS.URL}` | http://localhost:8404/haproxy?stats;csv | URL da stats page |
| `{$HAPROXY.BACKEND.QUEUE.WARN}` | 10 | Fila para alerta |
| `{$HAPROXY.BACKEND.RTIME.WARN}` | 500 | Latência backend (ms) |
| `{$HAPROXY.SERVER.DOWN.WARN}` | 1 | Servidores DOWN para alerta |

#### Gráficos incluídos
- Conexões e Sessões
- Servidores UP / DOWN
- Tráfego (bytes/s)
- Erros HTTP (4xx / 5xx)

---

### `template_apache.yaml`

Monitoramento completo do Apache HTTP Server via `mod_status`.
Baseado no uso real do Apache como servidor web e proxy reverso na SEFA/PA.

**Compatibilidade:** Zabbix 6.0 LTS e 7.0 LTS | Apache 2.4.x

#### Pré-requisito

```apache
<Location /server-status>
    SetHandler server-status
    Require ip 127.0.0.1 SEU_ZABBIX_IP
</Location>
```

#### Items monitorados

| Item | Tipo | Intervalo | Descrição |
|---|---|---|---|
| Processo em execução | Agent | 60s | Número de processos httpd/apache2 |
| CPU do processo (%) | Agent | 60s | CPU de todos os workers |
| Memória do processo (bytes) | Agent | 60s | RAM RSS total |
| Status page raw | HTTP Agent | 60s | Dados do mod_status (item master) |
| Workers ocupados | Dependent | — | Workers processando requisições |
| Workers ociosos | Dependent | — | Workers aguardando requisições |
| Utilização de workers (%) | Calculated | 60s | busy / (busy + idle) × 100 |
| Requisições por segundo | Dependent | — | Taxa de req/s |
| Bytes por segundo | Dependent | — | Taxa de transferência |
| Total de acessos | Dependent | — | Contador cumulativo |
| Uptime do servidor (s) | Dependent | — | Tempo desde o último restart |
| CPU Load do Apache (%) | Dependent | — | CPU reportada pelo mod_status |
| Tempo de resposta HTTP (s) | Agent | 60s | Latência do serviço |

#### Triggers configuradas

| Trigger | Severidade | Condição padrão |
|---|---|---|
| Processo parou | DISASTER | proc.num = 0 |
| Workers críticos | HIGH | > 95% ocupados |
| Workers elevados | WARNING | > 80% ocupados |
| Resposta HTTP lenta | WARNING | > 5s |
| Serviço reiniciado | INFO | uptime < 10 min |

#### Macros configuráveis

| Macro | Padrão | Descrição |
|---|---|---|
| `{$APACHE.STATUS.URL}` | http://localhost/server-status?auto | URL do mod_status |
| `{$APACHE.WORKERS.UTIL.CRIT}` | 95 | Workers críticos (%) |
| `{$APACHE.WORKERS.UTIL.WARN}` | 80 | Workers alerta (%) |
| `{$APACHE.RESPONSE.TIME.WARN}` | 5 | Resposta lenta (s) |
| `{$APACHE.PROCESS.NAME}` | httpd | Nome do processo (httpd ou apache2) |

#### Gráficos incluídos
- Workers (ocupados / ociosos)
- Requisições e Tráfego

---

### `template_docker.yaml`

Monitoramento completo do Docker Engine via **Zabbix Agent 2**.
Cobre daemon, containers (LLD), imagens, volumes, redes e métricas por container.

**Compatibilidade:** Zabbix 6.0 LTS e 7.0 LTS | Docker Engine 20.x+
**Requer:** Zabbix Agent 2 (não funciona com Agent clássico)

#### Pré-requisito

```bash
# Adicionar usuário zabbix ao grupo docker
usermod -aG docker zabbix
systemctl restart zabbix-agent2
```

#### Items monitorados

| Item | Tipo | Intervalo | Descrição |
|---|---|---|---|
| Daemon em execução | Agent | 60s | Processo dockerd rodando |
| Versão do Engine | Agent 2 | 1h | Versão instalada |
| Total de containers | Agent 2 | 60s | Todos os estados |
| Containers running | Agent 2 | 30s | Em execução |
| Containers stopped | Agent 2 | 60s | Parados/exited |
| Containers paused | Agent 2 | 60s | Pausados |
| Total de imagens | Agent 2 | 5m | Imagens no host |
| Imagens dangling | Agent 2 | 5m | Sem tag/não usadas |
| Total de volumes | Agent 2 | 5m | Volumes criados |
| Total de redes | Agent 2 | 5m | Redes Docker |
| Espaço /var/lib/docker | Agent | 5m | Disco usado pelo Docker |

#### LLD — por container (automático)

| Item | Intervalo | Descrição |
|---|---|---|
| Status do container | 30s | running, exited, paused... |
| CPU (%) | 60s | Uso de CPU |
| Memória (%) | 60s | % do limit configurado |
| Memória (bytes) | 60s | Uso absoluto em bytes |
| Rede recebida (Bps) | 60s | Bytes recebidos |
| Rede enviada (Bps) | 60s | Bytes enviados |

#### Triggers configuradas

| Trigger | Severidade | Condição padrão |
|---|---|---|
| Daemon parou | DISASTER | dockerd não encontrado |
| Container não está running (por LLD) | HIGH | state ≠ running |
| Memória crítica do container (por LLD) | HIGH | > 95% |
| Memória elevada do container (por LLD) | WARNING | > 80% |
| Imagens dangling acumuladas | INFO | ≥ 5 dangling |

#### Macros configuráveis

| Macro | Padrão | Descrição |
|---|---|---|
| `{$DOCKER.SOCK}` | unix:///var/run/docker.sock | Socket do daemon |
| `{$CONTAINER.CPU.WARN}` | 80 | CPU do container (%) |
| `{$CONTAINER.MEM.CRIT}` | 95 | Memória crítica (%) |
| `{$CONTAINER.MEM.WARN}` | 80 | Memória alerta (%) |
| `{$DOCKER.IMAGES.DANGLING.WARN}` | 5 | Imagens dangling |

#### Gráficos incluídos
- Containers por Estado (running / paused / stopped)
- Imagens e Volumes

---

## Em Breve

| Template | Descrição |
|---|---|
| `template_mysql.yaml` | MySQL via Zabbix Agent 2 — queries, conexões, replication lag |
| `template_oracle_db.yaml` | Oracle DB via ODBC — tablespace, sessions, wait events |
