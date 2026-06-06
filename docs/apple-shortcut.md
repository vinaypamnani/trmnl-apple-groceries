# Building the "Apple Groceries → TRMNL" Shortcut

This is the exact recipe for the Apple Shortcut that feeds the plugin's
**Shortcut view** (Pending + Completed). Most users should just **import the
prebuilt Shortcut** linked in the [README](../README.md#option-b--apple-shortcut-adds-the-completed-column);
this page is for building it from scratch or understanding what it does.

## Payload

The Shortcut POSTs this JSON to your plugin's **Webhook URL**. Note the
**`merge_variables` wrapper — TRMNL requires it**; the keys inside it become your
template variables. Sending `pending`/`completed` at the top level (no wrapper)
silently stores nothing.

```json
{
  "merge_variables": {
    "pending":   [ { "n": "Milk", "o": "2%" }, { "n": "Bananas", "o": "" } ],
    "completed": [ { "n": "Eggs" } ]
  }
}
```

`n` = name (required), `o` = note. Keep the payload under TRMNL's **2 kB**
webhook limit (~40 pending + 12 completed is comfortable).

## Setup inputs

Both values are asked once, on import, via the Shortcut's **Setup** tab
(Shortcut details → **Setup** / Import Questions). Each question binds to a **Text**
action, and a **Set Variable** captures it:

- *"Paste your TRMNL Webhook URL"* → Text action → **Set Variable** `WebhookURL`
- *"Which Reminders list holds your groceries?"* → Text action → **Set Variable** `ListName`

## Actions, in order

1. **Text** (empty) — bound to Setup question *"Paste your TRMNL Webhook URL"*.
   → **Set Variable** `WebhookURL`.
2. **Text** (empty) — bound to Setup question *"Which Reminders list holds your groceries?"*.
   → **Set Variable** `ListName`.
3. **Find Reminders** (pending)
   - **Where** `List` `is` the **`ListName`** variable — you *can* drop a variable
     into the List filter; that's how each user targets their own list without a
     hardcoded name.
   - **and** `Is Completed` `is` `false`
   - **Limit** 40 items.
4. **Repeat with Each** (the Find Reminders result):
   1. **Dictionary**:
      - `n` → Type Text → Repeat Item (its name)
      - `o` → Type Text → Repeat Item → **Notes**
   2. **Add to Variable** `Pending`
5. **Find Reminders** (completed)
   - **Where** `List` `is` the **`ListName`** variable
   - **and** `Is Completed` `is` `true`
   - **Limit** 12 items. *(Optional: add `Completion Date` `is in the last` `1`
     `day` and sort by `Completion Date`, Newest First, to show only recent buys.)*
6. **Repeat with Each** (the second result):
   1. **Dictionary**: `n` → Repeat Item (its name)
   2. **Add to Variable** `Completed`
7. **Dictionary** (the payload body) — **this is the step that's easy to get wrong**:
   - `pending`   → Type **Array** → Variable `Pending`
   - `completed` → Type **Array** → Variable `Completed`

   Both values **must** be type **Array**. If you leave them as **Text**, Shortcuts
   serializes each list into one big newline-joined string and the plugin can't
   render it.
   → **Set Variable** `mergeValues`.
8. **Get Contents of URL**
   - **URL**: Variable `WebhookURL`
   - **Method**: `POST`
   - **Request Body**: `JSON`
   - One field — key `merge_variables`, Type **Text**, value the **`mergeValues`**
     dictionary variable. (A dictionary dropped into a Text JSON field serializes as
     a nested object, giving the `{"merge_variables": {…}}` shape TRMNL wants.)
9. *(optional)* **Show Notification** — "Sent to buy to TRMNL".

## Notes & gotchas

- **`merge_variables` is mandatory.** It's the single most common reason a webhook
  "succeeds" but nothing shows up in the TRMNL console — see TRMNL's
  [webhook docs](https://docs.trmnl.com/go/private-plugins/webhooks).
- **`pending`/`completed` must be Array-typed** in the Dictionary action (step 7).
  Text-typed values stringify the list.
- **Empty lists are fine.** Sending only `pending` (no `completed`) still shows the
  Completed column with "Nothing in cart yet"; sending only `completed` shows
  "All shopped!" on the Pending side.
- **Stay under 2 kB.** The two `Limit` actions are what keep you there. Long lists
  trim on-device with an "and N more" indicator regardless.
- **Running it:** trigger manually, from a Home Screen widget, or via a Personal
  Automation (e.g. every few hours, or when you leave a location) so the display
  stays current. The plugin's `refresh_interval` only controls how often TRMNL
  re-renders what it last received — it does not pull from Reminders.
- **Sharing your build:** Shortcut details → Share → **Copy iCloud Link**, then drop
  that `https://www.icloud.com/shortcuts/…` URL into the README and the
  `webhook_url` field description.
