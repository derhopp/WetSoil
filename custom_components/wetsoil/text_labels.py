"""German/English user-facing labels; internal machine codes remain unchanged."""
from __future__ import annotations

STATUS_DE = {
    "not_checked": "Noch nicht geprüft",
    "complete": "Vollständig",
    "recorder_complete": "Recorder-Daten vollständig",
    "recorder_incomplete": "Recorder-Daten unvollständig",
    "recorder_not_loaded": "Recorder nicht aktiviert",
    "recorder_entity_excluded": "Sensor nicht im Recorder enthalten",
    "recorder_error": "Fehler beim Laden der Recorder-Daten",
    "intensity_72h_complete": "72 Stunden Niederschlagsintensität vollständig ausgewertet",
    "intensity_72h_incomplete": "72 Stunden Niederschlagsintensität unvollständig",
    "intensity_sensor_unavailable": "Niederschlagsintensitätssensor nicht verfügbar",
    "sensor_not_configured": "Kein Niederschlagssensor ausgewählt",
    "weather_unconfigured": "Keine Wetter-Entity ausgewählt",
    "weather_updating": "Wetterdaten werden aktualisiert",
    "weather_unavailable": "Wetter-Entity nicht verfügbar",
    "forecast_incomplete": "Wetterprognose unvollständig",
    "forecast_unavailable": "Keine Wetterprognose verfügbar",
    "hourly_incomplete": "Stundenprognose unvollständig",
    "daily_incomplete": "Tagesprognose unvollständig",
    "hourly_unavailable": "Stundenprognose nicht verfügbar",
    "daily_unavailable": "Tagesprognose nicht verfügbar",
    "incomplete": "Daten unvollständig",
    "ready": "Daten vollständig",
    "unavailable": "Nicht verfügbar",
    "allowed": "Bewässerung freigegeben",
    "raining": "Es regnet",
    "rain_3d_limit": "Historischer Niederschlagsgrenzwert erreicht",
    "rain_today_limit": "Heutiger Niederschlagsgrenzwert erreicht",
    "temperature_limit": "Temperaturgrenze erreicht",
    "invalid_precipitation": "Ungültiger Niederschlagswert",
    "invalid_parameters": "Ungültige Berechnungsparameter",
    "rain_or_unknown": "Regen oder unbekannter Regenstatus",
    "rain_sources_disagree": "Regensensor und Wetter-Entity widersprechen sich",
    "automatic_disabled": "Automatik deaktiviert",
    "no_valves": "Keine Ventile konfiguriert",
    "calendar_excluded": "Tag oder Monat nicht freigegeben",
    "already_running": "Bewässerung läuft bereits",
    "already_watered_today": "Heute bereits automatisch bewässert",
    "not_eligible": "Startbedingungen nicht erfüllt",
    "start_failed": "Start fehlgeschlagen",
    "stop_command_failed": "Ausschaltbefehl fehlgeschlagen",
    "valve_not_off": "Ventil ist bereits eingeschaltet oder nicht erreichbar",
    "previous_start_requires_explicit_stop": "Vorherigen Start bitte ausdrücklich stoppen",
    "manual": "Manuell",
    "auto": "Automatisch",
    "idle": "Bereit",
    "stopped": "Gestoppt",
    "starting": "Startet",
    "watering": "Bewässerung läuft",
    "error": "Fehler",
    "daily": "Tagesprognose",
    "hourly": "Stundenprognose"
}
STATUS_EN = {
    "not_checked": "Not checked yet",
    "complete": "Complete",
    "recorder_complete": "Recorder data complete",
    "recorder_incomplete": "Recorder data incomplete",
    "recorder_not_loaded": "Recorder not enabled",
    "recorder_entity_excluded": "Sensor excluded from Recorder",
    "recorder_error": "Failed to retrieve Recorder data",
    "intensity_72h_complete": "72-hour precipitation intensity history complete",
    "intensity_72h_incomplete": "72-hour precipitation intensity history incomplete",
    "intensity_sensor_unavailable": "Precipitation intensity sensor unavailable",
    "sensor_not_configured": "No precipitation sensor selected",
    "weather_unconfigured": "No weather entity selected",
    "weather_updating": "Updating weather",
    "weather_unavailable": "Weather entity unavailable",
    "forecast_incomplete": "Forecast incomplete",
    "forecast_unavailable": "Forecast unavailable",
    "hourly_incomplete": "Hourly forecast incomplete",
    "daily_incomplete": "Daily forecast incomplete",
    "hourly_unavailable": "Hourly forecast unavailable",
    "daily_unavailable": "Daily forecast unavailable",
    "incomplete": "Data incomplete",
    "ready": "Data complete",
    "unavailable": "Unavailable",
    "allowed": "Watering permitted",
    "raining": "Currently raining",
    "rain_3d_limit": "Historical precipitation limit reached",
    "rain_today_limit": "Today's precipitation limit reached",
    "temperature_limit": "Temperature threshold reached",
    "invalid_precipitation": "Invalid precipitation value",
    "invalid_parameters": "Invalid calculation parameters",
    "rain_or_unknown": "Rain or unknown rain status",
    "rain_sources_disagree": "Rain sensor and weather entity disagree",
    "automatic_disabled": "Automatic watering disabled",
    "no_valves": "No valves configured",
    "calendar_excluded": "Day or month excluded",
    "already_running": "Watering already running",
    "already_watered_today": "Already watered automatically today",
    "not_eligible": "Start conditions not met",
    "start_failed": "Start failed",
    "stop_command_failed": "Switch-off command failed",
    "valve_not_off": "Valve already on or unavailable",
    "previous_start_requires_explicit_stop": "Explicitly stop previous start",
    "manual": "Manual",
    "auto": "Automatic",
    "idle": "Idle",
    "stopped": "Stopped",
    "starting": "Starting",
    "watering": "Watering in progress",
    "error": "Error",
    "daily": "Daily forecast",
    "hourly": "Hourly forecast"
}

ENTITY_DE = {
    "State": "Status", "Blocking reason": "Sperrgrund",
    "Computed watering duration": "Berechnete Bewässerungsdauer",
    "Planned watering duration": "Geplante Bewässerungsdauer",
    "Remaining watering duration": "Restlaufzeit",
    "Daily forecast maximum temperature": "Maximale Tagesprognosetemperatur",
    "Forecast precipitation today": "Heutige Regenprognose",
    "Mean precipitation last three days": "Regenmittelwert letzte drei Tage",
    "Weather data quality": "Wetterdatenqualität",
    "Temperature factor": "Temperaturfaktor",
    "Today precipitation factor": "Heutiger Regenfaktor",
    "Historical precipitation factor": "Historischer Regenfaktor",
    "Last start": "Letzter Start", "Last end": "Letztes Ende",
    "Next scheduled start": "Nächster geplanter Start",
    "Configuration": "Konfiguration", "Last action": "Letzte Aktion",
    "Watering": "Bewässerung", "Automatic watering allowed": "Automatik zulässig",
    "Currently raining": "Aktueller Regen",
    "Base watering duration": "Basisberegnungszeit",
    "Daily precipitation limit": "Grenzwert Tagesniederschlag",
    "3-day precipitation limit": "Grenzwert Drei-Tage-Niederschlag",
    "Lower temperature threshold": "Untere Temperaturgrenze",
    "Upper temperature threshold": "Obere Temperaturgrenze",
    "Maximum safety runtime": "Maximale Laufzeit",
    "Scheduled start time": "Geplante Startzeit",
    "Precipitation sensor type": "Art der Niederschlagsmessung",
    "Automatic watering": "Automatische Bewässerung",
    "Start watering": "Bewässerung starten",
    "Stop watering": "Bewässerung stoppen",
    "Reset today": "Heutigen Laufstatus zurücksetzen",
    "Manual start": "Manueller Start",
    "Immediate stop": "Sofort-Stopp",
}



# Dynamic event records remain stored in English for stable diagnostics.
# The native event sensor localizes its DISPLAY state only; raw history
# and raw_code attributes continue to expose the original values.
EVENT_EXACT_DE = {
    "Today's watering markers reset by administrator": "Heutiger Laufstatus zurückgesetzt",
    "Nonexistent local start time: skipped": "Nicht existierende lokale Startzeit übersprungen",
    "Start failed; actuators may remain on. Use explicit Stop or external controls.": (
        "Start fehlgeschlagen; Aktor eventuell eingeschaltet. "
        "Bitte ausdrücklich stoppen oder extern bedienen."
    ),
    "Interrupted run not resumed; external shutdown is the user's responsibility": (
        "Unterbrochener Lauf nicht fortgesetzt; externe Abschaltung erforderlich"
    ),
    "WetSoil unloaded; actuator state left unchanged. External safety required.": (
        "Integration entladen; Aktor unverändert. Externe Absicherung erforderlich."
    ),
    "Predecessor missing: automatic irrigation disabled": (
        "Vorgänger fehlt: Automatische Bewässerung deaktiviert"
    ),
    "Predecessor deleted: automatic irrigation disabled": (
        "Vorgänger gelöscht: Automatische Bewässerung deaktiviert"
    ),
}
EVENT_PREFIX_DE = {
    "Automatic watering skipped: ": "Automatischer Start übersprungen: ",
    "Watering started: ": "Bewässerung gestartet: ",
    "WetSoil run stopped: ": "Bewässerung beendet: ",
}
STOP_REASON_DE = {"manual_stop": "Manueller Stopp", "complete": "Regulär beendet"}
STOP_REASON_EN = {"manual_stop": "Manual stop", "complete": "Completed"}


def event_text(value: str | None, language: str) -> str | None:
    """Render user-facing event text without rewriting stored event records."""
    if value is None:
        return None
    german = language.lower().startswith("de")
    if german:
        exact = EVENT_EXACT_DE.get(value)
        if exact is not None:
            return exact
    for prefix, translation in EVENT_PREFIX_DE.items():
        if not value.startswith(prefix):
            continue
        detail = value[len(prefix):]
        if prefix == "WetSoil run stopped: ":
            details = STOP_REASON_DE if german else STOP_REASON_EN
            description = details.get(detail, status_text(detail, language))
        elif prefix == "Automatic watering skipped: ":
            description = status_text(detail, language)
        else:
            description = detail
        if german:
            return translation + description
        return prefix + description
    return status_text(value, language)


def language_for(hass) -> str:
    code = getattr(getattr(hass, "config", None), "language", "en") or "en"
    return "de" if code.lower().startswith("de") else "en"


def status_text(code: str | None, language: str) -> str | None:
    if code is None:
        return None
    mapping = STATUS_DE if language.lower().startswith("de") else STATUS_EN
    if code in mapping:
        return mapping[code]
    if ":" in code:
        prefix, detail = code.split(":", 1)
        if prefix in mapping:
            return f"{mapping[prefix]}: {detail}"
    return code


def name_text(name: str, language: str) -> str:
    return ENTITY_DE.get(name, name) if language.lower().startswith("de") else name
