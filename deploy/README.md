# FrontDesk Deployment

Deploy FrontDesk (Frappe v15 + ERPNext v15 + custom app) on a fresh VM.

## Architecture

```
┌─────────────────────────────────────────────┐
│  Fresh VM (4GB+ RAM)                         │
│                                              │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Traefik │──│ Frontend │──│  Backend   │ │
│  │  (SSL)  │  │ (nginx)  │  │ (gunicorn) │ │
│  └─────────┘  └──────────┘  └────────────┘ │
│  ┌──────────────────┐  ┌─────────────────┐ │
│  │ MariaDB 11.8     │  │ Redis (x2)      │ │
│  └──────────────────┘  └─────────────────┘ │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐ │
│  │ Scheduler│ │Queue Short│ │Queue Long │ │
│  └──────────┘ └───────────┘ └───────────┘ │
│  ┌──────────┐                                │
│  │ Websocket│                                │
│  └──────────┘                                │
└─────────────────────────────────────────────┘
         │
         │ HTTPS API calls
         ▼
┌─────────────────────────────────────────────┐
│  Basira CRM (main Coolify server)           │
│  CRM of record — frontdesk syncs to it      │
└─────────────────────────────────────────────┘
```

## VM Requirements

| Spec | Minimum | Recommended |
|------|---------|-------------|
| RAM | 4 GB | 4-8 GB |
| CPU | 2 vCPU | 2-4 vCPU |
| Disk | 20 GB | 40 GB |
| OS | Ubuntu 22.04+ / Debian 12+ | Same |
| Ports | 80, 443 open | Same |

**Providers** (pick any, ~€4-8/mo):
- Hetzner Cloud — CX22 (4GB) or CX32 (8GB)
- Contabo — VPS S (4GB)
- DigitalOcean — Basic Droplet (4GB)

> The frontdesk stack uses ~1.2 GB RAM idle, leaving headroom for traffic spikes.

## Quick Start

### 1. Provision VM + point DNS

Create the VM, then add an A record pointing your subdomain to the VM's IP:

```
frontdesk.example.com  A  <VM_IP>
```

### 2. Install Docker

```bash
curl -fsSL https://get.docker.com | bash
```

### 3. Clone + run setup

```bash
git clone https://github.com/yasserbousrih/frontdesk
cd frontdesk/deploy
bash setup.sh
```

The script will:
- Clone frappe_docker
- Build a custom image (Frappe v15 + ERPNext v15 + frontdesk) — ~15 min
- Generate the production compose file with Traefik SSL
- Start all containers
- Create the Frappe site with both apps installed
- Enable the scheduler

When done, it prints your admin credentials.

### 4. Configure Business Settings

Login at `https://<your-domain>`, then:
1. Open **FrontDesk > Business Settings**
2. Set Omnichat API URL, token, sender (for WhatsApp notifications)
3. Set Google Review URL (for post-paid follow-ups)
4. Create **Staff Members** with working hours
5. Create **Services** with durations and prices

## Manual Steps (if setup.sh fails)

```bash
# Clone frappe_docker
git clone https://github.com/frappe/frappe_docker
cd frappe_docker

# Copy apps list
cp ../deploy/apps.json apps.json

# Build image (Frappe v15 + ERPNext + frontdesk)
docker build \
    --build-arg=FRAPPE_BRANCH=version-15 \
    --secret=id=apps_json,src=apps.json \
    --tag=frontdesk:v15 \
    --file=images/layered/Containerfile .

# Create env file
cat > custom.env << 'EOF'
CUSTOM_IMAGE=frontdesk
CUSTOM_TAG=v15
PULL_POLICY=missing
DB_PASSWORD=change-this-password
LETSENCRYPT_EMAIL=you@example.com
SITES_RULE=Host(`frontdesk.example.com`)
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
HTTP_PUBLISH_PORT=80
HTTPS_PUBLISH_PORT=443
EOF

# Generate compose
docker compose --env-file custom.env \
    -f compose.yaml \
    -f overrides/compose.mariadb.yaml \
    -f overrides/compose.redis.yaml \
    -f overrides/compose.https.yaml \
    config > compose.custom.yaml

# Start
docker compose -p frontdesk -f compose.custom.yaml up -d

# Wait for backend, then create site
docker compose -p frontdesk exec backend bench new-site frontdesk.example.com \
    --mariadb-user-host-login-scope='172.%.%.%' \
    --db-root-password change-this-password \
    --admin-password your-admin-password \
    --install-app erpnext \
    --install-app frontdesk

# Enable scheduler (2h reminders)
docker compose -p frontdesk exec backend bench --site frontdesk.example.com scheduler enable
```

## Coolify Integration (optional)

If you prefer managing via Coolify instead of standalone:

1. Add the VM as a **Server** in Coolify (Destinations > Add Server)
2. Create a new **Docker Compose** app in Coolify
3. Use `compose.noproxy.yaml` instead of `compose.https.yaml` (Coolify's Traefik handles SSL)
4. Point the app to the generated `compose.custom.yaml`

## Basira CRM Connection

FrontDesk connects to your Basira CRM via REST API from the separate VM. Configure the CRM endpoint URL in **Business Settings** after deployment. No VPN or private network needed — both services communicate over HTTPS.

## Updates

To update frontdesk after pushing new code:

```bash
cd frappe_docker
git pull  # in frontdesk repo first to get latest
docker build \
    --build-arg=FRAPPE_BRANCH=version-15 \
    --secret=id=apps_json,src=apps.json \
    --tag=frontdesk:v15 \
    --file=images/layered/Containerfile .
docker compose -p frontdesk -f compose.custom.yaml up -d
docker compose -p frontdesk exec backend bench --site <domain> migrate
```

## Resource Footprint

| Container | RAM |
|-----------|-----|
| MariaDB | 200-400 MiB |
| Redis (cache + queue) | ~100 MiB |
| Backend (gunicorn x2) | 300-400 MiB |
| Frontend (nginx) | 20 MiB |
| Websocket (node) | 50 MiB |
| Scheduler | 100 MiB |
| Queue short + long | ~200 MiB |
| Traefik | 30 MiB |
| **Total** | **~1.2 GiB** |

Leaves ~2.8 GB free on a 4 GB VM.
