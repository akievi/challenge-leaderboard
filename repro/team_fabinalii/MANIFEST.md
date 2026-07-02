# MANIFEST — team_fabinalii Reproduzierbarkeits-Paket

Snapshot-Datum: **2026-06-27** (UTC). Dieses Dokument hält fest, wo und wie
die `team_fabinalii`-Prognosen auf
https://bartzbeielstein.github.io/challenge-leaderboard/ erzeugt wurden.

## Ausführungs-Architektur (Original-Läufe)

| Item | Wert |
|---|---|
| OS | Windows 11 (10.0.26200) |
| Python | 3.13.1 (gepinnt in `.python-version`) |
| uv | 0.11.18 |
| Determinismus | LightGBM `deterministic=True`, `random_state=2026`, serieller Fit |

Reproduktion auf anderen Architekturen: Die Pipeline läuft auf
Linux/macOS/Windows. LightGBM-Fließkomma-Ergebnisse können sich zwischen
Architekturen minimal unterscheiden; bit-exakte Reproduktion wird für
Windows-x86_64 (Original-Architektur) beansprucht. Auf anderen Plattformen
sind die Werte praktisch gleich, aber evtl. nicht byte-identisch.

## Quell-Provenienz

| Item | Wert |
|---|---|
| Pipeline-Skript | `team_fabinalii_submit.py` — Standalone-Kopie von `lecture/12_challenge.ipynb` (cell-4), Kursrepo `numerische-mathematik-sose-26` |
| Leaderboard-Repo | `bartzbeielstein/challenge-leaderboard` (Fork: `akievi/challenge-leaderboard`) |
| Divergenzen zur Notebook-Version | (D1) CLI-Argumente statt fester Werte; (D2) `--snapshot`-Modus lädt Last+Wetter aus beigelegten Parquets statt live; (D3) Wetter im Snapshot ist **Archiv** (deterministisch), nicht Forecast. Modell/Lags/Hyperparameter identisch. |

## Modell (v2.0)

| Item | Wert |
|---|---|
| Forecaster | `ForecasterRecursive` (spotforecast2-safe) + LightGBM |
| Lags Di–Fr | [1, 2, 3, 24, 168] |
| Lags Mo/Sa/So | [24, 48, 72, 96, 120, 144, 168] (reine Tageslags) |
| Trainingsfenster | 730 Tage (rollend, endet target−1h) |
| Exogene | Kalender (hour/dayofweek/month) + Open-Meteo-Wetter (lat 51.165, lon 10.451) |
| Robustheit (CR-3) | Plausibilitäts-Klammer 20.000–100.000 MW + Lücken-Interpolation |

## Abhängigkeits-Pins

Alle `==`-gepinnt in `pyproject.toml`, vollständig in `requirements.txt`
(pip freeze der Original-Umgebung). Schlüsselpakete:

| Paket | Version |
|---|---|
| spotforecast2-safe | 3.0.0 |
| lightgbm | 4.6.0 |
| pandas | 3.0.2 |
| numpy | 2.2.0 |
| scikit-learn | 1.8.0 |
| entsoe-py | 0.8.0 |
| pyarrow | 24.0.0 |

## Daten-Snapshot (`data/interim/`)

ENTSO-E Transparency Platform (DE-Gebotszone), Snapshot 2026-06-27 (UTC):

| Datei | Inhalt | Abdeckung |
|---|---|---|
| `energy_load_snapshot.parquet` | Actual Total Load, stündlich | 730 Tage bis 2026-06-26 23:00 UTC (17.521 h) |
| `weather_snapshot.parquet` | Open-Meteo-Archiv-Wetter, 15 Variablen, stündlich | gleiches Fenster + Zieltag (17.545 h) |

Attribution: Lastdaten © ENTSO-E Transparency Platform
(https://transparency.entsoe.eu/), unter deren kostenfreien Datennutzungs-
bedingungen zu wissenschaftlichen Reproduktionszwecken. Wetterdaten
© Open-Meteo (https://open-meteo.com/), CC-BY 4.0.

## Integrität

SHA-256-Prüfsummen aller Paket-Dateien: `expected/SHA256SUMS`
(prüfen mit `sha256sum -c expected/SHA256SUMS`).

## Determinismus-Statement

- **Snapshot-Profil** (`--snapshot`, feste Last+Archiv-Wetter, `random_state=2026`,
  `deterministic=True`): **byte-identische** Ausgabe bei Wiederholung (zweimal
  verifiziert am 2026-06-27); Referenz-CSV in `expected/2026-06-27_reference.csv`.
- **Live-Profil** (default, ENTSO-E live + Wetter-**Forecast**): erzeugte die
  eingereichte Leaderboard-Submission. NICHT byte-reproduzierbar, da das
  Wetter-Forecast zeitabhängig aktualisiert wird und ENTSO-E Werte nachträglich
  revidieren kann. Re-Runs liegen nahe an, aber nicht identisch zur
  Live-Submission (dokumentierter, bewusster Unterschied — vgl. Model Card §6).
