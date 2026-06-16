# 🔍 Zabbix Templates

![Zabbix](https://img.shields.io/badge/Zabbix-6.x%20%7C%207.x-CC0000?style=for-the-badge&logo=zabbix&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![SNMP](https://img.shields.io/badge/SNMP-v2c%2Fv3-0075A8?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Maintained](https://img.shields.io/badge/Maintained-yes-brightgreen?style=for-the-badge)

Coleção de templates Zabbix desenvolvidos e utilizados em ambiente **corporativo de produção** na 
**SEFA — Secretaria da Fazenda do Estado do Pará**, gerenciando infraestrutura crítica de alta disponibilidade.

> Todos os templates foram testados em produção com Zabbix 6.0 LTS e 7.0 LTS.

---

## 📂 Estrutura do Repositório

```
zabbix-templates/
├── linux/
│   ├── template_linux_by_agent.yaml       # CPU, memória, disco, processos, carga
│   └── README.md
├── network/
│   ├── template_link_internet.yaml        # Uptime, latência, jitter, perda de pacotes
│   ├── template_mikrotik_snmp.yaml        # MikroTik via SNMP v2c — CPU, memória, temp, wireless, VPN
│   ├── template_switch_datacom.yaml       # Switch DATACOM DM1200E — CPU, STP, LACP, temperatura, MAC table
│   └── README.md
├── services/
│   ├── template_haproxy.yaml              # HAProxy — processo, frontends, backends, sessões, erros HTTP
│   ├── template_apache.yaml               # Apache — workers, requisições, tráfego, mod_status
│   ├── template_docker.yaml               # Docker — daemon, containers LLD, imagens, CPU/mem por container
│   └── README.md
├── database/
│   ├── template_mysql.yaml               # em breve
│   └── template_oracle_db.yaml           # em breve
├── kubernetes/
│   ├── template_k8s_nodes.yaml           # em breve
│   └── template_k8s_pods.yaml            # em breve
└── scripts/
    ├── check_certificate.sh              # em breve
    └── check_weblogic.py                 # em breve
```

---

## 📋 Templates Disponíveis

| Template | Categoria | Versão Zabbix | Coleta | Status |
|---|---|---|---|---|
| [Linux by Agent](./linux/template_linux_by_agent.yaml) | Linux | 6.0+ / 7.0+ | Zabbix Agent | ✅ Disponível |
| [Link Internet](./network/template_link_internet.yaml) | Network | 6.0+ / 7.0+ | ICMP + Agent | ✅ Disponível |
| [MikroTik SNMP](./network/template_mikrotik_snmp.yaml) | Network | 6.0+ / 7.0+ | SNMP v2c | ✅ Disponível |
| [Switch DATACOM DM1200E](./network/template_switch_datacom.yaml) | Network | 6.0+ / 7.0+ | SNMP v2c | ✅ Disponível |
| [HAProxy](./services/template_haproxy.yaml) | Services | 6.0+ / 7.0+ | HTTP Agent | ✅ Disponível |
| [Apache HTTP Server](./services/template_apache.yaml) | Services | 6.0+ / 7.0+ | Zabbix Agent | ✅ Disponível |
| [Docker](./services/template_docker.yaml) | Services | 6.0+ / 7.0+ | Agent 2 | ✅ Disponível |
| MySQL | Database | 6.0+ / 7.0+ | Agent 2 | 🔧 Em breve |
| Oracle DB | Database | 6.0+ / 7.0+ | ODBC | 🔧 Em breve |
| Kubernetes Nodes | Kubernetes | 6.0+ / 7.0+ | HTTP API | 🔧 Em breve |

---

## 🚀 Como Importar um Template

### Via Interface Web

1. Acesse **Data collection → Templates**
2. Clique em **Import** (canto superior direito)
3. Selecione o arquivo `.yaml` desejado
4. Marque as opções conforme necessário e clique em **Import**

### Via API (Zabbix 6.x/7.x)

```bash
curl -s -X POST https://SEU_ZABBIX/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "configuration.import",
    "params": {
      "format": "yaml",
      "rules": {
        "templates": {"createMissing": true, "updateExisting": true},
        "items": {"createMissing": true, "updateExisting": true},
        "triggers": {"createMissing": true, "updateExisting": true},
        "graphs": {"createMissing": true, "updateExisting": true}
      },
      "source": "'$(cat template_linux_by_agent.yaml)'"
    },
    "auth": "SEU_AUTH_TOKEN",
    "id": 1
  }'
```

---

## ⚙️ Requisitos

| Componente | Versão mínima |
|---|---|
| Zabbix Server | 6.0 LTS |
| Zabbix Agent | 2.0+ |
| PHP (frontend) | 8.0+ |

---

## 🔧 Configuração das Macros

Cada template usa macros configuráveis para facilitar o ajuste por host ou grupo de hosts.  
Defina as macros em **Administration → Macros** (global) ou diretamente no host.

---

## 👤 Autor

**João Paulo de Lima Saraiva**  
Analista de Redes Sênior | DevOps | Infraestrutura Crítica  
📍 Belém, PA — Brasil

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/joao-saraiva-41799428/)
[![Email](https://img.shields.io/badge/Email-D14836?style=flat&logo=gmail&logoColor=white)](mailto:joaoplsaraiva@gmail.com)
[![Credly](https://img.shields.io/badge/Credly-FF6B00?style=flat&logo=credly&logoColor=white)](https://www.credly.com/users/joao-paulo-lima-saraiva)

---

## 📄 Licença

Distribuído sob a licença MIT. Consulte [LICENSE](LICENSE) para mais informações.

---

> 💡 **Contribuições são bem-vindas!** Abra uma _issue_ ou envie um _pull request_.
