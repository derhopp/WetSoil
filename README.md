# WetSoil

## Status / Entwicklungsstand

**Development preview — NOT suitable for irrigation hardware.** The repository currently contains a pure, tested Node-RED algorithm, a name/area configuration flow, backend-stored settings and a read-only Lovelace card. Valve control, historical measured rainfall, scheduling, chaining and automatic resource registration are **not implemented**. All automatic and manual valve actions are intentionally disabled.

**Entwicklungsstand:** Noch keine funktionsfähige Bewässerungssteuerung. Derzeit nur Grundstruktur, Berechnung, gespeicherte Konfiguration und eine Status-Card. Keine Ventile anschließen oder unbeaufsichtigt betreiben.

## HACS installation (preliminary)

Add https://github.com/derhopp/WetSoil as a custom **Integration** repository in HACS, install, restart Home Assistant, then add WetSoil under Settings → Devices & services. Only the circuit name and Area are requested.

The frontend JavaScript is served at /wetsoil/wetsoil-card.js. Under Dashboard → Resources, add this path as a JavaScript module if necessary. Add the card via the graphical card picker, or with:

    type: custom:wetsoil-card
    entry_id: YOUR_CONFIG_ENTRY_ID

## Safety

The backend rejects enabling automatic watering. Manual start and stop controls are unimplemented and report errors instead of creating the false impression of switching physical valves. Measurements and weather freshness are not yet available. HACS/HA installation and runtime compatibility have not yet been manually confirmed.
