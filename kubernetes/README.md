# ☸️ Kubernetes Templates

Templates para monitoramento de clusters Kubernetes via HTTP Agent (API REST).
Desenvolvidos com base em experiência real com **Kubernetes, OpenShift 4.x e Rancher 2.x**
na SEFA/PA — ambientes críticos de produção com múltiplos namespaces e middlewares.

---

## Pré-requisito — ServiceAccount de monitoramento

Os dois templates usam o mesmo ServiceAccount. Crie uma vez e use em ambos:

```bash
# Criar ServiceAccount no namespace kube-system
kubectl create serviceaccount zabbix-monitor -n kube-system

# Associar a ClusterRole view (somente leitura em todos os recursos)
kubectl create clusterrolebinding zabbix-monitor \
  --clusterrole=view \
  --serviceaccount=kube-system:zabbix-monitor

# Gerar token de longa duração (Kubernetes 1.24+)
kubectl create token zabbix-monitor -n kube-system --duration=8760h
```

> **OpenShift:** substitua `kubectl` por `oc` e adicione `oc adm policy add-cluster-role-to-user view system:serviceaccount:kube-system:zabbix-monitor`

Configure o token na macro `{$K8S.API.TOKEN}` do host Zabbix (use Secret para proteger o valor).

---

## Templates Disponíveis

### `template_k8s_nodes.yaml`

Monitoramento de **nodes do cluster** via API REST do Kubernetes.
Cobre disponibilidade, pressão de recursos, capacidade, versão e eventos do cluster.

**Compatibilidade:** Zabbix 6.0 LTS e 7.0 LTS | Kubernetes 1.24+, OpenShift 4.x, Rancher 2.x

#### Como usar

1. Crie um host no Zabbix representando o **cluster** (não um node individual)
2. Defina o IP do host como o endereço do API Server
3. Configure as macros `{$K8S.API.URL}` e `{$K8S.API.TOKEN}`
4. Aplique o template — os nodes são descobertos automaticamente via LLD

#### Items monitorados

| Categoria | Item | Tipo | Intervalo |
|---|---|---|---|
| Cluster | Dados brutos dos nodes (item master) | HTTP Agent | 60s |
| Cluster | Total de nodes | Dependent | — |
| Cluster | Nodes Ready / NotReady | Dependent | — |
| Cluster | Nodes com MemoryPressure | Dependent | — |
| Cluster | Nodes com DiskPressure | Dependent | — |
| Cluster | Nodes com PIDPressure | Dependent | — |
| Cluster | Nodes com NetworkUnavailable | Dependent | — |
| Cluster | Warning events na última hora | HTTP Agent | 5m |
| Cluster | Capacidade total de CPU (millicores) | Dependent | — |
| Cluster | Capacidade total de memória (bytes) | Dependent | — |
| Sistema | Versão do Kubernetes (API Server) | HTTP Agent | 1h |
| LLD por node | Status Ready | HTTP Agent | 60s |
| LLD por node | Pods em execução | HTTP Agent | 60s |
| LLD por node | Capacidade de pods | HTTP Agent | 5m |
| LLD por node | Capacidade e alocação de CPU (millicores) | HTTP Agent | 5m/60s |
| LLD por node | Alocação de memória (bytes) | HTTP Agent | 60s |
| LLD por node | Versão do kubelet | HTTP Agent | 1h |

#### Triggers configuradas

| Trigger | Severidade | Condição padrão |
|---|---|---|
| Nodes NotReady no cluster | HIGH | ≥ 1 node NotReady |
| Node individual NotReady (LLD) | HIGH | condição Ready ≠ True |
| Nodes com MemoryPressure | HIGH | ≥ 1 node com pressão |
| Nodes com DiskPressure | HIGH | ≥ 1 node com pressão |
| Nodes com PIDPressure | WARNING | ≥ 1 node com pressão |
| Nodes com NetworkUnavailable | HIGH | ≥ 1 node com problema |
| Alto volume de Warning events | WARNING | > 50 eventos Warning |
| Node próximo do limite de pods (LLD) | WARNING | > 90% da capacidade |

#### Macros configuráveis

| Macro | Padrão | Descrição |
|---|---|---|
| `{$K8S.API.URL}` | https://kubernetes.default.svc:6443 | URL da API |
| `{$K8S.API.TOKEN}` | — | Bearer token da ServiceAccount |
| `{$K8S.NODE.CPU.WARN}` | 80 | CPU alocada no node para alerta (%) |
| `{$K8S.NODE.CPU.CRIT}` | 95 | CPU alocada — crítico (%) |
| `{$K8S.NODE.MEM.WARN}` | 80 | Memória alocada para alerta (%) |
| `{$K8S.NODE.MEM.CRIT}` | 95 | Memória alocada — crítico (%) |
| `{$K8S.NODE.PODS.WARN}` | 90 | Uso do limite de pods para alerta (%) |

#### Gráficos incluídos
- Nodes — Ready vs NotReady
- Nodes — Pressão de Recursos (Memory / Disk / PID)
- Warning Events no Cluster

---

### `template_k8s_pods.yaml`

Monitoramento de **pods e workloads** por namespace via API REST.
Cobre estados dos pods, containers problemáticos, Deployments, Jobs, PVCs e namespaces.

**Compatibilidade:** Zabbix 6.0 LTS e 7.0 LTS | Kubernetes 1.24+, OpenShift 4.x, Rancher 2.x

#### Como usar

1. Crie **um host por namespace** que deseja monitorar (ex: `k8s-namespace-webapp-prod`)
2. Ajuste a macro `{$K8S.NAMESPACE}` para o nome do namespace
3. Aplique o template ao host

> **Dica:** Para monitorar todos os namespaces em um único host, defina `{$K8S.NAMESPACE}` como vazio — a API retornará dados de todos.

#### Items monitorados

| Categoria | Item | Intervalo |
|---|---|---|
| Pods | Total, Running, Pending, Failed, Succeeded | 60s |
| Containers | CrashLoopBackOff, ImagePullBackOff, OOMKilled | 60s |
| Containers | Total de restarts acumulados | 60s |
| Containers | Containers sem resources.limits | 60s |
| Deployments | Total, degradados (réplicas insuf.), completamente down | 60s |
| Jobs | Jobs com falha, CronJobs ativos | 5m |
| Cluster | Total de namespaces, namespaces em Terminating | 2m/5m |
| Storage | PVCs em estado Lost ou Pending | 2m |

#### Triggers configuradas

| Trigger | Severidade | Condição padrão |
|---|---|---|
| Pods em estado Failed | HIGH | ≥ 1 pod Failed |
| Pods em estado Pending | WARNING | ≥ 3 pods Pending |
| Containers em CrashLoopBackOff | HIGH | ≥ 1 container |
| Containers em ImagePullBackOff | HIGH | ≥ 1 container |
| Containers OOMKilled | HIGH | ≥ 1 container |
| Deployment completamente down | DISASTER | readyReplicas = 0 |
| Deployment degradado | WARNING | ≥ 1 réplica indisponível |
| Jobs com falha | WARNING | ≥ 1 job falhado |
| Containers sem limits | INFO | ≥ 5 containers |
| PVCs com falha | HIGH | ≥ 1 PVC Lost/Pending |
| Namespace preso em Terminating | WARNING | ≥ 1 namespace |

#### Macros configuráveis

| Macro | Padrão | Descrição |
|---|---|---|
| `{$K8S.API.URL}` | https://kubernetes.default.svc:6443 | URL da API |
| `{$K8S.API.TOKEN}` | — | Bearer token da ServiceAccount |
| `{$K8S.NAMESPACE}` | default | Namespace a monitorar |
| `{$K8S.POD.RESTARTS.WARN}` | 5 | Restarts para alerta |
| `{$K8S.POD.RESTARTS.CRIT}` | 20 | Restarts críticos |
| `{$K8S.DEPLOY.UNAVAILABLE.WARN}` | 1 | Réplicas indisponíveis para alerta |
| `{$K8S.JOB.FAILED.WARN}` | 1 | Jobs com falha para alerta |
| `{$K8S.CONTAINER.NO.LIMITS.WARN}` | 5 | Containers sem limits para alerta |

#### Gráficos incluídos
- Pods — Distribuição por Estado (Running / Pending / Failed / Succeeded)
- Pods — Problemas de Containers (CrashLoop / OOMKill / ImagePullBackOff)
- Deployments (total / degradados / down)
- Total de Restarts acumulados

---

## Arquitetura de Monitoramento Recomendada

```
Zabbix Server
├── Host: k8s-cluster-prod          → template_k8s_nodes.yaml
│   Macro: K8S.API.URL = https://api.cluster.prod:6443
│   (Monitora todos os nodes via LLD)
│
├── Host: k8s-ns-webapp-prod        → template_k8s_pods.yaml
│   Macro: K8S.NAMESPACE = webapp-prod
│
├── Host: k8s-ns-middleware-prod    → template_k8s_pods.yaml
│   Macro: K8S.NAMESPACE = middleware (Kafka, Keycloak, 3Scale)
│
└── Host: k8s-ns-monitoring         → template_k8s_pods.yaml
    Macro: K8S.NAMESPACE = monitoring (Prometheus, Grafana, ELK)
```
