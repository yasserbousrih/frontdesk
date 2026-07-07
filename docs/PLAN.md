# FrontDesk — Build Plan

How we get from a docs-only repo to a barbershop running 30 days without WhatsApp. Stack decisions in [STACK.md](STACK.md), full feature detail in [FEATURES.md](FEATURES.md).

## Build order

```
Infra ─┐
Phase 0 ┴→ Phase 1 (MVP) → pilot shop 30 days → Phase 2 / Phase 3 (independent) → Phase 4
```

## Infra (deferred)

frappe_docker layered image (erpnext + frontdesk) → GHCR → Hetzner CX22 (4 GB, separate VM). Deploy artifacts in `deploy/`.

**Done when:** site live on Hetzner with frontdesk installed; push → redeploy in one step.

## Phase 0 — Foundation ✅ (week 1–2)

- [x] All DocTypes (Staff Member, Service, Booking, Customer Profile, Business Settings)
- [x] Availability engine + double-booking validation
- [x] `test_availability.py` — working hours, overlaps, closing-time edge (15 tests)
- [x] Clean `bench install-app frontdesk` on Frappe v15 + ERPNext v15
- [x] Custom roles: Frontdesk Manager, Frontdesk User

## Phase 1 — The MVP loop ✅ (week 2–4)

- [x] Booking website (`/book`) with Business Settings branding
- [x] Staff availability board (tablet) with walk-in check-in
- [x] Checkout → ERPNext Sales Invoice
- [x] Staff `/my-schedule` page
- [x] Rate limiting (Frappe built-in, config-only)
- [x] Booking confirmations (notifications module)
- [x] Race condition protection (SELECT FOR UPDATE on staff row)

## Phase 2 — Retention ✅ (week 4–6)

- [x] 2h pre-appointment reminders (hourly scheduler)
- [x] Post-paid follow-up tracking
- [x] ERPNext Loyalty Program — "FrontDesk Rewards" (auto-created on install)
- [x] Basira CRM sync — Customer Profile pushes to Basira on update
- [x] N+1 query fixes across all board/schedule/checkout pages

## Phase 3 — AI channels (to do)

Wire the existing VoxAI (voice) and Omnichat (WhatsApp conversational) into the integration API. Add `get_alternative_staff` for "Ahmed is full, Omar is free at the same time" suggestions.

**Done when:** a WhatsApp message and a phone call can each produce a confirmed booking with zero human involvement.

## Phase 4 — Verticals (to do)

Ship salon / clinic / spa **templates** (JSON fixtures — service lists, terminology, page wording). Vertical-specific features (packages, consent forms, multi-service visits) get built only when a paying client in that vertical exists.

## Verification

- **Phase 0:** `test_availability.py` — 15/15 green ✅
- **Phase 1:** manual end-to-end on phone + tablet against staging (pending deploy)
- **Phase 2/3:** every automation tested with a real WhatsApp number / test call before pilot
- **North star (ROADMAP):** one barbershop, 30 consecutive days, zero WhatsApp fallback
