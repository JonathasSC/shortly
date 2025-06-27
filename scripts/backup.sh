#!/bin/bash
set -e

ENV_FILE="./src/prod.env"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mysql}"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
FILENAME="mysql_backup_$TIMESTAMP.sql.gz"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

load_env_vars() {
  log "Carregando variáveis de ambiente do $ENV_FILE"
  while IFS='=' read -r key value; do
    if [[ $key =~ ^DB_ ]]; then
      value="${value%\"}"
      value="${value#\"}"
      value="$(echo -e "${value}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
      export "$key=$value"
    fi
  done < "$ENV_FILE"
}

validate_env_vars() {
  log "Verificando variáveis obrigatórias"
  : "${DB_NAME:?Variável DB_NAME não definida}"
  : "${DB_USER:?Variável DB_USER não definida}"
  : "${DB_PASSWORD:?Variável DB_PASSWORD não definida}"
  : "${DB_HOST:=localhost}"
}

prepare_backup_directory() {
  log "Criando pasta de backup: $BACKUP_DIR"
  mkdir -p "$BACKUP_DIR"
}

perform_backup() {
  log "📦 Iniciando backup do banco MySQL: $DB_NAME"
  mysqldump --login-path=backup "$DB_NAME" | gzip > "$BACKUP_DIR/$FILENAME"
  log "✅ Backup concluído: $BACKUP_DIR/$FILENAME"
}

rotate_old_backups() {
  log "♻️ Executando rotação de backups"

  # Remove backups com mais de 30 dias
  find "$BACKUP_DIR" -type f -name "mysql_backup_*.sql.gz" -mtime +30 -exec rm -f {} \;

  # Mantém apenas os 7 backups mais recentes
  ls -tp "$BACKUP_DIR"/mysql_backup_*.sql.gz | grep -v '/$' | tail -n +8 | xargs -I {} rm -- {}

  log "✅ Rotação de backups concluída"
}

run_backup_process() {
  log "==== 🚀 Iniciando Script de Backup ===="
  load_env_vars
  validate_env_vars
  prepare_backup_directory
  perform_backup
  rotate_old_backups
  log "==== ✅ Script finalizado ===="
}

# Executa tudo
run_backup_process
