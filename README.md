# WetSoil — Home Assistant irrigation integration

WetSoil is a weather-dependent multi-circuit irrigation integration with a bundled custom Lovelace card.

**EXPERIMENTAL — NOT APPROVED FOR UNATTENDED IRRIGATION.** Python tests, Home Assistant module imports and hassfest have passed CI. Real Home Assistant installations, hardware valve control, full chain operation, and browser compatibility have NOT been verified. HACS metadata validation has passed in recent CI runs.

[Deutsch](docs/README.de.md) | [Architecture](docs/architecture.md)

## Installation

1. In HACS, add https://github.com/derhopp/WetSoil as a custom repository of type Integration.
2. Install the integration and restart Home Assistant.
3. Go to Settings → Devices & services → Add integration → WetSoil.
4. Enter a name and select an existing Area. Create one entry per circuit.
5. With UI-managed Lovelace resources, WetSoil registers and cache-versions `/wetsoil/wetsoil-card.js` automatically. For YAML-managed resources, add the JavaScript module `/wetsoil/wetsoil-card.js` manually and reload resources. The bundled JS is not a separate repository.
6. Add the custom:wetsoil-card from the Dashboard editor and select a circuit in its graphical editor.

Installation is preliminary until tested with a running instance. Refresh the browser after frontend updates.

## Configuration

All major settings can be edited in the WetSoil card; the Home Assistant Config Flow asks only Name and Area. A central versioned storage model persists configuration independently of dashboard layouts. The custom authenticated WebSocket API restricts modifications and watering actions to Home Assistant admins.

Defaults: automation off; base time 30 seconds; forecast rain limit 2 mm; historical average rain limit 2 mm/day; lower temperature 23 °C; upper 35 °C; max safety time 3600 s; Monday–Saturday; April–October; 08:00 start; no chain; no valves.

Different circuits can share one weather entity, but assigned valve switches must be exclusive. A linear chain has one absolute start and at most one predecessor/successor for each entry.

## Weather and historical rainfall

Forecast selection now attempts a complete hourly forecast for the **entire current local calendar day** first; if hourly forecasts are unsupported or incomplete, it falls back to the provider's daily forecast. Both temperature and rain values are converted to °C and mm. Changing the selected Weather Entity invalidates the cache and requests the new provider immediately. Values are never retained from the previous provider. For hourly forecasts that begin only at the current hour, the daily fallback is intentionally used, since past hourly rain cannot be assumed zero.

Actual rainfall history comes only from a compatible selected sensor. Daily total and cumulative counter modes are supported. WetSoil maintains five-minute local samples and now attempts to backfill the previous three completed local days using **Home Assistant Recorder** when available. Recorder can store only state changes; a constant or infrequently updated sensor may not provide sufficient evidence of day-long coverage. Backfill is therefore accepted only for sufficiently dense, continuous, unit-consistent observations covering the local day's boundaries (including DST). Incomplete days, resets, unsupported units, missing Recorder and sensor changes are treated as unavailable, never zero. No forecast values are substituted for actual observations. The source of each accepted day is exposed in the WetSoil status API. If Recorder lacks complete samples, a multi-day warm-up remains necessary.

Current rain is evaluated from the weather entity and optional binary rain sensor; unknown sources never count as confirmed dry.

## Node-RED algorithm

Watering is weather-eligible ONLY IF observed three-day mean is strictly below its threshold, forecast daily precipitation is strictly below its threshold, daily maximum temperature is strictly greater than the lower threshold, and no rain is confirmed. A missing value is unavailable, not zero.

Below the upper temperature threshold, temperature factor is 1 + (T - lower) / (2 * (upper - lower)); at or above it the factor is 1.5. Rainfall factors equal 1 - measured / threshold and 1 - forecast / threshold. The duration is JavaScript Math.round(base time * temperature factor * both rain factors), at least half the base time. The card distinguishes computed and effective scheduled duration, including calendar/automatic gates.

## Safety and operating notes

Manual watering bypasses month, weekday and automatic-enabled restrictions; it does not bypass rain veto, the 3600-second default safety ceiling or occupied valves. Manual starts never trigger chains. Automatically skipped circuits forward their chains; manually stopped runs do not. Weather and external valve-state changes do not interrupt running cycles.

Valve commands are best-effort Home Assistant switch service calls. There are **no** automatic shutdown retries, hardware recovery attempts or actuator-state interventions outside WetSoil-owned runs. A successful service call does **not** prove the valve has physically closed. Provide your own external safety system. On restart, interrupted watering is not resumed and actuators are not modified.

## Known limitations

- No successful end-to-end running Home Assistant / physical valve test.
- Recorder backfill is conservative and requires sufficiently dense historical measurements. Missing, excluded or sparse Recorder data cannot be recovered. Forecast daily fallback is available; providers without a complete daily forecast still yield unavailable. UI-managed Lovelace resource registration and hash-based cache invalidation are supported; YAML resources still require explicit configuration.
- Some native backend entity labels and diagnostics are still English.
- Integration-level concurrency, daylight-saving-time and recovery testing remains incomplete.
- HACS validation requires configuring the repository About description and Topics on GitHub (not files in this repository).

GitHub Actions check Python tests, source imports, frontend syntax, hassfest and HACS. See https://github.com/derhopp/WetSoil/actions. No tags/releases were created.


## Actuator ownership (updated 2026-11-16)

WetSoil **does not perform independent safety shutdown**. The user must provide external hardware/automation protection against stuck valves, power loss, Home Assistant restarts or integration unloads. WetSoil **never switches actuators off while idle**, at integration startup/unload, on rain/state changes, or during recovery. Manual control outside WetSoil remains possible. WetSoil refuses to start its own run if an assigned switch already reports ON. For **its own started run only**, a completed countdown or explicit Stop issues one normal OFF command, without confirmation retries or safety lockouts. Unload cancels WetSoil's timer **without switching actuators off**. A partial start failure may leave an actuator ON; use explicit Stop or independent controls. Do not use unattended without independently verified fail-safe measures.


### Measured precipitation intensity (rolling 72 hours)

Under **Precipitation sensor type**, choose **Actual precipitation intensity (mm/h)** for a measured rain-rate entity. Supported units include `mm/h`, `mm/d`, `in/h`, `in/d`, `cm/h` and `cm/d`. WetSoil queries the Home Assistant Recorder for **exactly the previous 72 elapsed hours** and integrates the recorded rate over time (mm/h × hours) to find the rainfall total in mm. The weather algorithm receives one-third of that total as its average rainfall in mm/day. A sample's value is held until the next recorded change, as Recorder stores state changes rather than necessarily periodic samples.

This is separate from `daily` and `total` measurement modes, which continue to use completed local calendar days. Missing initial Recorder state, invalid readings, unavailable sensor, missing Recorder, or missing history yield **unavailable**, not a dry (zero rain) estimate. The card's History source status shows `intensity_72h_complete` when the rate history was usable. Rainfall history is measured data, not weather forecasts. Recorder data can be excluded by your Home Assistant configuration.

## Actual runs versus skipped automatic attempts

From this version onward, a scheduled slot that was checked but did **not** start a valve is only a **skipped attempt**. Disabled automation, missing sensors/history, rain veto or ineligible weather do not mark that circuit as watered. An explicitly changed later HH:MM time may therefore run on the same day when the required gates become valid.

The scheduler prevents repeated attempts for the **same exact local date and HH:MM**, while a successfully started automatic watering run is marked once per local day. A completed automatic run will not run again that day unless an administrator explicitly resets the status; this protection applies independently to chained circuits. Manual starts are visible as actual starts but do not consume the automatic day's allowance.

The card displays *Started today*, *Automatic run started today*, last real start, and the latest skip reason. Its **Reset today's run status** action clears the daily markers for the selected circuit without operating actuators or immediately triggering watering; the last actual start timestamp remains available as history. Reset is blocked during active or partly started WetSoil runs. A previously saved `last_attempt` from older versions is never treated as proof of irrigation.

Automatic watering can now be enabled while weather/history information is incomplete; the scheduler will skip the upcoming slot, recording its reason, rather than rejecting the configuration. Independent hardware safety remains the user's responsibility.


## New native controls, precision and live UI

Additional Home Assistant entities are available for scheduled start time (`time`) and precipitation sensor type (`select`); the existing Number entities and configuration sensor share the same persisted backend configuration as the card. The stored settings have an explicit v2 schema marker while older configuration dictionaries are migrated by filling missing defaults. The custom card listens for `wetsoil_updated` events and displays a running countdown without affecting the backend timer. It cleans up listeners when removed from a dashboard.

**Display/threshold precision:** Forecast and historical precipitation are rounded to 2 decimal places (mm) and temperature to 1 decimal place (°C). The watering algorithm rounds measured values **before** comparison to precipitation and temperature limits, so UI and threshold results agree. These are display/decision precision values; underlying Recorder samples retain their measured precision. A few significant boundary cases may therefore change compared with the previous full-precision comparisons.

The card translates known machine-readable status/error codes into German or English; native Status, Blocking reason and Weather quality sensors also display localized text, while retaining `raw_code` in their attributes for automation use. Unknown codes remain available unmodified for diagnosis.
