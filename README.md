# FrontDesk

**Booking + POS + AI receptionist for service businesses.**

---

## Why FrontDesk Exists

Service businesses (barbershops, salons, spas) currently manage bookings through WhatsApp chaos:

- Customer texts "you free?" → no reply for 20 minutes
- Barber doesn't know if the 3pm actually showed
- No record of who their regulars are
- Fresha/Booksy charge 200–400 QAR/month **plus** per-booking commissions
- Owners hate it but switching seems harder than suffering

FrontDesk replaces all of that with one system: the customer books the person they want, sees real-time availability, pays at the chair, and the owner gets CRM + loyalty built in.

---

## The Core Mechanic

> **Customer picks a specific person → sees their real-time availability → books a slot.**

This defines who FrontDesk is for:

### ✅ Books a PERSON (our target)

| Business | Why it fits | Ticket size |
|---|---|---|
| **Barbershops** | "I want Ahmed, not whoever's free." Current state: WhatsApp first-come. | 30–80 QAR |
| **Hair & beauty salons** | Women specifically request the same stylist every time. Bigger ticket. | 100–500 QAR |
| **Spas / massage** | Customer picks their therapist. Higher price point. | 200–500 QAR |
| **Nail studios** | Customer returns to the same nail tech. | 80–200 QAR |
| **Aesthetics / skin clinics** | Customer books a specific practitioner. Pricey. | 300–1,000+ QAR |
| **Makeup artists** | Books the artist directly, especially for weddings/events. | 500–2,000 QAR |
| **Personal trainers** | Books a specific coach for sessions. | 200–400 QAR/session |

### ❌ Not our model
- **Gyms** — membership, not per-session
- **Coworking** — books a desk/room, person doesn't matter
- **Car wash** — book a slot, not a specific washer
- **Medical/dental** — books next available doctor, heavy regulatory

---

## What's Built (Phase 0–2)

| Feature | Status |
|---|---|
| **Booking engine** with overlap detection | ✅ |
| **Staff availability board** (API + web) | ✅ |
| **My Schedule** page (staff view) | ✅ |
| **Checkout / POS** (booking → Sales Invoice) | ✅ |
| **2h pre-appointment reminders** (hourly scheduler) | ✅ |
| **Post-paid follow-up tracking** | ✅ |
| **Loyalty program** (FrontDesk Rewards, auto-created) | ✅ |
| **Basira CRM sync** (on Customer Profile update) | ✅ |
| **Race condition protection** (SELECT FOR UPDATE) | ✅ |
| **Rate limiting** (Frappe built-in, config-only) | ✅ |
| **15 availability tests** | ✅ |
| **Deploy artifacts** (frappe_docker + setup.sh) | ✅ |

### What's Next (Phase 3–4)

| Feature | Status |
|---|---|
| WhatsApp booking via Basira-Omnichat | 📋 Planned |
| Voice booking via VoxAI | 📋 Planned |
| AI agent-brain (unified cross-channel) | 📋 Planned |
| Vertical templates (barber, salon, spa) | 📋 Planned |

---

## Tech Stack

- **Framework:** Frappe v15+
- **ERP:** ERPNext v15+
- **Database:** MariaDB (via Frappe)
- **Frontend:** Frappe Desk + custom website pages
- **CRM:** Basira CRM (sync on customer update)
- **Deployment:** frappe_docker with Traefik

---

## Architecture

```
Customer
  │
  ├── Website ──────→ Frappe Website ───┐
  ├── WhatsApp ─────→ Omnichat ─────────┤  ← Phase 3
  ├── Phone Call ───→ VoxAI ────────────┤  ← Phase 3
  └── Walk-in ──────→ Staff Tablet ─────┘
                                              │
                                              ├── Booking Engine
                                              ├── Staff Availability Board
                                              ├── My Schedule
                                              ├── Checkout / POS
                                              ├── CRM (ERPNext + Basira)
                                              └── Loyalty (ERPNext)
```

---

## DocTypes

| DocType | Purpose |
|---|---|
| **Staff Member** | Person who delivers the service. Has working hours + services. |
| **Service** | What the business sells (haircut, facial, massage). Price + duration. |
| **Booking** | An appointment. Staff + customer + service + start time. Flags for reminders/follow-ups. |
| **Customer Profile** | Linked to ERPNext Customer. Phone, preferences, Basira CRM ID. |
| **Business Settings** | Single config doc. Omnichat credentials, Google review URL, POS settings. |

---

## API Endpoints

All under `/api/method/frontdesk.api.*`:

| Endpoint | Auth | Purpose |
|---|---|---|
| `availability.get_slots` | Guest | Available time slots for a staff + service + date |
| `bookings.create_booking` | Guest | Create a new booking |
| `board.get_board` | Desk | Staff availability board (today's bookings per staff) |
| `checkout.process_checkout` | Desk | Mark booking done, create Sales Invoice, trigger loyalty |
| `reminders.send_2h_reminders` | System | Hourly scheduler: send WhatsApp reminders for upcoming bookings |
| `followups.on_booking_update` | System | Hook: track post-paid follow-ups |
| `basira_crm.sync_customer_to_basira` | System | Hook: push Customer Profile changes to Basira CRM |

---

## Repository Structure

```
frontdesk/
├── frontdesk/
│   ├── hooks.py              # Install, doc events, scheduler
│   ├── api/                  # REST endpoints
│   │   ├── availability.py
│   │   ├── bookings.py
│   │   ├── board.py
│   │   ├── checkout.py
│   │   ├── reminders.py
│   │   ├── followups.py
│   │   ├── notifications.py
│   │   └── basira_crm.py
│   ├── www/                  # Website pages (public-facing)
│   │   ├── book.py
│   │   ├── board.py
│   │   ├── my_schedule.py
│   │   ├── checkout.py
│   │   └── index.py
│   ├── templates/
│   ├── config/
│   │   ├── desktop.py
│   │   └── docs.py
│   ├── doctype/              # 5 DocTypes + 2 child tables
│   │   ├── booking/
│   │   ├── staff_member/
│   │   ├── service/
│   │   ├── customer_profile/
│   │   ├── business_settings/
│   │   ├── staff_service/        # child: services a staff member offers
│   │   └── staff_working_hour/   # child: staff working hours
│   └── tests/
│       └── test_availability.py  # 15 tests
├── docs/
│   ├── STACK.md
│   ├── FEATURES.md
│   └── PLAN.md
├── deploy/
│   ├── apps.json
│   ├── setup.sh
│   └── README.md
├── pyproject.toml
└── README.md
```

---

## Installation

```bash
# Get the app
bench get-app https://github.com/yasserbousrih/frontdesk

# Install on a site
bench --site yoursite install-app frontdesk

# Enable scheduler for 2h reminders
bench --site yoursite scheduler enable
```

**Dependencies:**
- Frappe v15+
- ERPNext v15+

**Optional integrations (Phase 3):**
- Basira-Omnichat — WhatsApp booking
- VoxAI — voice booking

---

## License

MIT
