# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A [trmnlp](https://github.com/usetrmnl/trmnlp) project: a TRMNL e-ink plugin that
renders an Apple Reminders grocery list as Liquid markup. There is no application
code — the deliverable is `.liquid` templates plus a plugin definition that TRMNL
renders server-side. Output targets a 1-bit (black/white) e-ink display.

## Commands

`bin/trmnlp` wraps the official tool, running it locally if the `trmnl_preview`
gem is installed, otherwise via Docker. No Ruby needed locally.

```sh
bin/trmnlp serve     # live-reloading preview at http://localhost:4567
bin/trmnlp lint      # check against TRMNL best practices — must pass before push
bin/trmnlp login     # one-time, saves API key for push
bin/trmnlp push      # upload markup + settings to TRMNL
```

There is no test suite. `lint` is the gate; CI (`.github/workflows/trmnl.yml`)
lints every PR and runs `trmnlp push --force` on every push to `main`
(needs repo secret `TRMNL_API_KEY`).

## Architecture

Four layouts — `full`, `half_horizontal`, `half_vertical`, `quadrant` — TRMNL
picks one based on the device's mashup slot. Each is a standalone `.liquid` file
in `src/`.

**Dual data source (the central design constraint).** Every layout auto-detects
which of two payload shapes it received and adapts:
- **Shortcut** sends `pending` + `completed` arrays of `{ n, o }`
  (name / note). This is the superset → enables the Completed column.
- **Companion app** sends a `reminders` array of `{ title, notes, list_name }`
  (incomplete items only) → single "to buy" list, no Completed column.

Each layout opens with a Liquid block that resolves the source into `use_shortcut`,
then sets `pending_items` / `show_completed` accordingly, normalizing field names
with `item.title | default: item.n` and `item.notes | default: item.o`. The
**List Source** custom field (`list_source`) controls this: `companion` (default)
and `shortcut` force a view; `auto` detects from the payload (Shortcut wins when
`pending`/`completed` are present). A forced view that doesn't match the incoming
data renders empty. When editing one layout's detection/rendering logic, mirror the
change across all four — they share this contract, not code.

**Conditional fields.** TRMNL select fields support `conditional_validation`
(`when: <value>` → `hidden: [keynames]` and/or `required: [keynames]`). `list_source`
uses it to hide `apple_shortcut_url` / `webhook_url` when `companion` is selected
(shown for `auto` and `shortcut`). Hideable fields are marked `optional: true` so
the form saves while hidden. This only affects the settings UI, not rendering.

**Shared styles.** `src/shared.liquid` holds all CSS and is auto-prepended to each
layout by trmnlp (do **not** add `{% render "shared" %}` — that double-renders).
Convention: shared classes are prefixed `g-` (e.g. `.g-name`, `.g-pill`,
`.g-scale-large`). Compound selectors like `.title.g-pill-text` are intentional —
they raise specificity to beat the TRMNL framework CSS, which loads before this
`<style>`. Plain `g-` classes cover only properties the framework leaves unset
(line-clamp, min-width). Settings map to CSS vars: Font Size → `--ui-scale` via
`g-scale-*`, Title Lines → `--clamp` via `g-clamp*`.

**Overflow.** Long lists rely on TRMNL framework data attributes —
`data-list-limit`, `data-list-hidden-count` ("and N more"),
`data-overflow-max-cols`, `data-overflow-counter` — rather than manual slicing.

## Config files

- `src/settings.yml` — plugin definition **uploaded** by `push`: strategy
  (`webhook`), the live plugin `id` (pushes update this instance, not create new),
  and `custom_fields` (list_source, right_label, custom_label, title_lines,
  font_size). Note:
  `trmnlp pull` overwrites this file with the server copy.
- `.trmnlp.yml` — **local dev only**, not uploaded. Holds sample webhook data for
  the preview. Defaults to the Companion `reminders` shape; comment it out and add
  `pending:`/`completed:` arrays to preview the Shortcut view.

## Constraints

- Webhook payloads must stay under TRMNL's **2 kB** limit (~40 pending + 12
  completed items). Keep field names short on the Shortcut side (`n`/`o`).
- Design for 1-bit e-ink: no color/grayscale, no animation. The outlined header
  "pill" uses a multi-direction `text-shadow` to fake an outline in pure B/W.
