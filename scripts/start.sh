#!/bin/bash

ENV_FILE="./src/.env"
DOCKER_COMPOSE="docker compose"
SERVICE_NAME="shortly"

# Cores
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
RESET="\033[0m"

load_env_vars(){
  log "Carregando variaveis de ambiente do $ENV_FILE"
  set -a
  source "$ENV_FILE"
  export ENV_FILE="$ENV_FILE"
  set +a
}

validate_env_vars() {
  log "Verificando variaveis obrigatorias"
  : "${SSL_EMAIL:?Variavel SSL_EMAIL nao definida}"
}

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

pull_latest_code() {
    log "Atualizando codigo-fonte via git pull..."
    if ! git pull; then
        log_error "Erro ao fazer git pull. Abortando."
        exit 1
    fi
    log_success "Codigo atualizado com sucesso"
}

check_docker() {
    if ! command -v docker &>/dev/null; then
        log_error "Docker nao esta instalado. Abortando."
        exit 1
    fi
    if ! docker info &>/dev/null; then
        log_error "Docker nao esta em execucao. Inicie o servico e tente novamente."
        exit 1
    fi
}

check_docker_compose() {
    if ! command -v $DOCKER_COMPOSE &>/dev/null && ! docker compose version &>/dev/null; then
        log_error "Docker Compose nao esta instalado corretamente. Abortando."
        exit 1
    fi
}

stop_oldest_containers() {
    log "Parando containers antigos..."
    $DOCKER_COMPOSE down
    log_success "Containers antigos parados com sucesso"
}

build_app_containers() {
    log "Iniciando build dos containers da aplicação (Django + Celery + Flower)..."
    $DOCKER_COMPOSE build shortly shortly_asgi celery_worker celery_beat flower
    log_success "Build concluído com sucesso"
}

up_all_containers() {
    log "Levantando todos os containers..."
    $DOCKER_COMPOSE up -d
    log_success "Todos os containers levantados com sucesso"
}

collect_staticfiles() {
    log "Coletando arquivos estaticos..."
    $DOCKER_COMPOSE exec $SERVICE_NAME python3 manage.py collectstatic --no-input
    log_success "Arquivos estaticos coletados"
}

make_migrations() {
    log "Aplicando migracoes no Django..."
    nohup $DOCKER_COMPOSE exec $SERVICE_NAME python3 manage.py makemigrations
    log_success "Migracoes feitas com sucesso"
}

apply_migrations() {
    log "Aplicando migracoes no Django..."
    $DOCKER_COMPOSE exec $SERVICE_NAME python3 manage.py migrate
    log_success "Migracoes aplicadas com sucesso"
}

create_superuser_if_not_exists() {
    log "Tentando criar superusuario (caso nao exista)..."
    $DOCKER_COMPOSE exec $SERVICE_NAME python3 manage.py createsuperuser --no-input
    log_success "Tentativa de criacao de superusuario finalizada"
}

run_start() {
    print_header "Iniciando processo de Deploy"
    load_env_vars
    validate_env_vars
    check_docker
    check_docker_compose
    pull_latest_code
    stop_oldest_containers

    print_header "Build e up do Nginx (HTTP apenas)"
    $DOCKER_COMPOSE build nginx
    $DOCKER_COMPOSE up -d nginx

    print_header "Build e up dos demais containers"
    build_app_containers
    up_all_containers

    make_migrations
    apply_migrations
    create_superuser_if_not_exists
    collect_staticfiles
    print_header "Deploy Finalizado com Sucesso 🎉"
}

run_start
