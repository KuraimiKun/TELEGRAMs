#!/usr/bin/env bash
set -euo pipefail
for spec in 'gg-long-postgres postgres:16-alpine' 'gg-long-redis redis:7-alpine'; do
  read -r task_container task_image <<< "$spec"
  if docker container inspect "$task_container" >/dev/null 2>&1; then
    test "$(docker inspect --format '{{.Config.Image}}' "$task_container")" = "$task_image"
    docker start "$task_container" >/dev/null
  elif test "$task_container" = gg-long-postgres; then
    docker run -d --name "$task_container" -e POSTGRES_USER=gglong -e POSTGRES_DB=gg_long_integration -e POSTGRES_HOST_AUTH_METHOD=trust -p 127.0.0.1:55433:5432 "$task_image" >/dev/null
  else
    docker run -d --name "$task_container" -p 127.0.0.1:56380:6379 "$task_image" >/dev/null
  fi
done
for attempt in {1..45}; do
  if docker exec gg-long-postgres pg_isready -U gglong >/dev/null && test "$(docker exec gg-long-redis redis-cli ping)" = PONG; then break; fi
  if test "$attempt" = 45; then exit 1; fi
  sleep 1
done
for task_db in gg_long_concurrency gglong; do
  if ! docker exec gg-long-postgres psql -U gglong -d gg_long_integration -Atc "SELECT datname FROM pg_database WHERE datname='$task_db'" | rg -q "^$task_db$"; then
    docker exec gg-long-postgres psql -U gglong -d gg_long_integration -c "CREATE DATABASE $task_db" >/dev/null
  fi
done
docker exec gg-long-postgres psql -U gglong -d gg_long_integration -Atc 'SELECT 1'
docker exec gg-long-redis redis-cli ping
