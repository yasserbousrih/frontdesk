# AGENTS.md — FrontDesk (frontdesk app) project

Instructions for AI coding agents (agy / Claude Code / Hermes) working in this repo.

> **IMPORTANT — READ THIS AND IMPROVE IT.** Start each session by reading this file.
> If you discover a gotcha, a fixed bug, a tricky deploy step, or anything not captured here,
> ADD it to this file before finishing. This is a living doc; it grows from real work.

## What this is
The **FrontDesk** booking, POS, and front-desk operating system for service businesses (barber, salon, clinic, spa, gym, nail studio).
Source of truth for customer bookings, availability scheduling, front-desk board, checkout / POS invoicing, staff portals, and bilingual Arabic/English receipts & web pages.
Built on **Frappe / ERPNext** (Frappe v16).

## DEEP KNOWLEDGE lives in Hermes skills — read them for hard problems
The full accumulated expertise is in these Hermes skills under
`/root/.hermes/profiles/frappe-bot-2/skills/` (or default profile):
- **`frontdesk`** (software-development/) — full repo map, singletons, booking flows, appearance & theming, Arabic receipt rendering, time normalization, concurrency locking. Load EVERY time you touch frontdesk.
- **`frappe-bench-ops`** (software-development/) — bench/site debugging, app sync, fixtures, worker restarts.
- **`deepseek-token-budget`** / **`working-style`** / **`karpathy-guidelines`** — token discipline and coding quality.

---

## Architecture & Layout Map

```
/home/frappe/frontdesk/
├── AGENTS.md
├── ROADMAP.md
├── README.md
├── pyproject.toml
├── deploy/
├── docs/
└── frontdesk/                   # Bench app root (symlinked from /home/frappe/frappe-bench/apps/frontdesk)
    ├── hooks.py                 # App hooks (after_install, after_migrate, doc_events, scheduler)
    ├── modules.txt
    ├── config/                  # desktop.py, docs.py
    ├── data/                    # Vertical presets (barbershop, clinic, salon, spa)
    ├── fixtures/                # role_profile.json
    ├── frontdesk/
    │   ├── doctype/             # Booking, Business Settings, Customer Profile, Staff Member, Staff Service, Staff Working Hour
    │   ├── workspace/           # Desk workspace definition (number cards, quick lists, charts)
    │   └── desktop_icon/        # Desk grid icon (v16 home grid tile)
    ├── api/                     # Whitelisted REST endpoints
    │   ├── availability.py      # get_available_slots (multi-staff union, buffer, working hours)
    │   ├── bookings.py          # create_web_booking (auto-assign staff, race-free overlap check)
    │   ├── board.py             # get_board (live stations & walk-ins)
    │   ├── checkout.py          # process_checkout (POS Sales Invoice, loyalty, epson snapshot)
    │   ├── notifications.py     # send_booking_confirmation (WhatsApp via Omnichat)
    │   ├── reminders.py         # send_2h_reminders (scheduled 2h reminder)
    │   ├── followups.py         # on_booking_update (post-paid review request)
    │   └── basira_crm.py        # sync_customer_to_basira (Basira CRM upsert)
    ├── www/                     # Public web pages & theming
    │   ├── index.html / index.py        # Rich homepage (hero, story, services, how-it-works, gallery, testimonials, hours, CTA)
    │   ├── book.html / book.py          # Multi-step booking wizard with industry flows
    │   ├── board.html / board.py        # Front-desk station board / tablet view
    │   ├── checkout.html / checkout.py  # POS checkout interface
    │   ├── my_schedule.html / my_schedule.py # Staff portal queue view
    │   ├── _branding.py                 # Business Settings resolver, VERTICAL_LOOKS, VERTICAL_FLOWS
    │   └── _theme.py                    # 12 theme presets, Google Fonts matrix, WCAG contrast resolver
    └── tests/
        └── test_availability.py         # Standalone availability unit tests
```

---

## Top Critical Gotchas & Patterns

1. **Services-as-Items (ERPNext Item)**:
   - FrontDesk treats services as ERPNext **Item** records (`item_group="Services"`, `is_stock_item=0`).
   - Domain attributes are Custom Fields on Item: `duration_minutes`, `service_category`, `show_on_homepage`, `item_name_ar`, `department`.
   - Never re-introduce a standalone `Service` DocType.

2. **Concurrency & Race-Free Overlap Check**:
   - `Booking.validate` enforces no overlapping bookings for the same staff member.
   - MariaDB REPEATABLE READ requires a **locking read**: `frappe.db.sql("... FOR UPDATE")` on existing bookings so concurrent requests see uncommitted rows.

3. **v16 Time Handling (`datetime.timedelta`)**:
   - Frappe v16 returns Time fields from `db.sql`/`get_all` as `datetime.timedelta`.
   - Always normalize Time fields before using `.hour` or `.minute` using `_time_to_minutes()` / `normalize_time()`.

4. **v16 Guest Redirect**:
   - `login_manager.require_login` is removed in v16. Use:
     ```python
     if frappe.session.user == "Guest":
         frappe.local.flags.redirect_location = "/login"
         raise frappe.Redirect
     ```

5. **Single DocType Check Columns (Business Settings)**:
   - `frappe.get_single()` returns `None` for unset Check fields, but the first `.save()` writes untouched Checks as `0`.
   - Always set `show_*` toggles to `1` explicitly before the first save, or readers will hide all sections.

6. **Appearance & Theming System (Back House Structure)**:
   - `Business Settings` has an Appearance tab with 12 presets (Brass, Teal, Terracotta, Forest, Navy, Burgundy, Midnight, Desert, Ocean, Slate, Rose, Olive) + Custom.
   - Per-vertical default looks (`VERTICAL_LOOKS`) and flows (`VERTICAL_FLOWS`) defined in `_branding.py`.
   - Desk live preview iframe renders unsaved settings via `/?preview_settings=<urlencoded JSON>`.

7. **Bilingual Arabic/English Display**:
   - Website renders English name with Arabic directly underneath: `<span class="name-ar" lang="ar">...</span>`.
   - CSS: `display: block; font-family: var(--font-arabic); direction: rtl; unicode-bidi: isolate; font-weight: 600; color: var(--text);`.
   - Epson receipt printing snapshots `item_name_ar` onto Sales Invoice Item rows.

---

## Verification Commands

- **Unit tests**: `PYTHONPATH=/home/frappe/frontdesk python3 /home/frappe/frontdesk/frontdesk/tests/test_availability.py`
- **Compile check**: `python3 -c "import ast, glob; [ast.parse(open(f).read()) for f in glob.glob('/home/frappe/frontdesk/frontdesk/**/*.py', recursive=True)]; print('OK')"`
- **Bench migrate**: `bash /root/run-bench.sh --site frontdesk.local migrate`
- **Bench restart**: `bash /root/run-bench.sh restart`
- **Live web curl**: `curl -s -H "Host: frontdesk.local" http://127.0.0.1:8000/`
