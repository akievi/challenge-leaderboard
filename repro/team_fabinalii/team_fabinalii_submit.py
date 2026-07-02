"""
team_fabinalii_submit.py — Reproduzierbare 24h-DE-Lastprognose (Team Fabinalii).

Erzeugt die Submission-CSV, die auf
https://bartzbeielstein.github.io/challenge-leaderboard/ für Team
`team_fabinalii` eingereicht wurde. Standalone-Kopie der Pipeline aus
`lecture/12_challenge.ipynb` (cell-4) des Kursrepos.

MODELL (v2.0):
  - ForecasterRecursive + LightGBM (deterministisch, random_state=2026).
  - Hybrid-Lags nach Wochentag des Zieltags:
        Mo/Sa/So -> [24,48,72,96,120,144,168]   (reine Tageslags)
        Di–Fr    -> [1,2,3,24,168]                (Basis-Lags)
  - Trainingsfenster: 730 Tage (rollend, endet bei target-1h).
  - Exogene: Kalender (hour/dayofweek/month) + Open-Meteo-Wetter.
  - CR-3-Robustheit: Plausibilitäts-Klammer (20.000–100.000 MW) + Lücken-
    Interpolation.

REPRODUKTION (offline, --snapshot):
  Trainiert aus dem beigelegten Snapshot `data/interim/energy_load_snapshot.parquet`
  statt live von ENTSO-E; Wetter aus `data/interim/weather_snapshot.parquet`.
  Deterministisch -> Ergebnis muss `expected/<D>.csv` (Byte-Vergleich via
  SHA256SUMS) entsprechen.

LIVE (default):
  Lädt aktuelle ENTSO-E-Last + Open-Meteo-Wetter-Forecast (ENTSOE_API_KEY nötig).

Aufruf:
  # Offline-Reproduktion des Referenztags:
  python team_fabinalii_submit.py --snapshot --target-date 2026-06-27 --out out.csv
  # Live-Prognose für einen Zieltag:
  python team_fabinalii_submit.py --target-date 2026-07-05 --out out.csv
"""
import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from lightgbm import LGBMRegressor

from spotforecast2_safe import LinearlyInterpolateTS, ExogBuilder, Period
from spotforecast2_safe.forecaster.recursive import ForecasterRecursive

_HERE = Path(__file__).resolve().parent

_LGBM_PARAMS = dict(
    n_estimators=400, learning_rate=0.05, num_leaves=63,
    random_state=2026, deterministic=True, force_col_wise=True, verbose=-1,
)
_BASE_LAGS = [1, 2, 3, 24, 168]
_DAILY_LAGS = [24, 48, 72, 96, 120, 144, 168]
_DAILY_LAG_WEEKDAYS = {0, 5, 6}  # Mo, Sa, So
_LOAD_MIN_MW, _LOAD_MAX_MW = 20_000, 100_000
_PERIODS = [
    Period(name="hour",      n_periods=24, column="hour",      input_range=(0, 23)),
    Period(name="dayofweek", n_periods=7,  column="dayofweek", input_range=(0, 6)),
    Period(name="month",     n_periods=12, column="month",     input_range=(1, 12)),
]


def _select_lags(target: datetime) -> list:
    return _DAILY_LAGS if target.weekday() in _DAILY_LAG_WEEKDAYS else _BASE_LAGS


def _clamp(y: pd.Series) -> pd.Series:
    bad = (y < _LOAD_MIN_MW) | (y > _LOAD_MAX_MW)
    if bad.any():
        print(f"[CR-3] {int(bad.sum())} implausible Lastwert(e) verworfen: "
              f"{list(y.index[bad].strftime('%Y-%m-%d %H:%M'))}")
        y = y.mask(bad)
    return y


def _make_exog(y_index_min, target_hours, weather) -> pd.DataFrame:
    exog_cal = ExogBuilder(periods=_PERIODS, country_code="DE").build(
        start_date=y_index_min, end_date=target_hours[-1],
    )
    exog = exog_cal.join(weather, how="left")
    exog[weather.columns] = exog[weather.columns].ffill().bfill()
    exog.index = pd.DatetimeIndex(exog.index, freq="h")
    return exog


def _fit_predict(y, exog, target_hours, lags):
    train_idx = y.index.intersection(exog.index)
    y_train = y.loc[train_idx].copy()
    y_train.index = pd.DatetimeIndex(y_train.index, freq="h")
    fc = ForecasterRecursive(estimator=LGBMRegressor(**_LGBM_PARAMS), lags=lags)
    fc.fit(y=y_train, exog=exog.loc[train_idx])
    horizon = int((target_hours[-1] - y_train.index[-1]) / pd.Timedelta(hours=1))
    fidx = pd.date_range(y_train.index[-1] + pd.Timedelta(hours=1),
                         periods=horizon, freq="h", tz="UTC")
    return fc.predict(steps=horizon, exog=exog.loc[fidx]).loc[target_hours]


def _load_offline(target, train_start, train_end, target_hours):
    """Trainings-Last + Wetter aus beigelegten Snapshots (offline, deterministisch)."""
    load_snap = _HERE / "data" / "interim" / "energy_load_snapshot.parquet"
    wx_snap = _HERE / "data" / "interim" / "weather_snapshot.parquet"
    y = pd.read_parquet(load_snap)["load_mw"]
    y.index = pd.to_datetime(y.index, utc=True)
    y = _clamp(y).loc[train_start:train_end]
    y = y.loc[:y.last_valid_index()]
    y = LinearlyInterpolateTS(on_missing="raise").fit_transform(y)
    y.index = pd.DatetimeIndex(y.index, freq="h")
    weather = pd.read_parquet(wx_snap)
    weather.index = pd.to_datetime(weather.index, utc=True)
    return y, weather


def _load_live(target, train_start, train_end, target_hours):
    """Trainings-Last live von ENTSO-E + Wetter-Forecast von Open-Meteo."""
    from spotforecast2_safe.data.fetch_data import fetch_data, get_data_home
    from spotforecast2_safe.downloader.entsoe import download_new_data
    from spotforecast2_safe.weather import WeatherService
    download_new_data(api_key=os.environ["ENTSOE_API_KEY"], country_code="DE",
                      start=train_start.strftime("%Y%m%d%H%M"),
                      end=train_end.strftime("%Y%m%d%H%M"), force=True)
    interim = get_data_home() / "interim" / "energy_load.csv"
    df = fetch_data(filename=str(interim))
    df.index = pd.to_datetime(df.index, utc=True)
    col = next(c for c in df.columns if "Actual" in c and "Load" in c)
    y = _clamp(df[col].astype(float).resample("h").mean()).loc[train_start:train_end]
    y = y.loc[:y.last_valid_index()]
    y = LinearlyInterpolateTS(on_missing="raise").fit_transform(y)
    y.index = pd.DatetimeIndex(y.index, freq="h")
    ws = WeatherService(latitude=51.165, longitude=10.451,
                        cache_path=get_data_home() / "weather_live.parquet", use_forecast=True)
    weather = ws.get_dataframe(start=y.index.min(), end=target_hours[-1], freq="h", fill_missing=True)
    return y, weather


def main():
    ap = argparse.ArgumentParser(description="Team Fabinalii 24h load forecast")
    ap.add_argument("--target-date", required=True, help="Zieltag YYYY-MM-DD (UTC)")
    ap.add_argument("--days-back", type=int, default=730, help="Trainingsfenster in Tagen")
    ap.add_argument("--snapshot", action="store_true",
                    help="Offline aus beigelegten Snapshots reproduzieren (kein API-Key)")
    ap.add_argument("--out", default="submission.csv", help="Ausgabe-CSV")
    args = ap.parse_args()

    target = datetime.fromisoformat(args.target_date).replace(tzinfo=timezone.utc)
    train_end = target - timedelta(hours=1)
    train_start = train_end - timedelta(days=args.days_back)
    target_hours = pd.date_range(target, periods=24, freq="h", tz="UTC")
    lags = _select_lags(target)

    loader = _load_offline if args.snapshot else _load_live
    y, weather = loader(target, train_start, train_end, target_hours)
    exog = _make_exog(y.index.min(), target_hours, weather)
    y_pred = _fit_predict(y, exog, target_hours, lags)

    out = pd.DataFrame({
        "timestamp_utc": target_hours.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "forecast_mw": y_pred.values.round(2),
    })
    out.to_csv(args.out, index=False)
    wd = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][target.weekday()]
    lset = "Tageslags" if lags is _DAILY_LAGS else "Basis-Lags"
    mode = "offline/snapshot" if args.snapshot else "live"
    print(f"[{mode}] {args.target_date} ({wd} -> {lset}), days_back={args.days_back}")
    print(f"Geschrieben: {args.out}  (Mittel {y_pred.mean():,.0f} MW)")


if __name__ == "__main__":
    main()
