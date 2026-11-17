"""Localized native sensor labels retain diagnostic machine codes."""
import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "custom_components/wetsoil"
spec = importlib.util.spec_from_file_location("wetsoil_native_locales", BASE/"text_labels.py")
labels = importlib.util.module_from_spec(spec)
spec.loader.exec_module(labels)


def test_german_statuses_are_human_readable():
    assert labels.status_text("intensity_72h_complete", "de") == (
        "72 Stunden Niederschlagsintensität vollständig ausgewertet"
    )
    assert labels.status_text("automatic_disabled", "de") == "Automatik deaktiviert"
    assert labels.status_text("rain_today_limit", "de") == "Heutiger Niederschlagsgrenzwert erreicht"


def test_english_and_fallback_behaviour():
    assert labels.status_text("intensity_72h_complete", "en").startswith("72-hour")
    assert labels.status_text("rain_3d_limit", "fr") == "Historical precipitation limit reached"
    assert labels.status_text("custom_code", "de") == "custom_code"
    assert labels.status_text(None, "de") is None


def test_native_name_translation_is_not_coupled_to_storage_key():
    assert labels.name_text("Scheduled start time", "de") == "Geplante Startzeit"
    assert labels.name_text("Precipitation sensor type", "de") == "Art der Niederschlagsmessung"
    assert labels.name_text("Scheduled start time", "en") == "Scheduled start time"



def test_native_statuses_match_all_approved_card_translations():
    """Native and frontend known codes must never drift again."""
    import json
    import re

    frontend = (
        Path(__file__).resolve().parents[1]
        / "custom_components/wetsoil/frontend/wetsoil-card.js"
    ).read_text(encoding="utf-8")
    section = frontend.split("const LANG = ", 1)[1].split(
        "\n};\n\nconst STYLES", 1
    )[0] + "\n}"
    parsable = re.sub(r"([{,]\s*)([A-Za-z_$][\w$]*):", r'\1"\2":', section)
    card = json.loads(parsable)
    assert labels.STATUS_DE == card["de"]["messages"]
    assert labels.STATUS_EN == card["en"]["messages"]
    assert set(card["de"]["messages"]) == set(card["en"]["messages"])


def test_native_button_names_use_approved_card_labels():
    assert labels.name_text("Manual start", "de") == "Manueller Start"
    assert labels.name_text("Immediate stop", "de") == "Sofort-Stopp"
    assert labels.name_text("Manual start", "en") == "Manual start"
    assert labels.name_text("Immediate stop", "fr") == "Immediate stop"


def test_native_events_localized_without_changing_raw_codes():
    assert labels.event_text(
        "Automatic watering skipped: automatic_disabled", "de"
    ) == "Automatischer Start übersprungen: Automatik deaktiviert"
    assert labels.event_text(
        "Automatic watering skipped: automatic_disabled", "en"
    ) == "Automatic watering skipped: Automatic watering disabled"
    assert labels.event_text(
        "WetSoil run stopped: complete", "de"
    ) == "Bewässerung beendet: Regulär beendet"
    assert labels.event_text(
        "Watering started: 1800s", "de"
    ) == "Bewässerung gestartet: 1800s"
    assert labels.event_text(
        "Predecessor missing: automatic irrigation disabled", "de"
    ) == "Vorgänger fehlt: Automatische Bewässerung deaktiviert"
    assert labels.event_text(None, "de") is None
    assert labels.event_text("custom_event_code", "de") == "custom_event_code"
