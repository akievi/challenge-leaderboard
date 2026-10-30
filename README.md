# Team Fabinalii: day-ahead load forecast for Germany

This is a fork of [bartzbeielstein/challenge-leaderboard](https://github.com/bartzbeielstein/challenge-leaderboard), the scoring system of a live forecasting challenge in the course *Sicherheitskritische Zeitreihenprognose mit spotforecast2-safe* (Numerische Mathematik / DDMO, summer term 2026, TH Köln, Prof. Bartz-Beielstein). The fork holds the entry of **Team Fabinalii**: [@akievi](https://github.com/akievi), [@ffeith-thk](https://github.com/ffeith-thk) and [@VitaliiZakharuk](https://github.com/VitaliiZakharuk).

The scoring code, the workflows and all other teams' submissions come from the upstream repository. The original README is kept unchanged [further down](#original-readme-of-the-upstream-repository). Everything specific to our team lives in two folders:

| Path | Content |
|---|---|
| [`submissions/team_fabinalii/`](submissions/team_fabinalii) | the daily forecasts, the [model card](submissions/team_fabinalii/MODEL_CARD.md), the [development log](submissions/team_fabinalii/DEVLOG.md) and the license (MIT) |
| [`repro/team_fabinalii/`](repro/team_fabinalii) | a self-contained package that reruns one forecast offline and compares it with a stored reference |

## The task

Every day, each team submits a forecast of the German hourly electricity load for the next day: 24 values in MW, one CSV per target day, handed in as a pull request before the deadline. The next day the forecast is scored against the actual load published by the ENTSO-E Transparency Platform. The ranking uses the mean absolute error (MAE) over all scored days. The official ENTSO-E day-ahead forecast and two seasonal-naive baselines run alongside as reference entries.

## Our model

- **Forecaster:** a recursive multi-step forecaster from [`spotforecast2-safe`](https://github.com/sequential-parameter-optimization/spotforecast2-safe) around a LightGBM regressor (400 trees, learning rate 0.05, 63 leaves, fixed seed, deterministic mode).
- **Lags depend on the weekday of the target day.** Tuesday to Friday use the lags 1, 2, 3, 24 and 168 hours. Monday, Saturday and Sunday use only whole days (24, 48, ... 168 hours).
- **Training data:** the last 730 days of ENTSO-E load, refit for every submission, ending just before the target day so that nothing leaks.
- **Features:** hour, day of week and month, plus weather from Open-Meteo (the weather forecast for submissions).
- **Guard against bad data:** load values outside 20,000 to 100,000 MW are dropped and interpolated. This caught an ENTSO-E glitch of 1,124,884 MW.

## What we learned

The first version used the same lags on every day. On Saturday 20 June 2026 it was 7,371 MW off. The cause: for a Saturday, the 24-hour lag points to a Friday, and a Saturday's daily load is about 14 % lower than a Friday's. The recursive forecast carried the Friday shape into the weekend.

Weekday dummies changed nothing, because the model already had the day of week. An extra 336-hour lag made the mean error worse. What worked was the weekday-dependent lag set together with the longer training window. In a backtest over 13 to 25 months with archived weather, the mean MAE went from about 2,050 MW to about 1,720 MW with the new lags and to about 1,465 MW with the 730-day window. Backtest values compare the variants with each other. They are lower than the live scores because the live runs use a weather forecast. The full reasoning, including the failed attempts, is in the [development log](submissions/team_fabinalii/DEVLOG.md).

## Result

Scored on 47 days from 4 June to 20 July 2026 (one of them carried forward from the previous submission), based on the public leaderboard data:

| | Mean MAE |
|---|---|
| Team Fabinalii | 1,748 MW |
| ENTSO-E day-ahead forecast, same 47 days | 2,153 MW |
| Seasonal naive, 168 h, same 47 days | 2,445 MW |
| Seasonal naive, 24 h, same 47 days | 4,067 MW |

We beat the ENTSO-E forecast on 31 of the 47 days. The leaderboard data contains 25 entries, including the lecturer's reference models and the baselines. Team Fabinalii is 9th of them. In the last weeks, with the final model, we were in the middle of the field of student teams, behind the best teams. Our entry is not independently certified; the reproduction package is there so that someone can check it.

## Reproduce a forecast

```bash
cd repro/team_fabinalii
uv sync
uv run python team_fabinalii_submit.py --snapshot --target-date 2026-06-27 --out out.csv
diff out.csv expected/2026-06-27_reference.csv
```

This runs offline from a frozen snapshot of load and weather. Byte-identical output is only claimed for Windows on x86-64, the machine of the original runs. The [package README](repro/team_fabinalii/README.md) explains the live mode and the details.

---

## Original README of the upstream repository

# challenge-leaderboard

Automatisierte Bewertung der Live-Lastprognose-Challenge der Vorlesungen
*Sicherheitskritische Zeitreihenprognose mit spotforecast2-safe*
(Numerische Mathematik / DDMO, SoSe 2026, TH Köln, Bartz-Beielstein).

Webseite Leaderboard: https://bartzbeielstein.github.io/challenge-leaderboard/

Webseite ENTSO-E: https://transparency.entsoe.eu

Die Spielregeln stehen in Kapitel 12 des Skripts (`lecture/12_challenge.qmd`).
Dieses Repo ist die
*Bewertungs-Infrastruktur*: hier reichen Teams ihre täglichen
Vorhersagen ein, hier läuft das Scoring, hier wird das Leaderboard
gebaut und auf GitHub Pages publiziert.

## Setup für Teams (einmalig)

1. Forken Sie dieses Repo.
2. Lokal clonen, `pyproject.toml` per `uv sync` installieren.
3. Submission lokal erzeugen (siehe `make_submission.py` in Kapitel 12).
4. Für jede Submission: Feature-Branch → `submissions/<team_id>/<D>.csv`
   commiten → PR gegen `main` → automatischer Merge bei grünem Check.


### Sicherheitsmodell der PR-Pipeline

`validate-pr.yml` läuft unter `pull_request` und führt damit (bei
Fork-PRs) ungeprüften Team-Code aus — deshalb bekommt es **bewusst keine
Secrets** und kein Schreib-Token. Das Mergen erledigt das separate
`auto-merge.yml` per `workflow_run` im vertrauenswürdigen Basis-Repo-Kontext
(ohne PR-Code auszuführen) mit einem kurzlebigen **GitHub-App-Token**, und
nur für grün validierte PRs mit genau einer `submissions/**`-Datei. Setup:
siehe `DEPLOYMENT.md` Abschnitt 4a.

## Tageslauf-Timing & Robustheit

Der Score-Cron läuft *täglich* und bewertet „gestern" (UTC).
ENTSO-E veröffentlicht *Actual Total Load* (6.1.A) regulatorisch bis H+1,
real treten jedoch TSO-Verzögerungen, einzelne fehlende Stunden (DST) und
„HTTP 200 + No matching data" auf. 09:00 UTC gibt Sicherheitsmarge nach der
H+1-Frist der letzten UTC-Stunde (01:00 UTC). Ergänzend härtet
`score_day.py` den Abruf:

- **Retry/Backoff** bei transienten API-/Netzfehlern.
- **Sauberes Aufschieben** (`GroundTruthNotReady`) bei unvollständigem Tag —
  lieber morgen via **Catch-up** nachholen als raten (CR-3).
- **Lauter Fehlschlag**: kann der *primäre* Zieltag nicht gescort werden,
  endet der Lauf rot (Alarm); Nebentage werden still nachgeholt.

## `teams.yml`-Schema

```yaml
teams:
  - id: team_lambda                   # filename-safe, lowercase
    display_name: "Team Lambda"
    github_handles:
      - alice42
      - bob99
      - carol7
```

Nur Personen aus `github_handles` dürfen PRs für dieses Team mergen
(via `validate-pr.yml`-Check).

## Score-Logik

- *Primär*: MAE [MW] über die 24 Stunden eines Zieltages.
- *Aggregat (öffentliches Ranking)*: mittlere MAE = Summe der
  Tages-MAEs / Anzahl bewerteter Tage (aufsteigend).
- *LOCF*: Reicht ein Team an einem Zieltag keine Prognose ein, wird
  die jeweils letzte vorhandene Submission des Teams fortgeschrieben
  (last observation carried forward) und zählt als bewerteter Tag.
- *Tie-Break*: Anzahl bewerteter Tage (absteigend).
- *Sekundärmetriken (Anzeige, kein Ranking)*: mittlere RMSE, mittlere
  MAPE (De-facto-Referenzmetrik der Lastprognose-Praxis, vgl. Hong,
  Pinson & Fan 2016, IJF), **Mean Bias** = Ø(Prognose − Ist) (signiert;
  negativ = systematische Unterprognose) und **UPR** (Under-Prediction
  Rate) = Anteil der Stunden mit Prognose < Ist. Bias/UPR machen die im
  Netzbetrieb teurere Unterprognose-Richtung sichtbar, die
  vorzeichenblinde Metriken verbergen — die offiziellen
  ENTSO-E-Day-ahead-Lastprognosen sind nachweislich systematisch
  verzerrt: Möbius, Watermeyer, Grothe & Müsgens (2023), *Enhancing
  Energy System Models Using Better Load Forecasts*,
  [arXiv:2302.11017](https://arxiv.org/abs/2302.11017).

### Joker-Regel

Jedes Team darf während der gesamten Challenge **genau einen Joker**
einsetzen: EIN bereits bewerteter Zieltag wird durch eine
aktualisierte Prognose korrigiert; der Tag wird anschließend gegen die
committeten Ist-Werte (`data/actual_load.parquet`) neu bewertet — kein
frischer ENTSO-E-Abruf, keine Änderung an anderen Tagen oder Teams.

- *Buchführung* in `teams.yml`, Schlüssel `joker`: fehlt oder `false`
  = Joker verfügbar; nach Einsatz das ISO-Datum des ersetzten
  Zieltages (z. B. `joker: "2026-06-22"`). Der Joker gilt je
  Registry-Eintrag; der `_entsoe`-Geschwister-Eintrag behält seinen
  eigenen.
- Der Joker gilt für jeden **bereits bewerteten** Zieltag — auch für
  einen per LOCF bewerteten Tag ohne eigene Submission; die Datei
  `submissions/<team>/<datum>.csv` wird dann neu angelegt (einzige
  Ausnahme vom Deadline-Regime). Nicht bewertete Tage qualifizieren
  nicht. Die Ersatz-CSV muss dieselben Schema-Checks bestehen wie eine
  reguläre Submission.
- *Anwendung durch die Lehrenden* (nach Eingang der Joker-Mail):
  Ersatzdatei unter `joker/<team>/<datum>.csv` ablegen, dann
  `uv run python scripts/apply_joker.py --team <id> --date <datum>`
  und anschließend `scripts/build_leaderboard.py`. Das Skript setzt
  den `joker`-Schlüssel selbst und bewertet chirurgisch nur diesen
  einen (team, tag)-Score neu. Ein Joker-PR scheitert absichtlich am
  Deadline-Gate (`validate-pr.yml`) und wird admin-gemerged — das Gate
  selbst bleibt unangetastet.
- Exit-Code-Erweiterung: `4` = Joker-Regel verletzt (bereits
  eingesetzt, Zieltag nicht bewertet), `5` = committete Ist-Werte des
  Tages unvollständig.

### Pseudo-Team ENTSO-E

Die offizielle ENTSO-E-Day-ahead-Prognose nimmt als **Pseudo-Team**
`entsoe` (teams.yml: `pseudo: true`) am Ranking teil — in allen Tabellen
und Figuren. Seine Scores werden **nicht** über `submissions/`-CSVs
eingereicht, sondern zur Build-Zeit direkt aus den committeten
ENTSO-E-Daten abgeleitet (`data/actual_load.parquet`, Spalte
`entsoe_forecast_mw` → `entsoe_pseudo_scores()` in
`scripts/build_leaderboard.py`). Bewertet wird exakt der Zeitraum der
regulären Teams (erster bis letzter gescorter Zieltag, synchron); CSV-
Submissions für Pseudo-Teams lehnt `validate_submission.py` ab, und
`score_day.py` schließt sie vom täglichen Scoring aus.

Details und die Formeln in `lecture/12_challenge.qmd` (§
"Bewertungsmethodik im Detail").

## Visualisierung des Leaderboards

Zusätzlich zu den Tabellen rendert `scripts/build_leaderboard.py`
interaktive Plotly-Diagramme auf der GitHub-Pages-Seite (Figuren in
`scripts/charts.py`):

- **Prognose vs. Ist-Last** — pro Zieltag (Kalender rechts neben dem
  Plot) die 24-h-Prognose jedes Teams gegen die gemessene DE-Netzlast
  (ENTSO-E *Actual Total Load*), MAE je Team in der Legende.
- **Mittlere MAE je Team** — horizontales Balkendiagramm (grün = gut → rot).
- **Mittlerer RMSE / MAPE / Bias / UPR je Team** — analoge Balkendiagramme
  für jede Leaderboard-Spalte, je mit Erklärung. RMSE/MAPE: kleiner =
  besser; Bias (signiert) und UPR sortieren nach Distanz zum Idealwert
  (0 MW bzw. 50 %, gepunktete Referenzlinie). Anzeige-Metriken — das
  Ranking bleibt bei der MAE.
- **MAE-Verlauf** — Tages-MAE je Team über die Zeit; offene Marker
  kennzeichnen via LOCF fortgeschriebene Tage.
- **Tagesfehler je Team [MAE] / [RMSE] / [MAPE] / [Bias] / [UPR]** —
  Tabellen mit Tageswerten, Wochen-Umschalter (Default: jüngste Woche)
  und deutschen Datums-Headern („Di, 26.5.26"); fett = Tagesbester
  (Spaltenminimum bzw. am nächsten an 0/50 % für Bias/UPR).

Plotly.js ist einmalig in `index.html` eingebettet (self-contained,
offline-fähig, via `uv.lock` gepinnt; deterministische `div_id`s → CR-2).
Der Build läuft auf GitHub **ohne** API-Key und liest ausschließlich
committete Dateien.

### Ist-Last-Daten aktualisieren

Das Prognose-vs-Ist-Last-Diagramm (und das Pseudo-Team `entsoe`) braucht
die gemessene Netzlast samt Day-ahead-Prognose als committete Zeitreihe
(`data/actual_load.parquet`). Seit 2026-06-04 hält der tägliche
`Daily Scoring`-Workflow diese Datei **automatisch** aktuell
(`scripts/fetch_actuals.py` läuft nach dem Scoring mit dem
`ENTSOE_API_KEY`-Secret und committet das Ergebnis im selben Score-PR).

Ein lokaler Lauf ist nur noch als **Fallback/Backfill** nötig
(`ENTSOE_API_KEY` in der Umgebung):

```bash
uv run python scripts/fetch_actuals.py                  # alle relevanten Tage (Default)
uv run python scripts/fetch_actuals.py --from 2026-05-26 --to 2026-06-01
uv run python scripts/fetch_actuals.py --force          # bereits vollständige Tage neu laden
```

Anschließend `data/actual_load.parquet` per PR nach `main` bringen
(Admin-Merge — der PR berührt keine `submissions/**`-Datei, wird also von
`validate-pr.yml` pass-through abgenickt, aber bewusst **nicht**
auto-gemerged). Details: DEPLOYMENT.md, Abschnitt „Laufender Betrieb".

Das Skript nutzt dieselbe Download-Logik wie das Scoring
(`score_day.fetch_ground_truth`): **Retry/Backoff** bei transienten
Fehlern, **sauberes Aufschieben** noch unveröffentlichter Tage und
**Überspringen** bereits vollständig geladener Tage. Fehlt die Datei,
blendet der Build das Prognose-vs-Ist-Last-Diagramm sauber aus — die
übrigen Charts und Tabellen bleiben erhalten.

## Reproduzierbarkeit (CR-2)

Der Scoring-Workflow pinnt:

- Python-Version + Abhängigkeiten via `uv.lock` (commitet im Repo).
- `PYTHONHASHSEED=0`.
- ENTSO-E-Antwort als Snapshot im selben Commit wie das Score-Ergebnis.

Damit ist jeder Score-Stand bitweise nachvollziehbar — das ist
Art. 12 KI-VO (Aufzeichnung) plus CR-2 (Determinismus).
