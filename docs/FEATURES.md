# FrontDesk — Custom App Feature Set

FrontDesk owns exactly what nothing else in the stack provides. Everything below lives in the one Frappe app.

## 1. Data model (DocTypes)

| DocType | Fields | Notes |
|---|---|---|
| **Staff Member** | display name, photo, bio, linked Frappe User, active; child tables: Working Hours (weekday/start/end), Services Offered | The person the customer picks. Linked User enables staff self-login. |
| **Service** | name, duration (min), price, category | — |
| **Booking** | customer, staff, service, date, start/end, status, source (web / whatsapp / voice / walk-in), notes | Status: Booked → Completed → Paid, + Cancelled / No-Show. Double-booking guard uses `SELECT FOR UPDATE` on staff row. |
| **Customer Profile** | phone, name, preferred staff, notes, Basira CRM ID, link to ERPNext Customer | Thin — Basira CRM is the CRM of record. Auto-syncs on update. |
| **Business Settings** (single) | logo, colors, cover image, about text, contact/social links, vertical template, booking rules (slot buffer, cancellation window), Omnichat API URL/token/sender, Google review URL | Drives website branding + presets + notification config. |

## 2. Availability engine — the core

`get_available_slots(staff, service, date)` — working hours minus existing bookings, sliced by service duration. Guest-allowed, whitelisted.

**Every channel — web, WhatsApp, voice, walk-in — calls this one function.**

Booking `validate` rejects overlapping bookings (no double-booking, regardless of channel).

## 3. Customer-facing website (in-app, per-business branding)

- `www/` Jinja pages: landing page + `/book` flow — pick barber → service → slot → phone number → confirmed. Mobile-first, no customer login.
- Pages read **Business Settings** for branding: the owner changes logo, colors, photos, and text from Frappe Desk and the site updates instantly. No code, no theme editing.
- `ponytail:` one template + CSS variables driven by Business Settings; a visual page-builder comes only if clients demand different layouts, not different colors.

## 4. Vertical templates (Phase 4)

- Presets for **barbershop, salon, clinic, spa** (extensible).
- Each template = a fixture bundle: service list, terminology ("barber" / "stylist" / "practitioner"), default working hours, landing-page wording.
- Picking a template in Business Settings loads the preset; everything stays editable afterward.
- `ponytail:` templates are JSON fixtures, not a template engine.

## 5. Staff self-service

- Each Staff Member links to a Frappe User. Staff log in and see **their own schedule**: today's queue, who booked them, upcoming days.
- Portal page `/my-schedule` filtered to the logged-in user's Staff Member; user permissions guarantee staff only see their own bookings.

## 6. Staff board (front-desk tablet)

- Live page, one column per barber: current / next / free.
- Realtime updates via `frappe.publish_realtime` on Booking changes.
- "Add walk-in" button → creates Booking(source=walk-in) at the current time, so walk-ins never bypass the system.

## 7. Checkout

Tap a completed booking → services pre-filled → add extras → payment method → ERPNext Sales Invoice created. Loyalty points auto-applied.

## 8. Retention (Phase 2 — built)

- **2h reminders** — hourly scheduler job queries upcoming bookings and sends WhatsApp reminders via Omnichat. No-ops gracefully if Omnichat is unconfigured.
- **Post-paid follow-ups** — `on_update` hook tracks when a booking is marked Paid, sets `follow_up_sent` flag (set only on confirmed send success).
- **Loyalty** — `after_install` creates "FrontDesk Rewards" loyalty program (1 point per currency unit). ERPNext Loyalty Program engine handles points + redemption.
- **Basira CRM sync** — `on_update` hook on Customer Profile pushes contact data to Basira CRM (`POST /internal/contacts/upsert`).

## 9. Rate limiting

Frappe built-in rate limiter (`frappe/rate_limiter.py`) — Redis-backed, config-only via `site_config.json`:
```json
"rate_limit": {"limit": 100, "window": 60}
```
Returns HTTP 429 with `X-RateLimit-*` headers. Zero custom code.

## 10. Integration API (`frontdesk/api/`)

Whitelisted REST endpoints:

| Endpoint | Auth | Purpose |
|---|---|---|
| `availability.get_slots` | Guest | Available time slots for a staff + service + date |
| `bookings.create_booking` | Guest | Create a new booking |
| `board.get_board` | Desk | Staff availability board (today's bookings per staff) |
| `checkout.process_checkout` | Desk | Mark booking done, create Sales Invoice, trigger loyalty |
| `reminders.send_2h_reminders` | System | Hourly scheduler: send WhatsApp reminders for upcoming bookings |
| `basira_crm.sync_customer_to_basira` | System | Hook: push Customer Profile changes to Basira CRM |

### Consumers

| Consumer | Uses | Status |
|---|---|---|
| **Omnichat** | WhatsApp conversational booking + outbound notifications (confirmations, reminders) | Phase 3 |
| **VoxAI** | Voice booking — calls the endpoints above | Phase 3 |
| **Basira CRM** | Receives customer sync pushes from FrontDesk | ✅ Built |
