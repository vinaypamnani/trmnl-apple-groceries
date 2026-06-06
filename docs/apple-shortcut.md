# Building the "Apple Groceries → TRMNL" Shortcut

This is the exact recipe for the Apple Shortcut that feeds the plugin's
**Shortcut view** (Pending + Completed). Most users should just **import the
prebuilt Shortcut** linked in the [README](../README.md#option-b--apple-shortcut-adds-the-completed-column);
this page is for building it from scratch or understanding what it does.

The Shortcut POSTs this JSON to your plugin's **Webhook URL**:

```json
{
  "pending":   [ { "n": "Milk", "o": "2%", "f": true }, { "n": "Bananas" } ],
  "completed": [ { "n": "Eggs" } ]
}
```

`n` = name (required), `o` = note, `f` = flagged. Keep the payload under
TRMNL's **2 kB** webhook limit (~40 pending + 12 completed is comfortable).

## Actions, in order

1. **Text** — paste your Webhook URL here. Set this as the Shortcut's *Import
   Question* (Shortcut details → **Import Questions** → add a question like
   "Paste your TRMNL Webhook URL" bound to this Text action) so anyone importing
   the Shortcut is prompted for their own URL.
   → *Set Variable* `WebhookURL` to this Text.

2. **Find Reminders**
   - **Where**: `List` `is` `Grocery List` (change to your list's name)
   - **and** `Is Completed` `is` `false`
   - **Limit**: 40 items (keeps the payload small)
   → result is your pending reminders.

3. **Repeat with Each** (the Find Reminders result):
   1. **Dictionary**:
      - `n` → Repeat Item → **Name**
      - `o` → Repeat Item → **Notes**
      - `f` → Repeat Item → **Is Flagged** *(see note below)*
   2. **Add to Variable** `Pending`
   > To read `Name`/`Notes`/`Is Flagged`, use **Get Details of Reminders** on the
   > Repeat Item, or pick the property directly from the Repeat Item magic
   > variable.

4. **Find Reminders** (second one)
   - **Where**: `List` `is` `Grocery List`
   - **and** `Is Completed` `is` `true`
   - **and** `Completion Date` `is in the last` `1` `day`
   - **Sort by** `Completion Date`, **Newest First**
   - **Limit**: 12 items
   → recently checked-off reminders.

5. **Repeat with Each** (the second Find Reminders result):
   1. **Dictionary**: `n` → Repeat Item → **Name**
   2. **Add to Variable** `Completed`

6. **Dictionary** (the payload):
   - `pending`   → Variable `Pending`   (type: **Array**)
   - `completed` → Variable `Completed` (type: **Array**)

7. **Get Contents of URL**
   - **URL**: Variable `WebhookURL`
   - **Method**: `POST`
   - **Request Body**: `JSON`
   - **JSON**: the Dictionary from step 6

8. *(optional)* **Show Notification** — "Sent {{Pending count}} to buy to TRMNL".

## Notes & gotchas

- **`f` (flagged):** Apple Reminders flags are only exposed as **Is Flagged** on
  newer iOS versions. If your Shortcuts build doesn't offer it, drop `f`
  entirely (the layouts treat a missing `f` as not-flagged) or substitute
  `Priority is High`. The plugin's **Show Flags** setting must also be on.
- **Empty lists are fine.** Sending only `pending` (no `completed`) still shows
  the Completed column with "Nothing in cart yet"; sending only `completed`
  shows "All shopped!" on the Pending side.
- **Stay under 2 kB.** The two `Limit` actions above are what keep you there.
  Long lists trim on-device with an "and N more" indicator regardless.
- **Running it:** trigger manually, from a Home Screen widget, or via a Personal
  Automation (e.g. every few hours, or when you leave a location) so the display
  stays current. The plugin's `refresh_interval` only controls how often TRMNL
  re-renders what it last received — it does not pull from Reminders.
- **Sharing your build:** Shortcut details → Share → **Copy iCloud Link**, then
  drop that `https://www.icloud.com/shortcuts/…` URL into the README and the
  `webhook_url` field description.
