# 🗄️ Database Templates

Templates para monitoramento de bancos de dados relacionais utilizados em produção na SEFA/PA.

---

## Templates Disponíveis

### `template_mysql.yaml`

Monitoramento completo do **MySQL/MariaDB** via **Zabbix Agent 2** (plugin nativo).
Baseado no uso real do MySQL na SEFA/PA como banco de dados de sistemas internos e ferramentas de monitoramento.

**Compatibilidade:** Zabbix 6.0 LTS e 7.0 LTS | MySQL 5.7+, MySQL 8.x, MariaDB 10.x
**Requer:** Zabbix Agent 2 com plugin MySQL

#### Pré-requisito

```sql
-- Criar usuário de monitoramento
CREATE USER 'zabbix'@'localhost' IDENTIFIED BY 'SUA_SENHA';
GRANT USAGE, REPLICATION CLIENT, PROCESS,
      SHOW DATABASES, SHOW VIEW ON *.* TO 'zabbix'@'localhost';
FLUSH PRIVILEGES;
```

```ini
# /etc/zabbix/zabbix_agent2.d/mysql.conf
Plugins.Mysql.Sessions.Prod.Uri=tcp://localhost:3306
Plugins.Mysql.Sessions.Prod.User=zabbix
Plugins.Mysql.Sessions.Prod.Password=SUA_SENHA
```

#### Items monitorados

| Categoria | Item | Intervalo |
|---|---|---|
| Processo | mysqld em execução | 60s |
| Disponibilidade | Ping / tempo de resposta | 60s |
| Sistema | Versão, uptime | 60s / 1h |
| Conexões | Ativas, máximo, pico, recusadas, percentual de uso | 60s / 1h |
| Queries | QPS total, slow queries/s, SELECT/INSERT/UPDATE/DELETE por segundo | 60s |
| InnoDB | Buffer Pool (tamanho, dirty pages), leituras/escritas em disco | 60s / 1h |
| Locks | Lock waits/s, tempo médio de espera (ms) | 60s |
| Replicação | SQL Thread status, IO Thread status, lag (s) | 60s |
| Tráfego | Bytes recebidos/enviados por segundo | 60s |

#### Triggers configuradas

| Trigger | Severidade | Condição padrão |
|---|---|---|
| Processo parou | DISASTER | proc.num = 0 |
| Sem resposta ao ping | HIGH | ping = 0 |
| Conexões críticas | HIGH | > 95% de max_connections |
| Conexões elevadas | WARNING | > 80% de max_connections |
| Conexões sendo recusadas | HIGH | Connection_errors > 0 |
| Slow queries elevadas | WARNING | > 5/s |
| Lock waits elevados | WARNING | > 5/s |
| SQL Thread parado | HIGH | Slave_SQL_Running ≠ Yes |
| Lag crítico na replicação | HIGH | > 300s |
| Lag elevado na replicação | WARNING | > 30s |
| Servidor reiniciado | WARNING | uptime < 10 min |

#### Macros configuráveis

| Macro | Padrão | Descrição |
|---|---|---|
| `{$MYSQL.DSN}` | tcp://localhost:3306 | DSN de conexão |
| `{$MYSQL.USER}` | zabbix | Usuário de monitoramento |
| `{$MYSQL.CONNECTIONS.MAX.CRIT}` | 95 | Conexões críticas (%) |
| `{$MYSQL.CONNECTIONS.MAX.WARN}` | 80 | Conexões alerta (%) |
| `{$MYSQL.SLOW.QUERIES.WARN}` | 5 | Slow queries/s para alerta |
| `{$MYSQL.REPL.LAG.CRIT}` | 300 | Lag de replicação crítico (s) |
| `{$MYSQL.REPL.LAG.WARN}` | 30 | Lag de replicação alerta (s) |
| `{$MYSQL.LOCK.WAIT.WARN}` | 5 | Lock waits/s para alerta |

#### Gráficos incluídos
- Conexões (ativas e percentual de uso)
- Queries por tipo (SELECT/INSERT/UPDATE/DELETE)
- InnoDB I/O (leituras e escritas em disco)
- Replicação — Lag em segundos

---

### `template_oracle_db.yaml`

Monitoramento completo do **Oracle Database** via **ODBC**.
Baseado em uso real desde 2011 na SEFA/PA com Oracle 11g, 12c e 19c em ambientes críticos de produção da Secretaria da Fazenda do Estado do Pará.

**Compatibilidade:** Zabbix 6.0 LTS e 7.0 LTS | Oracle 11g, 12c, 19c, 21c
**Requer:** Driver Oracle ODBC e `odbc.ini` configurado no servidor Zabbix

#### Pré-requisito 1 — Usuário de monitoramento Oracle

```sql
CREATE USER zabbix IDENTIFIED BY SUA_SENHA;
GRANT CREATE SESSION TO zabbix;
GRANT SELECT ON v_$instance                  TO zabbix;
GRANT SELECT ON v_$database                  TO zabbix;
GRANT SELECT ON v_$session                   TO zabbix;
GRANT SELECT ON v_$sysstat                   TO zabbix;
GRANT SELECT ON v_$system_wait_class         TO zabbix;
GRANT SELECT ON v_$log                       TO zabbix;
GRANT SELECT ON v_$log_history               TO zabbix;
GRANT SELECT ON v_$sgastat                   TO zabbix;
GRANT SELECT ON v_$parameter                 TO zabbix;
GRANT SELECT ON v_$rman_backup_job_details   TO zabbix;
GRANT SELECT ON dba_tablespace_usage_metrics TO zabbix;
GRANT SELECT ON dba_scheduler_jobs           TO zabbix;
```

#### Pré-requisito 2 — Configurar ODBC

```ini
# /etc/odbc.ini
[ORACLE_PROD]
Driver     = Oracle 19c ODBC driver
ServerName = //oracle-host:1521/ORCL
UserID     = zabbix
Password   = SUA_SENHA
```

#### Items monitorados

| Categoria | Item | Intervalo |
|---|---|---|
| Instância | Status (OPEN/MOUNTED/...), modo do banco, nome, versão, uptime | 60s / 1h |
| Sessões | Ativas, total, bloqueadas, limite configurado | 30s / 60s |
| Tablespaces | SYSTEM, SYSAUX, USERS, TEMP — uso em % | 5m |
| SGA | Tamanho total, Buffer Cache, Shared Pool | 5m |
| Redo Logs | Switches/hora, status dos grupos | 5m |
| Wait Events | I/O, CPU, Concorrência (latch) em segundos | 60s |
| Backup RMAN | Status do último backup, horas desde o último backup | 30m |
| Jobs | Scheduler jobs com falha nas últimas 24h | 30m |

#### Triggers configuradas

| Trigger | Severidade | Condição padrão |
|---|---|---|
| Instância não está OPEN | DISASTER | STATUS ≠ OPEN |
| Sessões bloqueadas | HIGH | ≥ 5 sessões bloqueadas |
| Tablespace SYSTEM crítica | DISASTER | > 95% — banco pode travar |
| Tablespace SYSTEM elevada | HIGH | > 80% |
| Tablespace USERS crítica | HIGH | > 95% |
| Tablespace USERS elevada | WARNING | > 80% |
| Redo switches excessivos | WARNING | > 20/hora |
| Backup RMAN com falha | HIGH | status ≠ COMPLETED |
| Sem backup há > 2 dias | HIGH | > 48h sem backup |
| Sem backup há > 1 dia | WARNING | > 24h sem backup |
| Jobs com falha | WARNING | > 0 jobs falharam |
| Instância reiniciada | WARNING | uptime < 1 hora |

#### Macros configuráveis

| Macro | Padrão | Descrição |
|---|---|---|
| `{$ORACLE.DSN}` | ORACLE_PROD | Nome do DSN ODBC |
| `{$ORACLE.TABLESPACE.UTIL.CRIT}` | 95 | Tablespace crítica (%) |
| `{$ORACLE.TABLESPACE.UTIL.WARN}` | 80 | Tablespace alerta (%) |
| `{$ORACLE.BLOCKED.SESSIONS.WARN}` | 5 | Sessões bloqueadas para alerta |
| `{$ORACLE.REDO.SWITCHES.WARN}` | 20 | Log switches/hora |
| `{$ORACLE.BACKUP.AGE.CRIT}` | 2 | Dias sem backup — crítico |
| `{$ORACLE.BACKUP.AGE.WARN}` | 1 | Dias sem backup — alerta |
| `{$ORACLE.ACTIVE.SESSIONS.WARN}` | 100 | Sessões ativas para alerta |

#### Gráficos incluídos
- Sessões (ativas / total / bloqueadas)
- Tablespaces — uso % (SYSTEM, SYSAUX, USERS, TEMP)
- Wait Events (I/O / CPU / Concorrência)
- SGA — Buffer Cache e Shared Pool
