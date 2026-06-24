# CLAUDE.md — zabbix-templates

## Contexto do Projeto

Repositório de templates Zabbix desenvolvidos e utilizados em ambiente **corporativo de produção**
na **SEFA — Secretaria da Fazenda do Estado do Pará**, gerenciando infraestrutura crítica de alta disponibilidade.

Mantido por **João Paulo de Lima Saraiva** — Analista de Redes Sênior / DevOps com +15 anos de experiência.

---

## Sobre o Autor

- **Cargo atual:** Analista de Sistemas Sênior (DevOps) — FADESP/SEFA
- **Experiência com Zabbix:** desde 2011 (monitoramento de links, servidores, roteadores na SEFA)
- **Certificações relevantes:** ITIL V3, Red Hat OpenShift (DO280/DO370/DO480/DO467), CertiProf DevOps
- **Stack usada na SEFA:** Oracle Linux, CentOS, Ubuntu, VMware vSphere, Kubernetes, OpenShift, Rancher, HAProxy, Apache, Oracle WebLogic, Kafka, Ansible, GitLab CI, ArgoCD, Prometheus, Grafana, ELK Stack
- **Treinamento específico Zabbix:** Administração do Sistema de Monitoramento Zabbix — Plugue Insights (30h, 2018)

---

## Estrutura do Repositório

```
zabbix-templates/
├── linux/
│   ├── template_linux_by_agent.yaml   # CPU, memória, disco, rede, processos
│   └── README.md
├── network/
│   ├── template_link_internet.yaml    # Uptime, latência, jitter, perda, SLA
│   └── README.md
├── services/                          # em desenvolvimento
├── database/                          # em desenvolvimento
├── kubernetes/                        # em desenvolvimento
└── scripts/                           # em desenvolvimento
```

---

## Padrões e Convenções

### Formato dos arquivos
- Sempre `.yaml` (não `.yml`) — padrão Zabbix 6.x/7.x
- Compatibilidade mínima: **Zabbix 6.0 LTS**
- Testar também em Zabbix 7.0 LTS sempre que possível

### Nomenclatura de templates
```
template_<categoria>_<especificidade>.yaml

Exemplos:
  template_linux_by_agent.yaml
  template_mikrotik_snmp.yaml
  template_oracle_db.yaml
```

### Estrutura obrigatória de cada template YAML
Todo template deve conter:
- `uuid` único para o template e para cada item/trigger/graph
- `description` explicando o que monitora, versão compatível e autor
- `macros` configuráveis para todos os thresholds (nunca hardcode)
- `tags` nos items: `component` (cpu, memory, network, etc.) e `scope` (availability, performance, capacity)
- `triggers` com dependências configuradas (evitar spam de alertas)
- `graphs` para visualização das principais métricas

### Macros — convenção de nomenclatura
```
{$COMPONENTE.METRICA.NIVEL}

Exemplos:
  {$CPU.UTIL.CRIT}        → limite crítico de CPU
  {$CPU.UTIL.WARN}        → limite de alerta de CPU
  {$MEMORY.UTIL.MAX}      → uso máximo de memória
  {$ICMP.RESPONSE_TIME.WARN} → latência para alerta
```

### Severidades de triggers
| Severidade | Quando usar |
|---|---|
| DISASTER | Serviço completamente indisponível |
| HIGH | Impacto severo, requer ação imediata |
| WARNING | Degradação, monitorar com atenção |
| INFO | Mudança de estado, sem impacto |

---

## Ambientes de Referência (SEFA/PA)

Os templates foram criados com base na infraestrutura real da SEFA:

- **Servidores:** Oracle Linux 8/9, CentOS 7/8, Ubuntu 20.04/22.04
- **Rede:** Links internet com múltiplos provedores, switches DATACOM DM1200E, roteadores MikroTik
- **Serviços:** HAProxy, Apache, Oracle WebLogic 14c, Docker, Kubernetes/OpenShift/Rancher
- **Banco de dados:** Oracle DB, MySQL
- **Storage:** HP 3PAR, EMC Data Domain
- **Monitoramento:** Zabbix + Nagios (legado) → migração para Prometheus + Grafana + ELK Stack

---

## Como Contribuir / Expandir

### Próximos templates planejados
1. `kubernetes/template_k8s_nodes.yaml` — status e recursos dos nodes K8s
2. `kubernetes/template_k8s_pods.yaml` — pods por namespace, restarts, OOMKill
3. `scripts/check_certificate.sh` — valida expiração SSL de endpoints
4. `scripts/check_weblogic.py` — health Oracle WebLogic via WLST

### Ao criar novo template
1. Copie a estrutura de um template existente como base
2. Gere UUIDs únicos para todos os objetos (use `uuidgen` ou similar)
3. Teste importação no Zabbix antes de commitar
4. Atualize o `README.md` da pasta correspondente
5. Adicione entrada na tabela do `README.md` principal

---

## Comandos Úteis

```bash
# Validar YAML antes de importar
yamllint template_linux_by_agent.yaml

# Importar via API Zabbix
curl -s -X POST https://SEU_ZABBIX/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"configuration.import","params":{"format":"yaml","rules":{"templates":{"createMissing":true,"updateExisting":true}},"source":"YAML_CONTENT"},"auth":"TOKEN","id":1}'

# Gerar UUID para novos itens
uuidgen | tr '[:upper:]' '[:lower:]' | tr -d '-'
```

---

## Links Úteis

- [Repositório no GitHub](https://github.com/joaoplsaraiva/zabbix-templates)
- [Documentação Zabbix 7.0](https://www.zabbix.com/documentation/7.0)
- [Zabbix Community Templates](https://github.com/zabbix/community-templates)
- [LinkedIn do autor](https://www.linkedin.com/in/joao-saraiva-41799428/)
