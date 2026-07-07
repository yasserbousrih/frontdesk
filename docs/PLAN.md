# FrontDesk — Build Plan

How we get from a docs-only repo to a barbershop running 30 days without WhatsApp. Stack decisions in [STACK.md](STACK.md), full feature detail in [FEATURES.md](FEATURES.md).

## Build order

```
Infra ─┐
Phase 0 ┴→ Phase 1 (MVP) → pilot shop 30 days → Phase 2 / Phase 3 (independent) → Phase 4
```

## Infra (parallel with Phase 0)

frappe_docker layered image (erpnext + frontdesk) → GHCR → Coolify Docker Compose resource. Local dev = same stack in Docker Desktop.

**Done when:** site live on Coolify with frontdesk installed; push → redeploy in one step.

## Phase 0 — Foundation (week 1–2)

Scaffold `bench new-app frontdesk` and merge into this repo. Build:

- All DocTypes (Staff Member, Service, Booking, Customer Profile, Business Settings)
- Availability engine + double-booking validation
- `test_availability.py` — working hours, overlaps, closing-time edge
- Clean `bench install-app frontdesk` on Frappe v15 + ERPNext v15

**Done when:** barbers, services, and bookings are manageable in Desk; the slots API returns correct free slots; double-booking is rejected.

## Phase 1 — The MVP loop (week 2–4) — the sellable product

- Booking website (`/book`) with Business Settings branding
- Staff availability board (tablet) with walk-in check-in
- Checkout → ERPNext Sales Invoice
- WhatsApp booking confirmations via Omnichat send API
- Staff `/my-schedule` page

**Done when:** customer books from a phone → barber sees it on the tablet → checkout → visit logged. The full loop on real devices with zero WhatsApp coordination. This version goes to the first barbershop.

## Phase 2 — Retention (week 4–6)

All Frappe scheduler + hooks, no new architecture:

- Visit history on Customer Profile
- Hourly scheduler job → WhatsApp reminder 2h before appointment
- ERPNext Loyalty Program — points per visit
- Post-Paid hook → "book your next?" + Google review prompt via Omnichat

## Phase 3 — AI channels (week 6–8)

Wire the existing VoxAI (voice) and Omnichat (WhatsApp conversational) into the integration API. Add `get_alternative_staff` for "Ahmed is full, Omar is free at the same time" suggestions.

**Done when:** a WhatsApp message and a phone call can each produce a confirmed booking with zero human involvement.

## Phase 4 — Verticals (week 8+)

Ship salon / clinic / spa **templates** (JSON fixtures — service lists, terminology, page wording). Vertical-specific features (packages, consent forms, multi-service visits) get built only when a paying client in that vertical exists.

## Verification

- **Phase 0:** `test_availability.py` + fresh-site install
- **Phase 1:** manual end-to-end on phone + tablet against Coolify staging
- **Phase 2/3:** every automation tested with a real WhatsApp number / test call before pilot
- **North star (ROADMAP):** one barbershop, 30 consecutive days, zero WhatsApp fallback
