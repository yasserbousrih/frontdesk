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

8. **Online Payments & Gateway Settings (Back House Pattern)**:
   - FrontDesk integrates with Frappe's official `payments` app (`frappe/payments`, branch version-16).
   - `Business Settings` has the `tab_payments` tab with `enable_online_payments` (Check toggle), `payment_gateway` (None, FrontDesk Gateway, Paymob, Stripe, Cash On Service), `payment_mode` (Pay on Service, Online Now, Both), and `booking_payment_methods` (`FrontDesk Payment Method` child table).
   - `sync_gateway_from_settings()` auto-builds the `Payment Gateway`, `Payment Gateway Account` (tied to Company default cash/bank account and currency), and `Mode of Payment: Online` (`type: Phone`).
   - Web booking wizard (`/book`) reads `enable_online_payments` & `payment_mode`; when online pay is selected/required, passes `pay_online=1` and triggers `create_payment_request()`, generating a standard `Payment Request` linked to the `Booking` and returning `/fd_pay?pr=...`.
   - On payment authorization / webhook, `Payment Request` transitions to `Paid` and updates `Booking.status = "Paid"` while triggering WhatsApp confirmation.

---

## Verification Commands

- **Unit tests (availability)**: `PYTHONPATH=/home/frappe/frontdesk python3 /home/frappe/frontdesk/frontdesk/tests/test_availability.py`
- **Unit tests (payments)**: `bash /root/run-bench.sh --site frontdesk.local run-tests --module frontdesk.tests.test_payments`
- **Compile check**: `python3 -c "import ast, glob; [ast.parse(open(f).read()) for f in glob.glob('/home/frappe/frontdesk/frontdesk/**/*.py', recursive=True)]; print('OK')"`
- **Bench migrate**: `bash /root/run-bench.sh --site frontdesk.local migrate`
- **Bench restart**: `bash /root/run-bench.sh restart`
- **Live web curl**: `curl -s -H "Host: frontdesk.local" http://127.0.0.1:8000/`

## Clone / Fresh-Install Playbook
Complete recipe to go from a blank server to a working FrontDesk site.

### 1. Install bench + apps
```bash
cd /home/frappe/frappe-bench
bench get-app frontdesk git@github.com:basira/frontdesk.git --branch master
bench --site <site_name> install-app frontdesk
```
`after_install` fires and:
- Creates `Frontdesk Manager` and `Frontdesk User` roles (if absent)
- Creates `FrontDesk Rewards` loyalty program (if ERPNext is installed)
- Runs `_ensure_custom_fields` — creates all Item / Sales Invoice Item custom fields
- Seeds `Business Settings` defaults (only blank fields — `_seed_homepage_defaults`)
- Creates 4 sample service Items (if Item table is empty under "Services")
- Imports `fixtures/role_profile.json` → `Frontdesk Manager` + `Frontdesk User` role profiles
- Reloads `Business Settings` and `Homepage Section` DocTypes with `force=False`

### 2. After every `git pull`
```bash
git -C /home/frappe/frappe-bench/apps/frontdesk pull origin master
bash /root/run-bench.sh --site <site_name> migrate
```
`after_migrate` fires and:
- Re-runs `_ensure_custom_fields` (idempotent — only creates missing ones)
- Reloads `Business Settings` + `Homepage Section` with `force=False`
- Calls `_seed_homepage_defaults` which fills only empty fields

### 3. MIGRATION SAFETY RULES
- **`force=False`**: NEVER use `force=True` on `reload_doc`. It nukes and rebuilds the DocType from JSON, wiping Desk-made customizations. `force=False` adds new JSON fields without removing existing ones.
- **Seed guards**: `_seed_homepage_defaults` uses `if not bs.get(field)` before writing — removing this guard is a bug that would overwrite owner data on every migrate.
- **Custom fields via `_upsert_custom_field`**: uses `if frappe.db.exists("Custom Field", ...)` guard — idempotent. Never use raw DDL.
- **`field_order` must include ALL fields**: Frappe v16 uses `field_order` in the DocType JSON as the source of truth for ordering AND completeness. If a field is in `fields[]` but not in `field_order`, it gets ignored by `bench migrate`. Always keep `field_order` in sync with `fields` — the array must have the same length. (Bug found + fixed Aug 2026 for Tab Break fields.)

### 4. What survives a migrate
- All `tabSingles` data (Business Settings values) — always safe
- `tabHomepage Section` rows — child table data, never touched by migrate
- Custom Fields in `tabCustom Field` — survive with `force=False`
- Role Profiles from fixtures — re-imported each migrate (idempotent)

### 5. What does NOT survive a DB wipe
- All settings the owner configured — `after_install` seeds defaults
- Sample services created on first install
