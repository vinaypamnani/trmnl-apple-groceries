#!/usr/bin/env python3
"""
Build (and sign) a throwaway "Populate Groceries Test Data" Shortcut.

Adds a batch of sample grocery reminders to an Apple Reminders list so you can
screenshot the TRMNL plugin with a realistic list. The list name is asked once
on import (Setup question -> a ListName variable), so it isn't hardcoded into
every action.

    python3 scripts/build-test-data-shortcut.py            # -> dist/...signed.shortcut
    python3 scripts/build-test-data-shortcut.py --no-sign  # unsigned plist only

Each item becomes an `is.workflow.actions.addnewreminder` action whose
WFCalendarItemList references the ListName variable. Items are all incomplete
("to buy"); to show the Completed column, swipe a few complete in Reminders
before screenshotting.
"""
import argparse, os, plistlib, subprocess, sys, uuid

NAME = "Populate Groceries Test Data"
FILE_BASE = "Populate Groceries Test Data"
ICON = {"WFWorkflowIconGlyphNumber": 59511, "WFWorkflowIconStartColor": 4282601983}

# (title, note) — note "" means no note
ITEMS = [
    ("Bananas", ""),
    ("Whole milk", "2% if no whole"),
    ("Chicken thighs", "boneless, skinless"),
    ("Sourdough loaf", ""),
    ("Baby spinach", ""),
    ("Greek yogurt", "plain, full fat"),
    ("Olive oil", "extra virgin"),
    ("Cheddar cheese", "sharp"),
    ("Coffee beans", ""),
    ("Roma tomatoes", ""),
    ("Yellow onions", ""),
    ("Garlic", ""),
    ("Basmati rice", ""),
    ("Eggs", "dozen"),
    ("Avocados", ""),
    ("Honeycrisp apples", ""),
    ("Peanut butter", ""),
    ("Paper towels", ""),
]

U_LIST = "A2000000-0000-4000-8000-000000000001"  # the Text action that holds the list name


def out_attach(out_uuid, name):
    return {"OutputUUID": out_uuid, "OutputName": name, "Type": "ActionOutput"}

def single_out(out_uuid, name):
    return {"WFSerializationType": "WFTextTokenAttachment", "Value": out_attach(out_uuid, name)}

def var_attachment(var_name):  # a parameter that is "just this variable"
    return {"WFSerializationType": "WFTextTokenAttachment",
            "Value": {"Type": "Variable", "VariableName": var_name}}

def act(identifier, params):
    return {"WFWorkflowActionIdentifier": identifier, "WFWorkflowActionParameters": params}


def add_reminder(title, note):
    # The target list is `WFCalendarDescriptor` (NOT WFCalendarItemList) and takes a
    # token attachment — verified by extracting a known-good shortcut (extract-shortcut.sh).
    params = {"UUID": str(uuid.uuid4()).upper(),
              "WFCalendarItemTitle": title,
              "WFCalendarDescriptor": var_attachment("ListName")}
    if note:
        params["WFCalendarItemNotes"] = note
    return act("is.workflow.actions.addnewreminder", params)


def build_actions():
    actions = [
        # Setup input (asked once on import via WFWorkflowImportQuestions)
        act("is.workflow.actions.gettext", {"UUID": U_LIST, "WFTextActionText": ""}),
        act("is.workflow.actions.setvariable",
            {"WFVariableName": "ListName", "WFInput": single_out(U_LIST, "Text")}),
    ]
    actions += [add_reminder(t, n) for t, n in ITEMS]
    return actions


def build_plist():
    return {
        "WFWorkflowActions": build_actions(),
        "WFWorkflowClientVersion": "2700.0.4",
        "WFWorkflowHasOutputFallback": False,
        "WFWorkflowIcon": ICON,
        # DefaultValue is required for the question to show/persist in the Setup tab.
        "WFWorkflowImportQuestions": [
            {"ActionIndex": 0, "Category": "Parameter", "ParameterKey": "WFTextActionText",
             "DefaultValue": "Groceries", "Text": "Which Reminders list should I fill with test data?"},
        ],
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowName": NAME,
        "WFWorkflowOutputContentItemClasses": [],
        "WFWorkflowTypes": [],
    }


def main():
    ap = argparse.ArgumentParser(description="Build the Groceries test-data shortcut.")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "dist"))
    ap.add_argument("--no-sign", action="store_true")
    ap.add_argument("--mode", default="anyone", choices=["anyone", "people-who-know-me"])
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    unsigned = os.path.join(out_dir, f"{FILE_BASE}.shortcut")
    signed = os.path.join(out_dir, f"{FILE_BASE}.signed.shortcut")

    with open(unsigned, "wb") as f:
        plistlib.dump(build_plist(), f)
    subprocess.run(["plutil", "-lint", unsigned], check=True, stdout=subprocess.DEVNULL)
    print(f"wrote {unsigned}  ({len(ITEMS)} reminders -> list from the ListName setup question)")

    if args.no_sign:
        return
    if subprocess.run(["which", "shortcuts"], capture_output=True).returncode != 0:
        sys.exit("`shortcuts` CLI not found — run on macOS, or use --no-sign.")
    subprocess.run(["shortcuts", "sign", "--mode", args.mode,
                    "--input", unsigned, "--output", signed], check=True)
    print(f"signed {signed}")


if __name__ == "__main__":
    main()
