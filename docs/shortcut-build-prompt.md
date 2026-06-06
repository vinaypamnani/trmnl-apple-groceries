# Generate the Shortcut with Claude Code (macOS)

This is a paste-ready prompt for building the "Apple Groceries → TRMNL" Shortcut
**programmatically** on a Mac, using the
[generate-shortcuts-skill](https://github.com/drewocarr/generate-shortcuts-skill)
(which has Claude write the `.shortcut` plist directly and sign/import it via the
macOS `shortcuts` CLI — no GUI clicking).

It's the same shortcut described step-by-step in
[`apple-shortcut.md`](apple-shortcut.md); this page is the machine-facing spec.

## 1. Install the skill (on your Mac)

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/drewocarr/generate-shortcuts-skill.git \
  ~/.claude/skills/shortcuts-generator
```

> Note: that repo's own README shows a different clone URL
> (`shortcuts-generator.git`) — use the real path above. Restart Claude Code so
> the skill is detected.

## 2. Paste this prompt to Claude Code

> Using the shortcuts-generator skill, build a signed `.shortcut` named
> **"Apple Groceries → TRMNL"** that sends my grocery Reminders to a TRMNL
> webhook. Behaviour:
>
> 1. **Import questions** (both via `WFWorkflowImportQuestions`, asked once on
>    import — never hardcode these):
>    - *"Paste your TRMNL Webhook URL"* → store in a text variable `WebhookURL`
>      (bound to a Text action holding the URL).
>    - *"Which Reminders list holds your groceries?"* → bound to the **List**
>      filter of the Find Reminders actions, so the user picks their own list.
>      Use this **same selected list** in both Find Reminders actions below. If
>      Shortcuts can't share one import answer across both actions, add a second
>      matching import question rather than falling back to a hardcoded name.
> 2. **Find Reminders** where **List is the list chosen above** and **Is
>    Completed is false**, limit **40**. For each, build a dictionary
>    `{ "n": Name, "o": Notes, "f": Is Flagged }` and append it to a list
>    variable `Pending`. Omit `o` when Notes is empty.
> 3. **Find Reminders** where **List is that same chosen list**, **Is Completed
>    is true**, and **Completion Date is in the last 1 day**, sorted by
>    Completion Date **newest first**, limit **12**. For each, build
>    `{ "n": Name }` and append to a list variable `Completed`.
> 4. Build a dictionary `{ "pending": Pending, "completed": Completed }` (both
>    values are arrays).
> 5. **Get Contents of URL**: method **POST**, request body **JSON** set to that
>    dictionary, URL = `WebhookURL`.
> 6. Optionally show a notification: *"Sent <Pending count> to buy to TRMNL"*.
>
> Constraints: the JSON must match exactly `n` (name), `o` (note), `f` (flagged
> bool); the whole payload should stay small (the limits above keep it under
> 2 kB). If the Reminders actions don't expose **Is Flagged**, drop `f` rather
> than guessing — note that you did. Verify every action identifier against
> `ACTIONS.md`/`FILTERS.md` before writing the plist, then sign and tell me the
> output path.

## 3. After it generates

1. **Import & test:** double-click the `.shortcut`, run it once, and confirm your
   TRMNL plugin shows the Pending/Completed view. Expect to iterate — the loop +
   dictionary + magic-variable wiring is the fiddly part; if a field is wrong,
   paste the symptom back to Claude and have it patch the plist.
2. **Check flags:** if `f` made it in, flag a reminder and confirm the ⚑ shows
   (with **Show Flags** on in the plugin). If the skill dropped `f`, that's fine.
3. **Get the iCloud link for the plugin:** open the Shortcut → Share →
   **Copy iCloud Link**, then paste that `https://www.icloud.com/shortcuts/…`
   URL into the **Apple Shortcut** field's `value` in
   [`../src/settings.yml`](../src/settings.yml) (replacing `REPLACE_AFTER_SHARING`).

## Reference

- Human walkthrough of the same actions: [`apple-shortcut.md`](apple-shortcut.md)
- Payload contract: `{ "pending": [ {n,o,f} ], "completed": [ {n} ] }`, newest
  completed first, under TRMNL's 2 kB webhook limit.
