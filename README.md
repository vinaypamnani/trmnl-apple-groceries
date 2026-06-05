# Apple Grocery Reminders — TRMNL Plugin

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

### Option A · Companion app (recommended, no Shortcut)
1. Install [TRMNL Companion](https://apps.apple.com/us/app/trmnl-companion/id6752111280).
2. In the app's **Plugins** tab, pull to refresh, select this plugin, grant
   **Reminders** permission, and toggle your grocery list on. It syncs in the
   background.

The plugin receives a `reminders` array of your *incomplete* items, so the
display is a live "to buy" list (no Completed column, no flags — that data isn't
in the Companion payload).

### Option B · Apple Shortcut (adds the Completed column)
Build a Shortcut that POSTs to the plugin's **Webhook URL** (shown in the plugin
settings). Send both lists, newest-completed first:

```json
{
  "pending":   [ { "n": "Bananas" }, { "n": "Milk", "o": "2%", "f": true } ],
  "completed": [ { "n": "Eggs" } ]
}
```
`n` = name (required), `o` = note, `f` = flagged. Cap items so the payload stays
under TRMNL's **2 kB** webhook limit (~40 pending + 12 completed is comfortable).

## Settings

| Field | Effect |
| --- | --- |
| Webhook URL | POST target for the Shortcut method (Companion doesn't need it). |
| Right Label | Title-bar right side: Attribution, Your Name, or Blank. |
| Show Flags | Flag icon for flagged items. **Shortcut only.** |
| Title Lines | Max lines an item name wraps over (1–4); Full layout. |
| Font Size | Regular / **Large** (default) / Extra Large — scales the whole layout. |

## Project structure

```
src/full.liquid, half_horizontal.liquid, half_vertical.liquid, quadrant.liquid
src/settings.yml      plugin config + custom fields (uploaded)
.trmnlp.yml           local dev config + sample data (not uploaded)
.github/workflows/    lint + auto-deploy on push to main
bin/trmnlp            local/Docker wrapper
```
