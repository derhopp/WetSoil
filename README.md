# WetSoil

**Weather-aware irrigation for Home Assistant.** Schedule individual watering circuits, factor in weather and measured rainfall, and manage everything from a dedicated dashboard card.

![WetSoil — water droplet, green seedling and soil](custom_components/wetsoil/brand/icon.png?raw=1&v=2)

[![CI](https://github.com/derhopp/WetSoil/actions/workflows/checks.yml/badge.svg?branch=main)](https://github.com/derhopp/WetSoil/actions/workflows/checks.yml)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.11%20tested-41BDF5)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Experimental](https://img.shields.io/badge/Status-Experimental-orange.svg)](#project-status-and-safety)

**Project status: Experimental.** The underlying irrigation calculation has been used privately and refined over many years, originally in Node-RED. **The Home Assistant integration is newer, partly AI-generated, and still under active testing.** It is not a certified irrigation controller or a substitute for independent actuator protection.

[Deutsch](docs/README.de.md) · [Architecture](docs/architecture.md) · [Issues and feature requests](https://github.com/derhopp/WetSoil/issues) · [CI checks](https://github.com/derhopp/WetSoil/actions)

## Brand icon

WetSoil's icon combines **water** (the blue droplet), **soil** (brown earth layers) and **plant growth** (green seedling). The illustration above is the corrected, user-supplied artwork. This image replaces the incorrect icon on `main` for review; the published **0.1.1** release is unchanged.

## Highlights

- **One integration instance per watering circuit** — independent settings, Home Assistant device, entities and run state. Multiple circuits can use the same Weather Entity; valve switches must be assigned exclusively.
- **Weather-informed watering** — daily maximum forecast temperature, today's forecast rain, optional rain binary sensor and actual precipitation history.
- **Three measured-rain options** — daily rain-total sensor, cumulative rain counter or measured precipitation intensity integrated over the rolling last 72 hours.
- **Flexible schedules and chaining** — allowed weekdays/months, local start time, linear successor chains and manual control.
- **WetSoil dashboard card** — entity pickers, settings, forecast and history diagnostics, live multi-card synchronization, running countdown, readable German/English messages and reset of today's run marker.
- **Native Home Assistant entities** — sensors, binary sensors, number controls, automatic-mode switch, buttons, start-time entity and precipitation-type selector.
- **Transparent operating decisions** — weather factors, calculated duration versus actually planned duration, skipped attempts and actual starts are kept separate.

> **Before connecting water hardware:** WetSoil does **not** implement an independent emergency or safety shutoff. A Home Assistant restart, software error or unreachable actuator can leave a valve on. Provide separate, tested fail-safe protection. See [Project status and safety](#project-status-and-safety).

## Install with Home Assistant Marketplace

WetSoil targets Home Assistant **2026.11** and later compatible versions. Home Assistant's built-in **Marketplace** replaces the former HACS experience. Until WetSoil appears in the public Marketplace catalog, add it **from its repository link**.

1. Open **Settings → Marketplace** in Home Assistant.
2. Use the Marketplace option to **add from a link** and enter: **https://github.com/derhopp/WetSoil**. Select the integration source if prompted.
3. Install WetSoil, then **restart Home Assistant**.
4. Open **Settings → Devices & services → Add integration → WetSoil**.
5. Enter the **circuit name** and choose a Home Assistant **Area**. Repeat for each additional circuit.
6. Add the **WetSoil** dashboard card (`custom:wetsoil-card`) and choose the corresponding circuit in the card editor.

The card ships **inside this repository**; no separate card download or resource setup is required for UI-managed Lovelace resources. WetSoil registers its JavaScript module automatically on integration setup, retries registration at Home Assistant startup, and updates the existing URL when the bundled card changes. Following an integration upgrade, reload the dashboard/browser if it still shows an older card.

### Dashboard resource registration

| Dashboard resource configuration | What WetSoil does |
| --- | --- |
| **UI-managed resources (storage mode)** | Automatically creates or updates **one** JavaScript module resource, without changing unrelated entries |
| **YAML-managed resources / read-only configuration** | Does not modify the configuration; **you must register the resource manually** |

**Verify UI-managed registration:** After installing the integration and restarting Home Assistant, open your dashboard's resource management view (if available). There should be **one** JavaScript module entry whose URL begins with `/wetsoil/wetsoil-card.js`. The `?v=...` suffix is expected: it identifies the bundled JavaScript version for cache invalidation. You can then add `custom:wetsoil-card` to the dashboard; there is no separate frontend repository to install.

**YAML fallback:** Add the module URL `/wetsoil/wetsoil-card.js` to your manually managed Lovelace resources, for example:

```yaml
resources:
  - url: /wetsoil/wetsoil-card.js
    type: module
```

If the card still reports an unknown custom element, check that the WetSoil integration is loaded, that the resource URL is reachable, and that your resource management mode matches the instructions above. Reload the dashboard/browser after correcting the entry. Do **not** add a second manual resource if an automatic WetSoil resource is already present.

**Existing HACS installations:** Update the integration through the installation mechanism available in your Home Assistant setup. WetSoil configuration is stored separately from the dashboard layout; you do not need to recreate your circuits just to upgrade.

## Configure your circuits

The integration setup form intentionally asks for **name and Area only**. All irrigation settings are configured on the circuit's WetSoil card, with selected values also available through native Home Assistant entities. Each circuit is isolated from the others.

| Setting | Default for **new** circuits | Notes |
| --- | ---: | --- |
| Automatic watering | Off | Turn on after configuring and checking the circuit |
| Base watering duration | **1800 s (30 min)** | Weather algorithm adjusts this starting duration |
| Maximum runtime | 3600 s (60 min) | Upper bound for a WetSoil-owned run, **not an external safety shutoff** |
| Today's forecast rain limit | 2.00 mm | Watering blocked at or above the threshold |
| Historical average rain limit | 2.00 mm/day | Based on valid measured precipitation |
| Lower temperature threshold | 23.0 °C | Watering requires a higher temperature |
| Upper temperature threshold | 35.0 °C | Temperature factor capped at 1.5 |
| Allowed days | Monday–Saturday | Editable per circuit |
| Allowed months | April–October | Editable per circuit |
| Absolute start time | 08:00 | Local Home Assistant timezone |
| Watering valves | None | Select one or more `switch` entities |
| Predecessor | None | Optional for chained circuits |
| Weather / rain sensors | None | Select suitable existing Home Assistant entities |

**Changing the default to 1800 seconds affects newly created circuits only.** Already stored base-duration values remain unchanged on upgrade. Existing users can set **Base watering duration** in the card or the corresponding native number entity.

### Weather inputs

Select a `weather` entity. WetSoil prefers a **complete hourly forecast for the entire current local calendar day**. If the provider does not support hourly forecasts or the hourly data cannot cover the complete day, it falls back to **daily** forecasts. Past hours are not silently treated as rain-free. Forecast values are converted to °C and mm where supported, and switching weather providers invalidates the previous provider's forecast cache.

A `binary_sensor` reporting rain is **optional**. If it is configured, WetSoil compares its rain state with the Weather Entity. Unknown states or contradictory observations block **new** watering starts; they do not forcibly stop an already running circuit.

### Measured precipitation: choose one source type

Select a **precipitation sensor** and its **sensor type**:

| Sensor type | Typical sensor | Historical input |
| --- | --- | --- |
| **Daily** (`daily`) | Today's accumulated rainfall | Previous three **completed local calendar days** |
| **Cumulative** (`total`) | Monotonically increasing rain total | Differences across the previous three completed local days |
| **Intensity** (`intensity`) | Current precipitation rate, e.g. `mm/h` | **Exactly the previous rolling 72 elapsed hours** |

For `daily` and `total`, WetSoil uses its own samples and attempts to backfill complete days from Home Assistant **Recorder**. Cumulative counter resets, missing periods, inconsistent units and insufficient coverage do not count as zero rain.

For `intensity`, WetSoil integrates the recorded rain rate over the last 72 elapsed hours, then divides the resulting total millimeters by three to obtain an equivalent mean in **mm/day**. Supported rate units include `mm/h`, `mm/d`, `cm/h`, `cm/d`, `in/h` and `in/d`. The fixed 72-hour window is independent of daylight-saving clock changes.

**Recorded history matters:** Recorder must contain a valid state at the beginning of the requested period and valid readings throughout. Missing or invalid history produces an **unavailable** result rather than a false dry reading. The Card shows readable history diagnostics such as **“72-hour precipitation intensity history complete”**. With no precipitation sensor configured, historical rainfall cannot be established.

## How watering is calculated

WetSoil ports a privately established Node-RED irrigation calculation. It checks for available data, no detected/uncertain rain, and these strict conditions:

- **Forecast precipitation today** is below its configured daily limit.
- **Measured historical average** is below its configured limit.
- **Forecast daily maximum temperature** exceeds the lower threshold.

When eligible, WetSoil combines a temperature factor with two rain factors:

`rain factor = 1 − rainfall / rainfall limit`

`temperature factor = 1 + (temperature − lower limit) / (2 × (upper limit − lower limit))`, capped at **1.5** at/above the upper temperature threshold.

`duration = round(base duration × temperature factor × today's rain factor × historical rain factor)`

The duration is at least **half the base duration** when weather eligibility is satisfied, and the effective planned duration is additionally capped by **Maximum runtime**. With a new circuit's base duration of 1800 s, the half-base floor is **900 s**.

Precipitation is **displayed and compared** at **two decimal places** and temperature at **one decimal place**. Configured thresholds use the same precision; raw Recorder samples are not rewritten. Missing readings stay unavailable, never automatically become zero.

The dashboard distinguishes **weather-calculated duration** from **actually planned duration**, which also depends on automation, valves and calendar eligibility.

## Scheduling, chaining and manual operation

A circuit can start at an **absolute local time** on allowed days/months or **after another circuit**. Chains are linear: at most one successor per predecessor, with circular chains and shared valve assignments rejected.

An automatic slot that was **skipped** because automation was disabled, conditions were unsuitable or sensor information was missing is **not** marked as watered. You may move the start time to a later valid time on the same day and enable automation. A successful **automatic start** is recorded as today's actual automatic run; another automatic run is blocked until the run marker is explicitly reset.

The dashboard shows the last actual start, whether the circuit ran today, the latest skipped attempt and its reason. **Reset today's run status** clears the relevant day's markers without operating any valve or starting an immediate run. Manual starts are recorded but do not consume the automatic daily allowance. A manual stop does **not** start the next circuit. Regular skipped automatic circuits may advance to their successor.

The card receives live updates from Home Assistant and displays a countdown. This is **display only**: watering timers and commands run in the backend, independently of the browser.

## Home Assistant entities and diagnostics

Each configured circuit has its own device and entities, including:

| Type | Purpose |
| --- | --- |
| `sensor` | Status, reason, temperature, today's precipitation, measured rain average, factors, duration, next start, configuration and recent events |
| `binary_sensor` | Watering in progress, watering allowed, raining |
| `number` | Base time, rain limits, temperature limits, maximum runtime |
| `switch` | Automatic watering enabled/disabled |
| `button` | Manual start and immediate stop |
| `time` | Scheduled absolute start time |
| `select` | Precipitation source type: daily, cumulative or intensity |

Known status and rejection codes appear as readable English/German descriptions on the card. Selected native status sensors expose their underlying machine code as a `raw_code` attribute for diagnostics and automations. The interface updates multiple cards referring to the same circuit without a manual refresh.

## Project status and safety

**Experimental integration · Established private algorithm · AI-assisted implementation**

- The **irrigation algorithm** has been used and refined privately over many years. This does **not** establish the reliability of every new Home Assistant integration feature.
- The **Home Assistant integration** is experimental. It has automated unit tests, frontend tests, integration checks and Home Assistant runtime tests, with user-confirmed functional tests in a real Home Assistant installation. These do **not** constitute hardware certification or unattended-operation approval.
- **AI disclosure:** A substantial portion of the integration source code, tests and documentation was created or modified with assistance from generative AI. Human review, testing and responsibility for operation remain essential.
- **Independent actuator safety is mandatory for physical irrigation:** WetSoil sends a single Home Assistant `switch.turn_on` command for a WetSoil-owned run, waits for the configured duration, then sends one `switch.turn_off`. It does **not** require instantaneous ON feedback and does **not** retry emergency shutdowns, confirm physical valve closure or perform recovery-based safety intervention.
- WetSoil **does not switch off externally controlled actuators** during idle operation or at integration startup/unload. An interrupted run is not resumed after a Home Assistant restart. A partial command failure may leave a switch on. Provide an independent tested shutdown mechanism for lost connectivity, power interruptions, stuck actuators and Home Assistant failures.

**Start with virtual/test switches.** Do not connect an unattended pump or real irrigation valve until independent fail-safe measures have been tested.

## Compatibility and known limitations

- **Home Assistant:** Developed and CI-tested against Home Assistant **2026.11.0**. Compatibility with other releases and all weather providers is not guaranteed.
- **Weather:** Some providers expose only future hourly slots; a complete daily forecast is then needed for valid today's precipitation.
- **Recorder:** Historical measurements are accepted only when source and coverage are sufficient. The intensity mode requires usable recorded 72-hour data.
- **Dashboard:** Automatic resource registration applies to **UI-managed Lovelace resources**. YAML-managed resources require manual registration. Concurrent edits to the same circuit in separate editor tabs have not been fully conflict-tested.
- **Localization:** German and English are supported for known statuses and card messages; some uncommon upstream/Home Assistant errors may still show diagnostic detail.
- **Scheduling and tests:** Additional timezone, chain-midnight, concurrency and hardware-in-the-loop scenarios remain under investigation. See the open Issues for exact scope.

## Support, development and license

Found a bug or missing feature? [Open a GitHub issue](https://github.com/derhopp/WetSoil/issues) with the WetSoil commit/version, Home Assistant version, affected circuit, reproduction steps, relevant entity states and log messages. **Never publish credentials or access tokens.**

Development happens on [`main`](https://github.com/derhopp/WetSoil/tree/main). The current integration release is **0.1.1**. See [GitHub Releases](https://github.com/derhopp/WetSoil/releases) for versioned downloads and release notes.

WetSoil is licensed under the [MIT License](LICENSE). Contributions, testing reports and constructive feedback are welcome.
