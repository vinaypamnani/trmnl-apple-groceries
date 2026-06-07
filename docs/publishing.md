# Publishing checklist (and personal use)

How to publish this plugin as a TRMNL **recipe** without footguns, and how to run
your own real grocery list separately.

## Key facts to keep in mind

- The plugin instance you publish becomes the **Recipe Master**. Its **most recent
  screen render is the public preview image**, so it must show *demo* data, not your
  real list.
- **Edits to the master auto-propagate** to everyone who installed the recipe. Push
  changes deliberately.
- **Custom field values do NOT copy to installs/forks** — each installer gets their
  own blank `webhook_url`, Top Title, etc. Your values stay yours.
- There is **no "demo data" field**. For a webhook plugin you seed the preview by
  **POSTing fake data to the master's webhook URL** and force-refreshing.
- **Published recipes can't be self-deleted.** Unlisting/removal requires contacting
  TRMNL. Get it right before publishing.

## Part 1 — Before you publish (prep the master)

1. **Ship the latest code.** `git push` to `main` → CI runs `trmnlp push --force`,
   updating the master (id `325674`). Confirm the GitHub Action is green (it lints
   first). This deploys the `category: life`, the author bio, and the dropped
   `apple_shortcut_url` field.
2. **Confirm the icon** is set in the TRMNL portal (done).
3. **Set the master to the showcase view.** In the master's settings, set
   **List Source → Apple Shortcut** (so the demo payload below matches and you get
   the richest view — Pending + Completed — with no "fallback" footnote).
4. **Seed demo data.** Copy the master's **Webhook URL** (from the Webhook URL
   field) and run the seeder, then **force-refresh** the plugin (portal: the
   plugin's refresh, or refresh on a paired device):

   ```sh
   scripts/seed-demo-data.sh "<MASTER_WEBHOOK_URL>"
   ```

   It POSTs a clean ~25 to-buy + 6 completed sample list (≈0.8 kB). Edit the
   payload in that script if you want different demo items.
5. **Eyeball the preview** in the portal — confirm it renders the demo list nicely
   across the layout(s) you care about.
6. **Publish** from the portal. Author bio already has a contact (`github_url`) and a
   `category`, which the publish check requires.

> Keep the master pointed at this demo data. **Don't** connect your Companion app or
> run your real Shortcut against the master — that would overwrite the preview with
> your real groceries.

## Part 2 — Use it for yourself (separate from the master)

1. **Install your own published recipe** (or keep a separate private copy). This
   creates a **new instance with its own Webhook URL** — independent of the master.
2. In *that* instance, set **List Source** to the method you use.
3. **Companion app (easiest):** TRMNL Companion → Plugins → select this plugin →
   grant Reminders access → toggle your real "Groceries" list on. It posts to your
   instance automatically.
4. **Apple Shortcut (adds the Completed column):** import the shortcut (link is in
   the Webhook URL field's description), paste *your instance's* Webhook URL when
   prompted, and add automations (on a schedule / when Reminders closes).
5. Your real list now drives your device; the master stays in its demo state.

## Part 3 — Maintaining after publish

- **Every edit propagates.** Test locally first (`bin/trmnlp serve` / `build`); for
  risky changes, copy the plugin and test the copy before touching the master.
- **Keep the payload contract stable** — renaming `reminders`/`completed` or the
  `t`/`n` item keys would break every installed copy at once.
- **Re-seed demo data** only if a render change alters how the preview looks (repeat
  Part 1, steps 4–5).
- **Unlist/delete** ⇒ contact TRMNL; there's no self-serve removal.
