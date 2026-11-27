# WetSoil 0.1.3 — Transparent branding

This maintenance release includes the maintainer's latest improvements to the WetSoil logos, with a transparent background for a cleaner appearance in Home Assistant and the documentation.

## Changes

- Updated the integration icon at `custom_components/wetsoil/brand/icon.png` (128 × 128 pixels) with the maintainer's refined artwork and transparency.
- Updated the high-resolution documentation image at `docs/wetsoil-logo.png`, preserving the same water-droplet, seedling and soil motif.
- Added regression checks for **actual transparent pixels** and visible artwork, alongside existing PNG integrity, dimension and README-reference checks.
- Updated English/German documentation and the manifest version to **0.1.3**.
- Retained the deliberate removal of the duplicate `wetsoil-logo.png` from the repository root.

## Compatibility

This release changes branding, tests, documentation and release metadata only. It does not change the irrigation algorithm, entities, scheduling, persisted settings or switch control.

After updating through Home Assistant Marketplace, restart Home Assistant and refresh the browser if an older cached icon remains visible.

## Status and safety

WetSoil remains **experimental**. Its weather-based irrigation algorithm was used privately for many years, but the newer Home Assistant integration was developed with substantial generative AI assistance.

WetSoil does not provide an independent safety shutoff or physical valve-closure verification. Protect pumps and valves using independently tested safety measures.

License: MIT.
