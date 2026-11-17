# WetSoil 0.1.0 — Initial experimental release

WetSoil is a weather-aware irrigation integration for Home Assistant with independent watering circuits, a bundled dashboard card and native Home Assistant entities.

## Highlights

- **Multi-circuit irrigation:** independent config entries/devices with configurable schedules, allowed weekdays/months, linear chaining and manual operation.
- **Weather-aware duration:** daily maximum temperature, forecast rainfall and actual measured precipitation influence the long-established, privately used Node-RED-based irrigation formula.
- **Weather provider compatibility:** prefer a full-day hourly forecast; fall back to daily forecasts when hourly data is missing or incomplete. Provider switches invalidate cached values.
- **Measured rainfall history:** Recorder-assisted backfill for daily/cumulative rain sensors, or integration of precipitation-intensity readings over the last rolling **72 hours**.
- **Bundled dashboard card:** entity pickers, de/en status messages, automatic live synchronization between cards, watering countdown, skip and actual-run history, and an explicit reset for today's run marker.
- **Native Home Assistant controls:** sensors, binary sensors, numeric settings, automatic-mode switch, manual start/stop buttons, start-time entity and precipitation-source selector.
- **New-circuit default:** **1800 seconds (30 minutes)** base watering time. Existing saved durations are preserved.
- **Consistent precision:** rainfall shown and checked to 0.01 mm; temperatures to 0.1 °C.

## Installation

For Home Assistant 2026.11+, open **Settings → Marketplace**, add `https://github.com/derhopp/WetSoil` from a repository link if it is not yet listed, install and restart Home Assistant. Add **WetSoil** under **Settings → Devices & services**; each irrigation circuit needs its own entry (name and Area). Add the bundled `custom:wetsoil-card` to a dashboard.

See the [README](https://github.com/derhopp/WetSoil#readme) and [German guide](https://github.com/derhopp/WetSoil/blob/main/docs/README.de.md) for details.

## Experimental status and safety

**Experimental software — not certified for unattended or safety-critical irrigation.** The calculation algorithm has been used privately for many years, but the Home Assistant integration is comparatively new. Substantial parts of its code, tests and documentation were created or revised with generative AI assistance.

WetSoil sends ON at the start of its own run and a single OFF at its planned end or explicit Stop. It **does not** provide an independent emergency shutoff, valve-closure verification or recovery shutoff on Home Assistant restart/unload. An interrupted run may leave actuators active. **Provide independently tested physical/automation fail-safes before operating real pumps or valves.**

## Known limitations

- Weather providers may have incomplete daily/hourly forecasts; missing data does not count as zero.
- Recorder history must be valid and sufficiently complete; the intensity history status and provider differences still need wider field testing.
- YAML-managed dashboard resources require manual JavaScript module registration.
- Additional integration, concurrent-editor, daylight-saving and hardware-in-the-loop scenarios remain under testing.

Track ongoing work and report issues in [GitHub Issues](https://github.com/derhopp/WetSoil/issues). All five CI jobs (Python/frontend, Home Assistant import/runtime, hassfest and Marketplace/HACS validation) passed before release publication.

**License:** MIT.
