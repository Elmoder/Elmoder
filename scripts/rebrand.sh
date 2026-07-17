#!/usr/bin/env bash
# Rebrand the base APK to "ALMODER TV": name, icon, splash logo and theme,
# then rebuild and sign.
#
# Usage:
#   scripts/rebrand.sh <input.apk> [output.apk]
#
# Requirements (see README.md):
#   - java (JDK 17+)
#   - apktool.jar          (APKTOOL env var, or ./tools/apktool.jar)
#   - uber-apk-signer.jar  (SIGNER env var, or ./tools/uber-apk-signer.jar)
#   - python3 with Pillow  (pip install pillow)
set -euo pipefail

INPUT="${1:?usage: rebrand.sh <input.apk> [output.apk]}"
OUTPUT="${2:-ALMODER_TV.apk}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APKTOOL="${APKTOOL:-$ROOT/tools/apktool.jar}"
SIGNER="${SIGNER:-$ROOT/tools/uber-apk-signer.jar}"
LOGO="$ROOT/assets/almoder_tv_logo.png"

WORK="$(mktemp -d)"
PROJECT="$WORK/decoded"

echo ">> Decompiling $INPUT"
java -jar "$APKTOOL" d -f -o "$PROJECT" "$INPUT"

echo ">> Applying ALMODER TV branding"
python3 "$ROOT/scripts/rebrand.py" "$PROJECT" "$LOGO"

echo ">> Rebuilding"
java -jar "$APKTOOL" b "$PROJECT" -o "$WORK/unsigned.apk"

echo ">> Signing"
java -jar "$SIGNER" -a "$WORK/unsigned.apk" -o "$WORK/signed"
cp "$WORK"/signed/*.apk "$OUTPUT"

echo ">> Done: $OUTPUT"
