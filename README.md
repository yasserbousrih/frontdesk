# FrontDesk

A Frappe custom app for booking-based service businesses — **barbershops, salons, clinics, spas, gyms** — that combines POS, appointment booking, a customer-facing website, WhatsApp AI, voice AI, and ERP into one integrated system.

Part of the **Basira ecosystem** — the service-industry counterpart to [BackHouse](https://github.com/yasserbousrih/backhouse) (restaurant operations).

> **The idea:** A barbershop doesn't need a kitchen display or table ordering. It needs booking, checkout, and a 24/7 AI receptionist. FrontDesk assembles the right blocks for service businesses — without the restaurant overhead.

---

## Why FrontDesk Exists

Service businesses currently juggle 3–5 tools that don't talk to each other:

| They pay for | What it does | Problem |
|---|---|---|
| Fresha / Booksy | Booking + commission | Charged per booking. Barbershops hate it. |
| Square / generic POS | Checkout | Doesn't know the appointment. |
| WhatsApp Business | Customer comms | Manual replies. Missed bookings at night. |
| Loyalty app (Beans, etc.) | Rewards | Doesn't sync with POS or booking. |
| Website vendor | Online presence | Separate from booking system. |

**FrontDesk replaces all of them with one system.** The booking knows the loyalty points. The POS knows the appointment. The AI voice agent answers the phone at 11pm and books the slot directly into the calendar. Everything syncs.

---

## Building Blocks

FrontDesk assembles these blocks from the Basira ecosystem:

### Core (included in FrontDesk)
| Block | Description |
|---|---|
| **Appointment Booking** | Calendar slots, resource/staff booking, queue management. Built on Frappe's appointment system. |
| **Service POS** | Checkout, receipts, service-based pricing (no complex modifiers or KOT). Powered by [Ugy](https://github.com/yasserbousrih/ugy). |
| **Staff Board** | Real-time availability — who's free, who's busy, estimated wait time. |
| **Customer Website** | Public-facing site with live booking, service menu, staff profiles, SEO-optimized. |
| **Loyalty & Rewards** | Visit-based rewards (10th cut free), points, tiers. Synced with POS and booking. |

### Integrations
| Block | Description |
|---|---|
| **WhatsApp AI Agent** | Customers book via WhatsApp chat. AI handles FAQs, slot picking, reminders. Powered by [Basira Omnichat](https://github.com/yasserbousrih/basira-omnichat) + [Agent-Brain](https://github.com/yasserbousrih/agent-brain). |
| **Voice AI** | AI answers phone calls, books appointments, logs to CRM. Powered by [Vox](https://github.com/yasserbousrih/vox). |
| **CRM** | Customer profiles — preferred staff, visit history, spending, notes. |
| **Campaigns** | Broadcast WhatsApp messages, promos, re-engagement for no-shows. |
| **Printer** | Receipt printing via ESC/POS. Powered by [UCM](https://github.com/yasserbousrih/ucm). |
| **Frappe ERP** | Sales, inventory (products/supplies), expenses, payroll. Full back-office. |

---

## Target Industries

FrontDesk is designed for **appointment-based service businesses**. The same blocks configure differently per industry:

| Industry | Booking Style | POS Type | Extra Blocks |
|---|---|---|---|
| **Barbershop** | Pick barber → pick slot | Simple checkout | Loyalty (visit count) |
| **Hair & Beauty Salon** | Pick stylist → pick service → pick slot | Multi-service checkout | Loyalty, package deals |
| **Spa / Wellness** | Pick treatment → pick therapist → pick room | Service + product checkout | Room booking, packages |
| **Nail Salon** | Pick technician → pick service | Simple checkout | Loyalty |
| **Clinic / Dental** | Pick doctor → pick slot | Billing + insurance | Patient records, reminders |
| **Gym / Fitness** | Class booking or trainer booking | Membership billing | Subscriptions, attendance |
| **Massage Therapy** | Pick therapist → pick duration | Service checkout | Room booking |
| **Car Wash / Auto Detail** | Pick service → pick bay → pick slot | Service checkout | Vehicle history |
| **Tattoo Studio** | Pick artist → pick session length | Deposit + final payment | Portfolio, consultation booking |
| **Pet Grooming** | Pick groomer → pick service → pet size | Service checkout | Pet profiles |
| **Photography Studio** | Pick photographer → pick session type | Package billing | Session packages |
| **Tutoring Center** | Pick tutor → pick subject → pick slot | Billing | Attendance, progress tracking |
| **Yoga Studio** | Class booking | Membership + drop-in | Class capacity, waitlist |
| **Aesthetics / Laser Clinic** | Pick treatment → pick slot | Treatment packages | Medical notes, consent forms |

> **Adding a new vertical** = configuration, not a new build. If 80%+ of existing blocks apply and you need ≤2 new industry-specific blocks, it's a quick deployment.

---

## Architecture

```
                    ┌─────────────────────────────────┐
                    │         Customer Touchpoints      │
                    │                                   │
                    │   Website    WhatsApp    Phone    │
                    │   (booking)  (AI chat)   (Vox AI) │
                    └──────────┬────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │      FrontDesk       │
                    │   (Frappe App)       │
                    │                      │
                    │  • Booking/Calendar  │
                    │  • Staff Board       │
                    │  • Service POS       │
                    │  • Loyalty           │
                    │  • CRM               │
                    └──┬────────┬─────────┘
                       │        │
          ┌────────────▼──┐  ┌──▼───────────┐
          │     Ugy        │  │     UCM      │
          │  (POS Engine)  │  │ (Middleware) │
          │                │  │  • Printer   │
          └────────────────┘  │  • Payments  │
                              └──────────────┘
                       │
          ┌────────────▼──────────────┐
          │      Frappe ERP           │
          │  • Sales  • Inventory     │
          │  • Expenses • Payroll     │
          │  • HR     • Accounting    │
          └───────────────────────────┘
```

---

## Dependencies

FrontDesk integrates with these Basira ecosystem apps:

| App | Purpose | Required? |
|---|---|---|
| [Frappe](https://github.com/frappe/frappe) | Base framework | ✅ Yes |
| [ERPNext](https://github.com/frappe/erpnext) | ERP modules (sales, inventory, HR) | ✅ Yes |
| [Ugy](https://github.com/yasserbousrih/ugy) | POS engine | ✅ Yes |
| [UCM](https://github.com/yasserbousrih/ucm) | Middleware (printer, payments) | 🔶 Optional (for printing) |
| [Agent-Brain](https://github.com/yasserbousrih/agent-brain) | AI agent tools (CRM, booking, leads) | 🔶 Optional (for AI) |
| [Basira Omnichat](https://github.com/yasserbousrih/basira-omnichat) | WhatsApp AI agent | 🔶 Optional (for WhatsApp) |
| [Vox](https://github.com/yasserbousrih/vox) | Voice AI agent | 🔶 Optional (for phone) |

---

## Installation

```bash
# 1. Get the app
bench get-app https://github.com/yasserbousrih/frontdesk

# 2. Install on your site
bench --site your-site.com install-app frontdesk
```

---

## Status

🚧 **In Development** — Architecture and block mapping defined. Core doctypes and booking flow in progress.

## License

MIT
