# FrontDesk — Stack Decisions

The entire product is **one custom Frappe app + ERPNext**. No third-party POS, no separate frontend, no middleware.

| Layer | Choice | Cut |
|---|---|---|
| ERP / invoicing / loyalty | Frappe v15 + ERPNext v15 built-ins | — |
| CRM | **Basira CRM** (existing) — FrontDesk syncs customers & visits to it via API; ERPNext Customer kept only as the invoicing record | Building CRM features in FrontDesk |
| POS | Checkout screen inside FrontDesk (booking → Sales Invoice); ERPNext built-in Point of Sale for rare retail-only sales | POS Awesome (grocery-store UI), Ugy (revisit if a client needs cash drawer / shifts) |
| Website | Frappe `www/` pages inside the app, customizable per business from Desk | UCM middleware, React/separate frontend |
| AI channels | Existing VoxAI + Omnichat call FrontDesk's REST API | Agent-Brain dependency for MVP |
| Deploy | frappe_docker layered image on Coolify | — |

## Why no POS app

The booking already knows the customer, the staff member, and the services rendered. Checkout is one screen that invoices the booking. Any standalone POS (POS Awesome included) forces staff to re-enter data the system already has — those UIs are built for scanning groceries with zero prior context, the opposite of this product.

ERPNext's built-in Point of Sale stays available for the one edge case: a walk-in buying a retail product with no booking attached.

## Deployment

- **Image:** frappe_docker layered build — `apps.json` = erpnext + frontdesk → custom image → GHCR.
- **Coolify:** Docker Compose resource adapted from frappe_docker's `pwd.yml` (backend, nginx frontend, websocket, queue workers, scheduler, MariaDB, Redis). Coolify handles TLS + domain on the frontend service.
- **Local dev:** same compose stack in Docker Desktop with the frontdesk app bind-mounted (Frappe doesn't run natively on Windows).
