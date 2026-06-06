# Generate the Shortcut (script + spec)

There are two ways to (re)produce the **"Apple Groceries → TRMNL"** Shortcut. The
first is deterministic and reliable; the second is how it was originally derived.

## 1. Run the build script (recommended, reproducible)

[`scripts/build-shortcut.py`](../scripts/build-shortcut.py) writes the `.shortcut`
plist and signs it with the macOS `shortcuts` CLI. It encodes every action exactly
as the working Shortcut does (the tricky encodings are documented inline in the
script). Run it on a Mac:

```bash
python3 scripts/build-shortcut.py
# -> dist/Apple Groceries to TRMNL.signed.shortcut   (import this)
# -> dist/Apple Groceries to TRMNL.shortcut          (unsigned source)
```

Options: `--out <dir>`, `--no-sign` (skip signing / no `shortcuts` CLI),
`--mode people-who-know-me`.

Then import the signed file, answer the two **Setup** prompts (Webhook URL + list
name), and run it once. See [`apple-shortcut.md`](apple-shortcut.md) for what each
action does.

### Verifying / learning encodings from a real Shortcut

A couple of value encodings cannot be guessed and were lifted from a real Shortcut
exported from the app (**File → Export**). To read any signed `.shortcut` back into
plaintext plist:

```bash
scripts/extract-shortcut.sh "dist/Some Exported.shortcut" out.wflow.xml
```

It pulls the signer's public key out of the archive's certificate chain, `aea
decrypt`s the (signed, unencrypted) body, unpacks the Apple Archive, and converts
the workflow to XML. Handy when Shortcuts changes a format and the script needs a
fix — export a known-good build and diff.

## 2. Build from scratch with an LLM (how it was derived)

If you don't have the script, this prompt rebuilds it. Paste to Claude Code on a Mac
with a shortcuts-generation skill installed. **Heed the encoding notes** — getting
them wrong either crashes the editor on import or silently sends nothing.

> Build a signed `.shortcut` named **"Apple Groceries → TRMNL"** that sends my
> grocery Reminders to a TRMNL webhook:
>
> 1. **Setup questions** (`WFWorkflowImportQuestions`, asked once on import — never
>    hardcode): *"Paste your TRMNL Webhook URL"* → Text → Set Variable `WebhookURL`;
>    *"Which Reminders list holds your groceries?"* → Text → Set Variable `ListName`.
> 2. **Find Reminders** where **List is the `ListName` variable** and **Is Completed
>    is false**, limit 40. Repeat: build `{ "n": Name, "o": Notes, "f": Is Flagged }`
>    → add to `Pending`. (`n`/`o` Text, `f` Boolean.)
> 3. **Find Reminders** where **List is `ListName`** and **Is Completed is true**,
>    limit 12. Repeat: build `{ "n": Name }` → add to `Completed`.
> 4. **Dictionary** `{ pending: Pending, completed: Completed }` with **both values
>    typed Array** → Set Variable `mergeValues`.
> 5. **Get Contents of URL**: POST, JSON, one field `merge_variables` (Text) =
>    `mergeValues`. Body becomes `{ "merge_variables": { "pending": …, "completed": … } }`.
> 6. Optional notification.
>
> Encodings that must be exact:
> - **`merge_variables` wrapper is mandatory** — TRMNL stores nothing without it.
> - Variable in the **List filter**: `WFStringSubstitutableState` → `WFTextTokenString`.
> - **Array** dict value (a list variable): `WFArraySubstitutableParameterState` →
>   `WFTextTokenAttachment` (a plain text token crashes on import).
> - **Boolean** dict value (Is Flagged): `WFNumberSubstitutableState` →
>   `WFTextTokenAttachment` referencing the **Variable** `Repeat Item` with an
>   `Is Flagged` property aggrandizement.
> - Keep `n`/`o`/`f` field names exact and the payload under 2 kB.

## After it generates

1. **Import & test:** run it once and confirm the TRMNL plugin shows the
   Pending/Completed view. Flag a reminder and confirm the ⚑ appears (with **Show
   Flags** on in the plugin).
2. **Get the iCloud link:** Shortcut → Share → **Copy iCloud Link**, then paste that
   `https://www.icloud.com/shortcuts/…` URL into the **Apple Shortcut** field's
   `value` in [`../src/settings.yml`](../src/settings.yml) (replacing
   `REPLACE_AFTER_SHARING`) and the README.

## Reference

- Human walkthrough of the same actions: [`apple-shortcut.md`](apple-shortcut.md)
- Payload contract:
  `{ "merge_variables": { "pending": [ {n,o,f} ], "completed": [ {n} ] } }`,
  under TRMNL's 2 kB webhook limit.
