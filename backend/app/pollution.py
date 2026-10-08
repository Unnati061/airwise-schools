import hashlib
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import uuid4

from .evidence_contracts import EvidenceSnapshot, PollutantPoint

LATITUDE, LONGITUDE = 28.4744, 77.5030  # Fictional Greater Noida school vicinity.
FORECAST_URL = "https://air-quality-api.open-meteo.com/v1/air-quality?" + urlencode({
    "latitude": LATITUDE, "longitude": LONGITUDE, "hourly": "pm2_5,pm10",
    "domains": "cams_global", "timezone": "UTC", "forecast_days": 5})
LIMITATIONS = ["Regional model forecast, not a station observation or measured campus condition",
               "No Indian, US or European AQI is computed or substituted",
               "Native 3-hourly model output may be interpolated to hourly; local sources are unresolved",
               "Provider does not supply model issue time; generationtime_ms is request processing, not issuance"]


def utcnow():
    return datetime.now(timezone.utc)


def freshness(snapshot, at=None):
    at = at or utcnow()
    if snapshot.mode == "REPLAY":
        return "REPLAY"
    age = at - snapshot.retrieved_at
    if age > timedelta(hours=1) or age < -timedelta(minutes=5) or not snapshot.points:
        return "STALE"
    future = [p for p in snapshot.points if p.valid_time >= at]
    if not future:
        return "STALE"
    if any(not any(p.pollutant == pollutant and p.value is not None for p in future) for pollutant in ("PM2.5", "PM10")):
        return "MISSING_VALUES"
    return "FRESH"


def parse_forecast(raw, retrieved, raw_hash):
    if raw.get("utc_offset_seconds") != 0:
        raise ValueError("Expected UTC forecast")
    units = raw["hourly_units"]
    if any(units.get(k) not in ("\u03bcg/m\u00b3", "\u00b5g/m\u00b3") for k in ("pm2_5", "pm10")):
        raise ValueError("Unexpected pollutant units")
    times = raw["hourly"]["time"]
    if not times or len(times) > 144:
        raise ValueError("Unexpected forecast horizon")
    points = []
    for key, name in (("pm2_5", "PM2.5"), ("pm10", "PM10")):
        values = raw["hourly"][key]
        if len(values) != len(times):
            raise ValueError("Mismatched forecast arrays")
        for stamp, value in zip(times, values):
            points.append(PollutantPoint(pollutant=name, value=value,
                                        valid_time=datetime.fromisoformat(stamp).replace(tzinfo=timezone.utc)))
    return EvidenceSnapshot(id=str(uuid4()), mode="LIVE", source="Open-Meteo / CAMS global",
        source_url=FORECAST_URL, requested_latitude=LATITUDE, requested_longitude=LONGITUDE,
        grid_latitude=raw["latitude"], grid_longitude=raw["longitude"], retrieved_at=retrieved,
        source_units={k: units[k] for k in ("pm2_5", "pm10")}, raw_sha256=raw_hash,
        points=points, limitations=LIMITATIONS)


def fetch_forecast():
    with urlopen(FORECAST_URL, timeout=10) as response:
        content = response.read(500_001)
    if len(content) > 500_000:
        raise ValueError("Forecast response too large")
    raw = json.loads(content)
    return parse_forecast(raw, utcnow(), hashlib.sha256(content).hexdigest()), raw


def replay_forecast():
    # Deliberately synthetic fixed-date values; never inserted into the LIVE cache.
    stamp = datetime(2026, 10, 12, tzinfo=timezone.utc)
    raw = {"label": "SYNTHETIC REPLAY ONLY", "pm2_5": 180.0, "pm10": 260.0}
    snapshot = EvidenceSnapshot(id=str(uuid4()), mode="REPLAY", source="Labelled synthetic replay fixture",
        source_url="internal://synthetic-replay-v1", requested_latitude=LATITUDE, requested_longitude=LONGITUDE,
        grid_latitude=LATITUDE, grid_longitude=LONGITUDE, retrieved_at=utcnow(),
        resolution="Synthetic fixture: no physical model or spatial resolution",
        source_units={"pm2_5": "ug/m3", "pm10": "ug/m3"},
        raw_sha256=hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest(),
        points=[PollutantPoint(pollutant=name, value=value, valid_time=stamp + timedelta(hours=i))
                for name, value in (("PM2.5", 180.0), ("PM10", 260.0)) for i in range(24)],
        limitations=["SYNTHETIC REPLAY ONLY: invented concentrations for reliable demonstration", *LIMITATIONS])
    return snapshot, raw
