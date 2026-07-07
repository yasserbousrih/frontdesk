#!/usr/bin/env bash
set -euo pipefail

#══════════════════════════════════════════════════════════════
# FrontDesk — one-command deployment on a fresh VM
# Builds Frappe v15 + ERPNext v15 + frontdesk custom image,
# starts the full stack, creates the site.
#══════════════════════════════════════════════════════════════

# ── Config (override via env vars) ──────────────────────────
SITENAME="${SITENAME:-}"
DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -hex 16)}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-$(openssl rand -base64 12 | tr -dc 'A-Za-z0-9' | head -c 12)}"
LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_NAME="frontdesk"

# ── Helpers ─────────────────────────────────────────────────
red()    { echo -e "\033[31m$*\033[0m"; }
green()  { echo -e "\033[32m$*\033[0m"; }
yellow() { echo -e "\033[33m$*\033[0m"; }

# ── Preflight checks ────────────────────────────────────────
command -v docker >/dev/null 2>&1 || { red "Docker not found. Install: https://docs.docker.com/get-docker/"; exit 1; }
docker compose version >/dev/null 2>&1 || { red "Docker Compose v2 not found."; exit 1; }
command -v git >/dev/null 2>&1 || { red "git not found."; exit 1; }

# ── Interactive prompts (if env vars not set) ──────────────
if [ -z "$SITENAME" ]; then
    read -rp "$(yellow 'Site domain (e.g. frontdesk.example.com): ')" SITENAME
fi
[ -z "$SITENAME" ] && { red "SITENAME is required."; exit 1; }

if [ -z "$LETSENCRYPT_EMAIL" ]; then
    read -rp "$(yellow "Lets Encrypt email: ")" LETSENCRYPT_EMAIL
fi
[ -z "$LETSENCRYPT_EMAIL" ] && { red "LETSENCRYPT_EMAIL is required."; exit 1; }

green "\n═══ FrontDesk Deployment ═══"
echo "  Domain:    $SITENAME"
echo "  Email:     $LETSENCRYPT_EMAIL"
echo "  Project:   $PROJECT_NAME"
echo ""

# ── DNS check (non-blocking warning) ────────────────────────
VM_IP=$(curl -s ifconfig.me 2>/dev/null || echo "unknown")
DNS_IP=$(getent hosts "$SITENAME" 2>/dev/null | awk '{print $1}' || echo "")
if [ -n "$DNS_IP" ] && [ "$DNS_IP" != "$VM_IP" ]; then
    yellow "⚠ WARNING: $SITENAME resolves to $DNS_IP but this VM is $VM_IP"
    yellow "  Let's Encrypt will FAIL if DNS doesn't point here."
    read -rp "Continue anyway? (y/N) " confirm
    [ "$confirm" = "y" ] || exit 1
fi

# ── 1. Clone frappe_docker ──────────────────────────────────
FRAPPE_DOCKER_DIR="$REPO_DIR/frappe_docker"
if [ ! -d "$FRAPPE_DOCKER_DIR" ]; then
    echo ">>> Cloning frappe_docker..."
    git clone --depth 1 https://github.com/frappe/frappe_docker "$FRAPPE_DOCKER_DIR"
else
    green "✓ frappe_docker already cloned"
fi
cd "$FRAPPE_DOCKER_DIR"

# ── 2. Configure apps ───────────────────────────────────────
echo ">>> Configuring apps (Frappe v15 + ERPNext + FrontDesk)..."
cp "$SCRIPT_DIR/apps.json" apps.json

# ── 3. Build custom image ───────────────────────────────────
echo ">>> Building custom image..."
echo "    (10-20 min on first run — grabs Frappe + ERPNext + frontdesk)"
docker build \
    --build-arg=FRAPPE_BRANCH=version-15 \
    --secret=id=apps_json,src=apps.json \
    --tag=frontdesk:v15 \
    --file=images/layered/Containerfile .
green "✓ Image built: frontdesk:v15"

# ── 4. Generate .env ────────────────────────────────────────
echo ">>> Generating configuration..."
cat > custom.env << EOF
CUSTOM_IMAGE=frontdesk
CUSTOM_TAG=v15
PULL_POLICY=missing
DB_PASSWORD=$DB_PASSWORD
LETSENCRYPT_EMAIL=$LETSENCRYPT_EMAIL
SITES_RULE=Host(\`$SITENAME\`)
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
HTTP_PUBLISH_PORT=80
HTTPS_PUBLISH_PORT=443
EOF

# ── 5. Generate combined compose ────────────────────────────
echo ">>> Generating compose file..."
docker compose --env-file custom.env \
    -f compose.yaml \
    -f overrides/compose.mariadb.yaml \
    -f overrides/compose.redis.yaml \
    -f overrides/compose.https.yaml \
    config > compose.custom.yaml

# ── 6. Start the stack ──────────────────────────────────────
echo ">>> Starting containers..."
docker compose -p "$PROJECT_NAME" -f compose.custom.yaml up -d

echo ">>> Waiting for backend..."
for i in $(seq 1 60); do
    if docker compose -p "$PROJECT_NAME" exec -T backend bash -c "echo ok" >/dev/null 2>&1; then
        green "✓ Backend is ready"
        break
    fi
    sleep 3
    [ $i -eq 60 ] && { red "Backend didn't start in 3 min. Check: docker compose -p $PROJECT_NAME logs"; exit 1; }
done

# ── 7. Create site + install apps ───────────────────────────
echo ">>> Creating site $SITENAME..."
docker compose -p "$PROJECT_NAME" exec -T backend bench new-site "$SITENAME" \
    --mariadb-user-host-login-scope='172.%.%.%' \
    --db-root-password "$DB_PASSWORD" \
    --admin-password "$ADMIN_PASSWORD" \
    --install-app erpnext \
    --install-app frontdesk

green "✓ Site created with ERPNext + FrontDesk installed"

# ── 8. Enable scheduler ─────────────────────────────────────
echo ">>> Enabling scheduler..."
docker compose -p "$PROJECT_NAME" exec -T backend bench --site "$SITENAME" scheduler enable
green "✓ Scheduler enabled"

# ── Done ────────────────────────────────────────────────────
echo ""
green "════════════════════════════════════════════"
green " ✅ FrontDesk is live"
green "════════════════════════════════════════════"
echo ""
echo "  URL:           https://$SITENAME"
echo "  Admin login:   Administrator"
echo "  Admin pass:    $ADMIN_PASSWORD"
echo "  DB password:   $DB_PASSWORD"
echo ""
yellow "  ⚠ Save these credentials now."
echo ""
echo "  Next steps:"
echo "    1. Login at https://$SITENAME"
echo "    2. Set up Business Settings (Omnichat config, Google review URL)"
echo "    3. Create staff members, services, working hours"
echo "    4. Test booking at https://$SITENAME/book"
echo ""
