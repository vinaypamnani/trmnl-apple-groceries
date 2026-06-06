# Apple Groceries — TRMNL Plugin

Display your Apple Reminders grocery list on a TRMNL device. The layouts
auto-detect their data source, so you can feed them from **either**:

- the **TRMNL Companion iOS app** (recommended) — syncs your Reminders list
  automatically, nothing to build; shows your outstanding "to buy" items, or
- an **Apple Shortcut** you build — sends both items still to buy *and* recently
  checked-off items, for a "Pending / Completed" cart view.

Built as a [trmnlp](https://github.com/usetrmnl/trmnlp) project, so it previews
locally and deploys to TRMNL from Git.

## Layouts

| Layout | Shortcut view | Companion view |
| --- | --- | --- |
| Full | 2:1 Pending (2 sub-columns) + Completed | single "to buy" list (2 sub-columns) |
| Half Horizontal | Compact 2:1, Pending in 2 sub-columns | single compact list |
| Half Vertical | Pending above Completed | single full-height list |
| Quadrant | Pending + "✓ N done" footer | Pending + "N to buy" footer |

Long lists trim with an "and N more" indicator; item names clamp via **Title
Lines** (Full) or a single line (compact). Headers are outlined pills.

## Develop locally

No Ruby required — `bin/trmnlp` runs the official tool via Docker if needed.

```sh
bin/trmnlp serve     # preview at http://localhost:4567 (live-reloads on save)
bin/trmnlp lint      # check against TRMNL best practices
```

**Windows:** use the `.cmd` wrapper from PowerShell or cmd (same Docker fallback):

```powershell
bin\trmnlp.cmd serve
bin\trmnlp.cmd lint
```

The first run pulls the `trmnl/trmnlp` Docker image (one-time, a few hundred MB).

Edit `src/*.liquid`. Sample data and custom-field values for the preview live in
`.trmnlp.yml` (defaults to the Companion `reminders` shape; swap in
`pending`/`completed` to preview the Shortcut view).

## Deploy to TRMNL

This plugin already has an `id` in `src/settings.yml`, so pushes update the
existing instance (rather than creating a new one).

**Manual:**
```sh
bin/trmnlp login     # one-time, saves your API key
bin/trmnlp push      # upload markup + settings
```

**Automatic (GitHub):** `.github/workflows/trmnl.yml` lints every PR and runs
`trmnlp push --force` on every push to `main`. Add your TRMNL API key as a repo
secret named `TRMNL_API_KEY` to enable it.

## Connect your data — pick one method

Both feed the same layouts; they differ in setup effort and how much data they
send. The Shortcut is a **superset** — it adds the Completed ("in cart") column.

| | **Companion app** (Option A) | **Apple Shortcut** (Option B) |
| --- | --- | --- |
| Setup | Install app, toggle a list on — done | Import a Shortcut, paste webhook URL, set up automations |
| Sends | `reminders` (incomplete only) | `pending` **and** `completed`, with notes |
| Completed column | ❌ no | ✅ yes ("Pending / Completed" cart view) |
| Item notes | ✅ yes | ✅ yes |
| Updates | Automatic, in the background | Only when the Shortcut runs (manual or via automation) |
| Payload limit | Handled by the app | You stay under TRMNL's **2 kB** webhook limit |
| Best for | Set-and-forget "to buy" list | A live cart showing what's checked off too |

> Pick **one.** The layouts always prefer the Shortcut's `pending`/`completed`
> and only fall back to the Companion's `reminders` when neither is present — so
> if both ever send data, the Shortcut view takes precedence.

### Option A · Companion app (recommended, no Shortcut)
1. Install [TRMNL Companion](https://apps.apple.com/us/app/trmnl-companion/id6752111280).
2. In the app's **Plugins** tab, pull to refresh, select this plugin, grant
   **Reminders** permission, and toggle your grocery list on. It syncs in the
   background.

The plugin receives a `reminders` array of your *incomplete* items, so the
display is a live "to buy" list (no Completed column — that data isn't in the
Companion payload).

### Option B · Apple Shortcut (adds the Completed column)

**Quick start — import the prebuilt Shortcut:**

1. In this plugin's settings, open the **Apple Shortcut** field and tap the link
   on your iPhone to **Add Shortcut**.
2. On import it asks for your **Webhook URL** — paste the one from this plugin's
   settings (the Option B field).
3. Run it manually, or attach a Home Screen widget / Personal Automation so it
   syncs on a schedule. It POSTs your pending + recently-completed items.

Prefer to build it yourself, or want to see exactly what it does? The full
step-by-step actions are in [`docs/apple-shortcut.md`](docs/apple-shortcut.md).
Either way, the Shortcut POSTs this shape to your Webhook URL, newest-completed
first:

```json
{
  "pending":   [ { "n": "Bananas" }, { "n": "Milk", "o": "2%" } ],
  "completed": [ { "n": "Eggs" } ]
}
```
`n` = name (required), `o` = note. Cap items so the payload stays
under TRMNL's **2 kB** webhook limit (~40 pending + 12 completed is comfortable).

> **Why two lists instead of one tagged list (`c: true` for completed)?**
> Separate `pending`/`completed` arrays are smaller on the wire (completed items
> carry no per-item discriminator), map directly onto how the Shortcut builds the
> data (two "Find Reminders" filters), and split cleanly in Liquid — there's no
> clean "where-not" to pull pending items back out of a single tagged list. A
> single list would only help if we rendered completed items *inline* among
> pending ones, which the Pending/Completed column layout intentionally doesn't.

## Settings

| Field | Effect |
| --- | --- |
| Apple Shortcut *(optional)* | Copyable iCloud link to import the prebuilt Shortcut. **Shortcut only.** |
| Webhook URL *(optional)* | POST target for the Shortcut method (Companion doesn't need it). |
| Font Size | Regular / **Large** (default) / Extra Large — scales the whole layout. |
| Title Lines | Max lines an item name wraps over (1–4); Full layout. |
| Title-Bar Label | Title-bar right side: Date & Time, Battery, both, Custom text, or Blank. Date/time and battery use the device's own values. |
| Custom Title-Bar Text | Free text shown when Title-Bar Label is **Custom**. |

## Project structure

```
src/full.liquid, half_horizontal.liquid, half_vertical.liquid, quadrant.liquid
src/settings.yml      plugin config + custom fields (uploaded)
.trmnlp.yml           local dev config + sample data (not uploaded)
.github/workflows/    lint + auto-deploy on push to main
bin/trmnlp            local/Docker wrapper
```
