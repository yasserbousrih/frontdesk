# FrontDesk

**Booking + POS + AI receptionist for service businesses.**
The front-of-house counterpart to [BackHouse](https://github.com/yasserbousrih/backhouse) (restaurants). Same building blocks, assembled for businesses where the customer books a **specific person** — not a room, not a time slot.

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

This mechanic defines who FrontDesk is for:

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
- **Gyms** — membership, not per-session booking
- **Coworking** — books a desk/room, person doesn't matter
- **Car wash** — book a slot, not a specific washer
- **Medical/dental clinics** — books next available doctor, heavy regulatory complexity

---

## Launch Vertical: Barbershops + Salons

Starting here because:

1. **Volume** — every neighborhood in Doha has 3–5 barbershops. 500+ in the city.
2. **Pain is real** — WhatsApp chaos is the daily reality
3. **Fresha/Booksy are hated** — monthly subscription + commissions = double tax
4. **Low complexity** — no kitchen display, no delivery APIs, no inventory beyond retail
5. **Word of mouth** — one barbershop owner talks to three others. Industry is networked.

**The pitch:** "Your customer books the barber they want, sees when they're free, pays at the chair through the same system. One-time setup. Lower monthly than Fresha. Zero per-booking commission."

---

## Building Blocks

FrontDesk assembles these reusable blocks from the Basira ecosystem:

| Block | What it does | Source |
|---|---|---|
| **Booking Engine** | Customer picks staff member → sees real-time availability → books slot | FrontDesk (new) |
| **Staff Availability Board** | Live view of who's free, who's busy, who's next | FrontDesk (new) |
| **Simple POS** | Checkout at the chair. No KOT, no kitchen routing. Just totals + payment. | Ugy (POS engine) |
| **Booking Website** | Branded booking page per business. Mobile-first. | UCM (Unified Commercial Middleware) |
| **Omnichat** | WhatsApp booking flow via Basira-omnichat | Basira-omnichat |
| **VoxAI** | Voice booking — customer calls, AI books the appointment | VoxAI |
| **CRM** | Client history, preferences, visit count | Frappe ERPNext |
| **Loyalty** | Points, stamps, rewards — replaces paper stamp cards | Frappe ERPNext |
| **Agent-Brain** | Unified AI brain across chat, voice, and email channels | Agent-Brain |

### Architecture

```
Customer
  │
  ├── WhatsApp ──→ Basira-Omnichat ──┐
  ├── Website ───→ UCM ──────────────┤
  ├── Phone Call → VoxAI ────────────┼──→ Agent-Brain ──→ FrontDesk (Frappe)
  └── Walk-in ───→ Staff Tablet ─────┘                        │
                                                              ├── Staff Availability Board
                                                              ├── Booking Calendar
                                                              ├── POS (Ugy)
                                                              ├── CRM (ERPNext)
                                                              └── Loyalty (ERPNext)
```

---

## Tech Stack

- **Framework:** Frappe v15+
- **ERP:** ERPNext v15+
- **POS:** Ugy (custom Frappe POS engine)
- **Middleware:** UCM (Unified Commercial Middleware)
- **AI Layer:** Agent-Brain + Basira-omnichat + VoxAI
- **Database:** MariaDB (via Frappe)
- **Frontend:** Frappe Desk + custom pages

---

## Repository Structure

```
frontdesk/
├── frontdesk/
│   ├── doctypes/          # Staff Profile, Booking, Service Menu, Loyalty
│   ├── pages/             # Availability Board, Booking Page
│   ├── api/               # REST endpoints for UCM/Vox/Omnichat
│   └── fixtures/
├── pyproject.toml
├── ROADMAP.md             # MVP → launch → scale
└── README.md
```

---

## Installation

```bash
# Get the app
bench get-app https://github.com/yasserbousrih/frontdesk

# Install on a site
bench --site yoursite install-app frontdesk
```

**Dependencies:**
- Frappe v15+
- ERPNext v15+
- Ugy (POS engine) — optional, for checkout
- UCM (middleware) — for website booking
- Basira-omnichat — for WhatsApp booking
- VoxAI — for voice booking

---

## License

MIT
