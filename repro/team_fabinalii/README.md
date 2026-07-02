# team_fabinalii Reproduzierbarkeits-Paket — Lastprognose-Challenge SoSe26

Re-Run der 24h-DE-Lastprognose-Pipeline hinter den `team_fabinalii`-Einträgen
auf dem [Leaderboard](https://bartzbeielstein.github.io/challenge-leaderboard/):
ENTSO-E-Last → Plausibilitäts-Klammer + Lücken-Interpolation → Hybrid-Lags
(wochentag-abhängig) → LightGBM (rekursive 24h-Prognose) → Submission-CSV.

## Quickstart (offline-Reproduktion des 2026-06-27-Forecasts)

```sh
# Voraussetzung: uv (https://docs.astral.sh/uv/)
unzip team_fabinalii-repro-2026-06-27.zip && cd team_fabinalii-repro-2026-06-27
uv sync                                    # installiert die gepinnte Umgebung
uv run python team_fabinalii_submit.py --snapshot --target-date 2026-06-27 --out out.csv
sha256sum -c expected/SHA256SUMS           # prüft u.a. out gegen die Referenz
diff out.csv expected/2026-06-27_reference.csv   # muss identisch sein
```

Die Referenz `expected/2026-06-27_reference.csv` wurde am 2026-06-27 durch
**zwei** unabhängige Läufe byte-identisch bestätigt. Der Lauf braucht **keinen**
API-Key und **kein** Netzwerk (außer `uv sync`) — Last und Wetter liegen als
Snapshot in `data/interim/` bei.

## Was "reproduzieren" hier heißt — zwei Profile

| Profil | Kommando | Garantie |
|---|---|---|
| **Snapshot** (Standard oben) | `--snapshot` | byte-identisch zu `expected/2026-06-27_reference.csv` (Last + Archiv-Wetter eingefroren) |
| **Live** | (ohne `--snapshot`, braucht `ENTSOE_API_KEY`) | die Einstellungen, die die Leaderboard-Submission erzeugten; **nicht** byte-reproduzierbar (Wetter-Forecast zeitabhängig, ENTSO-E-Revisionen) |

Die eingereichte Leaderboard-Prognose entstand mit dem Live-Profil; das
Snapshot-Profil existiert, damit etwas exakt Prüfbares vorliegt (Modell-Logik
ist identisch, nur die Wetter-Quelle unterscheidet sich — Archiv statt Forecast).

## Live-Lauf (beliebiger künftiger Zieltag)

```sh
export ENTSOE_API_KEY=...
uv run python team_fabinalii_submit.py --target-date 2026-07-05 --out out.csv
uv run python team_fabinalii_submit.py --help
```

## Modell in Kürze

- **Hybrid-Lags:** Mo/Sa/So → reine Tageslags `[24,48,…,168]`, Di–Fr →
  Basis-Lags `[1,2,3,24,168]`. Grund: an wochenend-nahen Tagen schleppen kurze
  Lags das falsche Vortagsprofil rekursiv ein.
- **Trainingsfenster:** 730 Tage (2 Saison-Zyklen, datengestützt optimiert).
- **CR-3-Robustheit:** implausible Lastwerte (außerhalb 20.000–100.000 MW)
  werden verworfen und interpoliert — fängt ENTSO-E-Glitches ab.

Details, Herleitung und Validierung: siehe `MANIFEST.md` und die Model Card.

## Paket-Inhalt

| Pfad | Zweck |
|---|---|
| `team_fabinalii_submit.py` | die Pipeline (Standalone-CLI) |
| `pyproject.toml`, `requirements.txt`, `.python-version` | ==-gepinnte Umgebung (Python 3.13.1) |
| `data/interim/*.parquet` | eingefrorener Last- + Wetter-Snapshot (offline-fähig) |
| `expected/` | Referenz-CSV + `SHA256SUMS` |
| `MANIFEST.md` | Architektur, Provenienz, Pins, Determinismus-Statement |

Integritäts-Check: `sha256sum -c expected/SHA256SUMS`

## Troubleshooting

- **ENTSO-E-Fehler (nur Live-Läufe):** API-Key/Quote prüfen; für reine
  Reproduktion `--snapshot` nutzen (kein Netz nötig).
- **Abweichende Werte auf Linux/macOS:** möglich — Bit-Exaktheit nur für
  Windows-x86_64 beansprucht (siehe MANIFEST.md).
- **`[CR-3] … implausible Lastwert(e) verworfen`:** erwartet — der Klammer-
  Schutz meldet und ersetzt Datenglitches (z.B. 1.124.884 MW am 2026-06-25).
