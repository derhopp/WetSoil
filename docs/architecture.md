# Architecture and technical safety

## Components

- const.py: per-instance defaults and strict input validation
- config_flow.py: initial name / area configuration only
- algorithm.py: isolated Node-RED-equivalent weather calculation
- weather.py: forecast values, rain state, and persistent measured rainfall history
- validation.py: cross-instance valve uniqueness and chain graph validation
- schedule.py: timezone-aware helper for DST transitions and future calendar starts
- controller.py: circuit execution, ownership tracking, explicit stops, absolute starts and chains
- __init__.py: Home Assistant setup, admin-only WebSocket write commands, static frontend hosting
- sensor.py, number.py, switch.py, binary_sensor.py and button.py: HA entities
- frontend/wetsoil-card.js: bilingual central editing and operational dashboard

## Storage and API

Each circuit is a config entry, with a stable entry ID and unique ID. Settings are stored through a versioned Home Assistant Store; weather history uses a separate Store. The dashboard uses WebSocket commands wetsoil/list, wetsoil/update and wetsoil/action. Only admins can edit configuration or issue start/stop commands via that WebSocket API. The browser does not control watering timing; this is entirely backend-driven.

## Start gates and external safety ownership

Unknown rain, incomplete measured precipitation history and invalid forecast values prevent automatic starts. Manual starts remain blocked if rain is detected or cannot be ruled out. WetSoil serializes its own switch operations but does **not** retry shutdowns, interrupt a run on changed rain/valve states, or switch anything OFF on unload or restart. Off commands are issued only after normal expiry or explicit stop of a WetSoil-owned run. The Home Assistant switch state is feedback, not proof of physical valve closure. The user must provide independent fail-safe protection. No completed real-world safety test is claimed.

## Historical sensor model

The daily mode accepts a nondecreasing day counter, and total mode accepts a nondecreasing cumulative counter. Resets and gaps invalidate a local day. Only three *completed* preceding local days enter the mean; today is omitted. Sampling roughly every five minutes requires a minimum observation coverage per day. Recorder backfill is attempted for the three prior completed local days using a history query off the event loop. The aggregation accepts only dense, monotonic, unit-consistent samples, validates real local-day durations on DST changes, and merges valid values without overwriting stored completed days. Recorder records may be sparse even for otherwise healthy sensors; no data is fabricated and a three-day local warm-up may still be needed. Day provenance (observed/recorder) is exposed to the WebSocket API.

## Remaining risks

The Home Assistant runtime, frontend resource registration and live valve behavior must be tested together on a real HA instance. DST and midnight-spanning chains, weather-provider differences, stop races and power interruption recovery need more integration tests. The frontend static route is bundled with the Python integration but Dashboard Resources may need manual configuration.


## Explicit actuator ownership (2026-11-16)

WetSoil only controls actuators associated with an active, internally started run. No startup, periodic, rain-triggered, state-triggered, recovery or unload-time shutdowns remain. Normal expiry and explicit stop send one OFF request for switches WetSoil switched on. On partial start failure, owned devices can only be switched off via an explicit Stop. On unload, timers are cancelled without changing any actuator states. After restart, prior runs are not resumed and no OFF requests are emitted. Independent user-operated protection is mandatory.


## Weather forecast provider switching

Weather caching is scoped to the selected entity and local date, with the cache reset on provider changes. The integration attempts a complete-day hourly forecast first and falls back to a valid daily forecast. Incomplete hourly precipitation is never treated as an entire day's total. Forecast source, last refresh, and error state are included in the runtime snapshot. A stale/unavailable provider yields unavailable values rather than retaining a previous entity's data.
