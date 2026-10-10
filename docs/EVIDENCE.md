# Evidence

## Regional Forecast

Open-Meteo's air-quality API supplies CAMS global regional PM2.5/PM10 forecasts
for the fictional Greater Noida school coordinates, approximately 0.4 degree /
45 km model resolution. These are micrograms per cubic metre at forecast valid
times, not measured campus air. No Indian AQI is computed.

Snapshots retain source, coordinates, pollutant, units, valid time, retrieval
time, raw-body SHA-256 and model issue time only when actually supplied. The
provider did not supply model issue time in verified responses: retrieval age
must not be presented as model-cycle freshness. The 15-minute request cache and
one-hour retrieval-age review gate do not prove forecast accuracy.

Local station observations are unavailable. No privately configured OpenAQ key
and suitable fresh nearby station were established. No observation values are
invented. SYNTHETIC REPLAY is a separate, labelled cache/snapshot path; it never
silently fills a failed LIVE fetch.

## Policy Sources

backend/app/data/policy_excerpts.json is the authoritative curated record:
exact excerpts, URLs, jurisdiction, dates, page/paragraph IDs, verification time,
document hashes and excerpt hashes. Supplied evidence includes Ministry of
Health/NCDC guidance dated November 1, 2025 and September 2022, plus explicitly
labelled internal sample school policy.

These are advisories/internal review guidance, not a verified currently active
closure order. Pollution values never establish an active GRAP stage or school
closure. Official passages are shown beside model proposals; full evidence remains
expandable. Pasted notices are unverified until administrator review.

## Grounded Interpretation

Sydney amazon.nova-lite-v1:0 was verified with a bounded real call. Schemas reject
fabricated citation IDs and unsupported activities; ambiguous dates and unsupported
instructions require review. Only an authenticated administrator confirms
restrictions, with explicit date/weekday mapping and current input revision.

No automatic legal thresholds are implemented. Plans and metrics do not claim
measured exposure reduction, safer indoor air, health benefits or forecast accuracy.
English/Hindi text is an administrator-reviewed preview: nothing is sent.
