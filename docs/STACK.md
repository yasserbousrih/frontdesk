# FrontDesk — Stack Decisions

The entire product is **one custom Frappe app + ERPNext**. No third-party POS, no separate frontend, no middleware.

| Layer | Choice | Cut |
|---|---|---|
| ERP / invoicing / loyalty | Frappe v15 + ERPNext v15 built-ins | — |
| CRM | **Basira CRM** (existing) — FrontDesk syncs customers on Customer Profile update via API; ERPNext Customer kept only as the invoicing record | Building CRM features in FrontDesk |
| POS | Checkout screen inside FrontDesk (booking → Sales Invoice); ERPNext built-in Point of Sale for rare retail-only sales | POS Awesome (grocery-store UI) |
| Website | Frappe `www/` pages inside the app, customizable per business from Desk | React/separate frontend |
| AI channels | VoxAI + Omnichat call FrontDesk's REST API (Phase 3) | — |
| Deploy | frappe_docker layered image on separate Hetzner VM | Coolify colocation (Basira already tight on RAM) |

## Why no POS app

The booking already knows the customer, the staff member, and the services rendered. Checkout is one screen that invoices the booking. Any standalone POS forces staff to re-enter data the system already has — those UIs are built for scanning groceries with zero prior context, the opposite of this product.

ERPNext's built-in Point of Sale stays available for the one edge case: a walk-in buying a retail product with no booking attached.

## Deployment

- **Image:** frappe_docker layered build — `apps.json` = erpnext + frontdesk → custom image → GHCR.
- **Server:** Hetzner CX22 (4 GB RAM, 2 vCPU) — separate from Coolify to avoid OOM on the shared Basira VM.
- **Stack:** frappe_docker's `pwd.yml` (backend, nginx frontend, websocket, queue workers, scheduler, MariaDB, Redis). Traefik handles TLS + domain.
- **Local dev:** same compose stack in Docker Desktop with the frontdesk app bind-mounted (Frappe doesn't run natively on Windows).
