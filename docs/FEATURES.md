# FrontDesk — Custom App Feature Set

FrontDesk owns exactly what nothing else in the stack provides. Everything below lives in the one Frappe app.

## 1. Data model (DocTypes)

| DocType | Fields | Notes |
|---|---|---|
| **Staff Member** | display name, photo, bio, linked Frappe User, active; child tables: Working Hours (weekday/start/end), Services Offered | The person the customer picks. Linked User enables staff self-login. |
| **Service** | name, duration (min), price, category | — |
| **Booking** | customer, staff, service, date, start/end, status, source (web / whatsapp / voice / walk-in), notes | Status = plain select: Booked → Seated → In Progress → Completed → Paid, + Cancelled / No-Show. Controller-validated transitions — no Frappe Workflow engine. |
| **Customer Profile** | phone, name, preferred staff, notes, Basira CRM ID, link to ERPNext Customer | Thin — Basira CRM is the CRM of record. |
| **Business Settings** (single) | logo, colors, cover image, about text, contact/social links, vertical template, booking rules (slot buffer, cancellation window) | Drives website branding + presets. |

## 2. Availability engine — the core

`get_available_slots(staff, service, date)` — working hours minus existing bookings, sliced by service duration. Guest-allowed, whitelisted.

**Every channel — web, WhatsApp, voice, walk-in — calls this one function.**

Booking `validate` rejects overlapping bookings (no double-booking, regardless of channel).

## 3. Customer-facing website (in-app, per-business branding)

- `www/` Jinja pages: landing page + `/book` flow — pick barber → service → slot → phone number → confirmed. Mobile-first, no customer login.
- Pages read **Business Settings** for branding: the owner changes logo, colors, photos, and text from Frappe Desk and the site updates instantly. No code, no theme editing.
- `ponytail:` one template + CSS variables driven by Business Settings; a visual page-builder comes only if clients demand different layouts, not different colors.

## 4. Vertical templates

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

Tap a completed booking → services pre-filled → add extras → payment method → ERPNext Sales Invoice created. Visit pushed to Basira CRM.

## 8. Integration API (`frontdesk/api/`)

Token-authenticated endpoints:

`get_slots` · `create_booking` · `reschedule` · `cancel` · `find_customer` · `get_alternative_staff`

| Consumer | Uses |
|---|---|
| **VoxAI** (existing) | Voice booking — calls the endpoints above |
| **Omnichat** (existing) | WhatsApp conversational booking + outbound notifications (confirmations, reminders) via its send API |
| **Basira CRM** | Customer + visit sync on Customer Profile changes and Booking → Paid |
