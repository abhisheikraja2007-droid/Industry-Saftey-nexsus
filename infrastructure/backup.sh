#!/bin/bash
# ============================================================
# PostgreSQL Backup Script — Industrial Safety AI
# Usage:
#   ./backup.sh              — Create backup
#   ./backup.sh restore backup_file.sql.gz  — Restore from backup
# ============================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_CONTAINER="industrial-safety-ai-postgres-1"
DB_USER="${POSTGRES_USER:-safety_user}"
DB_NAME="${POSTGRES_DB:-safety_db}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/safety_db_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

if [[ "${1:-}" == "restore" ]]; then
    RESTORE_FILE="${2:-}"
    if [[ -z "$RESTORE_FILE" ]]; then
        echo "❌ Usage: ./backup.sh restore <backup_file.sql.gz>"
        exit 1
    fi
    echo "⚠️  WARNING: This will overwrite all data in '$DB_NAME'. Proceed? [y/N]"
    read -r confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Restore cancelled."
        exit 0
    fi
    echo "🔄 Restoring from $RESTORE_FILE ..."
    gunzip -c "$RESTORE_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"
    echo "✅ Restore completed."
else
    echo "📦 Creating backup to $BACKUP_FILE ..."
    docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists | gzip > "$BACKUP_FILE"
    BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)"
    
    # Verify backup
    echo "🔍 Verifying backup integrity..."
    if gunzip -t "$BACKUP_FILE" 2>/dev/null; then
        echo "✅ Backup integrity verified."
    else
        echo "❌ Backup integrity check FAILED."
        exit 1
    fi
    
    # Retention: keep last 7 backups
    ls -t "$BACKUP_DIR"/safety_db_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm -f
    echo "🗑️  Old backups cleaned up (kept last 7)."
fi
