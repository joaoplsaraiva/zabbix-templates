# 🔧 Scripts de Monitoramento

Scripts externos para o Zabbix — usados via `UserParameter` no agente.
Desenvolvidos com base em necessidades reais de monitoramento na SEFA/PA.

---

## Instalação geral

```bash
# Copiar scripts para o diretório de scripts do Zabbix Agent
sudo mkdir -p /etc/zabbix/scripts
sudo cp check_certificate.sh /etc/zabbix/scripts/
sudo cp check_weblogic.py /etc/zabbix/scripts/

# Ajustar permissões
sudo chmod 750 /etc/zabbix/scripts/check_certificate.sh
sudo chmod 750 /etc/zabbix/scripts/check_weblogic.py
sudo chown zabbix:zabbix /etc/zabbix/scripts/check_*.{sh,py}
```

---

## Scripts Disponíveis

### `check_certificate.sh`

Verifica a expiração de certificados SSL/TLS em endpoints HTTPS ou arquivos `.pem`.
Retorna o número de dias até a expiração (negativo = já expirado).

**Baseado em:** monitoramento de certificados Let's Encrypt (via Cert-Manager) e
certificados autoassinados do RestPKI da Lacuna na SEFA/PA.

**Dependências:** `bash`, `openssl`, `date` (GNU — padrão no Fedora/CentOS/Oracle Linux)

#### Instalação e configuração no Zabbix Agent

```bash
# /etc/zabbix/zabbix_agent2.d/ssl_cert.conf
# ou /etc/zabbix/zabbix_agentd.d/ssl_cert.conf

UserParameter=ssl.cert.expiry[*],/etc/zabbix/scripts/check_certificate.sh "$1" "$2"
```

```bash
# Reiniciar o agente após configurar
sudo systemctl restart zabbix-agent2
# ou: sudo systemctl restart zabbix-agent
```

#### Uso do script

```bash
# Verificar endpoint HTTPS na porta padrão (443)
./check_certificate.sh meusite.com.br
# Saída: 127  (dias restantes)

# Verificar porta customizada
./check_certificate.sh meusite.com.br 8443
# Saída: 45

# Verificar arquivo .pem local
./check_certificate.sh /etc/ssl/certs/meu-certificado.pem
# Saída: -3  (expirado há 3 dias)

# Modo verbose — detalhes completos do certificado
./check_certificate.sh --verbose meusite.com.br
./check_certificate.sh --verbose meusite.com.br 8443
```

#### Configurar item no Zabbix

| Campo | Valor |
|---|---|
| Tipo | Zabbix Agent (Active) |
| Chave | `ssl.cert.expiry[meusite.com.br,443]` |
| Tipo de informação | Numérico (inteiro) |
| Unidade | `days` |
| Intervalo | `1h` |

#### Triggers recomendadas

```
# Certificado expira em menos de 30 dias
last(ssl.cert.expiry[{HOST.CONN},{$SSL.PORT}]) < 30
→ Severidade: WARNING

# Certificado expira em menos de 14 dias
last(ssl.cert.expiry[{HOST.CONN},{$SSL.PORT}]) < 14
→ Severidade: HIGH

# Certificado já expirado
last(ssl.cert.expiry[{HOST.CONN},{$SSL.PORT}]) <= 0
→ Severidade: DISASTER
```

#### Valores de retorno

| Valor | Significado |
|---|---|
| `> 0` | Dias restantes até a expiração |
| `0` | Expira hoje |
| `< 0` | Expirado há N dias |
| `-999` | Erro (host inacessível, timeout, arquivo não encontrado) |

---

### `check_weblogic.py`

Health check para **Oracle WebLogic Server 12c e 14c** via REST Management API.
Retorna métricas de servers, JVM, thread pool, datasources JDBC e aplicações.
Suporta LLD (Low Level Discovery) para descoberta automática de componentes.

**Baseado em:** administração real do Oracle WebLogic na SEFA/PA:
- WebLogic 11g (2019-2021) → 12c (2021-2023) → 14c (2023-2026)
- Aplicações Java da Secretaria da Fazenda do Estado do Pará

**Dependências:** Python 3.6+, `requests` (`pip3 install requests`)

**Compatível com:** WebLogic 12c (12.2.x) e 14c (14.1.x)

#### Instalação e configuração

```bash
# Instalar dependência Python
pip3 install requests

# /etc/zabbix/zabbix_agent2.d/weblogic.conf
UserParameter=weblogic.check[*],/etc/zabbix/scripts/check_weblogic.py "$1" "$2" "$3" "$4" "$5" --server "$6" --name "$7"
```

#### Habilitar REST Management API no WebLogic

```xml
<!-- Em $DOMAIN_HOME/config/config.xml, dentro de <server>: -->
<rest-management-interface>
  <enabled>true</enabled>
</rest-management-interface>
```

Ou via console admin:
`Environment → Servers → AdminServer → General → Enable RESTful Management Services`

#### Métricas disponíveis

**Servers**

| Métrica | Retorno | Descrição |
|---|---|---|
| `server.state` | String | Estado do server (RUNNING, FAILED, ADMIN...) |
| `server.health` | String | Saúde (HEALTH_OK, HEALTH_WARN, HEALTH_CRITICAL) |
| `server.running.count` | Inteiro | Servers RUNNING no domínio |
| `server.failed.count` | Inteiro | Servers FAILED no domínio |

**JVM**

| Métrica | Retorno | Descrição |
|---|---|---|
| `jvm.heap.used` | Inteiro (bytes) | Heap JVM em uso |
| `jvm.heap.max` | Inteiro (bytes) | Heap JVM máximo (-Xmx) |
| `jvm.heap.util` | Float (%) | Percentual de uso do heap |
| `jvm.uptime` | Inteiro (ms) | Uptime da JVM |

**Thread Pool**

| Métrica | Retorno | Descrição |
|---|---|---|
| `thread.hogging` | Inteiro | Threads hogging (possível deadlock) |
| `thread.queue` | Inteiro | Fila de trabalho pendente |
| `thread.total` | Inteiro | Total de execute threads |

**Datasources JDBC** (requer `--name jdbc/nomeDS`)

| Métrica | Retorno | Descrição |
|---|---|---|
| `datasource.state` | String | Estado (Running, Suspended, Shutdown) |
| `datasource.pool.available` | Inteiro | Conexões disponíveis no pool |
| `datasource.pool.unavailable` | Inteiro | Conexões indisponíveis |
| `datasource.wait` | Inteiro | Requisições aguardando conexão |

**Aplicações** (requer `--name nome-da-app` para `app.state`)

| Métrica | Retorno | Descrição |
|---|---|---|
| `app.state` | String | Estado (STATE_ACTIVE, STATE_FAILED...) |
| `app.active.count` | Inteiro | Apps STATE_ACTIVE no server |
| `app.failed.count` | Inteiro | Apps STATE_FAILED no server |

**LLD Discovery (JSON para Zabbix)**

| Métrica | Macros geradas |
|---|---|
| `discovery.servers` | `{#SERVER.NAME}`, `{#SERVER.STATE}`, `{#SERVER.HOST}`, `{#SERVER.PORT}` |
| `discovery.datasources` | `{#DS.NAME}`, `{#DS.STATE}`, `{#DS.SERVER}` |
| `discovery.apps` | `{#APP.NAME}`, `{#APP.STATE}`, `{#APP.SERVER}` |

#### Exemplos de uso

```bash
# Estado do AdminServer
./check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA server.state

# Heap JVM de um Managed Server
./check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA jvm.heap.util \
  --server ManagedServer1

# Estado de um datasource JDBC
./check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA datasource.state \
  --name jdbc/sefaOracleDS

# Estado de uma aplicação deployada
./check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA app.state \
  --name sefa-nfe-webapp

# LLD — descoberta de servers para o Zabbix
./check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA discovery.servers

# Usando HTTPS com certificado autoassinado
./check_weblogic.py wls.sefa.pa.gov.br 7002 weblogic SENHA server.state --ssl
```

#### Configurar itens no Zabbix

```
# Item: Estado do server
Chave:  weblogic.check[{HOST.CONN},7001,{$WLS.USER},{$WLS.PASSWORD},server.state,AdminServer,]
Tipo:   Zabbix Agent (Active)
TInfo:  Texto

# Item: Heap JVM usado (bytes)
Chave:  weblogic.check[{HOST.CONN},7001,{$WLS.USER},{$WLS.PASSWORD},jvm.heap.used,AdminServer,]
Tipo:   Zabbix Agent (Active)
TInfo:  Numérico (inteiro)
Unid.:  B

# Item: Datasource JDBC
Chave:  weblogic.check[{HOST.CONN},7001,{$WLS.USER},{$WLS.PASSWORD},datasource.state,AdminServer,jdbc/sefaDS]
Tipo:   Zabbix Agent (Active)
TInfo:  Texto
```

#### Macros recomendadas no host

```
{$WLS.USER}     = weblogic
{$WLS.PASSWORD} = (secret)
{$WLS.PORT}     = 7001
```

---

## Referências

- [OpenSSL s_client](https://www.openssl.org/docs/man1.1.1/man1/s_client.html)
- [WebLogic REST Management API Reference (14c)](https://docs.oracle.com/en/middleware/standalone/weblogic-server/14.1.1.0/wlrmr/)
- [Zabbix UserParameter](https://www.zabbix.com/documentation/current/en/manual/config/items/userparameters)
