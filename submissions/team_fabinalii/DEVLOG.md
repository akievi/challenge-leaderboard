# Entwicklungs-Log — Lastprognose-Challenge (team_fabinalii)

Dieses Log dokumentiert alle Änderungen am Prognose-Algorithmus in
[`12_challenge.ipynb`](12_challenge.ipynb) (cell-4) sowie deren Erfolg/Misserfolg.
Gepflegt von Claude. Neueste Einträge oben.

Bewertungsgrundlage: ENTSO-E `Actual Load` (DE), primäre Metrik MAE [MW].
Leaderboard-Aggregat (Stand 2026-06-22): **mean_mae = 2.006 MW**, Rang 10, 12 Submissions.

---

## Referenz: eingereichte Submissions (Leaderboard-Scores)

Quelle: `https://bartzbeielstein.github.io/challenge-leaderboard/data/daily.json`

| Datum (Zieltag) | Wochentag | MAE | RMSE | MAPE | Bias |
|---|---|---:|---:|---:|---:|
| 2026-06-04 | Do | 2.650 | 3.112 | 5,43 % | −2.293 |
| 2026-06-05 | Fr | 3.667 | 4.180 | 7,30 % | −3.495 |
| 2026-06-06 | Sa | 1.509 | 1.901 | 3,62 % | −175 |
| 2026-06-07 | So | 1.655 | 1.921 | 4,06 % | +1.345 |
| 2026-06-08 | Mo | 2.118 | 2.532 | 4,09 % | −511 |
| 2026-06-09 | Di | 1.980 | 2.351 | 3,54 % | −1.980 |
| 2026-06-10 | Mi | 893 | 1.106 | 1,65 % | +81 |
| 2026-06-11 | Do | 1.816 | 2.821 | 3,62 % | +868 |
| 2026-06-12 | Fr | 2.558 | 3.214 | 4,55 % | −1.579 |
| 2026-06-13 | Sa | 2.733 | 2.967 | 6,34 % | +2.733 |
| 2026-06-14 | So | 796 | 995 | 2,01 % | +136 |
| 2026-06-15 | Mo | 1.361 | 1.641 | 2,63 % | −90 |
| 2026-06-16 | Di | 1.081 | 1.318 | 2,10 % | +741 |
| 2026-06-17 | Mi | 770 | 877 | 1,45 % | −367 |
| 2026-06-18 | Do | 1.388 | 1.636 | 2,48 % | −1.277 |
| 2026-06-19 | Fr | 1.006 | 1.275 | 1,79 % | −865 |
| **2026-06-20** | **Sa** | **7.371** | **8.018** | **15,90 %** | **+7.371** |
| 2026-06-21 | So | 2.302 | 2.625 | 5,15 % | −2.302 |

**Beobachtung:** Die meisten Tage liegen bei 770–2.700 MW. **2026-06-20 (Sa) ist
ein katastrophaler Ausreißer (7.371 MW, Bias +7.371)** — das Modell hat massiv
überprognostiziert. Beide Samstage mit positivem Bias (06-13: +2.733, 06-20: +7.371)
deuten auf systematische Wochenend-Überprognose hin.

---

## ⚠️ Wichtig: evaluate() ist KEIN bit-exaktes Replay einer Submission

Bewusste Design-Entscheidung (2026-06-23, vom Nutzer bestätigt): so belassen.

- `make_submission` nutzt **Wetter-FORECAST** (`use_forecast=True`,
  `weather_live.parquet`) — denn für morgen gibt es nur die Wettervorhersage.
- `evaluate` nutzt **Wetter-ARCHIV** (`use_forecast=False`,
  `weather_eval.parquet`) — für vergangene Tage liegen die Ist-Wetterwerte vor.

→ Folge: `evaluate("D")` reproduziert NICHT exakt den damaligen Submission-
Forecast für D. Es liefert eine etwas **optimistischere** Prognose, weil es das
tatsächliche Wetter „kennt", das die Submission noch nicht hatte. Der
`train_snapshot.parquet` friert nur die LAST ein, NICHT die Wettervorhersage.

**Konsequenzen für die Interpretation:**
- `evaluate()`-MAE = Best-Case-Check (Modellgüte bei perfektem Wetter), nicht
  der Leaderboard-Wert.
- Batch-Vergleiche im DEVLOG (alle mit Archiv-Wetter) sind untereinander gültig
  (relativer Vergleich), aber die absoluten MAEs weichen vom Leaderboard ab.
- Echte Submission-Güte nur am Leaderboard ablesbar.

## Bestätigte Baseline (echter Submission-Code)

Stand 2026-06-22 vom Nutzer verifiziert — dies ist der Code der die
Leaderboard-Submissions (mean MAE ~2.006) erzeugt hat:

- **Modell:** `ForecasterRecursive` + `LGBMRegressor`
  (n_estimators=400, lr=0.05, num_leaves=63, random_state=2026, deterministic)
- **lags:** `[1, 2, 3, 24, 168]`
- **Exog:** `ExogBuilder` (hour, dayofweek, month) + Wetter (51.165, 10.451)
- **KEINE** Wochenend-Gewichtung, **KEIN** `_add_daytype`
- **Wetter Submission:** `use_forecast=True`, cache `weather_live.parquet`
- **Wetter evaluate:** `use_forecast=False`, cache `weather_eval.parquet`
- **Trainingsfenster:** 90 Tage, endet bei `target - 1h` (kein Leakage)

Im Notebook (cell idx=4) wieder hergestellt + Snapshot/Log-Reproduzierbarkeit
ergänzt (Modell/Daten unverändert).

---

## Sonstige Artefakte

- **2026-06-22 — Model Card erstellt & ausgefüllt:**
  [`submissions/team_fabinalii/MODEL_CARD.md`](submissions/team_fabinalii/MODEL_CARD.md),
  Struktur nach sf2-safe-Template (14 Abschnitte). Beschreibt die rekursive
  Baseline. Eingetragen: Lizenz MIT; Repo = bartzbeielstein/challenge-leaderboard;
  3 Mitglieder (Akiev, Feith, Zakharuk) mit @smail.th-koeln.de-Adressen.
- **2026-06-22 — LICENSE-Datei erstellt:**
  [`submissions/team_fabinalii/LICENSE`](submissions/team_fabinalii/LICENSE),
  MIT-Volltext, Copyright 2026 alle 3 Mitglieder.

### Upload-/Abgabe-Prozess für Model Card (recherchiert aus challenge-leaderboard)

Das Leaderboard hat eine Sektion **„About the Models"** mit 3 Artefakt-Spalten
pro Team, gesteuert über `teams.yml` (Single Source of Truth, dozenten-gepflegt):

1. **`model_card_link`** → URL zur Model Card. Fehlt sie → „missing" + Warn-Icon.
2. **`software_link`** → URL zu einem **Reproduzierbarkeits-ZIP** der Prognose-
   Software. Vorbild: [`repro/team4/`](file) im Leaderboard-Repo — enthält
   Pipeline-Skript, gepinnte Umgebung (`uv.lock`), gefrorenen ENTSO-E-Snapshot,
   `expected/`-Referenz-CSVs + SHA256SUMS, `MANIFEST.md`. Wird als GitHub-Release-
   ZIP gehostet. Freiwillig (kein Warn-Icon wenn fehlt).
3. **`certified: "Yes"/"No"`** → wird **NICHT** vom Team selbst gesetzt. Ein
   ANDERES Team reproduziert eure Ergebnisse, füllt
   [`Certificate.md`](file) aus, kompiliert es zu PDF und mailt es an die
   Dozentur. Erst dann setzt die Dozentur `certified: "Yes"` (✅).

**Konkreter Abgabe-Weg (Model Card):**
- Da kein Self-Service-PR-Mechanismus für `teams.yml` existiert (organizer-
  maintained), läuft die Eintragung **per E-Mail an Prof. Bartz-Beielstein**
  (gleicher Kanal wie Team-Anmeldung).
- Mail-Inhalt: Team-ID `team_fabinalii`, öffentliche URL der Model Card
  (sobald im Professor-Repo gehostet → raw.githubusercontent.com-Link).

**Offen vor Abgabe:**
1. Model Card + LICENSE ins Professor-Repo pushen (oder per PR), öffentliche
   URL ermitteln.
2. E-Mail an Dozentur: `model_card_link` für `team_fabinalii` in `teams.yml`.
3. Optional/später: Reproduzierbarkeits-ZIP bauen (Vorbild `repro/team4/`) →
   `software_link`. Und Zertifizierung durch ein anderes Team anstoßen.

## Diagnose Wochenend-Überprognose (2026-06-22)

**Befund:** Samstage werden systematisch überprognostiziert. Ursache ist
**lag-24**: Für einen Samstag-Zieltag zeigt lag-24 (= "gestern, gleiche
Stunde") auf den **Freitag** — einen Werktag mit ~13,7 % höherer Tageslast.
Der rekursive Forecaster lehnt sich an lag-24 an und zieht die Samstags-
Prognose hoch Richtung Freitags-Profil. Die Kalender-`dayofweek`-Exog ist
zu schwach, um das zu überstimmen.

**Belege:**
- Fri→Sat Tageslast-Drop (06–18h): 56.314 → 48.593 MW (−13,7 %).
- Für 06-20 betrug die Fri(06-19)→Sat-Lücke in der Morgen-Rampe (4–13h)
  **+10.000 bis +14.000 MW** — exakt dort lag der Prognosefehler (+7.000–9.700).
- 06-20 war als Samstag NICHT ungewöhnlich hoch (48.401 MW Tagesmittel vs.
  ~46.000 typisch) → das Problem ist die Profil-Form, nicht das Niveau.

**Hypothese für Fix #1:** Explizite Tagestyp-Features
(`is_saturday`/`is_sunday`/`is_weekday`) hinzufügen, damit das Modell
`dayofweek` stärker gewichtet und lag-24 an Übergangstagen weniger vertraut.
→ Wird über ALLE Tage 06-04…06-21 gemessen (Baseline vs. +daytype).

## Validierte Fix-Versuche Wochenende (2026-06-22)

Methode: alle Kandidaten über ALLE 18 Tage (06-04…06-21) gemessen, jeweils
mit Wetter-Archiv (`use_forecast=False`). Absolute MAEs hier weichen von den
Leaderboard-Werten ab (dort Wetter-Forecast), aber die **relativen** Vergleiche
zwischen Varianten sind gültig.

### Fix #1: Tagestyp-Dummies (is_saturday/is_sunday/is_weekday) — ❌ NO-OP
Byte-identische Ergebnisse zur Baseline über 9 Tage. `dayofweek` (Period-Feature)
kodiert die Info bereits → LightGBM splittet nie auf den redundanten Spalten.
Verworfen.

### Fix #2: Zusätzliche Lags — ❌ KEIN klarer Gewinn
| Variante | Mean MAE | Sa-only |
|---|---:|---:|
| base `[1,2,3,24,168]` | **2.052** | 3.485 |
| +336 `[...,336]` | 2.220 (schlechter) | 3.298 |
| +48,336 | 2.017 (−1,7 %, Rauschen) | 3.480 |

- **+336 verworfen:** Mean schlechter; katastrophaler Ausreißer 06-15 Mo
  1.270 → 5.428 (4×). lag-336 destabilisiert die Rekursion.
- **+48,336:** nur 1,7 % besser (Rauschen) und löst das Sa-Problem NICHT
  (Sa-Mean 3.480 ≈ Baseline; 06-20 bleibt 7.848). Nicht überzeugend.

**Erkenntnis:** Das Samstags-Problem liegt NICHT im Lag-Set. Selbst mit
weekend-korrekten Lags (168/336) bleibt 06-20 bei ~7.800 MAE.

### Fix #3: Interaktions-Feature `wk_lag168 = load(t-168) × is_weekend` — ❌ SCHLECHTER
Idee: dem Modell die Last "letztes Wochenende, gleiche Stunde" als nur an
Sa/So aktives Exog geben, um lag-24 (Freitag) an Samstagen zu überstimmen.

| Variante | Mean | Sa | So | Werktag |
|---|---:|---:|---:|---:|
| base | **2.052** | **3.485** | 864 | **1.892** |
| interact | 2.254 | 3.619 | 874 | 2.143 |

Schlechter auf ALLEN Aggregaten. Machte Samstage sogar schlechter (Gegenteil
des Ziels). Gleicher katastrophaler Ausreißer wie +336: **06-15 Mo
1.270 → 4.783** (+3.513). 06-20 unverändert (~7.945). Verworfen.

**Zwischenfazit nach 3 Fixes:** Weder Tagestyp-Dummies, noch zusätzliche Lags,
noch ein Wochenend-Interaktions-Feature verbessern die Baseline. Das
wiederkehrende Muster (06-15 Mo bricht bei zwei verschiedenen Fixes weg)
deutet darauf hin, dass zusätzliche load-basierte Features die Rekursion
destabilisieren.

### Fix #4: Post-hoc Wochenend-Bias-Korrektur (flat + hourly) — ❌ KEIN GEWINN
Idee: in-sample Bias des Modells an vergangenen Wochenend-Tagen schätzen
(flat = ein Skalar, hourly = 24h-Profil) und vom Wochenend-Forecast abziehen.
Per Konstruktion werktagsneutral. Lauf nach 10/18 Tagen abgebrochen — Ergebnis
eindeutig.

| Variante | Mean (10d) | Weekend |
|---|---:|---:|
| base | **1.977** | 1.050 |
| flat | 1.979 | 1.054 |
| hourly | 1.982 | 1.066 |

**Entscheidender Befund:** Der geschätzte Wochenend-Bias ist klein UND im
Vorzeichen inkonsistent: 06-06 +17, 06-07 +12, **06-13 −102** (Modell
unterprognostiziert hier). Es gibt also keinen stabilen Bias zum Korrigieren.
Beide Korrektur-Varianten minimal schlechter als Baseline. Verworfen.

## ⚠️ ZWISCHENFAZIT REVIDIERT — siehe DURCHBRUCH unten

Das frühere Fazit "Baseline nicht verbesserbar, 06-20 unfixbar" war FALSCH.
Fehler in der Analyse: Es wurde nie der Leaderboard-Vergleich gezogen. Auf
06-20 erzielten ANDERE Teams MAE 926–2.400 (Bester: chronos 926). Wir hatten
7.371 — klarer Ausreißer NACH UNTEN. 06-20 ist also KEIN schwerer Tag, sondern
ein struktureller Defekt in UNSERER Pipeline. Alle 4 obigen Fixes scheiterten,
weil sie denselben kaputten Baseline-Kern teilten.

## 🎯 DURCHBRUCH (2026-06-23): Tageslags lösen das Wochenend-Problem

**Root Cause gefunden:** Die kurzen Lags **`[1, 2, 3]`** in der Baseline sind
schuld. Bei rekursiver Prognose ab Freitag-23:00-Origin schleppen sie das
Stunde-zu-Stunde-Momentum des Werktags Freitag in den Samstag-Forecast →
das Modell baut eine werktags-förmige Morgen-Rampe (06-20: Peak 59.841 MW @ 6 Uhr
statt tatsächlich 50.762 @ 8 Uhr).

**Fix:** Lags auf **Vielfache von 24** umstellen:
`[24, 48, 72, 96, 120, 144, 168]`. Jeder Lag zeigt dann auf dieselbe Stunde an
einem Vortag; lag-168 = letzter Samstag verankert das Wochenend-Profil korrekt.
Kein kurzes Momentum mehr.

**Validierung über ALLE 18 Tage (Archiv-Wetter):**

| Variante | Mean MAE | Sa | Werktag |
|---|---:|---:|---:|
| base `[1,2,3,24,168]` | 1.998 | 3.485 | **1.892** |
| **daily `[24,48,…,168]`** | **1.723** ✅ | **1.412** ✅ | 1.950 |
| daily_mix `[1,24,…,168]` | 2.374 ❌ | 4.270 | 2.127 |

- **Mean −14 % (1.998 → 1.723).**
- **Samstage −59 % (3.485 → 1.412).**
- **06-20: 7.987 → 1.730** (von schlechtester zu wettbewerbsfähiger Prognose).
- Werktage nur +58 MW (+3 %) teurer — durch Sa-Gewinn weit überkompensiert.
- **`daily_mix` (mit lag-1) verworfen:** schon lag-1 allein reicht, um die
  Werktags-Drift wieder einzuschleppen. Fix muss REINE Tageslags sein.

**Übernommen:** Notebook cell-4 → `_LAGS = [24, 48, 72, 96, 120, 144, 168]`.

**Dank an Nutzer-Hinweis:** Der entscheidende Anstoß war der Leaderboard-
Vergleich ("andere Teams hatten kein Problem mit den Samstagen") — ohne ihn
wäre die falsche "unfixbar"-Schlussfolgerung stehen geblieben.

## 🎯 HYBRID-LAGS (2026-06-23): bestes Setup

Statt überall Tageslags: **lag-Set abhängig vom Zieltag wählen**. Die
Per-Wochentag-Analyse zeigte, dass Basis-Lags an Werktagen/Sonntag besser
sind (kurze Lags helfen dort), Tageslags nur am Samstag gewinnen (riesig).

| Strategie | Mean MAE | Samstag |
|---|---:|---:|
| nur Basis `[1,2,3,24,168]` | 1.998 | 3.485 |
| nur Tageslags `[24,…,168]` | 1.724 | 1.412 |
| **Hybrid (Sa=Tageslags, sonst Basis)** | **1.653** ✅ | 1.412 |

Hybrid schlägt beide reinen Varianten (−17 % vs. Basis, −4 % vs. nur-Tageslags),
weil es die Werktags-Stärke der Basis-Lags behält UND den Samstags-Gewinn
mitnimmt. (Optimum „Mo+Do+Sa=Tageslags" gäbe 1.554, aber Mo/Do gewannen nur
knapp → Overfitting aufs Test-Sample; verworfen. Nur der Samstags-Switch ist
mechanistisch robust.)

**Übernommen in cell-4:** `_select_lags(target)` → Samstag `_DAILY_LAGS`,
sonst `_BASE_LAGS`. `make_submission` UND `evaluate` nutzen dieselbe Auswahl
(konsistent/reproduzierbar). Log protokolliert `lags_set` + `weekday`.

### 📊 GROSS-SAMPLE-BACKTEST (2026-06-23): 13 Monate, alle Wochentage

Der 18-Tage-Vergleich war zu klein. Daher: 13 Monate ENTSO-E-Last (9.504 h)
einmal geladen, rollendes 90-Tage-Fenster, je ~43 Tage pro Wochentag
backgetestet (base vs. daily lags, Kalender-Exog ohne Wetter — Wetter ist
für den Lag-Vergleich konstant).

| Tag | n | base | daily | Win % | meanΔ | medianΔ | Entscheidung |
|---|--:|--:|--:|--:|--:|--:|---|
| Mo | 43 | 2.878 | 2.444 | **65 %** | **−434** | **−261** | ✅ daily (konsistent) |
| Di | 43 | 1.608 | 1.602 | 42 % | −7 | +116 | base |
| Mi | 44 | 1.885 | 2.066 | 45 % | +181 | +34 | base |
| Do | 44 | 2.027 | 2.027 | 48 % | −0 | +85 | base |
| Fr | 44 | 2.329 | 2.537 | 45 % | +208 | +105 | base |
| Sa | 43 | 2.611 | 2.160 | 49 % | **−450** | +30 | ✅ daily (Versicherung) |
| So | 43 | 2.319 | 1.910 | **56 %** | **−409** | **−57** | ✅ daily (konsistent) |

**Klares, mechanistisch kohärentes Ergebnis:** Tageslags helfen genau an den
**wochenend-nahen Tagen Mo/Sa/So** und schaden mitten in der Woche (Di–Fr).
- **Mo** (65 %, med −261) und **So** (56 %, med −57): konsistente Gewinne —
  lag-24 zeigt auf So bzw. Sa (abweichendes Profil).
- **Sa** (49 %, med +30, aber mean −450): Versicherung gegen Ausreißer wie
  06-20 (Werktags-Rampe). Verhindert seltene Katastrophen.
- **Di–Fr**: daily verliert klar (Win ≤48 %, med ≥0) — lag-24 = normaler
  Werktag, kein Profil-Mismatch. Basis behalten.

**Korrektur meiner früheren Aussage:** Ich hatte Montag mit nur 2 Tagen als
„nicht robust" verworfen. Im 43-Tage-Sample ist Mo sogar der **konsistenteste**
daily-Gewinn. Nutzer-Hinweis (größeres Sample!) war goldrichtig.

**Übernommen in cell-4:** `_DAILY_LAG_WEEKDAYS = {0, 5, 6}` (Mo, Sa, So) →
Tageslags; Di–Fr → Basis-Lags.

---

### (Historisch) Verworfen mit Klein-Sample: Montag auf Tageslags?
*Diese Notiz ist durch den Gross-Sample-Backtest oben überholt — Mo wird
nun DOCH übernommen. Bleibt als Lerneffekt stehen.*
Hypothese (Nutzer): Montags lag-24 = Sonntag (niedrig) zieht Montag-Forecast
runter, analog zum Samstag. Daten zeigen: Tageslags gewinnen montags zwar
(mean base 1.400 → daily 1.112) und Sat+Mon gäbe 1.621 (vs. 1.653 Sat-only).
**ABER Kurven-Check (06-15) widerlegt den Mechanismus:** Basis-Lags werden
NICHT zum niedrigen Sonntag gezogen — Basis-Bias = **+674** (Überprognose),
nicht negativ. Sonntags-Tagesschnitt 43.249, Montag-Ist 56.558, Basis-Pred
56.655 (praktisch korrektes Niveau). Der daily-Gewinn montags ist ein vager
Ganztags-Effekt OHNE klaren Mechanismus, nur 2 Tage, kleine Margen
(+207, +371). → Nicht robust genug, **Montag NICHT übernommen**. Nur Samstag
hat einen bulletproof-Mechanismus (Freitag-Momentum). Hybrid bleibt Sat-only.

**Offen:** Erste Live-Submissions (besonders nächster Samstag) am Leaderboard
verifizieren (echtes Forecast-Wetter). Lehre: IMMER gegen Leaderboard/andere
Teams vergleichen UND Mechanismus per Kurven-Check bestätigen, bevor ein
Per-Wochentag-Switch übernommen wird (kleine Sample-Gewinne = Overfitting-Falle).

## 🛡️ AUSREISSER-SCHUTZ (2026-06-26): Plausibilitäts-Klammer

**Vorfall:** Prognose für 2026-06-27 (Sa) explodierte auf bis zu **259.915 MW**
(Tagesmittel 101.761 statt ~46.000). Ursache: **ein korrupter ENTSO-E-Wert**
im Trainingsfenster — `2026-06-25 16:00 = 1.124.884 MW` (≈18× normal, ein
Daten-Glitch der Quelle). Die rekursiven Tageslags zogen den Monsterwert in
die Vorhersage und verstärkten ihn.

**Warum nicht abgefangen:** `LinearlyInterpolateTS(on_missing="raise")` behandelt
nur NaN (fehlende Werte), NICHT vorhandene Ausreißer. Der absurde Wert lief
ungeprüft durch.

**Fix (in `_load_series`, gilt für make_submission UND evaluate):**
Plausibilitäts-Klammer `_LOAD_MIN_MW=20.000`, `_LOAD_MAX_MW=100.000`. Werte
außerhalb → NaN → von der bestehenden Interpolation gefüllt. Mit Audit-Print
(`[CR-3] N implausible Lastwert(e) verworfen ...`).

**Verifiziert:** Nach Klammer 06-27-Prognose plausibel — Max 50.357, Mittel
46.725 MW (vgl. Vorsamstag 06-20 ~45.835). Genau 1 Wert verworfen.

**Lehre:** CR-3-Fail-Safe muss auch grobe Ausreißer abfangen, nicht nur Lücken.
Live-Datenquellen liefern gelegentlich Glitches — eine physikalische
Plausibilitätsgrenze ist Pflicht.

## 📈 TRAININGSFENSTER OPTIMIERT (2026-06-26): days_back 90 → 365

`days_back=90` war aus der Original-Baseline übernommen, nie validiert.
Backtest über **131 Zieltage** (25 Monate ENTSO-E, alle 3 Tage gesampelt,
Hybrid-Lags + Clamp, Kalender-Exog), 8 Fenstergrößen auf identischen Zieltagen:

| days_back | mean MAE | median |
|---:|---:|---:|
| **365** | **1.632** | 1.444 |
| 270 | 1.819 | 1.352 |
| 180 | 1.853 | 1.485 |
| 120 | 2.015 | 1.662 |
| 90 (alt) | 2.048 | 1.668 |
| 60 | 2.049 | 1.655 |
| 45 | 2.180 | 1.817 |
| 30 | 2.342 | 1.857 |

**365 Tage gewinnt klar: 1.632 vs. 90→2.048 (−20 %).** Monotoner Trend
(mehr Historie → besser) — ein volles Jahr deckt den kompletten Saison-Zyklus
ab. (270 hat zwar den niedrigsten *Median* 1.352, aber 365 den niedrigsten
*Mean* und ist robuster gegen schlechte Tage → für rolling-mean-MAE-Wertung
die richtige Wahl.)

**Kosten/Hinweise:** mehr Trainingsdaten pro Fit (Laufzeit Minuten, kein
Problem); zieht entsprechend mehr ENTSO-E pro Lauf; Plausibilitäts-Clamp jetzt
umso wichtiger (mehr Daten = mehr Glitch-Chancen).

### Nachtrag (2026-06-26): längere Fenster bis 3 Jahre getestet → 730 gewählt
Backtest über **194 Zieltage** (4,3 Jahre ENTSO-E, alle 2 Tage), Fenster
365–1095:

| days_back | mean MAE | vs 365 | Grenzgewinn |
|---:|---:|---:|---:|
| 365 | 1.528 | — | — |
| 540 | 1.492 | −2,4 % | −2,4 % |
| **730 (2 J.)** | **1.465** | **−4,1 %** | −1,8 % |
| 1095 (3 J.) | 1.452 | −5,0 % | −0,9 % |

Trend war NICHT (wie vermutet) ein Plateau/Abfall — mehr Historie hilft weiter,
ABER mit starkem Diminishing-Return: 365→730 bringt −4,1 %, 730→1095 nur noch
−0,9 % bei 50 % mehr Daten/Laufzeit. **Sweet Spot = 730 Tage** (zwei volle
Saison-Zyklen, ~80 % des verfügbaren Gewinns, danach flach). 1095 verworfen:
zu teuer für ~0,9 %, zudem mehr Drift-Risiko (alte Netz-Muster).

**Übernommen:** `days_back=730` als Default in make_submission UND evaluate.

## Änderungs-Historie

### 2026-06-22 — Direkte Strategie (statt rekursiv) + weekend_weight 5→10
**Status: ⚠️ NICHT ERFOLGREICH (laut Nutzer-Feedback) — wird zurückgerollt/überprüft**

- **Was:** `ForecasterRecursive` ersetzt durch manuelle direkte Multi-Step-Strategie
  (ein LightGBM-Modell pro Horizont-Schritt h=1..24). `_WEEKEND_WEIGHT` 5→10.
- **Motivation:** Rekursive Prognose driftet auf Wochenend-Zieltagen ins
  Werktagsmuster (Morgen-Rampe zu steil). 2026-06-20 als Auslöser.
- **Isolierte Messung (nur 2026-06-20):** MAE 5.290 → 3.813 MW.
- **Aber:** Nutzer berichtet, die Änderung war insgesamt nicht erfolgreich.
  Vermutlich Verschlechterung auf den vielen guten Werktagen (770–2.000 MW),
  die der rekursive Ansatz bereits sehr gut traf. → Vergleich über ALLE Tage nötig.
- **Nächster Schritt:** Aktuellen Algorithmus auf allen eingereichten Zieltagen
  evaluieren und gegen die Leaderboard-Scores vergleichen (siehe Vergleichs-Sektion unten).

---

## Vergleichs-Läufe (aktueller Algorithmus vs. Leaderboard)

### 2026-06-22 — Aktueller Algorithmus (direkt, weekend_weight=10) auf eingereichten Zieltagen

Lauf nach 6 von 18 Tagen abgebrochen — das Ergebnis war eindeutig genug.

| Datum | Wochentag | Submitted MAE | Aktuell (direkt) | Faktor |
|---|---|---:|---:|---:|
| 2026-06-04 | Do | 2.650 | 6.301 | 2,4× ❌ |
| 2026-06-05 | Fr | 3.667 | 6.108 | 1,7× ❌ |
| 2026-06-06 | Sa | 1.509 | 3.193 | 2,1× ❌ |
| 2026-06-07 | So | 1.655 | 3.908 | 2,4× ❌ |
| 2026-06-08 | Mo | 2.118 | 5.834 | 2,8× ❌ |
| 2026-06-09 | Di | 1.980 | 5.528 | 2,8× ❌ |

**Fazit:** Die direkte Strategie ist an JEDEM getesteten Tag deutlich
schlechter — auch an Wochenenden (06-06, 06-07). Sie hat die Werktags-
Genauigkeit zerstört und nicht einmal das Wochenend-Problem gelöst.
Eindeutiger Misserfolg.

**Warum vermutlich:** Pro-Schritt-Modelle (24 separate LGBMs) sehen jeweils
nur ~2.000 Trainingszeilen und können den glatten autoregressiven Tagesgang
nicht so gut lernen wie der rekursive Forecaster, der die volle Lag-Dynamik
nutzt. Die isolierte 06-20-Messung (5.290→3.813) war nicht repräsentativ.

---

### 2026-06-22 — REVERT auf rekursive Strategie (weekend_weight=5)
**Status: ✅ WIEDERHERGESTELLT (bekannter guter Stand, mean MAE ~2.006)**

- `_build_pipeline` zurückgesetzt auf `ForecasterRecursive` + LightGBM.
- `_WEEKEND_WEIGHT` zurück 10→5.
- Log-Feld `"strategy": "recursive"`.
- Snapshot-Reproduzierbarkeit unverändert erhalten.

**KORREKTUR 2026-06-22 (später):** Nutzer hat den *echten* Submission-Code
geliefert (`revert_cell.py` war nicht identisch!). Wahre Leaderboard-Config:
- **lags = `[1, 2, 3, 24, 168]`** (NICHT `[...,48,...,336]`)
- **KEIN weekend_weight / weight_func** — gar keine Wochenend-Gewichtung
- **KEIN `_add_daytype`** (keine is_saturday/is_sunday/is_weekday-Features)
- Submission-Wetter: `use_forecast=True`, cache `weather_live.parquet`
- Evaluate-Wetter:  `use_forecast=False`, cache `weather_eval.parquet`
→ Notebook auf diese echte Baseline gesetzt. Frühere "Verbesserungen"
(extra Lags, daytype, weekend_weight) waren also bereits Abweichungen vom
Baseline-Stand und NICHT Teil der ~2.006-MAE-Submissions.

**Offen (Wochenend-Problem):** Beide Samstage haben positiven Bias
(06-13: +2.733, 06-20: +7.371 → systematische Überprognose an Sa).
Künftige Ansätze sollten gezielt die Sa-Überprognose dämpfen, OHNE die
Werktags-Genauigkeit zu opfern. Kandidaten (noch nicht getestet):
- weekend_weight moderat erhöhen (6–7) und einzeln gegen Leaderboard prüfen
- separates additives Wochenend-Korrekturmodell auf den Residuen
- Bias-Korrektur nur für Sa-Zieltage
**Wichtig:** jede Änderung über MEHRERE Tage gegen Leaderboard testen,
nicht nur den einen Ausreißertag.
