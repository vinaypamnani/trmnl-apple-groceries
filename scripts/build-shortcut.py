#!/usr/bin/env python3
"""
Build (and sign) the "Apple Groceries → TRMNL" Shortcut, deterministically.

Run on a Mac (needs the `shortcuts` CLI for signing):

    python3 scripts/build-shortcut.py                 # -> dist/Apple Groceries to TRMNL.signed.shortcut
    python3 scripts/build-shortcut.py --out /tmp/x    # custom output dir
    python3 scripts/build-shortcut.py --no-sign       # write unsigned plist only

What it produces (see docs/apple-shortcut.md for the human walkthrough):

  Setup question -> Text -> Set Variable WebhookURL
  Setup question -> Text -> Set Variable ListName
  Find Reminders  (List is {ListName}, Is Completed false, limit 40)
    Repeat: Dictionary { n, o, f } -> add to Pending
  Find Reminders  (List is {ListName}, Is Completed true, limit 12)
    Repeat: Dictionary { n } -> add to Completed
  Dictionary { pending: [Pending], completed: [Completed] }  (values typed Array)
    -> Set Variable mergeValues
  Get Contents of URL  POST {WebhookURL}  JSON  { merge_variables: {mergeValues} }

Every non-obvious encoding below was verified by extracting a known-good shortcut
exported from the Shortcuts app (see scripts/extract-shortcut.sh):
  * variable in a Find Reminders List filter -> WFStringSubstitutableState / WFTextTokenString
  * Array-typed dict value (a list variable)  -> WFArraySubstitutableParameterState / WFTextTokenAttachment
  * Boolean-typed dict value (Is Flagged)     -> WFNumberSubstitutableState / WFTextTokenAttachment (Variable "Repeat Item")
  * TRMNL webhook body must be wrapped in `merge_variables`
"""
import argparse, os, plistlib, subprocess, sys

ORC = "￼"  # U+FFFC object-replacement placeholder
NAME = "Apple Groceries → TRMNL"   # shortcut display name (WFWorkflowName)
FILE_BASE = "Apple Groceries to TRMNL"  # ASCII filename base for the output files
ICON = {"WFWorkflowIconGlyphNumber": 59511, "WFWorkflowIconStartColor": 4282601983}

# ---- token / value helpers --------------------------------------------------
def text_token(s, attachments=None):
    val = {"string": s}
    if attachments:
        val["attachmentsByRange"] = attachments
    return {"WFSerializationType": "WFTextTokenString", "Value": val}

def out_attach(uuid, name, aggr=None):
    d = {"OutputUUID": uuid, "OutputName": name, "Type": "ActionOutput"}
    if aggr:
        d["Aggrandizements"] = aggr
    return d

def single_out(uuid, name, aggr=None):
    return {"WFSerializationType": "WFTextTokenAttachment", "Value": out_attach(uuid, name, aggr)}

def var_attach(name, aggr=None):
    d = {"Type": "Variable", "VariableName": name}
    if aggr:
        d["Aggrandizements"] = aggr
    return d

def var_token(name):                       # "just this variable" inside a Text field
    return text_token(ORC, {"{0, 1}": var_attach(name)})

def array_var(name):                       # Array-typed dict value referencing a list variable
    return {"WFSerializationType": "WFArraySubstitutableParameterState",
            "Value": {"WFSerializationType": "WFTextTokenAttachment", "Value": var_attach(name)}}

def bool_property(prop):                    # Boolean-typed dict value from the Repeat Item's property
    return {"WFSerializationType": "WFNumberSubstitutableState",
            "Value": {"WFSerializationType": "WFTextTokenAttachment",
                      "Value": var_attach("Repeat Item",
                                          [{"PropertyName": prop, "Type": "WFPropertyVariableAggrandizement"}])}}

def dict_field(items):
    return {"WFSerializationType": "WFDictionaryFieldValue",
            "Value": {"WFDictionaryFieldValueItems": items}}

def kv(key, value, item_type=0):
    return {"WFItemType": item_type, "WFKey": text_token(key), "WFValue": value}

def act(identifier, params):
    return {"WFWorkflowActionIdentifier": identifier, "WFWorkflowActionParameters": params}

NOTES = [{"PropertyName": "Notes", "Type": "WFPropertyVariableAggrandizement"}]

# ---- Find Reminders filter (List is {ListName}, Is Completed = bool) ---------
def list_row():
    return {"Property": "List", "Operator": 4, "Removable": True,
            "Values": {"Unit": 4, "Enumeration": {
                "WFSerializationType": "WFStringSubstitutableState",
                "Value": {"WFSerializationType": "WFTextTokenString",
                          "Value": {"string": ORC,
                                    "attachmentsByRange": {"{0, 1}": var_attach("ListName")}}}}}}

def completed_row(value):
    return {"Property": "Is Completed", "Operator": 4, "Removable": True,
            "Values": {"Bool": value, "Unit": 4}}

def content_filter(rows):
    return {"WFSerializationType": "WFContentPredicateTableTemplate",
            "Value": {"WFActionParameterFilterPrefix": 1, "WFContentPredicateBoundedDate": False,
                      "WFActionParameterFilterTemplates": rows}}

# fixed (uppercase) UUIDs
U_URL  = "A1000000-0000-4000-8000-000000000002"
U_LIST = "A1000000-0000-4000-8000-000000000001"
U_FP   = "A1000000-0000-4000-8000-000000000003"
U_RPS  = "A1000000-0000-4000-8000-000000000004"
U_RPE  = "A1000000-0000-4000-8000-000000000005"
G_RP   = "B1000000-0000-4000-8000-000000000004"
U_DP   = "A1000000-0000-4000-8000-000000000006"
U_FC   = "A1000000-0000-4000-8000-000000000008"
U_RCS  = "A1000000-0000-4000-8000-000000000009"
U_RCE  = "A1000000-0000-4000-8000-00000000000A"
G_RC   = "B1000000-0000-4000-8000-000000000009"
U_DC   = "A1000000-0000-4000-8000-00000000000B"
U_MV   = "A1000000-0000-4000-8000-00000000000D"
U_GET  = "A1000000-0000-4000-8000-00000000000C"


def build_actions():
    return [
        # Setup inputs (asked once on import via WFWorkflowImportQuestions)
        act("is.workflow.actions.gettext", {"UUID": U_URL, "WFTextActionText": ""}),
        act("is.workflow.actions.setvariable",
            {"WFVariableName": "WebhookURL", "WFInput": single_out(U_URL, "Text")}),
        act("is.workflow.actions.gettext", {"UUID": U_LIST, "WFTextActionText": ""}),
        act("is.workflow.actions.setvariable",
            {"WFVariableName": "ListName", "WFInput": single_out(U_LIST, "Text")}),
        # Pending: incomplete reminders in the chosen list
        act("is.workflow.actions.filter.reminders",
            {"UUID": U_FP, "WFContentItemFilter": content_filter([list_row(), completed_row(False)]),
             "WFContentItemLimitEnabled": True, "WFContentItemLimitNumber": 40}),
        act("is.workflow.actions.repeat.each",
            {"UUID": U_RPS, "GroupingIdentifier": G_RP, "WFControlFlowMode": 0,
             "WFInput": single_out(U_FP, "Reminders")}),
        act("is.workflow.actions.dictionary",
            {"UUID": U_DP, "WFItems": dict_field([
                kv("n", text_token(ORC, {"{0, 1}": out_attach(U_RPS, "Repeat Item")})),
                kv("o", text_token(ORC, {"{0, 1}": out_attach(U_RPS, "Repeat Item", NOTES)})),
                kv("f", bool_property("Is Flagged"), item_type=4)])}),
        act("is.workflow.actions.appendvariable",
            {"WFVariableName": "Pending", "WFInput": single_out(U_DP, "Dictionary")}),
        act("is.workflow.actions.repeat.each",
            {"UUID": U_RPE, "GroupingIdentifier": G_RP, "WFControlFlowMode": 2}),
        # Completed: recently checked-off reminders in the chosen list
        act("is.workflow.actions.filter.reminders",
            {"UUID": U_FC, "WFContentItemFilter": content_filter([list_row(), completed_row(True)]),
             "WFContentItemLimitEnabled": True, "WFContentItemLimitNumber": 12}),
        act("is.workflow.actions.repeat.each",
            {"UUID": U_RCS, "GroupingIdentifier": G_RC, "WFControlFlowMode": 0,
             "WFInput": single_out(U_FC, "Reminders")}),
        act("is.workflow.actions.dictionary",
            {"UUID": U_DC, "WFItems": dict_field([
                kv("n", text_token(ORC, {"{0, 1}": out_attach(U_RCS, "Repeat Item")}))])}),
        act("is.workflow.actions.appendvariable",
            {"WFVariableName": "Completed", "WFInput": single_out(U_DC, "Dictionary")}),
        act("is.workflow.actions.repeat.each",
            {"UUID": U_RCE, "GroupingIdentifier": G_RC, "WFControlFlowMode": 2}),
        # Payload dictionary (values typed Array) -> mergeValues
        act("is.workflow.actions.dictionary",
            {"UUID": U_MV, "WFItems": dict_field([
                kv("pending", array_var("Pending"), item_type=2),
                kv("completed", array_var("Completed"), item_type=2)])}),
        act("is.workflow.actions.setvariable",
            {"WFVariableName": "mergeValues", "WFInput": single_out(U_MV, "Dictionary")}),
        # POST { "merge_variables": {mergeValues} }
        act("is.workflow.actions.downloadurl",
            {"UUID": U_GET, "WFURL": var_token("WebhookURL"), "WFHTTPMethod": "POST",
             "WFHTTPBodyType": "JSON",
             "WFJSONValues": dict_field([kv("merge_variables", var_token("mergeValues"))])}),
    ]


def build_plist():
    return {
        "WFWorkflowActions": build_actions(),
        "WFWorkflowClientVersion": "2700.0.4",
        "WFWorkflowHasOutputFallback": False,
        "WFWorkflowIcon": ICON,
        # DefaultValue ("Default Answer") is required for the question to show/persist
        # in the app's Setup tab — verified against an imported shortcut that keeps it.
        "WFWorkflowImportQuestions": [
            {"ActionIndex": 0, "Category": "Parameter", "ParameterKey": "WFTextActionText",
             "DefaultValue": "", "Text": "Paste your TRMNL Webhook URL"},
            {"ActionIndex": 2, "Category": "Parameter", "ParameterKey": "WFTextActionText",
             "DefaultValue": "", "Text": "Which Reminders list holds your groceries?"},
        ],
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowName": NAME,
        "WFWorkflowOutputContentItemClasses": [],
        "WFWorkflowTypes": [],
    }


def main():
    ap = argparse.ArgumentParser(description="Build the Apple Groceries -> TRMNL shortcut.")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "dist"),
                    help="output directory (default: repo dist/)")
    ap.add_argument("--no-sign", action="store_true", help="write the unsigned plist only")
    ap.add_argument("--mode", default="anyone", choices=["anyone", "people-who-know-me"])
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    unsigned = os.path.join(out_dir, f"{FILE_BASE}.shortcut")
    signed = os.path.join(out_dir, f"{FILE_BASE}.signed.shortcut")

    with open(unsigned, "wb") as f:
        plistlib.dump(build_plist(), f)
    subprocess.run(["plutil", "-lint", unsigned], check=True, stdout=subprocess.DEVNULL)
    print(f"wrote {unsigned}")

    if args.no_sign:
        return
    if not subprocess.run(["which", "shortcuts"], capture_output=True).returncode == 0:
        sys.exit("`shortcuts` CLI not found — run on macOS, or use --no-sign.")
    subprocess.run(["shortcuts", "sign", "--mode", args.mode,
                    "--input", unsigned, "--output", signed], check=True)
    print(f"signed {signed}")


if __name__ == "__main__":
    main()
