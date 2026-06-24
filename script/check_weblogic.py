#!/usr/bin/env python3
# =============================================================================
# check_weblogic.py
# =============================================================================
# Health check para Oracle WebLogic Server via REST Management API.
# Retorna métricas de saúde dos servers, datasources, aplicações e JVM
# no formato esperado pelo Zabbix (valor simples ou JSON para LLD).
#
# Uso no Zabbix:
#   UserParameter=weblogic.check[*],/etc/zabbix/scripts/check_weblogic.py $1 $2 $3 $4 $5
#
# Parâmetros:
#   $1 = host (ex: weblogic.sefa.pa.gov.br)
#   $2 = porta admin (ex: 7001)
#   $3 = usuário admin (ex: weblogic)
#   $4 = senha admin
#   $5 = métrica (server.state, server.health, datasource.state,
#                 app.state, jvm.heap.used, jvm.heap.max,
#                 cluster.servers, discovery.servers, discovery.datasources,
#                 discovery.apps)
#
# Exemplos de chamada:
#   check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA server.state
#   check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA jvm.heap.used
#   check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA discovery.servers
#
# Desenvolvido por: João Paulo de Lima Saraiva
# Baseado em uso real do Oracle WebLogic 11g, 12c e 14c na SEFA/PA:
#   - Analista de Sistema Sênior (DevOps) — FADESP/SEFA (2022-2026)
#   - Administração de Oracle WebLogic como middleware das aplicações Java
#     da Secretaria da Fazenda do Estado do Pará
#
# Compatível com: WebLogic 12c (12.2.x) e 14c (14.1.x)
# Requer: Python 3.6+, requests
#
# Repositório: https://github.com/joaoplsaraiva/zabbix-templates
# =============================================================================

import sys
import json
import argparse
import urllib3
import logging
from typing import Any, Dict, Optional, Union

try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    print("ERRO: módulo 'requests' não encontrado. Instale com: pip3 install requests")
    sys.exit(1)

# Suprime warnings de certificado SSL autoassinado (comum em WebLogic)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── Configurações ────────────────────────────────────────────────────────────
TIMEOUT        = 15          # Timeout das requisições HTTP em segundos
ERROR_VALUE    = -1          # Valor de retorno em caso de erro numérico
ERROR_STRING   = "ERROR"     # Valor de retorno em caso de erro de string
API_BASE_PATH  = "/management/weblogic/latest"

# Logging para diagnóstico (vai para stderr, não interfere no retorno do Zabbix)
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s [check_weblogic] %(message)s",
    stream=sys.stderr
)
log = logging.getLogger(__name__)


# =============================================================================
# Cliente WebLogic REST API
# =============================================================================

class WebLogicClient:
    """
    Cliente para a WebLogic REST Management API.

    Documentação da API:
    https://docs.oracle.com/en/middleware/standalone/weblogic-server/14.1.1.0/wlrmr/

    Endpoints principais usados:
      /management/weblogic/latest/domainRuntime/serverRuntimes          - servers
      /management/weblogic/latest/domainRuntime/serverRuntimes/{}/JVMRuntime - JVM
      /management/weblogic/latest/domainRuntime/serverRuntimes/{}/JDBCServiceRuntime - datasources
      /management/weblogic/latest/domainRuntime/deploymentManager       - apps
    """

    def __init__(self, host: str, port: int, user: str, password: str,
                 use_ssl: bool = False, verify_ssl: bool = False):
        self.host       = host
        self.port       = port
        self.auth       = HTTPBasicAuth(user, password)
        self.verify_ssl = verify_ssl
        scheme          = "https" if use_ssl else "http"
        self.base_url   = f"{scheme}://{host}:{port}{API_BASE_PATH}"
        self.session    = requests.Session()
        self.session.auth    = self.auth
        self.session.verify  = verify_ssl
        self.session.headers.update({
            "Accept":       "application/json",
            "Content-Type": "application/json",
            "X-Requested-By": "Zabbix"
        })

    def _get(self, path: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Realiza GET na REST API do WebLogic."""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            log.error(f"Sem conexão com {self.host}:{self.port} — verifique host, porta e firewall")
            return None
        except requests.exceptions.Timeout:
            log.error(f"Timeout ({TIMEOUT}s) ao conectar em {self.host}:{self.port}")
            return None
        except requests.exceptions.HTTPError as e:
            log.error(f"HTTP {e.response.status_code} em {url}: {e}")
            return None
        except ValueError as e:
            log.error(f"Resposta não é JSON válido: {e}")
            return None

    # ── Servers ───────────────────────────────────────────────────────────────

    def get_server_runtimes(self) -> Optional[Dict]:
        """Retorna runtime de todos os servers do domínio."""
        return self._get("/domainRuntime/serverRuntimes", params={"fields": "name,state,health,listenAddress,listenPort,serverVersion"})

    def get_server_state(self, server_name: str = "AdminServer") -> str:
        """
        Retorna o estado de um server específico.
        Estados possíveis: RUNNING, STARTING, STANDBY, ADMIN, RESUMING,
                          SUSPENDING, FORCE_SUSPENDING, SHUTDOWN, FAILED,
                          FAILED_NOT_RESTARTABLE
        """
        data = self._get(f"/domainRuntime/serverRuntimes/{server_name}")
        if not data:
            return ERROR_STRING
        return data.get("state", ERROR_STRING)

    def get_server_health(self, server_name: str = "AdminServer") -> str:
        """
        Retorna o estado de saúde de um server.
        Valores: HEALTH_OK, HEALTH_WARN, HEALTH_CRITICAL, HEALTH_FAILED,
                HEALTH_OVERLOADED, LOW_MEMORY_REASON
        """
        data = self._get(f"/domainRuntime/serverRuntimes/{server_name}")
        if not data:
            return ERROR_STRING
        health = data.get("health", {})
        return health.get("state", ERROR_STRING) if isinstance(health, dict) else str(health)

    def count_servers_running(self) -> int:
        """Conta quantos servers estão em estado RUNNING no domínio."""
        data = self.get_server_runtimes()
        if not data:
            return ERROR_VALUE
        servers = data.get("items", [])
        return sum(1 for s in servers if s.get("state") == "RUNNING")

    def count_servers_failed(self) -> int:
        """Conta quantos servers estão em estado FAILED no domínio."""
        data = self.get_server_runtimes()
        if not data:
            return ERROR_VALUE
        servers = data.get("items", [])
        return sum(1 for s in servers if s.get("state") in ("FAILED", "FAILED_NOT_RESTARTABLE"))

    # ── JVM ───────────────────────────────────────────────────────────────────

    def get_jvm_heap_used(self, server_name: str = "AdminServer") -> int:
        """
        Retorna memória heap JVM usada em bytes.
        Heap usado = total alocado - livre.
        """
        data = self._get(f"/domainRuntime/serverRuntimes/{server_name}/JVMRuntime",
                         params={"fields": "heapSizeCurrent,heapFreeCurrent,heapSizeMax"})
        if not data:
            return ERROR_VALUE
        heap_current = data.get("heapSizeCurrent", 0)
        heap_free    = data.get("heapFreeCurrent", 0)
        return max(0, heap_current - heap_free)

    def get_jvm_heap_max(self, server_name: str = "AdminServer") -> int:
        """Retorna memória heap máxima configurada na JVM em bytes (-Xmx)."""
        data = self._get(f"/domainRuntime/serverRuntimes/{server_name}/JVMRuntime",
                         params={"fields": "heapSizeMax"})
        if not data:
            return ERROR_VALUE
        return data.get("heapSizeMax", ERROR_VALUE)

    def get_jvm_heap_util(self, server_name: str = "AdminServer") -> float:
        """Retorna percentual de uso do heap JVM."""
        used = self.get_jvm_heap_used(server_name)
        max_ = self.get_jvm_heap_max(server_name)
        if used == ERROR_VALUE or max_ == ERROR_VALUE or max_ <= 0:
            return float(ERROR_VALUE)
        return round(used / max_ * 100, 2)

    def get_jvm_uptime(self, server_name: str = "AdminServer") -> int:
        """Retorna uptime da JVM em milissegundos."""
        data = self._get(f"/domainRuntime/serverRuntimes/{server_name}/JVMRuntime",
                         params={"fields": "uptime"})
        if not data:
            return ERROR_VALUE
        return data.get("uptime", ERROR_VALUE)

    # ── Thread Pool ───────────────────────────────────────────────────────────

    def get_thread_pool_hogging(self, server_name: str = "AdminServer") -> int:
        """
        Retorna threads hogging (travadas) no thread pool do WebLogic.
        Threads hogging = executando por mais tempo que o threshold configurado.
        Valor > 0 indica possível deadlock ou processamento lento.
        """
        data = self._get(f"/domainRuntime/serverRuntimes/{server_name}/threadPoolRuntime",
                         params={"fields": "hoggingThreadCount,executeThreadTotalCount,queueLength"})
        if not data:
            return ERROR_VALUE
        return data.get("hoggingThreadCount", ERROR_VALUE)

    def get_thread_pool_queue(self, server_name: str = "AdminServer") -> int:
        """Retorna tamanho atual da fila de trabalho do thread pool."""
        data = self._get(f"/domainRuntime/serverRuntimes/{server_name}/threadPoolRuntime",
                         params={"fields": "queueLength"})
        if not data:
            return ERROR_VALUE
        return data.get("queueLength", ERROR_VALUE)

    def get_thread_pool_total(self, server_name: str = "AdminServer") -> int:
        """Retorna número total de execute threads no thread pool."""
        data = self._get(f"/domainRuntime/serverRuntimes/{server_name}/threadPoolRuntime",
                         params={"fields": "executeThreadTotalCount"})
        if not data:
            return ERROR_VALUE
        return data.get("executeThreadTotalCount", ERROR_VALUE)

    # ── Datasources (JDBC) ────────────────────────────────────────────────────

    def get_datasource_state(self, server_name: str = "AdminServer",
                              datasource_name: str = "jdbc/datasource") -> str:
        """
        Retorna estado de um datasource JDBC.
        Estados: Running, Suspended, Shutdown, Unknown
        """
        path = (f"/domainRuntime/serverRuntimes/{server_name}"
                f"/JDBCServiceRuntime/JDBCDataSourceRuntimeMBeans/{datasource_name}")
        data = self._get(path, params={"fields": "name,state,enabled,numAvailable,numUnavailable"})
        if not data:
            return ERROR_STRING
        return data.get("state", ERROR_STRING)

    def get_datasource_pool_available(self, server_name: str = "AdminServer",
                                       datasource_name: str = "jdbc/datasource") -> int:
        """Retorna conexões disponíveis no pool do datasource."""
        path = (f"/domainRuntime/serverRuntimes/{server_name}"
                f"/JDBCServiceRuntime/JDBCDataSourceRuntimeMBeans/{datasource_name}")
        data = self._get(path, params={"fields": "numAvailable"})
        if not data:
            return ERROR_VALUE
        return data.get("numAvailable", ERROR_VALUE)

    def get_datasource_pool_unavailable(self, server_name: str = "AdminServer",
                                         datasource_name: str = "jdbc/datasource") -> int:
        """Retorna conexões indisponíveis no pool do datasource."""
        path = (f"/domainRuntime/serverRuntimes/{server_name}"
                f"/JDBCServiceRuntime/JDBCDataSourceRuntimeMBeans/{datasource_name}")
        data = self._get(path, params={"fields": "numUnavailable"})
        if not data:
            return ERROR_VALUE
        return data.get("numUnavailable", ERROR_VALUE)

    def get_datasource_wait_seconds(self, server_name: str = "AdminServer",
                                     datasource_name: str = "jdbc/datasource") -> int:
        """Retorna segundos médios de espera por conexão no pool."""
        path = (f"/domainRuntime/serverRuntimes/{server_name}"
                f"/JDBCServiceRuntime/JDBCDataSourceRuntimeMBeans/{datasource_name}")
        data = self._get(path, params={"fields": "waitingForConnectionCurrentCount"})
        if not data:
            return ERROR_VALUE
        return data.get("waitingForConnectionCurrentCount", ERROR_VALUE)

    # ── Aplicações ────────────────────────────────────────────────────────────

    def get_app_state(self, app_name: str, server_name: str = "AdminServer") -> str:
        """
        Retorna estado de deploy de uma aplicação.
        Estados: STATE_ACTIVE, STATE_PREPARED, STATE_NEW, STATE_ADMIN,
                STATE_RETIRED, STATE_FAILED
        """
        data = self._get(f"/domainRuntime/serverRuntimes/{server_name}"
                         f"/applicationRuntimes/{app_name}",
                         params={"fields": "name,deploymentState,healthState"})
        if not data:
            return ERROR_STRING
        return data.get("deploymentState", ERROR_STRING)

    def count_apps_active(self, server_name: str = "AdminServer") -> int:
        """Conta aplicações em estado STATE_ACTIVE no servidor."""
        data = self._get(f"/domainRuntime/serverRuntimes/{server_name}/applicationRuntimes",
                         params={"fields": "name,deploymentState"})
        if not data:
            return ERROR_VALUE
        apps = data.get("items", [])
        return sum(1 for a in apps if a.get("deploymentState") == "STATE_ACTIVE")

    def count_apps_failed(self, server_name: str = "AdminServer") -> int:
        """Conta aplicações com falha no servidor."""
        data = self._get(f"/domainRuntime/serverRuntimes/{server_name}/applicationRuntimes",
                         params={"fields": "name,deploymentState"})
        if not data:
            return ERROR_VALUE
        apps = data.get("items", [])
        return sum(1 for a in apps if a.get("deploymentState") == "STATE_FAILED")

    # ── Discovery LLD ─────────────────────────────────────────────────────────

    def discovery_servers(self) -> str:
        """
        Retorna JSON para LLD do Zabbix — descoberta de servers do domínio.
        Formato: {"data": [{"{#SERVER.NAME}": "...", ...}]}
        """
        data = self.get_server_runtimes()
        if not data:
            return json.dumps({"data": []})
        servers = data.get("items", [])
        result = []
        for s in servers:
            result.append({
                "{#SERVER.NAME}":    s.get("name", ""),
                "{#SERVER.STATE}":   s.get("state", ""),
                "{#SERVER.HOST}":    s.get("listenAddress", ""),
                "{#SERVER.PORT}":    str(s.get("listenPort", "")),
                "{#SERVER.VERSION}": s.get("serverVersion", ""),
            })
        return json.dumps({"data": result}, ensure_ascii=False)

    def discovery_datasources(self, server_name: str = "AdminServer") -> str:
        """
        Retorna JSON para LLD — descoberta de datasources JDBC do servidor.
        """
        path = (f"/domainRuntime/serverRuntimes/{server_name}"
                f"/JDBCServiceRuntime/JDBCDataSourceRuntimeMBeans")
        data = self._get(path, params={"fields": "name,state,enabled"})
        if not data:
            return json.dumps({"data": []})
        datasources = data.get("items", [])
        result = []
        for ds in datasources:
            result.append({
                "{#DS.NAME}":    ds.get("name", ""),
                "{#DS.STATE}":   ds.get("state", ""),
                "{#DS.ENABLED}": str(ds.get("enabled", "")),
                "{#DS.SERVER}":  server_name,
            })
        return json.dumps({"data": result}, ensure_ascii=False)

    def discovery_apps(self, server_name: str = "AdminServer") -> str:
        """
        Retorna JSON para LLD — descoberta de aplicações deployadas.
        """
        data = self._get(f"/domainRuntime/serverRuntimes/{server_name}/applicationRuntimes",
                         params={"fields": "name,deploymentState"})
        if not data:
            return json.dumps({"data": []})
        apps = data.get("items", [])
        result = []
        for app in apps:
            result.append({
                "{#APP.NAME}":   app.get("name", ""),
                "{#APP.STATE}":  app.get("deploymentState", ""),
                "{#APP.SERVER}": server_name,
            })
        return json.dumps({"data": result}, ensure_ascii=False)


# =============================================================================
# Dispatcher de métricas
# =============================================================================

METRICS: Dict[str, Any] = {
    # Servers
    "server.state":              lambda c, args: c.get_server_state(args.server),
    "server.health":             lambda c, args: c.get_server_health(args.server),
    "server.running.count":      lambda c, args: c.count_servers_running(),
    "server.failed.count":       lambda c, args: c.count_servers_failed(),

    # JVM
    "jvm.heap.used":             lambda c, args: c.get_jvm_heap_used(args.server),
    "jvm.heap.max":              lambda c, args: c.get_jvm_heap_max(args.server),
    "jvm.heap.util":             lambda c, args: c.get_jvm_heap_util(args.server),
    "jvm.uptime":                lambda c, args: c.get_jvm_uptime(args.server),

    # Thread Pool
    "thread.hogging":            lambda c, args: c.get_thread_pool_hogging(args.server),
    "thread.queue":              lambda c, args: c.get_thread_pool_queue(args.server),
    "thread.total":              lambda c, args: c.get_thread_pool_total(args.server),

    # Datasources
    "datasource.state":          lambda c, args: c.get_datasource_state(args.server, args.name),
    "datasource.pool.available": lambda c, args: c.get_datasource_pool_available(args.server, args.name),
    "datasource.pool.unavailable": lambda c, args: c.get_datasource_pool_unavailable(args.server, args.name),
    "datasource.wait":           lambda c, args: c.get_datasource_wait_seconds(args.server, args.name),

    # Aplicações
    "app.state":                 lambda c, args: c.get_app_state(args.name, args.server),
    "app.active.count":          lambda c, args: c.count_apps_active(args.server),
    "app.failed.count":          lambda c, args: c.count_apps_failed(args.server),

    # LLD Discovery
    "discovery.servers":         lambda c, args: c.discovery_servers(),
    "discovery.datasources":     lambda c, args: c.discovery_datasources(args.server),
    "discovery.apps":            lambda c, args: c.discovery_apps(args.server),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Health check Oracle WebLogic via REST Management API para Zabbix",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Métricas disponíveis:
  Servers:
    server.state           Estado do server (RUNNING, FAILED, etc.)
    server.health          Saúde do server (HEALTH_OK, HEALTH_WARN, etc.)
    server.running.count   Número de servers RUNNING no domínio
    server.failed.count    Número de servers FAILED no domínio

  JVM:
    jvm.heap.used          Heap JVM usado (bytes)
    jvm.heap.max           Heap JVM máximo configurado (bytes)
    jvm.heap.util          Percentual de uso do heap JVM (%)
    jvm.uptime             Uptime da JVM (ms)

  Thread Pool:
    thread.hogging         Threads hogging (travadas)
    thread.queue           Tamanho da fila de trabalho
    thread.total           Total de execute threads

  Datasources:
    datasource.state       Estado de um datasource (--name obrigatório)
    datasource.pool.available  Conexões disponíveis no pool
    datasource.pool.unavailable Conexões indisponíveis
    datasource.wait        Requisições aguardando conexão no pool

  Aplicações:
    app.state              Estado de uma app (--name obrigatório)
    app.active.count       Número de apps STATE_ACTIVE
    app.failed.count       Número de apps STATE_FAILED

  LLD (Discovery):
    discovery.servers      JSON LLD com todos os servers do domínio
    discovery.datasources  JSON LLD com todos os datasources
    discovery.apps         JSON LLD com todas as aplicações

Exemplos:
  check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA server.state
  check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA jvm.heap.util --server ManagedServer1
  check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA datasource.state --name jdbc/sefaDS
  check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA app.state --name sefa-webapp
  check_weblogic.py wls.sefa.pa.gov.br 7001 weblogic SENHA discovery.servers
        """
    )

    parser.add_argument("host",     help="Hostname ou IP do Admin Server WebLogic")
    parser.add_argument("port",     type=int, help="Porta do Admin Server (ex: 7001)")
    parser.add_argument("user",     help="Usuário administrador WebLogic")
    parser.add_argument("password", help="Senha do usuário administrador")
    parser.add_argument("metric",   choices=METRICS.keys(), help="Métrica a coletar")

    parser.add_argument("--server", default="AdminServer",
                        help="Nome do Managed Server (padrão: AdminServer)")
    parser.add_argument("--name",   default="",
                        help="Nome do datasource ou aplicação (obrigatório para datasource.* e app.state)")
    parser.add_argument("--ssl",    action="store_true",
                        help="Usar HTTPS (padrão: HTTP)")
    parser.add_argument("--verify-ssl", action="store_true",
                        help="Verificar certificado SSL (padrão: ignorar — útil para certs autoassinados)")
    parser.add_argument("--timeout", type=int, default=TIMEOUT,
                        help=f"Timeout das requisições HTTP em segundos (padrão: {TIMEOUT})")

    return parser


def main() -> int:
    parser  = build_parser()
    args    = parser.parse_args()

    # Validações adicionais
    if args.metric in ("datasource.state", "datasource.pool.available",
                       "datasource.pool.unavailable", "datasource.wait",
                       "app.state") and not args.name:
        log.error(f"A métrica '{args.metric}' requer --name (nome do datasource ou aplicação)")
        print(ERROR_STRING)
        return 1

    # Instancia o cliente
    client = WebLogicClient(
        host       = args.host,
        port       = args.port,
        user       = args.user,
        password   = args.password,
        use_ssl    = args.ssl,
        verify_ssl = args.verify_ssl,
    )

    # Executa a métrica solicitada
    try:
        handler = METRICS[args.metric]
        result  = handler(client, args)
        print(result)
        return 0
    except KeyError:
        log.error(f"Métrica desconhecida: {args.metric}")
        print(ERROR_STRING)
        return 1
    except Exception as e:
        log.error(f"Erro inesperado ao coletar '{args.metric}': {e}")
        print(ERROR_STRING)
        return 1


if __name__ == "__main__":
    sys.exit(main())
