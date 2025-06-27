#!/bin/bash

DOCKER_COMPOSE="docker compose"
SERVICE_NAME="shortly"  # Altere conforme o nome do seu serviço
ADMIN_COMMAND="create_admin"

# Cores
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
RESET="\033[0m"

# Log helpers
log() {
  echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
  log "${GREEN}✔ $1${RESET}"
}

log_error() {
  log "${RED}❌ $1${RESET}"
}

log_warn() {
  log "${YELLOW}⚠ $1${RESET}"
}

print_header() {
  local text=" $1 "
  local text_length=${#text}
  local border=$(printf '%*s' "$text_length" '' | tr ' ' '=')

  echo -e "\n${YELLOW}${border}"
  echo "$text"
  echo -e "${border}${RESET}\n"
}

# Funções principais
pull_latest_code() {
    log "Atualizando código-fonte via git pull..."
    if ! git pull; then
        log_error "Erro ao fazer git pull. Abortando."
        exit 1
    fi
    log_success "Código atualizado com sucesso"
}

verify_ubuntu_version() {
    UBUNTU_VERSION=$(lsb_release -cs)
    log "Versão do Ubuntu: $UBUNTU_VERSION"
    if [ "$UBUNTU_VERSION" = "focal" ]; then
        DOCKER_COMPOSE="docker-compose"
    fi
}

check_docker() {
    if ! command -v docker &>/dev/null; then
        log_error "Docker não está instalado. Abortando."
        exit 1
    fi
    if ! docker info &>/dev/null; then
        log_error "Docker não está em execução. Inicie o serviço e tente novamente."
        exit 1
    fi
}

stop_oldest_containers() {
    log "Parando containers antigos..."
    $DOCKER_COMPOSE down
    log_success "Containers antigos parados com sucesso"
}

build_containers() {
    log "Iniciando build dos containers..."
    $DOCKER_COMPOSE build
    log_success "Build concluído com sucesso"
}

up_containers() {
    log "Levantando containers..."
    $DOCKER_COMPOSE up -d
    log_success "Containers levantados com sucesso"
}

apply_migrations() {
    log "Aplicando migrações no Django..."
    $DOCKER_COMPOSE exec $SERVICE_NAME python3 manage.py migrate
    log_success "Migrações aplicadas com sucesso"
}

create_superuser_if_not_exists() {
    log "Tentando criar superusuário (caso não exista)..."
    $DOCKER_COMPOSE exec $SERVICE_NAME python3 manage.py $ADMIN_COMMAND
    log_success "Tentativa de criação de superusuário finalizada"
}

run_start() {
    print_header "Iniciando processo de Deploy"
    check_docker
    verify_ubuntu_version
    # pull_latest_code
    stop_oldest_containers
    build_containers
    up_containers
    apply_migrations
    create_superuser_if_not_exists
    print_header "Deploy Finalizado com Sucesso 🎉"
}

# Executar tudo
run_start
