#!/usr/bin/env bash
# =============================================================================
# check_certificate.sh
# =============================================================================
# Verifica expiração de certificados SSL/TLS em endpoints HTTPS ou arquivos .pem
# Retorna os dias restantes até a expiração do certificado.
#
# Uso no Zabbix:
#   UserParameter=ssl.cert.expiry[*],/etc/zabbix/scripts/check_certificate.sh "$1" "$2"
#
# Parâmetros:
#   $1 = hostname ou IP do servidor (ex: meusite.com.br ou 192.168.1.10)
#   $2 = porta HTTPS (padrão: 443) ou caminho para arquivo .pem (opcional)
#
# Retorno:
#   Número inteiro de dias até a expiração (positivo = ainda válido)
#   Número negativo = certificado já expirado há N dias
#   -999 = erro (host inacessível, sem certificado, timeout)
#
# Exemplos de uso:
#   ./check_certificate.sh meusite.com.br         # porta 443 (padrão)
#   ./check_certificate.sh meusite.com.br 8443    # porta customizada
#   ./check_certificate.sh /etc/ssl/meu-cert.pem  # arquivo local .pem
#
# Desenvolvido por: João Paulo de Lima Saraiva
# Baseado em uso real na SEFA/PA para monitoramento de certificados
# Let's Encrypt (via Cert-Manager) e certificados autoassinados do RestPKI.
#
# Repositório: https://github.com/joaoplsaraiva/zabbix-templates
# =============================================================================

set -euo pipefail

# ─── Configurações ────────────────────────────────────────────────────────────
readonly TIMEOUT=10          # Timeout da conexão em segundos
readonly ERROR_CODE=-999     # Código de retorno em caso de erro
readonly SCRIPT_NAME="$(basename "$0")"

# ─── Funções ──────────────────────────────────────────────────────────────────

usage() {
  cat <<EOF
Uso: ${SCRIPT_NAME} <host_ou_arquivo> [porta]

  host_ou_arquivo  Hostname, IP ou caminho para arquivo .pem
  porta            Porta HTTPS (padrão: 443)

Exemplos:
  ${SCRIPT_NAME} meusite.com.br
  ${SCRIPT_NAME} meusite.com.br 8443
  ${SCRIPT_NAME} /etc/ssl/cert.pem
  ${SCRIPT_NAME} 192.168.1.50 443
EOF
  exit 1
}

log_error() {
  echo "[${SCRIPT_NAME}] ERRO: $*" >&2
}

# Verifica dependências obrigatórias
check_deps() {
  local missing=()
  for cmd in openssl date; do
    if ! command -v "${cmd}" &>/dev/null; then
      missing+=("${cmd}")
    fi
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    log_error "Dependências não encontradas: ${missing[*]}"
    echo "${ERROR_CODE}"
    exit 1
  fi
}

# Converte data de expiração do certificado para timestamp Unix
cert_date_to_epoch() {
  local cert_date="$1"
  # OpenSSL retorna datas no formato: "Nov 30 23:59:59 2025 GMT"
  # Compatível com GNU date (Linux) e BSD date (macOS)
  if date --version &>/dev/null 2>&1; then
    # GNU date (Linux / Fedora / CentOS / Oracle Linux)
    date -d "${cert_date}" +%s 2>/dev/null || echo "0"
  else
    # BSD date (macOS)
    date -j -f "%b %d %T %Y %Z" "${cert_date}" +%s 2>/dev/null || echo "0"
  fi
}

# Obtém a data de expiração de um endpoint HTTPS
get_expiry_from_endpoint() {
  local host="$1"
  local port="${2:-443}"

  # Conecta ao endpoint e extrai o certificado
  local cert_info
  cert_info=$(echo | timeout "${TIMEOUT}" openssl s_client \
    -connect "${host}:${port}" \
    -servername "${host}" \
    -verify_return_error \
    2>/dev/null | openssl x509 -noout -dates 2>/dev/null) || {
    log_error "Não foi possível conectar em ${host}:${port} (timeout: ${TIMEOUT}s)"
    echo "${ERROR_CODE}"
    return 1
  }

  echo "${cert_info}" | grep "notAfter" | cut -d= -f2
}

# Obtém a data de expiração de um arquivo .pem
get_expiry_from_file() {
  local cert_file="$1"

  if [[ ! -f "${cert_file}" ]]; then
    log_error "Arquivo não encontrado: ${cert_file}"
    echo "${ERROR_CODE}"
    return 1
  fi

  if [[ ! -r "${cert_file}" ]]; then
    log_error "Sem permissão de leitura: ${cert_file}"
    echo "${ERROR_CODE}"
    return 1
  fi

  openssl x509 -noout -enddate -in "${cert_file}" 2>/dev/null \
    | cut -d= -f2 || {
    log_error "Arquivo inválido ou não é um certificado PEM: ${cert_file}"
    echo "${ERROR_CODE}"
    return 1
  }
}

# Calcula dias restantes a partir da data de expiração
calc_days_remaining() {
  local expiry_date="$1"

  if [[ -z "${expiry_date}" || "${expiry_date}" == "${ERROR_CODE}" ]]; then
    echo "${ERROR_CODE}"
    return 1
  fi

  local expiry_epoch
  expiry_epoch=$(cert_date_to_epoch "${expiry_date}")

  if [[ "${expiry_epoch}" == "0" ]]; then
    log_error "Não foi possível parsear a data: ${expiry_date}"
    echo "${ERROR_CODE}"
    return 1
  fi

  local now_epoch
  now_epoch=$(date +%s)

  local diff_seconds=$(( expiry_epoch - now_epoch ))
  local days_remaining=$(( diff_seconds / 86400 ))

  echo "${days_remaining}"
}

# Exibe informações detalhadas do certificado (modo verbose)
show_cert_details() {
  local host="$1"
  local port="${2:-443}"

  echo "=== Detalhes do Certificado SSL ==="
  echo "Host : ${host}:${port}"
  echo "Data : $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""

  echo | timeout "${TIMEOUT}" openssl s_client \
    -connect "${host}:${port}" \
    -servername "${host}" \
    2>/dev/null | openssl x509 -noout \
    -subject \
    -issuer \
    -dates \
    -fingerprint \
    2>/dev/null || {
    echo "Erro: não foi possível obter detalhes do certificado."
    return 1
  }
}

# ─── Main ─────────────────────────────────────────────────────────────────────

main() {
  # Validação de argumentos
  if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
    usage
  fi

  check_deps

  local target="$1"
  local port="${2:-443}"
  local expiry_date
  local days_remaining

  # Modo verbose para diagnóstico manual
  if [[ "${target}" == "--verbose" || "${target}" == "-v" ]]; then
    if [[ $# -lt 2 ]]; then
      log_error "Modo verbose requer um hostname: ${SCRIPT_NAME} -v <host> [porta]"
      exit 1
    fi
    show_cert_details "$2" "${3:-443}"
    exit 0
  fi

  # Detecta se é arquivo .pem ou endpoint de rede
  if [[ "${target}" == *.pem || "${target}" == *.crt || "${target}" == *.cer || -f "${target}" ]]; then
    # ── Modo arquivo ──────────────────────────────────────────────────────────
    expiry_date=$(get_expiry_from_file "${target}") || {
      echo "${ERROR_CODE}"
      exit 1
    }
  else
    # ── Modo endpoint ─────────────────────────────────────────────────────────
    # Valida porta
    if ! [[ "${port}" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
      log_error "Porta inválida: ${port} (deve ser entre 1 e 65535)"
      echo "${ERROR_CODE}"
      exit 1
    fi

    expiry_date=$(get_expiry_from_endpoint "${target}" "${port}") || {
      echo "${ERROR_CODE}"
      exit 1
    }
  fi

  # Calcula e retorna os dias restantes
  days_remaining=$(calc_days_remaining "${expiry_date}") || {
    echo "${ERROR_CODE}"
    exit 1
  }

  echo "${days_remaining}"
}

main "$@"
