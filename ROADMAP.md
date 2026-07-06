# FrontDesk — Roadmap & MVP

---

## MVP Definition

**Goal:** One barbershop using FrontDesk to take bookings end-to-end, with zero WhatsApp involved.

**The MVP loop:**
```
Customer opens booking link → picks barber → sees available slots → books → barber sees it on his board → customer shows up → checkout at chair → visit logged to CRM
```

That's it. If this loop works, the MVP is done.

---

## Phase 0 — Foundation (Week 1–2)

The Frappe scaffolding. No customer-facing features yet.

| Task | What | Done when |
|---|---|---|
| DocType: Staff Member | Links to Employee, has bio, photo, specialties, working hours | Can create a barber profile |
| DocType: Service | Name, duration, price, assigned to staff member(s) | Can list "Haircut — 30 min — 40 QAR" |
| DocType: Booking | Customer, staff member, service, date/time, status | Can create and view a booking |
| DocType: Customer Profile | Links to ERPNext Customer, adds preferences, notes | Can tag a customer's preferred barber |
| Availability logic | Staff working hours + existing bookings = free slots | API returns available slots for a barber on a date |
| Bench setup | App installs clean on Frappe v15 + ERPNext v15 | `bench install-app frontdesk` works |

**Deliverable:** The data model exists. You can create barbers, services, and bookings manually via Frappe desk.

---

## Phase 1 — The Booking Loop (Week 2–4)

This is the MVP that goes to the first client.

| Task | What | Done when |
|---|---|---|
| Booking Page (web) | Mobile-first page: pick barber → pick service → pick slot → confirm | Customer can book from a phone browser |
| Staff Availability Board | Live page showing all barbers: free / busy / next-up | Barber can glance at tablet and know his queue |
| Booking confirmation | WhatsApp or SMS notification to customer + barber | Both parties get notified on booking |
| Walk-in check-in | Staff can add a walk-in to the board from tablet | Walk-ins don't bypass the system |
| Simple checkout | Staff selects services rendered → total → mark paid | Transaction logged to ERPNext |
| Status workflow | Booked → Seated → In Progress → Completed → Paid | Status flows correctly end-to-end |

**Deliverable:** A barbershop can run their entire booking + checkout flow on FrontDesk. Zero WhatsApp needed.

**This is the sellable product.** Everything after this is expansion.

---

## Phase 2 — Retention Layer (Week 4–6)

Once the core loop works, add what keeps customers coming back.

| Task | What | Why |
|---|---|---|
| Visit history | Customer profile shows all past visits, barber, service, amount | "You haven't seen Ahmed in 6 weeks" |
| Automated reminders | WhatsApp reminder 2 hours before appointment | Reduces no-shows (barbershops' #1 revenue leak) |
| Loyalty / stamp card | Digital stamp card: 10 visits = 1 free | Replaces paper cards everyone loses |
| Rebooking flow | After visit, automatic "Book your next?" with next available slot | Increases return rate |
| Reviews prompt | Post-visit WhatsApp asking for Google review | SEO + social proof for the business |

**Deliverable:** The system actively drives repeat business, not just records it.

---

## Phase 3 — AI Layer (Week 6–8)

Connect the booking engine to the AI channels.

| Task | What | Why |
|---|---|---|
| WhatsApp booking (Omnichat) | Customer chats on WhatsApp → Agent-Brain reads FrontDesk availability → books | Most Qatar customers prefer WhatsApp over a website |
| Voice booking (VoxAI) | Customer calls → AI answers → checks availability → books | Catches the older demographic who calls instead of texts |
| AI receptionist | Handles reschedules, cancellations, "what time is Ahmed free?" | Offloads the owner's phone entirely |
| Smart suggestions | "Ahmed is fully booked, but Omar has the same availability — want him?" | Maximizes utilization across all barbers |

**Deliverable:** Customer can book through any channel — web, WhatsApp, voice — and it all syncs to the same booking engine.

---

## Phase 4 — Vertical Expansion (Week 8+)

Once barbershops are working, expand to adjacent verticals by reusing blocks:

| Vertical | What changes from barbershop | New blocks needed |
|---|---|---|
| **Salons** | Longer services, multiple services per visit, gender-specific staff | Room/station booking (optional) |
| **Spas** | Packages, couples bookings, therapist preference | Package deals |
| **Nail studios** | Similar to salon, simpler | — |
| **Aesthetics clinics** | Consultation flow, treatment packages, consent forms | Consent DocType |

Each vertical = same booking engine + availability board + POS, with minor config changes and maybe one new DocType.

---

## What's NOT in the MVP

Explicitly deferring these to avoid scope creep:

- ❌ Online payment before visit (cash at chair is fine for MVP)
- ❌ Inventory / retail product management
- ❌ Multi-branch / multi-location
- ❌ Staff scheduling / shift management (just working hours)
- ❌ Marketing campaigns
- ❌ Analytics dashboard (basic numbers only)
- ❌ Marketplace / discovery (each business gets their own booking page, no aggregator)

These come after the loop is proven with paying clients.

---

## Success Metric for MVP

> **One barbershop uses FrontDesk for 30 consecutive days without falling back to WhatsApp.**

If they revert to WhatsApp, the MVP failed. Find out why, fix it, try again.

Secondary metrics:
- No-show rate drops vs their pre-FrontDesk baseline
- Average tickets per barber per day increases (better queue management)
- Owner voluntarily refers another barbershop owner
