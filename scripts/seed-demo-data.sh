#!/usr/bin/env bash
#
# Seed the Recipe Master's preview with clean demo data, so the public preview
# image shows a sample grocery list (NOT your real one). There is no "demo data"
# field for webhook plugins — you POST fake data to the master's webhook URL and
# force-refresh.
#
# Usage:
#   scripts/seed-demo-data.sh <MASTER_WEBHOOK_URL>
#   WEBHOOK_URL=https://... scripts/seed-demo-data.sh
#
# The master's webhook URL is in its "Webhook URL" settings field. After running
# this, FORCE-REFRESH the plugin (TRMNL portal, or on a paired device) so the
# preview re-renders. Set the master's List Source to "Apple Shortcut" first, so
# this Shortcut-shaped payload matches and you get the Pending + Completed view
# with no "(fallback)" footnote.
#
set -euo pipefail

URL="${1:-${WEBHOOK_URL:-}}"
if [ -z "$URL" ]; then
  echo "usage: scripts/seed-demo-data.sh <MASTER_WEBHOOK_URL>   (or set WEBHOOK_URL)" >&2
  exit 1
fi

# ~25 to-buy + 6 completed, item keys t=title n=note (matches the Shortcut payload).
read -r -d '' PAYLOAD <<'JSON' || true
{"merge_variables":{
  "reminders":[
    {"t":"Bananas"},
    {"t":"Whole milk","n":"2% if no whole"},
    {"t":"Sourdough loaf"},
    {"t":"Baby spinach"},
    {"t":"Greek yogurt","n":"plain, full fat"},
    {"t":"Olive oil","n":"extra virgin"},
    {"t":"Cheddar cheese","n":"sharp"},
    {"t":"Coffee beans"},
    {"t":"Roma tomatoes"},
    {"t":"Yellow onions"},
    {"t":"Garlic"},
    {"t":"Eggs","n":"dozen"},
    {"t":"Avocados"},
    {"t":"Honeycrisp apples"},
    {"t":"Chicken thighs","n":"boneless, skinless"},
    {"t":"Basmati rice"},
    {"t":"Black beans","n":"2 cans"},
    {"t":"Penne pasta"},
    {"t":"Marinara sauce"},
    {"t":"Parmesan"},
    {"t":"Butter","n":"unsalted"},
    {"t":"Lemons"},
    {"t":"Carrots"},
    {"t":"Bell peppers"},
    {"t":"Ground beef","n":"1 lb"}
  ],
  "completed":[
    {"t":"Paper towels"},
    {"t":"Orange juice"},
    {"t":"Bagels"},
    {"t":"Cream cheese"},
    {"t":"Sparkling water"},
    {"t":"Dish soap"}
  ]
}}
JSON

echo "POSTing demo data (${#PAYLOAD} bytes) to the master webhook..."
curl -fsS -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"
echo
echo "Done. Now FORCE-REFRESH the plugin so the preview re-renders."
