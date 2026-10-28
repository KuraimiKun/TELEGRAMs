#!/bin/sh
# Postgres dump + bot data (cookies) archive with retention.
#
#   backup.sh            run one backup now
#   backup.sh --loop     run daily at BACKUP_HOUR_UTC (used by the `backup` compose service)
#
# Restore: see docs/OPERATIONS.md ("Backups & restore").
set -eu

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
HOUR="${BACKUP_HOUR_UTC:-3}"

run_backup() {
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  mkdir -p "$BACKUP_DIR"
  echo "[backup] $ts starting"

  # Custom format: compressed, restorable selectively with pg_restore.
  pg_dump --format=custom --no-owner --file="$BACKUP_DIR/db-$ts.dump.part"
  mv "$BACKUP_DIR/db-$ts.dump.part" "$BACKUP_DIR/db-$ts.dump"

  if [ -d /data ]; then
    # Only small, irreplaceable files (cookies, configs); downloads are transient and excluded.
    tar -czf "$BACKUP_DIR/data-$ts.tar.gz.part" -C /data --exclude='*/downloads' --exclude='*/public' . \
      && mv "$BACKUP_DIR/data-$ts.tar.gz.part" "$BACKUP_DIR/data-$ts.tar.gz"
  fi

  find "$BACKUP_DIR" -maxdepth 1 -type f \( -name 'db-*.dump' -o -name 'data-*.tar.gz' \) \
    -mtime +"$RETENTION_DAYS" -delete
  echo "[backup] $ts done: $(ls -1 "$BACKUP_DIR" | wc -l) files kept"
}

if [ "${1:-}" != "--loop" ]; then
  run_backup
  exit 0
fi

while :; do
  # Seconds since UTC midnight (expr avoids the octal trap of "08"/"09" in $(( ))).
  now=$(expr "$(date -u +%H)" \* 3600 + "$(date -u +%M)" \* 60 + "$(date -u +%S)")
  target=$(expr "$HOUR" \* 3600)
  delay=$(expr \( "$target" - "$now" + 86400 \) % 86400)
  [ "$delay" -eq 0 ] && delay=86400
  echo "[backup] next run in ${delay}s"
  sleep "$delay"
  run_backup || echo "[backup] FAILED" >&2
done
