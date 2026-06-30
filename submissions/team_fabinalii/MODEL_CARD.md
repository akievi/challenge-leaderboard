# Model Card — Team Fabinalii: 24h-DE-Lastprognose

## 1. Model Details

| Feld | Wert |
|---|---|
| Name | Team Fabinalii — 24h DE Load Forecaster |
| Version | 2.0 (Hybrid-Lags + 2-Jahres-Fenster, Stand 2026-06-27) |
| Typ | Rekursive Multi-Step-Zeitreihenprognose (Gradient Boosting), wochentag-abhängiges Lag-Set |
| Entwickelt von | Team Fabinalii (team_fabinalii) |
| Aufgebaut auf | [`spotforecast2-safe`](https://github.com/sequential-parameter-optimization/spotforecast2-safe) v3.0.0 |
| Sprache | Python 3.13 |
| Lizenz | MIT |
| Repository | https://github.com/bartzbeielstein/challenge-leaderboard (Submissions unter `submissions/team_fabinalii/`) |
| Technischer Bericht | Dieses Dokument + [DEVLOG.md](../../DEVLOG.md) |

**Abhängigkeiten (Kern):**

- `spotforecast2-safe` 3.0.0 — `ForecasterRecursive`, `ExogBuilder`,
  `LinearlyInterpolateTS`, `WeatherService`, ENTSO-E-Downloader
- `lightgbm` 4.6.0 — Gradient-Boosting-Regressor
- `pandas` 3.0.2, `numpy` 2.2.0 — Datenverarbeitung

**Verantwortlichkeiten:**

| Verantwortung | Partei | Kontakt |
|---|---|---|
| Modell-Design & Training | Team Fabinalii | inalbek.akiev@smail.th-koeln.de, fabian.feith@smail.th-koeln.de, vitalii.zakharuk@smail.th-koeln.de |
| Datenquelle Last | ENTSO-E Transparency Platform | api.entsoe.eu |
| Datenquelle Wetter | Open-Meteo (via `WeatherService`) | open-meteo.com |
| Bibliothek | sequential-parameter-optimization | github.com/sequential-parameter-optimization |

---

## 2. Intended Use and Scope

**Zielanwendung:** 24-Stunden-Day-Ahead-Prognose der deutschen
Stundenlast (`Actual Load`, MW) für die Lastprognose-Challenge. Es wird
genau eine Prognose pro Zieltag *D* erzeugt, abgegeben am Vortag *D-1*.

**Integration:** Aufruf über `make_submission(team, target_date, repo_root)`;
erzeugt eine spielregelkonforme CSV (24 Zeilen, `timestamp_utc`,
`forecast_mw`) im Leaderboard-Repo.

**Grenzen und Ausschlüsse:**

- Nur deutsche Regelzone (DE/`DE_LU`); nicht auf andere Länder validiert.
- Horizont fest 24 h; kein Multi-Day-Forecast.
- Keine Unsicherheits-/Intervallprognose, nur Punktprognose.
- Nicht für sicherheitskritische Echtzeit-Netzsteuerung gedacht.
- Verlässt sich auf rechtzeitige ENTSO-E-Veröffentlichung; bei großen
  Datenlücken degradiert die Genauigkeit.

---

## 3. How to Get Started

Installation (Kursumgebung):

```sh
uv sync          # installiert spotforecast2-safe>=3,<4 + Abhängigkeiten
export ENTSOE_API_KEY=...   # ENTSO-E-Schlüssel erforderlich
```

Aufruf (aus dem Notebook `lecture/12_challenge.ipynb`, cell-4):

```python
path = make_submission(
    team="team_fabinalii",
    target_date="2026-06-10",
    repo_root=Path(r"...\challenge-leaderboard"),
)
```

Rückwärtige Bewertung gegen Ground Truth:

```python
scores = evaluate("2026-06-07")                 # Re-Run nach Datum
scores = evaluate(log_path=".../2026-06-07.log.json")  # exakte Reproduktion
```

---

## 4. Technical Specification

### Task and model family

Rekursive Multi-Step-Prognose mit einem `ForecasterRecursive`
(spotforecast2-safe), der einen LightGBM-Regressor kapselt. Die Vorhersage
für Schritt *h+1* wird als Lag-Input für Schritt *h+2* zurückgespeist, bis
der 24-h-Horizont des Zieltags abgedeckt ist.

### Mathematical description

Die Zielgröße ist die Stundenlast $y_t$. Das Modell schätzt rekursiv
$\hat{y}_{t+1} = f(\text{Lags},\ \mathbf{x}_{t+1})$ mit exogenen Features
$\mathbf{x}$ (Kalender + Wetter). **Das Lag-Set hängt vom Wochentag des
Zieltags ab** (Hybrid, datengestützt über 13–25 Monate backgetestet):

- **Di–Fr:** $\{1, 2, 3, 24, 168\}$ — kurze Lags + Tages-/Wochenlag.
- **Mo / Sa / So:** $\{24, 48, 72, 96, 120, 144, 168\}$ — reine Tageslags
  (Vielfache von 24).

**Begründung:** An wochenend-nahen Tagen (Mo/Sa/So) zeigt der Lag-24 auf
einen Tag mit *abweichendem* Lastprofil (Sa→Fr, So→Sa, Mo→So). Die kurzen
Lags $\{1,2,3\}$ schleppen dann rekursiv das falsche Profil-Momentum ein
(z.B. die steile Werktags-Morgenrampe in einen Samstag). Reine Tageslags
referenzieren stets dieselbe Stunde an Vortagen und vermeiden das.

### Architecture

- **Daten:** ENTSO-E `Actual Load` (DE), **730-Tage-Trainingsfenster**
  (2 volle Saison-Zyklen), stündlich resampled. Lücken über
  `LinearlyInterpolateTS(on_missing="raise")` geschlossen; zusätzlich
  **Plausibilitäts-Klammer** (CR-3): Lastwerte außerhalb 20.000–100.000 MW
  werden als fehlend markiert und interpoliert (fängt ENTSO-E-Glitches
  wie 1.124.884 MW ab, die `on_missing` nicht erkennt).
- **Exogene:** `ExogBuilder` erzeugt Perioden-Features (hour, dayofweek,
  month) + `WeatherService` (Open-Meteo, lat 51.165, lon 10.451).
- **Regressor:** LightGBM, deterministisch konfiguriert.

### Training

Modell wird pro Submission **frisch** auf den letzten 730 Tagen trainiert
(rollendes Fenster, endet bei `target − 1 h`, kein Leakage des Zieltags).
Das Lag-Set wird per `_select_lags(target)` nach Wochentag gewählt.

| Hyperparameter | Wert |
|---|---|
| `n_estimators` | 400 |
| `learning_rate` | 0.05 |
| `num_leaves` | 63 |
| `lags` (Di–Fr) | [1, 2, 3, 24, 168] |
| `lags` (Mo/Sa/So) | [24, 48, 72, 96, 120, 144, 168] |
| `days_back` | 730 |
| `random_state` | 2026 |
| `deterministic` | True |
| `force_col_wise` | True |

### Design objectives

1. **Determinismus (CR-2):** fester Seed, `deterministic=True` → byte-
   identische Resultate bei gleichem Datenstand.
2. **Fail-Safe (CR-3):** `on_missing="raise"` für Lücken **plus**
   Plausibilitäts-Klammer gegen Ausreißer.
3. **Reproduzierbarkeit:** Trainingsdaten-Snapshot (`.train_snapshot.parquet`)
   + Parameter-Log (`.log.json`) je Submission. `evaluate(log_path=...)` lädt
   den Snapshot zurück und reproduziert die Prognose (bis auf Wetter-Quelle,
   s.u.).

---

## 5. Interfaces and Runtime

**Input:** ENTSO-E `Actual Load`-CSV (über Downloader), Open-Meteo-Wetter,
Zieltag als `YYYY-MM-DD`.
**Output:** CSV mit 24 Zeilen (`timestamp_utc` ISO-UTC, `forecast_mw` float,
strikt positiv).

**Plattform:** CPU genügt; Training (~730 Tage × 1 Modell) in Minuten.
Kein GPU nötig.

| Abhängigkeit | Lizenz |
|---|---|
| spotforecast2-safe | AGPL-3.0-or-later |
| lightgbm | MIT |
| pandas | BSD-3-Clause |
| numpy | BSD-3-Clause |

**Energiekosten:** vernachlässigbar (Sekunden-CPU-Training pro Tag).

---

## 6. Data and Operational Design Domain

**Datensätze:** ENTSO-E DE-Last (live), Open-Meteo-Wetter (Forecast für
Submission, Archiv für Evaluation).

| Bedingung | Gültiger Bereich | Außerhalb |
|---|---|---|
| Region | Deutschland (DE / DE_LU) | nicht validiert |
| Horizont | 24 h Day-Ahead | nicht unterstützt |
| Lastniveau | ~35.000–75.000 MW | Extrapolation unsicher |
| Datenlücken | einzelne Stunden (interpoliert) | große Lücken → `raise` |
| Ausreißer | außerhalb 20.000–100.000 MW → verworfen + interpoliert | dauerhaft falsche Quelle |
| Wetter-Verzug | Archiv ~5 Tage (ffill/bfill) | längere Ausfälle degradieren |

**Im gültigen Bereich bleiben:**

- 730-Tage-Fenster sicherstellen (≥2 Jahre ENTSO-E-Historie verfügbar).
- `ENTSOE_API_KEY` gültig und Quote ausreichend.
- Bei Feiertagen/Sonderlast: Ergebnis manuell plausibilisieren.

---

## 7. Evaluation

Primärmetrik **MAE** [MW] über die 24 Zielstunden, zusätzlich RMSE und MAPE
(Diagnose). Bewertung gegen ENTSO-E *final values* via `evaluate()`.

**Backtest der aktuellen Konfiguration (v2.0)** über große Stichproben
(13–25 Monate ENTSO-E, Archiv-Wetter; relative Vergleiche gültig, absolute
MAEs weichen vom Live-Leaderboard ab, das Wetter-Forecast nutzt):

| Konfiguration | mean MAE (Backtest) |
|---|---|
| Baseline v1 (Basis-Lags, 90 T.) | ~2.050 MW |
| + Hybrid-Lags (Mo/Sa/So → Tageslags) | ~1.720 MW |
| + 730-Tage-Fenster (v2.0) | **~1.465 MW** |

**Behobene Schwäche (war v1):** systematische Überprognose an Samstagen
(2026-06-20: MAE 7.371). Ursache: kurze Lags schleppten das Freitags-
Momentum in den Samstag. Durch Hybrid-Lags behoben — Samstage liegen jetzt
auf dem Niveau der besten Teams. Details + Validierung in
[DEVLOG.md](../../DEVLOG.md).

---

## 8. Model Transparency

- **Unsicherheit:** keine Intervalle; reine Punktprognose. Konfidenz nur
  indirekt über historische MAE-Streuung.
- **Auditierbarkeit:** vollständiger Code in
  [`12_challenge.ipynb`](../../12_challenge.ipynb) cell-4; jede Submission
  hinterlegt Snapshot + Parameter-Log → exakt nachvollziehbar.
- **Feature-Attribution:** LightGBM-Feature-Importances zugänglich über
  den gekapselten Regressor (nicht standardmäßig exportiert).

---

## 9. Operation: Monitoring and Response

- **Überwachung:** Datenqualität (ENTSO-E-Lücken), Drift (Tages-MAE-Verlauf
  im Leaderboard), Ausreißer-Bias (insb. Wochenende).
- **Response:** bei auffälligem Tages-MAE → Vergleich gegen Wochen-Persistenz
  (Last vor 168 h) als Sanity-Check; Re-Submission bis Deadline *D-1* 23:59.
- **Logging:** `.log.json` + `.train_snapshot.parquet` je Zieltag erlauben
  forensische Reproduktion.

---

## 10. Compliance Support

Bezug zur EU-KI-VO (AI Act) gemäß Kursrahmen:

- **Art. 10 (Daten-Governance):** dokumentierte Quelle (ENTSO-E final),
  Lückenbehandlung Fail-Safe.
- **Art. 12 (Aufzeichnung):** Snapshot/Log-Trail je Submission, Git-History.
- **Art. 13 (Transparenz):** diese Model Card + offener Code.
- **Art. 15 (Robustheit/Genauigkeit):** Determinismus (CR-2), gepinnte
  Abhängigkeiten (`uv.lock`).

---

## 11. Glossary

| Begriff | Bedeutung |
|---|---|
| Zieltag *D* | Tag, für den die Prognose gilt |
| Lag | um *n* Stunden zurückliegender Lastwert als Feature |
| Rekursiv | Vorhersage wird als Input des nächsten Schritts genutzt |
| Exog | exogenes Feature (Kalender/Wetter) |
| MAE | Mean Absolute Error [MW] |
| Ground Truth | ENTSO-E final veröffentlichte Ist-Last |

---

## 12. How to Audit

1. `12_challenge.ipynb` cell-4 öffnen, `make_submission`/`evaluate` lesen.
2. Hyperparameter (Abschnitt 4) gegen Code prüfen
   (`_BASE_LAGS`, `_DAILY_LAGS`, `_DAILY_LAG_WEEKDAYS`, `_LGBM_PARAMS`, `days_back`).
3. Wochentag-Logik prüfen: `_select_lags(target)` → Mo/Sa/So Tageslags, sonst Basis.
4. `evaluate(log_path=...)` mit einem vorhandenen `.log.json` ausführen →
   Ergebnis entspricht der damaligen Submission (Wetter-Quelle s. Abschnitt 6).
5. Kein Leakage: Trainingsfenster endet bei `target − 1 h` (verifizieren).
6. Determinismus: gleicher Snapshot → identische Vorhersage (zweimal laufen).
7. Plausibilitäts-Klammer greift: implausible Lastwerte werden verworfen
   (Konsolen-Ausgabe `[CR-3] … implausible Lastwert(e) verworfen`).
8. Leaderboard-Score gegen `data/daily.json` abgleichen.

---

## 13. Citation, Authors, and Contact

**Team:** Team Fabinalii (team_fabinalii)

| Mitglied | GitHub | E-Mail |
|---|---|---|
| Inalbek Akiev | akievi | inalbek.akiev@smail.th-koeln.de |
| Fabian Feith | ffeith-thk | fabian.feith@smail.th-koeln.de |
| Vitalii Zakharuk | VitaliiZakharuk | vitalii.zakharuk@smail.th-koeln.de |

Aufbauend auf:

```bibtex
@software{spotforecast2safe,
  title  = {spotforecast2-safe},
  author = {{Sequential Parameter Optimization}},
  url    = {https://github.com/sequential-parameter-optimization/spotforecast2-safe},
  note   = {Version 3.0.0}
}
```

---

## 14. Disclaimer and Liability

**Haftungsbeschränkung.** Dieses Modell ist ein studentischer Beitrag zur
Lastprognose-Challenge (SoSe 2026) und dient ausschließlich Lehr- und
Wettbewerbszwecken.

Es ist **nicht** für den produktiven Betrieb in kritischer Infrastruktur
freigegeben. Eine etwaige Integration in reale Netzsteuerung liegt allein
in der Verantwortung des Integrators, der eigene Validierung, Monitoring
und Risikobewertung durchführen muss.

Der Code dieses Modells wird unter der **MIT-Lizenz** bereitgestellt:
Weiterverwendung und Modifikation sind unter Beibehaltung des
Copyright-Hinweises gestattet, ohne Gewährleistung.
