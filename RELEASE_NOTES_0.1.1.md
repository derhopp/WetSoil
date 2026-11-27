# WetSoil 0.1.1 — New branding

This maintenance release introduces a refreshed **WetSoil brand icon**: a blue water droplet surrounding a green seedling and layered soil. It is included in the integration's `brand/icon.png` and displayed in both English and German documentation.

## Changes

- Replaced the previous Home Assistant / Marketplace integration icon with the user-approved new design.
- Updated the English README and German guide with the new branding and current release version.
- Increased the integration version to **0.1.1**.

## Compatibility

- Configuration, irrigation algorithm, entities, service behavior and dashboard functionality are **unchanged** from the previous `main` code.
- Existing circuits retain their settings; no migration is required.
- Home Assistant may cache the old integration icon. After upgrading through Marketplace/HACS, restart Home Assistant and refresh the browser if the icon is still old.

## Experimental status and safety

WetSoil remains **experimental**. Its underlying irrigation algorithm has been used privately for years, but the newer integration was substantially developed with generative AI assistance and is not certified for unattended irrigation.

**Independent actuator protection remains mandatory for real hardware.** WetSoil does not provide emergency valve shutdown or physical closure confirmation. See the [README](https://github.com/derhopp/WetSoil#readme) for limitations.

**License:** MIT.
