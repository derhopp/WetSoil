# WetSoil — Home Assistant irrigation integration

WetSoil is a weather-dependent multi-circuit irrigation integration with a bundled custom Lovelace card.

**EXPERIMENTAL — NOT APPROVED FOR UNATTENDED IRRIGATION.** Python tests, Home Assistant module imports and hassfest have passed CI. Real Home Assistant installations, hardware valve control, full chain operation, and browser compatibility have NOT been verified. HACS currently fails metadata validation because this GitHub repository lacks a description and valid topics.

[Deutsch](docs/README.de.md) | [Architecture](docs/architecture.md)

## Installation

1. In HACS, add https://github.com/derhopp/WetSoil as a custom repository of type Integration.
2. Install the integration and restart Home Assistant.
3. Go to Settings → Devices & services → Add integration → WetSoil.
4. Enter a name and select an existing Area. Create one entry per circuit.
5. Under Dashboard → Resources, add JavaScript module /wetsoil/wetsoil-card.js. The JS file is provided by the same integration repository, not a separate card repository.
6. Add the custom:wetsoil-card from the Dashboard editor and select a circuit in its graphical editor.

Installation is preliminary until tested with a running instance. Refresh the browser after frontend updates.

## Configuration

All major settings can be edited in the WetSoil card; the Home Assistant Config Flow asks only Name and Area. A central versioned storage model persists configuration independently of dashboard layouts. The custom authenticated WebSocket API restricts modifications and watering actions to Home Assistant admins.

Defaults: automation off; base time 30 seconds; forecast rain limit 2 mm; historical average rain limit 2 mm/day; lower temperature 23 °C; upper 35 °C; max safety time 3600 s; Monday–Saturday; April–October; 08:00 start; no chain; no valves.

Different circuits can share one weather entity, but assigned valve switches must be exclusive. A linear chain has one absolute start and at most one predecessor/successor for each entry.

## Weather and historical rainfall

The weather entity supplies daily forecast temperature and precipitation where the provider supports these. Rainfall and temperature units are converted to mm and °C. Hourly forecast fallback is not yet implemented.

Actual rainfall history comes only from a compatible selected sensor. Daily total and cumulative counter modes are supported, with approximately five-minute sampling and a persistent Store. After enabling a sensor, at least **three fully observed days** are required before the history gate can allow watering. Gaps, unknown states and counter resets invalidate observations. The integration does not backfill history from Recorder yet. Forecasts are never substituted for observed history.

Current rain is evaluated from the weather entity and optional binary rain sensor; unknown sources never count as confirmed dry.

## Node-RED algorithm

Watering is weather-eligible ONLY IF observed three-day mean is strictly below its threshold, forecast daily precipitation is strictly below its threshold, daily maximum temperature is strictly greater than the lower threshold, and no rain is confirmed. A missing value is unavailable, not zero.

Below the upper temperature threshold, temperature factor is 1 + (T - lower) / (2 * (upper - lower)); at or above it the factor is 1.5. Rainfall factors equal 1 - measured / threshold and 1 - forecast / threshold. The duration is JavaScript Math.round(base time * temperature factor * both rain factors), at least half the base time. The card distinguishes computed and effective scheduled duration, including calendar/automatic gates.

## Safety and operating notes

Manual watering bypasses month, weekday and automatic-enabled restrictions; it does not bypass rain veto, the 3600-second default safety ceiling or occupied valves. Manual starts never trigger chains. Automatically skipped circuits forward their chains; manually stopped or safety-aborted runs do not.

Valve commands are best-effort Home Assistant switch service calls with bounded timeouts and retries, and available entity feedback is checked. A successful service call does **not** prove the valve has physically closed. Use independent hardware safety measures. After restart interrupted watering must not automatically resume.

## Known limitations

- No successful end-to-end running Home Assistant / physical valve test.
- No Recorder backfill, no hourly forecast fallback and no automatic Lovelace resource registration.
- Some native backend entity labels and diagnostics are still English.
- Integration-level concurrency, daylight-saving-time and recovery testing remains incomplete.
- HACS validation requires configuring the repository About description and Topics on GitHub (not files in this repository).

GitHub Actions check Python tests, source imports, frontend syntax, hassfest and HACS. See https://github.com/derhopp/WetSoil/actions. No tags/releases were created.
