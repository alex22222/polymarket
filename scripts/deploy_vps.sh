#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE="${POLYMTRADE_VPS:-}"
KEY="${POLYMTRADE_SSH_KEY:-$HOME/.ssh/polymtrade_vultr_ed25519}"
REMOTE_DIR="${POLYMTRADE_REMOTE_DIR:-/home/polymtrade/polymarket}"
REMOTE_USER="${POLYMTRADE_REMOTE_USER:-polymtrade}"
SERVICE="${POLYMTRADE_SERVICE:-polymtrade}"
DRY_RUN=""

usage() {
  cat <<'EOF'
Usage:
  POLYMTRADE_VPS=root@<server-ip> scripts/deploy_vps.sh

Optional env:
  POLYMTRADE_SSH_KEY       SSH private key path, default ~/.ssh/polymtrade_vultr_ed25519
  POLYMTRADE_REMOTE_DIR    Remote project dir, default /home/polymtrade/polymarket
  POLYMTRADE_REMOTE_USER   Remote runtime user, default polymtrade
  POLYMTRADE_SERVICE       systemd service name, default polymtrade

Flags:
  --dry-run                Show rsync changes without deploying
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN="--dry-run"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$REMOTE" ]]; then
  echo "POLYMTRADE_VPS is required, for example: root@1.2.3.4" >&2
  usage >&2
  exit 2
fi

if [[ ! -f "$KEY" ]]; then
  echo "SSH key not found: $KEY" >&2
  exit 2
fi

cd "$ROOT_DIR"

DEPLOY_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
DEPLOY_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
DEPLOY_DIRTY=""
if ! git diff --quiet --ignore-submodules -- 2>/dev/null; then
  DEPLOY_DIRTY="-dirty"
fi
DEPLOY_VERSION="${DEPLOY_SHA}${DEPLOY_DIRTY}"
DEPLOY_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "Local checks..."
python3 -m compileall -q polymtrade
node --check polymtrade/web/app.js

echo "Syncing code to $REMOTE:$REMOTE_DIR ..."
rsync -az --delete --progress $DRY_RUN \
  -e "ssh -i $KEY" \
  --exclude ".git/" \
  --exclude ".venv/" \
  --exclude "__pycache__/" \
  --exclude "backups/" \
  --exclude "*.pyc" \
  --exclude ".DS_Store" \
  --exclude ".env" \
  --exclude "polymtrade.sqlite" \
  --exclude "*.sqlite" \
  --exclude "*.sqlite3" \
  --exclude "*.sqlite-wal" \
  --exclude "*.sqlite-shm" \
  --exclude "automation.log" \
  --exclude "server.log" \
  --exclude "monitor.log" \
  "$ROOT_DIR/" "$REMOTE:$REMOTE_DIR/"

if [[ -n "$DRY_RUN" ]]; then
  echo "Dry run complete. No remote changes were applied."
  exit 0
fi

echo "Applying ownership, verifying remote code, and restarting service..."
ssh -i "$KEY" "$REMOTE" "set -euo pipefail
  chown -R $REMOTE_USER:$REMOTE_USER '$REMOTE_DIR'
  cd '$REMOTE_DIR'
  cat > .deploy_version.json <<'VERSION_JSON'
{\"version\":\"$DEPLOY_VERSION\",\"sha\":\"$DEPLOY_SHA\",\"branch\":\"$DEPLOY_BRANCH\",\"deployed_at\":\"$DEPLOY_AT\",\"source\":\"deploy\"}
VERSION_JSON
  chown $REMOTE_USER:$REMOTE_USER .deploy_version.json
  sudo -u $REMOTE_USER .venv/bin/python3 -m compileall -q polymtrade
  if command -v node >/dev/null 2>&1; then
    sudo -u $REMOTE_USER node --check polymtrade/web/app.js
  else
    echo 'Remote node not found; skipping remote app.js syntax check (already checked locally).'
  fi
  systemctl restart '$SERVICE'
  sudo -u $REMOTE_USER .venv/bin/python3 - <<'PY'
from polymtrade.storage.db import connect, insert_log
with connect('polymtrade.sqlite') as conn:
    insert_log(conn, 'INFO', 'deploy', 'Deploy completed: $DEPLOY_VERSION', '$DEPLOY_AT branch=$DEPLOY_BRANCH sha=$DEPLOY_SHA')
PY
  systemctl status '$SERVICE' --no-pager
"

echo "Deploy complete: $DEPLOY_VERSION"
