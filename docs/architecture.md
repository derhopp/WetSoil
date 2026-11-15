# Architecture and technical safety

## Components

- const.py: per-instance defaults and strict input validation
- config_flow.py: initial name / area configuration only
- algorithm.py: isolated Node-RED-equivalent weather calculation
- weather.py: forecast values, rain state, and persistent measured rainfall history
- validation.py: cross-instance valve uniqueness and chain graph validation
- schedule.py: timezone-aware helper for DST transitions and future calendar starts
- controller.py: circuit execution, locks, safety stops, absolute starts and chains
- __init__.py: Home Assistant setup, admin-only WebSocket write commands, static frontend hosting
- sensor.py, number.py, switch.py, binary_sensor.py and button.py: HA entities
- frontend/wetsoil-card.js: bilingual central editing and operational dashboard

## Storage and API

Each circuit is a config entry, with a stable entry ID and unique ID. Settings are stored through a versioned Home Assistant Store; weather history uses a separate Store. The dashboard uses WebSocket commands wetsoil/list, wetsoil/update and wetsoil/action. Only admins can edit configuration or issue start/stop commands via that WebSocket API. The browser does not control watering timing; this is entirely backend-driven.

## Fail-closed watering behavior

Unknown rain, incomplete measured precipitation history and invalid forecast values prevent automatic starts. Manual starts remain blocked if rain is detected or cannot be ruled out. A controller serializes valve switching and retries failed shutdowns. The Home Assistant switch state is feedback, not physical valve proof. The controller attempts OFF on unload and restart recovery. No completed real-world safety test is claimed.

## Historical sensor model

The daily mode accepts a nondecreasing day counter, and total mode accepts a nondecreasing cumulative counter. Resets and gaps invalidate a local day. Only three *completed* preceding local days enter the mean; today is omitted. Sampling roughly every five minutes requires a minimum observation coverage per day. The current version does not backfill Recorder history and may require a three-day warm-up.

## Remaining risks

The Home Assistant runtime, frontend resource registration and live valve behavior must be tested together on a real HA instance. DST and midnight-spanning chains, weather-provider differences, stop races and power interruption recovery need more integration tests. The frontend static route is bundled with the Python integration but Dashboard Resources may need manual configuration.
