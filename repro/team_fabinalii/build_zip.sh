#!/usr/bin/env bash
# Baut das verteilbare Reproduzierbarkeits-ZIP (Maintainer-Tool, nicht im ZIP).
#
# Prüft zuerst alle Prüfsummen (Integritäts-Gate), staged dann die Paket-
# Dateien nach dist/<NAME>/ und zippt. Bricht ab, wenn eine Datei driftet.
set -euo pipefail
cd "$(dirname "$0")"

NAME="team_fabinalii-repro-2026-06-27"
STAGE="dist/$NAME"

# 1. Integritäts-Gate.
sha256sum -c expected/SHA256SUMS --quiet \
  || { echo "FEHLER: Prüfsummen-Drift -- Build abgebrochen." >&2; exit 1; }

# 2. Staging.
rm -rf "$STAGE" "dist/$NAME.zip"
mkdir -p "$STAGE/expected" "$STAGE/data/interim"
cp team_fabinalii_submit.py pyproject.toml requirements.txt .python-version \
   LICENSE README.md MANIFEST.md "$STAGE/"
cp expected/2026-06-27_reference.csv expected/SHA256SUMS "$STAGE/expected/"
cp data/interim/energy_load_snapshot.parquet \
   data/interim/weather_snapshot.parquet "$STAGE/data/interim/"

# 3. Zip.
( cd dist && zip -r -X -q "$NAME.zip" "$NAME" )
rm -rf "$STAGE"
ls -lh "dist/$NAME.zip"
