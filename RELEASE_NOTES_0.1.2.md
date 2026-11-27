# WetSoil 0.1.2 — Corrected branding

This maintenance release replaces the incorrect icon included with 0.1.1 with the **manually corrected WetSoil artwork** supplied and verified by the maintainer. The icon now displays the intended blue water droplet, green seedling and layered soil.

## Changes since 0.1.1

- Corrected the bundled integration/Marketplace icon at `custom_components/wetsoil/brand/icon.png` (128 × 128 px).
- Added matching `wetsoil-logo.png` at the repository root and a high-resolution `docs/wetsoil-logo.png` for the project documentation.
- Updated the English README and German guide to reference the same approved logo artwork consistently.
- Removed the obsolete 0.1.1 publication workflow and prepared the 0.1.2 workflow.
- Updated `manifest.json` to version **0.1.2**.

## Compatibility

This release changes **branding, documentation and release metadata only**. The irrigation algorithm, entities, storage format, settings and Home Assistant automation behavior are unchanged. Existing installations and circuit configurations are preserved.

If the previous icon remains visible after updating through the Home Assistant Marketplace, restart Home Assistant and refresh the browser; icon assets may be cached.

## Experimental status and safety

WetSoil remains experimental. Its irrigation algorithm has been used privately for many years; the Home Assistant integration was developed with substantial generative AI assistance.

WetSoil does not provide an independent emergency or failsafe shutdown for irrigation hardware. Use independently tested actuator protection for pumps or valves. See the [README](https://github.com/derhopp/WetSoil#readme).

**License:** MIT.
