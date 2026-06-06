#!/usr/bin/env bash
# Decrypt a signed (.shortcut, AEA-wrapped) file and dump the workflow plist as XML.
# Usage: scripts/extract-shortcut.sh "path/to/Some.shortcut" [out.wflow.xml]
# Works for "anyone"/"people-who-know-me" signed shortcuts (no password needed):
# the signer's public key is embedded in the archive's certificate chain.
set -euo pipefail

IN="${1:?usage: extract-shortcut.sh <input.shortcut> [output.xml]}"
OUT="${2:-${IN%.shortcut}.wflow.xml}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. Pull the signing cert out of the AEA auth-data segment and export its public key (PEM).
python3 - "$IN" "$TMP/cert0.der" <<'PY'
import plistlib, struct, sys
data = open(sys.argv[1], "rb").read()
assert data[:4] == b"AEA1", "not an AEA1-signed shortcut"
seg_len = struct.unpack_from("<I", data, 8)[0]
chain = plistlib.loads(data[12:12+seg_len])["SigningCertificateChain"]
open(sys.argv[2], "wb").write(chain[0])
PY
openssl x509 -inform DER -in "$TMP/cert0.der" -noout -pubkey > "$TMP/signer.pem"

# 2. Decrypt (verify-only; profile has no encryption) and unpack the Apple Archive.
aea decrypt -i "$IN" -o "$TMP/archive.aa" -sign-pub "$TMP/signer.pem"
aa extract -i "$TMP/archive.aa" -d "$TMP/out"

# 3. Convert the workflow plist to readable XML.
WFLOW="$(find "$TMP/out" -name '*.wflow' | head -1)"
plutil -convert xml1 -o "$OUT" "$WFLOW"
echo "wrote $OUT"
