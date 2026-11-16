"""German/English user-facing labels; internal machine codes remain unchanged."""
from __future__ import annotations

STATUS_DE = {
    "idle": "Bereit", "starting": "Startet", "watering": "Bewässerung läuft",
    "stopped": "Gestoppt", "error": "Fehler", "ready": "Daten vollständig",
    "incomplete": "Daten unvollständig", "not_checked": "Noch nicht geprüft",
    "unavailable": "Nicht verfügbar", "weather_unavailable": "Wetterdaten nicht verfügbar",
    "weather_unconfigured": "Keine Wetter-Entity ausgewählt",
    "weather_updating": "Wetterdaten werden aktualisiert",
    "forecast_incomplete": "Wetterprognose unvollständig",
    "intensity_72h_complete": "Niederschlagsintensität für 72 Stunden vollständig ausgewertet",
    "intensity_72h_incomplete": "Niederschlagsintensität für 72 Stunden unvollständig",
    "intensity_sensor_unavailable": "Niederschlagsintensitätssensor nicht verfügbar",
    "recorder_not_loaded": "Recorder nicht aktiviert",
    "recorder_complete": "Recorder-Daten vollständig",
    "recorder_incomplete": "Recorder-Daten unvollständig",
    "recorder_entity_excluded": "Sensor von Recorder ausgeschlossen",
    "recorder_error": "Recorder-Abfrage fehlgeschlagen",
    "sensor_not_configured": "Kein Niederschlagssensor ausgewählt",
    "complete": "Vollständig", "allowed": "Bewässerung zulässig",
    "raining": "Regen erkannt", "rain_or_unknown": "Regen oder unbekannter Regenstatus",
    "rain_sources_disagree": "Regensensor und Wetter-Entity widersprechen sich",
    "weather_unavailable": "Wetterdaten nicht verfügbar",
    "rain_today_limit": "Regenlimit für heute erreicht",
    "rain_3d_limit": "Historisches Regenlimit erreicht",
    "temperature_limit": "Temperaturgrenze erreicht",
    "invalid_precipitation": "Ungültiger Niederschlagswert",
    "invalid_parameters": "Ungültige Berechnungsparameter",
    "automatic_disabled": "Automatik deaktiviert",
    "no_valves": "Keine Ventile konfiguriert",
    "calendar_excluded": "Wochentag oder Monat nicht zulässig",
    "already_running": "Bewässerung läuft bereits",
    "already_watered_today": "Heute bereits automatisch bewässert",
    "not_eligible": "Startbedingungen nicht erfüllt",
    "manual": "Manuell", "auto": "Automatisch",
}
STATUS_EN = {
    "idle": "Idle", "starting": "Starting", "watering": "Watering",
    "stopped": "Stopped", "error": "Error", "ready": "Data complete",
    "incomplete": "Data incomplete", "not_checked": "Not checked yet",
    "unavailable": "Unavailable", "weather_unavailable": "Weather unavailable",
    "weather_unconfigured": "No weather entity selected",
    "weather_updating": "Updating weather",
    "forecast_incomplete": "Forecast incomplete",
    "intensity_72h_complete": "72-hour precipitation intensity history complete",
    "intensity_72h_incomplete": "72-hour precipitation intensity history incomplete",
    "intensity_sensor_unavailable": "Precipitation intensity sensor unavailable",
    "recorder_not_loaded": "Recorder not enabled",
    "recorder_complete": "Recorder data complete",
    "recorder_incomplete": "Recorder data incomplete",
    "recorder_entity_excluded": "Sensor excluded from Recorder",
    "recorder_error": "Recorder query failed",
    "sensor_not_configured": "No precipitation sensor selected",
    "complete": "Complete", "allowed": "Watering permitted",
    "raining": "Raining", "rain_or_unknown": "Rain or unknown rain state",
    "rain_sources_disagree": "Rain sensor and weather entity disagree",
    "rain_today_limit": "Daily precipitation limit reached",
    "rain_3d_limit": "Historical precipitation limit reached",
    "temperature_limit": "Temperature limit reached",
    "invalid_precipitation": "Invalid precipitation",
    "invalid_parameters": "Invalid parameters",
    "automatic_disabled": "Automation disabled",
    "no_valves": "No valves configured",
    "calendar_excluded": "Day or month excluded",
    "already_running": "Already watering",
    "already_watered_today": "Already watered automatically today",
    "not_eligible": "Start conditions not met",
    "manual": "Manual", "auto": "Automatic",
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
}


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
